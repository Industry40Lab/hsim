# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 18:03:34 2022

@author: Lorenzo
"""

import pymulate as sim
from pymulate import Generator, Server, Router, ServerDoubleBuffer,ServerWithBuffer, Queue, StoreSelect
from pymulate import function, action
from chfsm import Transition, State
import numpy as np
import pandas as pd
from simpy import AllOf, AnyOf
from collections import OrderedDict

        
class Server(ServerWithBuffer):
    def build(self):
        super().build()
        self.Control = None
    def subscribe(self,item):
        return self.QueueIn.subscribe(item)
Working = Server._states_dict('Working')
Blocking = Server._states_dict('Blocking')
@function(Working)
def f(self):
    self.var.entity = self.var.request.read()
    self.var.entity.routing.remove(self.sm._name)
W2B = Transition(Working, Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)),action=lambda self:self.Control.refresh())
Working._transitions = [W2B]

class PreShop(StoreSelect):
    def build(self):
        super().build()
        self.Release = self.env.event()
#         self.Dummy = self.env.event()
#         self.Dummy.succeed()
Sending = PreShop._states_dict('Sending')
@function(Sending)
def f20(self):
    self.var.requestIn = self.Release
    self.var.requestOut = []
    self.var.requestDict = {}
    for item in self.Queue.items:
        if self.condition_check(item,self.Next):
            self.var.requestOut.append(self.Next.subscribe(item))
    if self.var.requestOut == []:
        if len(self.Queue.items)==0:
            self.Queue.put_event.restart()
            self.var.requestIn = self.Queue.put_event
        self.var.requestOut = [self.var.requestIn]
refresh = Transition(Sending,Sending,lambda self:self.Release)
@action(refresh)
def f13(self):
    if hasattr(self.var.requestOut[0],'item'):
        for req in self.var.requestOut:
            req.cancel()
    self.Release.restart()
    
Sending._transitions.pop(0)
Sending._transitions.append(refresh)

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
        self.PreShop = None
    def control(self,*args):
        x = 0
        for obj in env._objects:
            if type(obj) is not PreShop:
                x += countWIP(obj)
        if x<self.limits:
            return True
        else:
            return False
    def __call__(self,*args):
        if self.control():
            return True
        else:
            return False
    def refresh(self):
        if not self.PreShop.Release.triggered:
            self.PreShop.Release.succeed()
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
        self.index = 0
        self.n_machines = n_machines
        self.config = config
        self.n = 3
    def __call__(self):
        self.index += 1
        return Entity(self.index,self._serviceTime(),self._routing())
    def _serviceTime(self):
        pass
    def _routing(self):
        x = np.random.choice(range(1,1+self.n_machines),np.random.randint(1,1+self.n_machines),replace=False)
        if self.config == 'F':
            x.sort()
        return [str('M%d' %i) for i in x]

class Entity():
    def __init__(self,ID,serviceTime,routing):
        self.ID = ID
        self.serviceTime = serviceTime
        self.routing = routing
      
def router_control(item,target):
    print(item.routing,target._name)

    if item.routing == []:
        if target._name == 'T':
            return True
        else:
            return False
    elif item.routing[0] == target._name:
        return True
    else:
        return False
    

    
# %% code

if __name__ == '__main__':
    np.random.seed(1)
    n_machines = 10
    env = sim.Environment()
    C = CONWIP(12)
    g = Generator(env,serviceTime=1)
    preshop_pool = PreShop(env)
    router = Router(env)
    servers = OrderedDict()
    for i in range(1,n_machines+1):
        name = 'M'+str(i)
        servers[name] =Server(env,name,serviceTime=1)
        servers[name].Next = router.Queue
        servers[name].Control = C
    T = sim.Store(env)
    T._name = 'T'
    
    g.Next = preshop_pool.Queue
    g.createEntity = createEntity(n_machines,'F')
    C.PreShop = preshop_pool
    preshop_pool.Next = router.Queue
    preshop_pool.condition_check = C.control
    router.Next = [server for server in servers.values()]+[T]
    router.condition_check = router_control
    
    from time import time
    tic = time()
    env.run(20)
    print(time()-tic)
    # 
    env.run(15)
