
from jobman import DD, expand, flatten

import pynet.layer as layer
from pynet.model import *
from pynet.layer import *
from pynet.datasets.mnist import Mnist, Mnist_Blocks
import pynet.datasets.spec as spec
import pynet.datasets.mnist as mnist
import pynet.datasets.transfactor as tf
import pynet.datasets.mapping as mapping
import pynet.learning_method as learning_methods
from pynet.learning_rule import LearningRule
from pynet.log import Log
from pynet.train_object import TrainObject
from pynet.cost import Cost
import pynet.datasets.preprocessor as preproc
import pynet.datasets.dataset_noise as noisy
import pynet.layer_noise as layer_noise
import cPickle
import os

import theano
from theano.sandbox.cuda.var import CudaNdarraySharedVariable
floatX = theano.config.floatX

class AE:

    def __init__(self, state):
        self.state = state

    def run(self):
        log = self.build_log()
        dataset = self.build_dataset()

        learning_rule = self.build_learning_rule()
        model = self.build_model(dataset)
        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                model = model)
        train_obj.run()


    def build_log(self, save_to_database=None, id=None):
        log = Log(experiment_name = id is not None and '%s_%s'%(self.state.log.experiment_name,id) \
                                    or self.state.log.experiment_name,
                description = self.state.log.description,
                save_outputs = self.state.log.save_outputs,
                save_learning_rule = self.state.log.save_learning_rule,
                save_model = self.state.log.save_model,
                save_epoch_error = self.state.log.save_epoch_error,
                save_to_database = save_to_database)
        return log


    def build_dataset(self):
        dataset = None

        preprocessor = None if self.state.dataset.preprocessor.type is None else \
                       getattr(preproc, self.state.dataset.preprocessor.type)()

        # if self.state.dataset.noise.type == 'BlackOut' or self.state.dataset.noise.type == 'MaskOut':
        #     noise = None if self.state.dataset.noise.type is None else \
        #         getattr(noisy, self.state.dataset.noise.type)(ratio=self.state.dataset.noise.ratio)
        # else:
        #     noise = getattr(noisy, self.state.dataset.noise.type)()
        noise = None if self.state.dataset.dataset_noise.type is None else \
                getattr(noisy, self.state.dataset.dataset_noise.type)()

        if self.state.dataset.preprocessor.type == 'Scale':
            preprocessor.max = self.state.dataset.preprocessor.global_max
            preprocessor.min = self.state.dataset.preprocessor.global_min
            preprocessor.buffer = self.state.dataset.preprocessor.buffer
            preprocessor.scale_range = self.state.dataset.preprocessor.scale_range

        if self.state.dataset.type == 'Mnist':
            dataset = Mnist(train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                            preprocessor = preprocessor,
                            noise = noise,
                            batch_size = self.state.dataset.batch_size,
                            num_batches = self.state.dataset.num_batches,
                            iter_class = self.state.dataset.iter_class,
                            rng = self.state.dataset.rng)
            train = dataset.get_train()
            dataset.set_train(train.X, train.X)
            valid = dataset.get_valid()
            dataset.set_valid(valid.X, valid.X)
            test = dataset.get_test()
            dataset.set_test(test.X, test.X)

        elif self.state.dataset.type[:12] == 'Mnist_Blocks':
            dataset = getattr(mnist, self.state.dataset.type)(
                            feature_size = self.state.dataset.feature_size,
                            target_size = self.state.dataset.feature_size,
                            train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                            preprocessor = preprocessor,
                            noise = noise,
                            batch_size = self.state.dataset.batch_size,
                            num_batches = self.state.dataset.num_batches,
                            iter_class = self.state.dataset.iter_class,
                            rng = self.state.dataset.rng)

        elif self.state.dataset.type[:4] == 'P276':
            dataset = getattr(spec, self.state.dataset.type)(
                            train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                            preprocessor = preprocessor,
                            noise = noise,
                            batch_size = self.state.dataset.batch_size,
                            num_batches = self.state.dataset.num_batches,
                            iter_class = self.state.dataset.iter_class,
                            rng = self.state.dataset.rng)
            train = dataset.get_train()
            dataset.set_train(train.X, train.X)
            valid = dataset.get_valid()
            dataset.set_valid(valid.X, valid.X)
            test = dataset.get_test()
            dataset.set_test(test.X, test.X)

        elif self.state.dataset.type[:5] == 'Laura':
            dataset = getattr(spec, self.state.dataset.type)(
                            feature_size = self.state.dataset.feature_size,
                            target_size = self.state.dataset.feature_size,
                            train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                            preprocessor = preprocessor,
                            noise = noise,
                            batch_size = self.state.dataset.batch_size,
                            num_batches = self.state.dataset.num_batches,
                            iter_class = self.state.dataset.iter_class,
                            rng = self.state.dataset.rng)

        elif self.state.dataset.type[:18] == 'TransFactor_Blocks':
            dataset = getattr(tf, self.state.dataset.type)(
                            feature_size = self.state.dataset.feature_size,
                            target_size = self.state.dataset.feature_size,
                            train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                            preprocessor = preprocessor,
                            noise = noise,
                            batch_size = self.state.dataset.batch_size,
                            num_batches = self.state.dataset.num_batches,
                            iter_class = self.state.dataset.iter_class,
                            rng = self.state.dataset.rng)

        elif self.state.dataset.type[:11] == 'TransFactor':
            dataset = getattr(tf, self.state.dataset.type)(
                            # feature_size = self.state.dataset.feature_size,
                            # target_size = self.state.dataset.feature_size,
                            train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                            preprocessor = preprocessor,
                            noise = noise,
                            batch_size = self.state.dataset.batch_size,
                            num_batches = self.state.dataset.num_batches,
                            iter_class = self.state.dataset.iter_class,
                            rng = self.state.dataset.rng)
            train = dataset.get_train()
            dataset.set_train(train.X, train.X)
            valid = dataset.get_valid()
            dataset.set_valid(valid.X, valid.X)
            test = dataset.get_test()
            dataset.set_test(test.X, test.X)



        return dataset


    def build_learning_method(self):

        if self.state.learning_method.type == 'SGD':
            learn_method = getattr(learning_methods,
                           self.state.learning_method.type)(
                           learning_rate = self.state.learning_method.learning_rate,
                           momentum = self.state.learning_method.momentum)

        elif self.state.learning_method.type == 'AdaGrad':
            learn_method = getattr(learning_methods,
                           self.state.learning_method.type)(
                           learning_rate = self.state.learning_method.learning_rate,
                           momentum = self.state.learning_method.momentum)

        elif self.state.learning_method.type == 'AdaDelta':
            learn_method = getattr(learning_methods,
                           self.state.learning_method.type)(
                           rho = self.state.learning_method.rho,
                           eps = self.state.learning_method.eps)

        else:
            raise TypeError("not SGD, AdaGrad or AdaDelta")


        return learn_method


    def build_learning_rule(self):
        learning_rule = LearningRule(max_col_norm = self.state.learning_rule.max_col_norm,
                                    L1_lambda = self.state.learning_rule.L1_lambda,
                                    L2_lambda = self.state.learning_rule.L2_lambda,
                                    training_cost = Cost(type = self.state.learning_rule.cost),
                                    stopping_criteria = {'max_epoch' : self.state.learning_rule.stopping_criteria.max_epoch,
                                                        'epoch_look_back' : self.state.learning_rule.stopping_criteria.epoch_look_back,
                                                        'cost' : Cost(type=self.state.learning_rule.stopping_criteria.cost),
                                                        'percent_decrease' : self.state.learning_rule.stopping_criteria.percent_decrease})
        return learning_rule


    def build_one_hid_model(self, input_dim):
        model = AutoEncoder(input_dim=input_dim, rand_seed=self.state.model.rand_seed)

        h1_noise = None if self.state.hidden1.layer_noise.type is None else \
              getattr(layer_noise, self.state.hidden1.layer_noise.type)()

        if self.state.hidden1.layer_noise.type in ['BlackOut', 'MaskOut', 'BatchOut']:
            h1_noise.ratio = self.state.hidden1.layer_noise.ratio


        elif self.state.hidden1.layer_noise.type == 'Gaussian':
            h1_noise.std = self.state.hidden1.layer_noise.std
            h1_noise.mean = self.state.hidden1.layer_noise.mean

        hidden1 = getattr(layer, self.state.hidden1.type)(dim=self.state.hidden1.dim,
                                                        name=self.state.hidden1.name,
                                                        dropout_below=self.state.hidden1.dropout_below,
                                                        noise=h1_noise)
                                                        # blackout_below=self.state.hidden1.blackout_below)
        model.add_encode_layer(hidden1)
        h1_mirror = getattr(layer, self.state.h1_mirror.type)(dim=input_dim,
                                                            name=self.state.h1_mirror.name,
                                                            W=hidden1.W.T,
                                                            dropout_below=self.state.h1_mirror.dropout_below)
                                                            # blackout_below=self.state.h1_mirror.blackout_below)
        model.add_decode_layer(h1_mirror)
        return model

    def build_one_hid_model_no_transpose(self, input_dim):
        model = AutoEncoder(input_dim = input_dim, rand_seed=self.state.model.rand_seed)
        hidden1 = getattr(layer, self.state.hidden1.type)(dim=self.state.hidden1.dim,
                                                        name=self.state.hidden1.name,
                                                        dropout_below=self.state.hidden1.dropout_below,
                                                        noise=None if self.state.hidden1.layer_noise is None else \
                                                              getattr(layer_noise, self.state.hidden1.layer_noise)())
                                                        # blackout_below=self.state.hidden1.blackout_below)
        model.add_encode_layer(hidden1)
        h1_mirror = getattr(layer, self.state.h1_mirror.type)(dim=input_dim,
                                                            name=self.state.h1_mirror.name,
                                                            dropout_below=self.state.h1_mirror.dropout_below)
                                                            # blackout_below=self.state.h1_mirror.blackout_below)
        model.add_decode_layer(h1_mirror)
        return model

    def build_two_hid_model(self, input_dim):
        model = AutoEncoder(input_dim=input_dim, rand_seed=self.state.model.rand_seed)
        hidden1 = getattr(layer, self.state.hidden1.type)(dim=self.state.hidden1.dim,
                                                        name=self.state.hidden1.name,
                                                        dropout_below=self.state.hidden1.dropout_below,
                                                        noise=None if self.state.hidden1.layer_noise is None else \
                                                              getattr(layer_noise, self.state.hidden1.layer_noise)())
                                                        # blackout_below=self.state.hidden1.blackout_below)
        model.add_encode_layer(hidden1)

        hidden2 = getattr(layer, self.state.hidden2.type)(dim=self.state.hidden2.dim,
                                                        name=self.state.hidden2.name,
                                                        dropout_below=self.state.hidden2.dropout_below,
                                                        noise=None if self.state.hidden2.layer_noise is None else \
                                                              getattr(layer_noise, self.state.hidden2.layer_noise)())
                                                        # blackout_below=self.state.hidden2.blackout_below)
        model.add_encode_layer(hidden2)

        hidden2_mirror = getattr(layer, self.state.h2_mirror.type)(dim=self.state.hidden1.dim,
                                                                name=self.state.h2_mirror.name,
                                                                dropout_below=self.state.h2_mirror.dropout_below,
                                                                # blackout_below=self.state.h2_mirror.blackout_below,
                                                                W = hidden2.W.T)
        model.add_decode_layer(hidden2_mirror)

        hidden1_mirror = getattr(layer, self.state.h1_mirror.type)(dim=input_dim,
                                                                name=self.state.h1_mirror.name,
                                                                dropout_below=self.state.h1_mirror.dropout_below,
                                                                # blackout_below=self.state.h1_mirror.blackout_below,
                                                                W = hidden1.W.T)
        model.add_decode_layer(hidden1_mirror)
        return model


    def build_database(self, dataset, learning_rule, learning_method, model):
        save_to_database = {'name' : self.state.log.save_to_database_name,
                            'records' : {'Dataset'          : dataset.__class__.__name__,
                                         'max_col_norm'     : learning_rule.max_col_norm,
                                         'Weight_Init_Seed' : model.rand_seed,
                                         'Dropout_Below'    : str([layer.dropout_below for layer in model.layers]),
                                         'Learning_Method'  : learning_method.__class__.__name__,
                                         'Batch_Size'       : dataset.batch_size,
                                         'Dataset_Noise'    : dataset.noise.__class__.__name__,
                                         'Dataset_Dir'      : dataset.data_dir,
                                         'Feature_Size'     : dataset.feature_size(),
                                         'nblocks'          : dataset.nblocks(),
                                         'Layer_Types'      : str([layer.__class__.__name__ for layer in model.layers]),
                                         'Layer_Dim'        : str([layer.dim for layer in model.layers]),
                                         'Preprocessor'     : dataset.preprocessor.__class__.__name__,
                                         'Training_Cost'    : learning_rule.cost.type,
                                         'Stopping_Cost'    : learning_rule.stopping_criteria['cost'].type}
                            }

        if learning_method.__class__.__name__ == "SGD":
            save_to_database["records"]["Learning_rate"] = learning_method.learning_rate
            save_to_database["records"]["Momentum"]    = learning_method.momentum
        elif learning_method.__class__.__name__ == "AdaGrad":
            save_to_database["records"]["Learning_rate"] = learning_method.learning_rate
            save_to_database["records"]["Momentum"]    = learning_method.momentum
        elif learning_method.__class__.__name__ == "AdaDelta":
            save_to_database["records"]["rho"] = learning_method.rho
            save_to_database["records"]["eps"] = learning_method.eps
        else:
            raise TypeError("not SGD, AdaGrad or AdaDelta")

        layer_noise = []
        layer_noise_params = []
        for layer in model.layers:
            layer_noise.append(layer.noise.__class__.__name__)
            if layer.noise.__class__.__name__ in ['BlackOut', 'MaskOut', 'BatchOut']:
                layer_noise_params.append(layer.noise.ratio)

            elif layer.noise.__class__.__name__ is 'Gaussian':
                layer_noise_params.append((layer.noise.mean, layer.noise.std))

            else:
                layer_noise_params.append(None)

        save_to_database["records"]["Layer_Noise"] = str(layer_noise)
        save_to_database["records"]["Layer_Noise_Params"] = str(layer_noise_params)

        return save_to_database

