'''
Science.py

'''
from bnpy.data import WordsData, AdmixMinibatchIterator
import os

data_dir = '/Users/daeil/Dropbox/research/liv-test/topic_models/data/wikipedia/'
matfilepath = os.environ['BNPYDATADIR'] + 'wiki_bnpy.mat'

if not os.path.exists(matfilepath):
    matfilepath = data_dir + 'wiki_bnpy.mat'

def get_data(seed=8675309, nObsTotal=25000, **kwargs):
    ''' Grab data from matfile specified by matfilepath
    '''
    Data = WordsData.read_from_mat( matfilepath )
    Data.summary = get_data_info(Data.nDocTotal, Data.vocab_size)
    return Data

def get_minibatch_iterator(seed=8675309, nBatch=10, nObsBatch=None, nObsTotal=25000, nLap=1, allocModelName=None, dataorderseed=0, **kwargs):
    Data = WordsData.read_from_mat( matfilepath )
    DataIterator = AdmixMinibatchIterator(Data, nBatch=nBatch, nObsBatch=nObsBatch, nLap=nLap, dataorderseed=dataorderseed)
    DataIterator.summary = get_data_info(Data.nDocTotal, Data.vocab_size)
    return DataIterator

def get_data_info(D, V):
    return 'Wikipedia Data. D=%d. VocabSize=%d' % (D,V)