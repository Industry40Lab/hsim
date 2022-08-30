# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 18:03:34 2022

@author: Lorenzo
"""

import pymulate as sim
from pymulate import Generator, Server, Router0, ServerDoubleBuffer,ServerWithBuffer, Queue, StoreSelect
from pymulate import function, action
from chfsm import Transition, State
import numpy as np
import pandas as pd
from simpy import AllOf, AnyOf
from collections import OrderedDict
from stores import Box, Store

        
class Server(ServerWithBuffer):
    def build(self):
        super().build()
        self.Control = None
    def subscribe(self,item):
        return self.QueueIn.subscribe(item)
    def put(self,item):
        return self.QueueIn.put(item)
Working = Server._states_dict('Working')
Blocking = Server._states_dict('Blocking')
Starving = Server._states_dict('Starving')
@function(Working)
def f(self):
    self.var.entity = self.var.request.read()
    if not self.sm._name[1] == 'x':
        self.var.entity.routing.remove(self.sm._name)
W2B = Transition(Working, Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)),action=lambda self:self.Control.refresh())
Working._transitions = [W2B]
@function(Blocking)
def fb(self):
    target = self.sm.routing_target(self.sm.var.entity,self.sm.Next)
    self.sm.var.requestOut = target.put(self.sm.var.entity)
B2S = Transition(Blocking, Starving, lambda self: self.sm.var.requestOut,action=lambda self: self.sm.var.request.confirm())
Blocking._transitions = [B2S]


class PreShop(StoreSelect):
    def build(self):
        super().build()
        self.Release = self.env.event()
Sending = PreShop._states_dict('Sending')
@function(Sending)
def f20(self):
    for item in self.sm.Queue.items:
        if self.sm.condition_check(item,self.Next):
            self.sm.Next.put(item)
            self.sm.Queue.items.remove(item)
    if len(self.sm.Queue.items)==0:
        self.sm.Queue.put_event.restart()
        self.sm.var.request = self.Queue.put_event
    else:
        self.sm.var.request = self.Release
refresh = Transition(Sending,Sending,lambda self:self.var.request)
@action(refresh)
def f13(self):
    self.Release.restart()
Sending._transitions = [refresh]

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

# def countWIP(obj):
#     x = 0
#     for store in obj._messages.values():
#         try:
#             x += len(store.items)
#         except:
#             pass
#     return x

class CONWIP():
    def __init__(self,env,limits):
        self.env = env
        self.limits = limits
        self.PreShop = None
        self.list=self.listing(env)
    def listing(self,env):
        L = []
        for obj in env._objects:
            if type(obj) is not PreShop:
                for store in obj._messages.values():
                    if str(type(store)) == str(Store):
                        if hasattr(store,'items'):
                            L.append(store)
        return L
    def control(self,*args):
        x = sum([len(q.items) for q in self.list])
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
      
def router_control(item,target_list):
    if item.routing == []:
        return target_list[-1]
    else:
        return target_list[[i._name for i in target_list].index(item.routing[0])]
    

    
# %% code

if __name__ == '__main__':
    np.random.seed(1)
    n_machines = 10
    env = sim.Environment()
    C = CONWIP(env,12)
    g = Generator(env,serviceTime=1)
    init = Server(env,serviceTime=0)
    preshop_pool = PreShop(env)
    servers = OrderedDict()
    for i in range(1,n_machines+1):
        name = 'M'+str(i)
        servers[name] = Server(env,name,serviceTime=1)
        servers[name].Control = C
    T = sim.Store(env)
    T._name = 'T'
    
    g.Next = preshop_pool.Queue
    g.createEntity = createEntity(n_machines,'F')
    C.PreShop = preshop_pool
    preshop_pool.Next = init
    preshop_pool.condition_check = C.control
    init.Next = [server for server in servers.values()]+[T]
    init.routing_target = router_control
    init.Control = C
    for server in servers.values():
        server.Next = [server for server in servers.values()]+[T]
        server.routing_target = router_control
    
    from time import time
    tic = time()
    env.run(90)
    print(time()-tic)
    # 
    env.run(15)
