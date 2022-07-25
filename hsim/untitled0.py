# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 18:03:34 2022

@author: Lorenzo
"""

import pymulate as sim
from pymulate import Generator, Server, Router, ServerDoubleBuffer
from pymulate import function
from CHFSM import Transition
import numpy as np
import pandas as pd


class Switch(Router):
    def condition_check(self,item,target):
        if target._name == item.routing[0]:
            return True
        else:
            return False
        
class Server(ServerDoubleBuffer):
    pass
ForwardingOut = Server._states_dict('ForwardingOut')
@function(ForwardingOut)
def f4(self):
    self.var.entityOut = self.var.requestOut.read()
    self.var.entityOut.routing.remove(self._name)

class Generator(Generator):
    def build(self):
        self.Go = self.env.event()
Sending = Generator._states_dict('Sending')
Waiting = Generator._states_dict('Waiting')
S2W = Transition(Sending,Waiting,lambda self: self.Go,action=lambda self:self.Go.restart())
Sending._transitions = [S2W]
    
   
class OR():
    def __init__(self,limits,objs):
        self.objs = objs
        self.limits = limits
    def __call__(self):
        if self.control():
            return True
        else:
            return False
        
class CONWIP(OR):
    def __call__(self):
        x = 0
        for obj in self.objs:
            x += len(obj)
        if x<self.limits:
            return True
        else:
            return False
        
class COBACABANA():
    def __call__(self,obj):
        pass

class DEWIP():
    def __call__(self):
        pass
            
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