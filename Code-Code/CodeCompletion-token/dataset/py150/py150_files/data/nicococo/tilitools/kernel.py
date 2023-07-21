from cvxopt import matrix,spmatrix,sparse,exp
from cvxopt.blas import dot,dotu
from cvxopt.solvers import qp
import numpy as np
import pylab as pl

class Kernel:

	def __init__(self):
		pass

	@staticmethod
	def get_kernel(X, Y, type='linear', param=1.0):
		"""Calculates a kernel given the data X and Y (dims x exms)"""
		(Xdims,Xn) = X.size
		(Ydims,Yn) = Y.size
    	
		kernel = matrix(1.0)
		if type=='linear':
			print('Calculating linear kernel with size {0}x{1}.'.format(Xn,Yn))
			kernel = matrix([ dotu(X[:,i],Y[:,j]) for j in range(Yn) for i in range(Xn)], (Xn,Yn), 'd')

		if type=='rbf':
			print('Calculating Gaussian kernel with size {0}x{1}.'.format(Xn,Yn))
			kernel = matrix([dotu(X[:,i]-Y[:,j],X[:,i]-Y[:,j]) for j in range(Yn) for i in range(Xn)], (Xn,Yn))
			kernel = exp(-param*kernel)
		return kernel


	@staticmethod
	def get_diag_kernel(X, type='linear', param=1.0):
		"""Calculates the kernel diagonal given the data X (dims x exms)"""
		(Xdims,Xn) = X.size
    	
		kernel = matrix(1.0)
		if type=='linear':
			print('Calculating diagonal of a linear kernel with size {0}x{1}.'.format(Xn,Xn))
			kernel = matrix([ dotu(X[:,i],X[:,i]) for i in range(Xn)], (Xn,1), 'd')
		
		if type=='rbf':
			print('Gaussian kernel diagonal is always exp(0)=1.')
			kernel = matrix(1.0, (Xn,1), 'd')

		return kernel


	@staticmethod
	def center_kernel(K):
		print('IMPLEMENTED ME')
		return K


	@staticmethod 
	def normalize_kernel(K):
		print('IMPLEMENTED ME')		
		return K