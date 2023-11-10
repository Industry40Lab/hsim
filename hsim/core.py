# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:07:24 2022

@author: Lorenzo
"""

from simpy import Environment, Event
from simpy.core import BoundClass
from simpy.events import PENDING, Interruption
import pandas as pd
from warnings import warn
# from states import State

class Event(Event):
    def restart(self):
        self._value = PENDING
        self.callbacks = []
        
class Interruption(Interruption):
    def _interrupt(self, event: Event) -> None:
        if self.process._value is not PENDING:
            return
        # self.process._target.callbacks.remove(self.process._resume)
        self.process._resume(self)

class Environment(Environment):
    def __init__(self,log=None,initial_time=0):
        super().__init__(initial_time)
        self._objects = list()
        # self.log = log
        # if log==None:
        #     self.log = createLog()        
        # self.state_log2 = pd.DataFrame(columns=['Resource','ResourceName','State','StateName','timeIn','timeOut'])
        self.state_log = list()
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
    event = BoundClass(Event)
    def threshold(self,value):
        th = ev(1)
        th.set_env(self)
        return th
    @property
    def log(self):
        return pd.DataFrame(self.state_log,columns=['Resource','ResourceName','State','StateName','entity','store','timeIn','timeOut'])
    #dangerous
    from warnings import warn
    warn('Bypassing "None" callbakcs')
    def step(self):
        if len(self._queue)>0:
            if self._queue[0][-1].callbacks is None:
                self._queue[0][-1].callbacks = []
        super().step()

class State_Log(pd.DataFrame):
    def __init__(self):
        columns=['Resource','State','timeIn','timeOut']
        super().__init__(columns=columns)
    def add(self,data):
        pass
    def read(self):
        x = self.copy()     
        for i in range(len(self.env.state_log)):
            x.loc[i].Resource

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
    
def method_lambda(self,function):
    if not hasattr(function,'__self__'):
        return function(self)
    else:
        return function()
    # try:
    #     return function()
    # except TypeError:
    #     return function(self)

class thvar(float,object):
    def __init__(self,value):
        self._value=value
        self._threshold = dict()
    def __add__(self,x):
        return self.create(self._value + x)
    def __sub__(self,x):
        return self.create(self._value - x)
    def __pow__(self,x):
        return self.create(self._value**x)
    def __float__(self):
        return float(self._value)
    def __int__(self):
        return int(self._value)
    def __repr__(self):
        return str(self._value)
    def __iadd__(self,other):       
        return self.update(self._value + other)
    def __isub__(self,other):
        return self.update(self._value - other) 
    def __imul__(self, other):
        return self.update(self._value*other) 
    def __ipow__(self, other):
        return self.update(self._value**other) 
    def __imod__(self,other):
        return self.update(other) 
    def __ilshift__(self,other):
        self._threshold.update({'up':other})
        self.threshold_fun(self._value)
        return self
    def __irshift__(self,other):
        self._threshold.update({'down':other})
        return self
    def create(self,value):
        return self.__class__(value)
    def update(self,value):
        self.threshold_fun(value)
        self._value = value
        return self
    def threshold_fun(self,value):
        if self.check(value):
            warn(RuntimeWarning('Break threshold'))
    def check(self,value):
        if 'up' in self._threshold.keys():
            if value > self._threshold['up']:
                return True
        if 'down' in self._threshold.keys():
            if value < self._threshold['down']:
                return True
        return False
    
class ev(thvar,Event):
    def threshold_fun(self,value):
        if not self.check(value) and not self._event.triggered:
            self.succeed()
    def set_env(self,env):
        super(Event,self).__init__(env)
        return self
    def triggered(self):
        return self._ok
    
# if __name__ == '__main__':
#     a=thvar(2)
#     a<<=1
    
if __name__ == '__main__':
    env=Environment()

    a=ev(1)
    a.set_env(env)

if __name__ == '__main__':
    env=Environment()
    b=env.threshold(1)
    
    # a<<=3
    # a+=3