class AE_Testing(AE):

    def __init__(self, state):
        self.state = state


    def run(self):

        dataset = self.build_dataset()
        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()

        model = self.build_one_hid_model(dataset.feature_size())

        if self.state.log.save_to_database_name:
            database = self.build_database(dataset, learning_rule, learn_method, model)
            log = self.build_log(database)

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)
        train_obj.run()

        # fine tuning
        log.info("fine tuning")
        train_obj.model.layers[0].dropout_below = None
        train_obj.setup()
        train_obj.run()

class Laura_Mapping(AE):
    def __init__(self, state):
        self.state = state

    def run(self):
        preprocessor = None if self.state.dataset.preprocessor is None else \
                       getattr(preproc, self.state.dataset.preprocessor)()
        dataset = getattr(mapping, self.state.dataset.type)(feature_size = self.state.dataset.feature_size,
                                                            target_size = self.state.dataset.target_size,
                                                            train_valid_test_ratio = self.state.dataset.train_valid_test_ratio,
                                                            preprocessor = preprocessor,
                                                            batch_size = self.state.dataset.batch_size,
                                                            num_batches = self.state.dataset.num_batches,
                                                            iter_class = self.state.dataset.iter_class,
                                                            rng = self.state.dataset.rng)
        model = MLP(input_dim = self.state.dataset.feature_size, rand_seed=self.state.model.rand_seed)
        hidden1 = getattr(layer, self.state.hidden1.type)(dim=self.state.hidden1.dim,
                                                        name=self.state.hidden1.name,
                                                        dropout_below=self.state.hidden1.dropout_below)
        model.add_layer(hidden1)

        hidden2 = getattr(layer, self.state.hidden2.type)(dim=self.state.hidden2.dim,
                                                        name=self.state.hidden2.name,
                                                        dropout_below=self.state.hidden2.dropout_below)
        model.add_layer(hidden2)

        output = getattr(layer, self.state.output.type)(dim=self.state.output.dim,
                                                        name=self.state.output.name,
                                                        dropout_below=self.state.output.dropout_below)
        model.add_layer(output)

        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()
        database = self.build_database(dataset, learning_rule, learn_method, model)
        log = self.build_log(database)

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)

        train_obj.run()


