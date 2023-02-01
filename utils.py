# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 16:48:02 2022

@author: Lorenzo
"""

   
import pandas as pd

def stats(env):
    y = pd.DataFrame(env.state_log,columns=['Resource', 'ResourceID', 'State', 'StateID', 'timeIn', 'timeOut'])
    t = env.now
    y.loc[y.timeOut.values==None,'timeOut'] = t
    y=y.fillna(t) #test
    stats = dict()
    for res in y.Resource.unique():
        v = dict()
        for state in y.loc[y.Resource==res,'State'].unique():
            x=y.loc[(y.Resource==res) & (y.State==state),('timeIn','timeOut')]
            x = sum(x.timeOut - x.timeIn)/t
            v[state] = x
        stats[res] = v
    return stats

