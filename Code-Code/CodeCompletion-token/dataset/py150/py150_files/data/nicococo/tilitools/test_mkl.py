import cvxopt as co
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt
import math

from ssad import SSAD
from ocsvm import OCSVM
from mkl import MKLWrapper
from kernel import Kernel


if __name__ == '__main__':
	"""
	MKL is a wrapper around a specific method (here SSAD) and
	takes a list of kernels as input argument. 

	For training each of the kernels should have the same size,
	say NxN. Each kernel captures a different feature representation 
	of the very same training data points. E.g., kernel1 is a BOW
	kernel, kernel2 is a Lexical Diversity kernel of the data points
	x_1,...,x_N.

	During training and testing, the order of the kernels
	should stay the same, e.g. if kernel1 is a BOW kernel during
	training, it must be kernel1 during testing as well.

	For testing, the kernel should have size M x N_1:
	M is the number of test samples and N_1 the number of 
	support vectors (N_1 <= N).

	"""
	P_NORM = 2.1 # mixing coefficient lp-norm regularizer
	N_pos = 100 
	N_neg = 100
	N_unl = 200

	# 1. STEP: TRAINING DATA
	# 1.1. generate training labels
	yp = co.matrix(1,(1,N_pos),'i')
	yu = co.matrix(0,(1,N_unl),'i')
	yn = co.matrix(-1,(1,N_neg),'i')
	Dy = co.matrix([[yp], [yu], [yn], [yn], [yn], [yn]])
	
	# 1.2. generate training data
	co.setseed(11)
	Dtrainp = co.normal(2,N_pos)*0.4
	Dtrainu = co.normal(2,N_unl)*0.4
	Dtrainn = co.normal(2,N_neg)*0.3
	Dtrain21 = Dtrainn-1
	Dtrain21[0,:] = Dtrainn[0,:]+1
	Dtrain22 = -Dtrain21

	# 1.3. concatenate training data
	Dtrain = co.matrix([[Dtrainp], [Dtrainu], [Dtrainn+1.0], [Dtrainn-1.0], [Dtrain21], [Dtrain22]])

	# 1.4. build the training kernels:
	# - same training sample for each kernel = they have the same size
	# - each kernel captures a feature representation of the samples Dtrain
	#   e.g., kernel1 is a BOW kernel, kernel2 a Lexical Diversity kernel
	#   here: kernel1 und kernel2 are Gaussian kernels with different shape parameters
	# 	and kernel3 is a simple linear kernel
	kernel1 = Kernel.get_kernel(Dtrain, Dtrain, type='rbf', param=1.0)
	kernel2 = Kernel.get_kernel(Dtrain, Dtrain, type='rbf', param=1.0/50.0)
	kernel3 = Kernel.get_kernel(Dtrain, Dtrain, type='rbf', param=1.0/100.0)
	kernel4 = Kernel.get_kernel(Dtrain, Dtrain, type='linear')

	# MKL: (default) use SSAD
	ad = SSAD([],Dy,1.0,1.0,1.0/(N_unl*0.05),1.0)
	#ad = OCSVM(kernel1,C=0.02)

	# 2. STEP: TRAIN WITH A LIST OF KERNELS 
	ssad = MKLWrapper(ad,[kernel1,kernel2,kernel3,kernel4],Dy,P_NORM)
	ssad.train_dual()

	# 3. TEST THE TRAINING DATA (just because we are curious)
	# 3.1. build the test kernel
	kernel1 = Kernel.get_kernel(Dtrain, Dtrain[:,ssad.get_support_dual()], type='rbf', param=1.0)
	kernel2 = Kernel.get_kernel(Dtrain, Dtrain[:,ssad.get_support_dual()], type='rbf', param=1.0/50.0)
	kernel3 = Kernel.get_kernel(Dtrain, Dtrain[:,ssad.get_support_dual()], type='rbf', param=1.0/100.0)
	kernel4 = Kernel.get_kernel(Dtrain, Dtrain[:,ssad.get_support_dual()], type='linear',)

	# 3.2. apply the trained model
	thres = np.array(ssad.get_threshold())[0,0]
	pred = ssad.apply_dual([kernel1,kernel2,kernel3,kernel4])
	pred = np.array(pred)
	pred = pred.transpose()

	# 4. STEP: GENERATE A TEST DATA GRID
	# 4.1. generate test data from a grid for nicer plots
	delta = 0.1
	x = np.arange(-3.0, 3.0, delta)
	y = np.arange(-3.0, 3.0, delta)
	X, Y = np.meshgrid(x, y)    
	(sx,sy) = X.shape
	Xf = np.reshape(X,(1,sx*sy))
	Yf = np.reshape(Y,(1,sx*sy))
	Dtest = np.append(Xf,Yf,axis=0)
	print(Dtest.shape)

	# 4.2. build the test kernels
	kernel1 = Kernel.get_kernel(co.matrix(Dtest), Dtrain[:,ssad.get_support_dual()], type='rbf', param=1.0)
	kernel2 = Kernel.get_kernel(co.matrix(Dtest), Dtrain[:,ssad.get_support_dual()], type='rbf', param=1.0/50.0)
	kernel3 = Kernel.get_kernel(co.matrix(Dtest), Dtrain[:,ssad.get_support_dual()], type='rbf', param=1.0/100.0)
	kernel4 = Kernel.get_kernel(co.matrix(Dtest), Dtrain[:,ssad.get_support_dual()], type='linear')

	# 4.3. apply the trained model on the test data
	res = ssad.apply_dual([kernel1,kernel2,kernel3,kernel4])

	# 5. STEP: PLOT RESULTS
	# make a nice plot of it
	Z = np.reshape(res,(sx,sy))

	# 5.1. plot training and test data
	plt.figure()
	plt.contourf(X, Y, Z, 20)
	plt.contour(X, Y, Z, [np.array(ssad.get_threshold())[0,0]])
	plt.scatter(Dtrain[0,ssad.get_support_dual()],Dtrain[1,ssad.get_support_dual()],60,c='w') 
	plt.scatter(Dtrain[0,N_pos:N_pos+N_unl-1],Dtrain[1,N_pos:N_pos+N_unl-1],10,c='g') 
	plt.scatter(Dtrain[0,0:N_pos],Dtrain[1,0:N_pos],20,c='r') 
	plt.scatter(Dtrain[0,N_pos+N_unl:],Dtrain[1,N_pos+N_unl:],20,c='b') 

	# 5.2. plot the influence of each kernel
	plt.figure()
	plt.bar([i+1 for i in range(4)], ssad.get_mixing_coefficients())

	plt.show()
	print('finished')