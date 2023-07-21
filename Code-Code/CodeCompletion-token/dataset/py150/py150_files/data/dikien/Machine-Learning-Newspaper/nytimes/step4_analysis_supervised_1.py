# -*- coding: UTF-8 -*-

from sklearn.metrics import accuracy_score
from time import time
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import preprocessing
from sklearn.feature_selection import SelectPercentile, f_classif, chi2
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.ensemble import AdaBoostClassifier
from sklearn.naive_bayes import BernoulliNB
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn import cross_validation
from sklearn import metrics
import matplotlib.pyplot as plt
from itertools import cycle

def plot(nFeatures, data):
    colors = cycle('rgbcmykw')
    algorithm = sorted(data)

    fig = plt.figure()
    ax = fig.add_subplot(111)

    for j, c in zip(algorithm, colors):
        # for j in algorithm:
        #     plt.scatter(nFeatures, data[j], label=j)
        ax.plot(nFeatures, data[j], label=j, color=c)
        ax.scatter(nFeatures, data[j], color=c)

    plt.xlabel("#-Features(SelectPercentile)")
    plt.ylabel("Accuracy")
    plt.title("Accuracy vs #-Features for different classifiers")
    # ax.set_xscale("log")
    box = ax.get_position()
    ax.set_position([box.x0, box.y0 + box.height * 0.3,
                    box.width, box.height * 0.7])
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=3)

    plt.legend(loc=4)
    plt.show()


def preprocess(article_file, lable_file, k):

    features = pickle.load(open(article_file))
    features = np.array(features)

    # transform non-numerical labels (as long as they are hashable and comparable) to numerical labels
    lables = pickle.load(open(lable_file))
    le = preprocessing.LabelEncoder()
    le.fit(lables)
    lables = le.transform(lables)
    # print le.inverse_transform([0])

    ### text vectorization--go from strings to lists of numbers
    vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5, min_df=1,
                                 stop_words='english')
    features_train_transformed = vectorizer.fit_transform(features)

    # selector : SelectPercentile
    selector = SelectPercentile(f_classif, percentile=k)
    selector.fit(features_train_transformed, lables)

    # selector : SelectKBest
    # selector = SelectKBest(k=k)
    # selector.fit(features_train_transformed, lables)

    # selector : chi2
    # selector = SelectPercentile(score_func=chi2)
    # selector.fit(features_train_transformed, lables)

    features_train_transformed = selector.transform(features_train_transformed).toarray()

    return features_train_transformed, lables, vectorizer, selector, le, features

# nFeatures = np.arange(50, 1000, 50)
nFeatures = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

data = {}

for k in nFeatures:

    features, labels, vectorizer, selector, le, features_data = preprocess("pkl/article_2_people.pkl", "pkl/lable_2_people.pkl", k)
    features_train, features_test, labels_train, labels_test = cross_validation.train_test_split(features, labels, test_size=0.1, random_state=42)

    for name, clf in [
        ('AdaBoostClassifier', AdaBoostClassifier(algorithm='SAMME.R')),
        ('BernoulliNB', BernoulliNB(alpha=1)),
        ('GaussianNB', GaussianNB()),
        ('DecisionTreeClassifier', DecisionTreeClassifier(min_samples_split=100)),
        ('KNeighborsClassifier', KNeighborsClassifier(n_neighbors=50, algorithm='ball_tree')),
        ('RandomForestClassifier', RandomForestClassifier(min_samples_split=100)),
        ('SVC', SVC(kernel='linear', C=1))
    ]:

        if not data.has_key(name):
            data[name] = []

        print "*" * 100
        print('Method: {}'.format(name) + ' the number of feature is {}'.format(k))

        # Fit on the whole data:
        t0 = time()
        clf.fit(features_train, labels_train)
        print ("training time:", round(time()-t0, 3), "s")

        # Predict on the whole data:
        y_pred = clf.predict(features_test)
        print ("predicting time:", round(time()-t0, 3), "s")

        score_accuracy = accuracy_score(y_pred, labels_test, normalize=True)
        # score_f1 = metrics.f1_score(y_pred, labels_test)
        print('accuracy score on training: {}'.format(score_accuracy))
        # print('f1 score on training: {}'.format(score_f1))
        # print metrics.classification_report(y_pred, labels_test)
        # print metrics.confusion_matrix(y_pred, labels_test)
        # print "validation:", metrics.explained_variance_score(y_pred, labels_test)
        print "*"* 100

        data[name].append(score_accuracy)


plot(nFeatures, data)