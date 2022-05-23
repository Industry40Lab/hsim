# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:07:24 2022

@author: Lorenzo
"""

from simpy import Environment
from simpy.core import BoundClass
import pandas as pd
# from states import State

class Environment(Environment):
    def __init__(self,log=None,initial_time=0):
        super().__init__(initial_time)
        self._objects = list()
        self.log = log
        if log==None:
            self.log = createLog()           
    def logF(self,entity,resource,operator,activity,time=True):
        if time:
            time = self.now
        [entity,operator]=[x if x is not None else "" for x in [entity,operator]]
        self.log.loc[(self.log["timeOut"]==-1) & (self.log["resource"]==resource),"timeOut"]=time
        self.log.loc[len(self.log)] = [entity,resource,operator,activity,time,-1]
    def run(self,until=None):
        at = float(until)
        if at <= self.now:
            print('Time %d <= %d (current time) --> executing until %d' %(at, self.now, at+self.now))
            at += self.now
        super().run(at)
    def add_object(self,obj):
        self._objects.append(obj)
    # state = BoundClass(State)


# global log
def createLog():
    # global log
    log = pd.DataFrame(columns = ["entity","resource","operator","activity","timeIn","timeOut"])  
    return log

class dotdict(dict):
    """MATLAB-like dot.notation access to dictionary attributes"""
    def __getattr__(self,name):
        try:
            super().__getattr__(name)
            return super().__getitem__(name)
        except AttributeError:
            raise AttributeError()
    def __setattr__(self,name,value):
        super().__setitem__(name,value)
        super().__setattr__(name, value)
    def __delattr__(self,name):
        super().__delattr__(name)
        super().__delitem__(name)
    def __repr__(self):
        return str(vars(self))
    def keys(self):
        return vars(self).keys()
    def values(self):
        return vars(self).values()
    def __len__(self):
        return len(self.keys())
    