class Laura(AE):

    def __init__(self, state):
        self.state = state


    def run(self):

        dataset = self.build_dataset()
        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()

        # import pdb
        # pdb.set_trace()

        if self.state.num_layers == 1:
            model = self.build_one_hid_model(dataset.feature_size())
        elif self.state.num_layers == 2:
            model = self.build_two_hid_model(dataset.feature_size())
        else:
            raise ValueError()

        database = self.build_database(dataset, learning_rule, learn_method, model)
        log = self.build_log(database)

        dataset.log = log

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)

        train_obj.run()

        log.info("Fine Tuning")

        for layer in train_obj.model.layers:
            layer.dropout_below = None
            layer.noise = None

        train_obj.setup()
        train_obj.run()

class Laura_Continue(AE):

    def __init__(self, state):
        self.state = state


    def build_model(self):
        with open(os.environ['PYNET_SAVE_PATH'] + '/log/'
                    + self.state.hidden1.model + '/model.pkl') as f1:
            model = cPickle.load(f1)
        return model

    def run(self):

        dataset = self.build_dataset()
        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()

        model = self.build_model()

        if self.state.fine_tuning_only:
            for layer in model.layers:
                layer.dropout_below = None
                layer.noise = None
            print "Fine Tuning Only"

        if self.state.log.save_to_database_name:
            database = self.build_database(dataset, learning_rule, learn_method, model)
            database['records']['model'] = self.state.hidden1.model
            log = self.build_log(database)

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)

        train_obj.run()

        if not self.state.fine_tuning_only:
            log.info("..Fine Tuning after Noisy Training")
            for layer in train_obj.model.layers:
                layer.dropout_below = None
                layer.noise = None
            train_obj.setup()
            train_obj.run()



