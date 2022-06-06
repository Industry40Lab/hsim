# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 16:48:02 2022

@author: Lorenzo
"""

   

def stats(env):
    y = env.state_log
    t = env.now
    y.loc[y.timeOut.values==None,'timeOut'] = t
    stats = dict()
    for res in y.Resource.unique():
        v = dict()
        for state in y.loc[y.Resource==res,'State'].unique():
            x=y.loc[(y.Resource==res) & (y.State==state),('timeIn','timeOut')]
            x = sum(x.timeOut - x.timeIn)/t
            v[state] = x
        stats[res] = v
    return stats