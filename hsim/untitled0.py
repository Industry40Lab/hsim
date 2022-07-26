# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 18:03:34 2022

@author: Lorenzo
"""

import pymulate as sim
from pymulate import Generator, Server, Router, ServerDoubleBuffer,ServerWithBuffer
from pymulate import function
from chfsm import Transition, State
import numpy as np
import pandas as pd
from simpy import AllOf, AnyOf


        
class Server(ServerWithBuffer):
    def build(self):
        super().build()
        self.Control = None
Working = Server._states_dict('Working')
Blocking = Server._states_dict('Blocking')
@function(Working)
def f(self):
    self.var.entity = self.var.request.read()
    self.var.entity.routing.remove(self.sm._name)
# W2B = Transition(Working, Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
# Working._transitions = [W2B]


class Generator(Generator):
    def build(self):
        self.Next = None
        self.Release = self.env.event()
Sending = State('Sending',True)
@function(Sending)
def f5(self):
    self.Release.restart()
    self.var.entity = self.createEntity()
S2S = Transition(Sending,Sending,lambda self: AllOf(self.env,[self.Release, self.Next.put(self.var.entity)]))
Sending._transitions = [S2S]
Generator._states = [Sending]

class OR():
    def __init__(self,limits):
        self.limits = limits

def calcWIP(obj):
    x = 0
    for store in obj._messages.values():
        try:
            x += len(store.items)
        except:
            pass
    return x

def countWIP(obj):
    x = 0
    for store in obj._messages.values():
        try:
            x += len(store.items)
        except:
            pass
    return x

class CONWIP():
    def __init__(self,limits):
        self.limits = limits
    def control(self):
        x = 0
        for obj in env._objects:
            x += countWIP(obj)
        if x<self.limits:
            return True
        else:
            return False
    def __call__(self):
        if self.control():
            if not self.Release.triggered:
                self.Release.succeed()

class COBACABANA():
    def __call__(self,obj):
        pass

class DEWIP():
    def __call__(self,item,station=None):
        if station == None:
            self.release_control(item)
        else:
            self.go_ahead(item)
    def release_control(self,item):
        pass
    def get_by_name(self,name):
        return [obj for obj in env._objects if obj.name == name][0]
            
            
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
if __name__ == '__main__' and 1:
    env = sim.Environment()
    C = CONWIP(10)
    g = Generator(env)
    g.createEntity = createEntity(1,'F')
    s = Server(env,'M1',serviceTime=1)
    T = sim.Store(env)
    C.Release = g.Release
    s.Control = C
    s.Next = T
    g.Next = s.QueueIn
    while env.now<20:
        env.step()
        C()


if __name__ == '__main__' and 0:
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