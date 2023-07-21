#-*- coding: utf8
'''
Unit tests for the main sherlock model.
'''
from __future__ import division, print_function

from tribeflow.tests import files

from numpy.testing import assert_equal
from numpy.testing import assert_array_equal

from tribeflow import dataio

def test_initialize():
    tstamps, Trace, previous_stamps, Count_zh, Count_oz, count_h, count_z, \
            prob_topics_aux, Theta_zh, Psi_oz, hyper2id, obj2id = \
            dataio.initialize_trace(files.SIZE10, 2, 10)
    
    assert_equal(len(hyper2id), 3)
    assert_equal(len(obj2id), 6) 
    
    assert_equal(Trace.shape[0], 10)
    assert_equal(Trace.shape[1], 4)
    
    for z in [0, 1]:
        assert previous_stamps._size(z) > 0

    assert_equal(count_h[0], 4)
    assert_equal(count_h[1], 4)
    assert_equal(count_h[2], 2)
    
    assert_equal(count_z.sum(), 20) #depends on memory
    
    #We can only test shapes and sum, since assignments are random
    assert_equal(Count_zh.shape, (2, 3))
    assert_equal(Count_oz.shape, (6, 2))
    
    assert_equal(Count_zh.sum(), 10)
    assert_equal(Count_oz.sum(), 20)
    
    assert (prob_topics_aux == 0).all()

    #Simple sanity check on topic assigmnets. Check if topics have valid
    #ids and if count matches count matrix        
    from collections import Counter
    c = Counter(Trace[:, -1])
    for topic in c:
        assert topic in [0, 1]
        assert c[topic] == count_z[topic] / 2

def test_initialize_limits():
    tstamps, Trace, previous_stamps, Count_zh, Count_oz, count_h, count_z, \
            prob_topics_aux, Theta_zh, Psi_oz, hyper2id, obj2id = \
            dataio.initialize_trace(files.SIZE10, 2, 10, 2, 5)
    
    assert len(tstamps) == 3