class Laura_Two_Layers(AE):

    def __init__(self, state):
        self.state = state


    def build_model(self, input_dim):
        with open(os.environ['PYNET_SAVE_PATH'] + '/log/'
                    + self.state.hidden1.model + '/model.pkl') as f1:
            model1 = cPickle.load(f1)

        with open(os.environ['PYNET_SAVE_PATH'] + '/log/'
                    + self.state.hidden2.model + '/model.pkl') as f2:
            model2 = cPickle.load(f2)

        model = AutoEncoder(input_dim=input_dim)
        while len(model1.encode_layers) > 0:
            model.add_encode_layer(model1.pop_encode_layer())
        while len(model2.encode_layers) > 0:
            model.add_encode_layer(model2.pop_encode_layer())
        while len(model2.decode_layers) > 0:
            model.add_decode_layer(model2.pop_decode_layer())
        while len(model1.decode_layers) > 0:
            model.add_decode_layer(model1.pop_decode_layer())
        return model

    def run(self):

        dataset = self.build_dataset()
        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()

        model = self.build_model(dataset.feature_size())
        model.layers[0].dropout_below = self.state.hidden1.dropout_below

        if self.state.log.save_to_database_name:
            database = self.build_database(dataset, learning_rule, learn_method, model)
            database['records']['h1_model'] = self.state.hidden1.model
            database['records']['h2_model'] = self.state.hidden2.model
            log = self.build_log(database)

        log.info("Fine Tuning")
        for layer in model.layers:
            layer.dropout_below = None
            layer.noise = None

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)

        train_obj.run()

