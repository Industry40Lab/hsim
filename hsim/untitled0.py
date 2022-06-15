# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 18:03:34 2022

@author: Lorenzo
"""

import pymulate as sim
from pymulate import Generator
from pymulate import State
from pymulate import function, do


class Generator(sim.Generator):
    def __init__(self, env, name=None, createEntity=None,checkCondition=None):
        super().__init__(env, name, createEntity)
        self.var.Trigger = env.event()
        self.var.checkCondition = checkCondition
    def build(self):
        Create = State('Create',True)
        @function(Create)
        def fcn2(self):
            return self.var.Trigger
        @do(Create)
        def do2(self,event):
            if self.var.checkCondition():
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

                
            
# %% code
if __name__ == '__main__':
    env = sim.Environment()
    g = Generator(env)
    T = sim.Store(env)
    g.connections['after'] = T
    g.var.Trigger.succeed()
    g.var.checkCondition = CONWIP(5,[T])
    env.run(10)