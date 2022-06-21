# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 18:03:34 2022

@author: Lorenzo
"""

import pymulate as sim
from pymulate import Generator, Server
from pymulate import State
from pymulate import function, do
import numpy as np
import pandas as pd




class Generator(sim.Generator):
    def __init__(self, env, name=None, createEntity=None,releaseCheck=None):
        super().__init__(env, name, createEntity)
        self.var.Trigger = env.event()
        self.var.releaseCheck = releaseCheck
    def build(self):
        Create = State('Create',True)
        @function(Create)
        def fcn2(self):
            return self.var.Trigger
        @do(Create)
        def do2(self,event):
            if self.var.releaseCheck():
                try:
                    self.var.entity = self.var.createEntity()
                except:
                    self.var.entity = object()
                return Wait
            else:
                self.var.Trigger.restart()
        Wait = State('Wait')
        @function(Wait)
        def fcn(self):
            return self.connections['after'].put(self.var.entity)
        @do(Wait)
        def do1(self,event):
            self.var.entity = None
            return Create
        return [Create,Wait]  

   
class CONWIP():
    def __init__(self,limit,objects):
        self.objects = objects
        self.limit = limit
    def __call__(self):
        x = 0
        for obj in self.objects:
            x += len(obj)
        if x<self.limit:
            return True
        else:
            return False
            
class createEntity():
    def __init__(self,n_machines,config):
        self.index = 1
        self.n_machines = n_machines
        self.config = config
        self.n = 3
    def __call__(self):
        return Entity(self._serviceTime(),self._routing())
    def _serviceTime(self):
        pass
    def _routing(self):
        x = np.random.choice(range(1,1+self.n_machines),np.random.randint(1,1+self.n_machines),replace=False)
        if self.config == 'F':
            x.sort()
        return [str('M%d' %i) for i in x]

class Entity():
    def __init__(self,serviceTime,routing):
        self.serviceTime = serviceTime
        self.routing = routing
   
            
# %% code
if __name__ == '__main__':
    env = sim.Environment()
    g = Generator(env)
    T = sim.Store(env)
    g.connections['after'] = T
    g.var.Trigger.succeed()
    g.var.releaseCheck = CONWIP(5,[T])
    g.var.createEntity = createEntity(6,'F')
    env.run(10)
    T.items.pop()
    g.var.Trigger.succeed()
    env.run(20)