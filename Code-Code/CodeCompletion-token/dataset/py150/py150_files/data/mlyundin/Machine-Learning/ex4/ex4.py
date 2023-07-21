import scipy.io as sio
import numpy as np
from scipy.optimize import minimize

from common_functions import add_zero_feature, sigmoid, matrix_args_array_only

def sigmoid_gradient(z):
    return np.multiply(sigmoid(z), 1-sigmoid(z))

@matrix_args_array_only
def cf_nn(nn_params, input_layer_size, hidden_layer_size, num_labels, X, Y, lambda_coef):

    Theta1 = nn_params[0, :hidden_layer_size * (input_layer_size + 1)].reshape((hidden_layer_size, (input_layer_size + 1)))
    Theta2 = nn_params[0, hidden_layer_size * (input_layer_size + 1):].reshape((num_labels, (hidden_layer_size + 1)))

    m = Y.shape[1]
    Y = Y.A

    A_1 = X
    Z_2 = Theta1*A_1.T
    A_2 = sigmoid(Z_2)
    A_2 = add_zero_feature(A_2, axis=0)
    Z_3 = Theta2*A_2
    A_3 = sigmoid(Z_3)
    H = A_3.A

    J = np.sum(-Y*np.log(H) - (1-Y)*np.log(1-H))/m

    reg_J = 0.0
    reg_J += np.sum(np.power(Theta1, 2)[:, 1:])
    reg_J += np.sum(np.power(Theta2, 2)[:, 1:])

    J += reg_J*(float(lambda_coef)/(2*m))

    return J

@matrix_args_array_only
def gf_nn(nn_params, input_layer_size, hidden_layer_size, num_labels, X, Y, lambda_coef):

    Theta1 = nn_params[0, :hidden_layer_size * (input_layer_size + 1)].reshape((hidden_layer_size, (input_layer_size + 1)))
    Theta2 = nn_params[0, hidden_layer_size * (input_layer_size + 1):].reshape((num_labels, (hidden_layer_size + 1)))

    m = Y.shape[1]

    A_1 = X
    Z_2 = Theta1*A_1.T
    A_2 = sigmoid(Z_2)
    A_2 = add_zero_feature(A_2, axis=0)
    Z_3 = Theta2*A_2
    A_3 = sigmoid(Z_3)

    DELTA_3 = A_3 - Y
    DELTA_2 = np.multiply((Theta2.T*DELTA_3)[1:, :], sigmoid_gradient(Z_2))
    Theta1_grad = (DELTA_2 * A_1)/m
    Theta2_grad = (DELTA_3 * A_2.T)/m

    lambda_coef = float(lambda_coef)
    Theta1_grad[:, 1:] += (lambda_coef/m)*Theta1[:, 1:]
    Theta2_grad[:, 1:] += (lambda_coef/m)*Theta2[:, 1:]

    return np.concatenate((Theta1_grad.A1, Theta2_grad.A1))

def rand_initialize_weights(L_in, L_out):
    epsilon_init = 0.12
    return np.random.rand(L_out, 1 + L_in) * 2 * epsilon_init - epsilon_init

if __name__ == '__main__':
    data = sio.loadmat('ex4data1.mat')
    y = data['y']
    X = data['X']

    X = add_zero_feature(X)

    data = sio.loadmat('ex4weights.mat')
    Theta1 = data['Theta1']
    Theta2 = data['Theta2']

    nn_params = np.concatenate((Theta1.ravel(), Theta2.ravel()))

    input_layer_size  = 400
    hidden_layer_size = 25
    num_labels = 10
    m = len(y)

    Y = (np.arange(num_labels)[:, np.newaxis] == (y.T-1)).astype(float)

    for lambda_coef in (0, 1):
        print 'Cost function = {}, lambda = {}'.format(cf_nn(nn_params, input_layer_size, hidden_layer_size, num_labels, X, Y, lambda_coef), lambda_coef)

    initial_Theta1 = rand_initialize_weights(input_layer_size, hidden_layer_size)
    initial_Theta2 = rand_initialize_weights(hidden_layer_size, num_labels)

    initial_nn_params = np.concatenate((initial_Theta1.ravel(), initial_Theta2.ravel()))

    res = minimize(cf_nn, initial_nn_params, method='L-BFGS-B', jac=gf_nn, options={'disp': True, 'maxiter':100},
                        args=(input_layer_size, hidden_layer_size, num_labels, X, Y, lambda_coef)).x

    Theta1 = res[:hidden_layer_size * (input_layer_size + 1)].reshape((hidden_layer_size, (input_layer_size + 1)))
    Theta2 = res[hidden_layer_size * (input_layer_size + 1):].reshape((num_labels, (hidden_layer_size + 1)))


    h1 = sigmoid(np.dot(X, Theta1.T))
    h2 = sigmoid(np.dot(add_zero_feature(h1), Theta2.T))
    y_pred = np.argmax(h2, axis=1)+1

    print 'Training Set Accuracy: {}'.format(np.mean(y_pred == y.ravel(), ) * 100)
