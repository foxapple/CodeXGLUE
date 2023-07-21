#-*- coding: utf8
from __future__ import division, print_function

from tribeflow import _learn
from tribeflow.mycollections.stamp_lists import StampLists

import tribeflow
import pandas as pd
import plac
import numpy as np

def main(model, out_fpath):
    store = pd.HDFStore(model)
    
    from_ = store['from_'][0][0]
    to = store['to'][0][0]
    assert from_ == 0
    
    trace_fpath = store['trace_fpath'][0][0]
    kernel_class = store['kernel_class'][0][0]
    kernel_class = eval(kernel_class)

    Theta_zh = store['Theta_zh'].values
    Psi_sz = store['Psi_sz'].values
    count_z = store['count_z'].values[:, 0]
    P = store['P'].values
    residency_priors = store['residency_priors'].values[:, 0]
    
    previous_stamps = StampLists(count_z.shape[0])

    mem_size = store['Dts'].values.shape[1]
    tstamps = store['Dts'].values[:, 0]
    assign = store['assign'].values[:, 0]
    for z in xrange(count_z.shape[0]):
        idx = assign == z
        previous_stamps._extend(z, tstamps[idx])

    hyper2id = dict(store['hyper2id'].values)
    obj2id = dict(store['source2id'].values)
    
    HSDs = []
    Dts = []

    with open(trace_fpath) as trace_file:
        for i, l in enumerate(trace_file): 
            if i < to:
                continue
            
            spl = l.strip().split('\t')
            dts_line = [float(x) for x in spl[:mem_size]]
            h = spl[mem_size]
            d = spl[-1]
            sources = spl[mem_size + 1:-1]
            
            all_in = h in hyper2id and d in obj2id
            for s in sources:
                all_in = all_in and s in obj2id
            
            if all_in:
                trace_line = [hyper2id[h]] + [obj2id[s] for s in sources] + \
                        [obj2id[d]]
                HSDs.append(trace_line)
                Dts.append(dts_line)
    
    trace_size = sum(count_z)
    kernel = kernel_class()
    kernel.build(trace_size, count_z.shape[0], residency_priors)
    kernel.update_state(P)
    
    num_queries = min(10000, len(HSDs))
    queries = np.random.choice(len(HSDs), size=num_queries)

    HSDs = np.array(HSDs, dtype='i4')[queries].copy()
    Dts = np.array(Dts, dtype='d')[queries].copy()
    rrs = _learn.reciprocal_rank(Dts, \
            HSDs, previous_stamps, Theta_zh, Psi_sz, count_z, kernel)
    
    np.savetxt(out_fpath, rrs)
    print(rrs.mean(axis=0))
    store.close()
    
plac.call(main)
