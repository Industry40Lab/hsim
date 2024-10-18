# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 16:48:02 2022

@author: Lorenzo
"""

   
import pandas as pd

def stats(env):
    y = pd.DataFrame(env.state_log,columns=['Resource', 'ResourceID', 'State', 'StateID', 'entity', 'store','timeIn', 'timeOut'])
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

def stats2(log):
    y = log
    t = log['timeOut'].max()
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

def stats3(log):
    y = log
    t = log['timeOut'].max()
    y.loc[y.timeOut.values==None,'timeOut'] = t
    y=y.fillna(t) #test
    stats = dict()
    for res in y.ResourceName.unique():
        v = dict()
        for state in y.loc[y.ResourceName==res,'StateName'].unique():
            x=y.loc[(y.Resource==res) & (y.State==state),('timeIn','timeOut')]
            x = sum(x.timeOut - x.timeIn)/t
            v[state] = x
        stats[res] = v
    return stats

def createGantt(df):
    import plotly.express as px
    now=pd.Timestamp.today()
    now._hour=8
    now._minute=0
    now._second=0
    df.timeIn=pd.to_timedelta(df.timeIn,'s')+now
    df.timeOut=pd.to_timedelta(df.timeOut,'s')+now
    df.timeOut.fillna(df.timeOut.max(),inplace=True)
    fig = px.timeline(df, x_start="timeIn", x_end="timeOut", y="ResourceName", color="StateName")
    return fig