class Laura_Three_Layers(AE):
    def __init__(self, state):
        self.state = state


    def build_model(self, input_dim):
        with open(os.environ['PYNET_SAVE_PATH'] + '/log/'
                    + self.state.hidden1.model + '/model.pkl') as f1:
            model1 = cPickle.load(f1)

        with open(os.environ['PYNET_SAVE_PATH'] + '/log/'
                    + self.state.hidden2.model + '/model.pkl') as f2:
            model2 = cPickle.load(f2)

        with open(os.environ['PYNET_SAVE_PATH'] + '/log/'
                    + self.state.hidden3.model + '/model.pkl') as f3:
            model3 = cPickle.load(f3)

        model = AutoEncoder(input_dim=input_dim)

        model.add_encode_layer(model1.pop_encode_layer())
        model.add_encode_layer(model2.pop_encode_layer())
        model.add_encode_layer(model3.pop_encode_layer())
        model.add_decode_layer(model3.pop_decode_layer())
        model.add_decode_layer(model2.pop_decode_layer())
        model.add_decode_layer(model1.pop_decode_layer())

        return model

    def run(self):

        dataset = self.build_dataset()
        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()

        model = self.build_model(dataset.feature_size())

        model.layers[0].dropout_below = self.state.hidden1.dropout_below
        model.layers[1].dropout_below = self.state.hidden2.dropout_below
        model.layers[2].dropout_below = self.state.hidden3.dropout_below

        if self.state.log.save_to_database_name:
            database = self.build_database(dataset, learning_rule, learn_method, model)
            database['records']['h1_model'] = self.state.hidden1.model
            database['records']['h2_model'] = self.state.hidden2.model
            database['records']['h3_model'] = self.state.hidden3.model
            log = self.build_log(database)

        log.info("Fine Tuning")
        for layer in model.layers:
            layer.dropout_below = None
            layer.noise = None

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)
        train_obj.run()


class Laura_Two_Layers_No_Transpose(AE):

    def __init__(self, state):
        self.state = state


    def run(self):

        dataset = self.build_dataset()
        learning_rule = self.build_learning_rule()
        learn_method = self.build_learning_method()

        if self.state.num_layers == 1:
            model = self.build_one_hid_model_no_transpose(dataset.feature_size())
        else:
            raise ValueError()

        if self.state.log.save_to_database_name:
            database = self.build_database(dataset, learning_rule, learn_method, model)
            log = self.build_log(database)

        train_obj = TrainObject(log = log,
                                dataset = dataset,
                                learning_rule = learning_rule,
                                learning_method = learn_method,
                                model = model)

        train_obj.run()

        # fine tuning
        log.info("fine tuning")
        train_obj.model.layers[0].dropout_below = None
        train_obj.setup()
        train_obj.run()
