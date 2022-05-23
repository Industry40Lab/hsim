# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, CompositeState
from chfsm import function, do, on_entry, on_exit, on_interrupt
from stores import Store
from core import Environment
from simpy import AllOf, AnyOf

class Server(CHFSM):
    def build(self):
        Starve = State('Starve',True)
        @function(Starve)
        def sth(self):
            self.var.request = self.Store.subscribe()
            return self.var.request
        @do(Starve)
        def u(self,event):
            return Work
        Work = State('Work')
        @function(Work)
        def foo(self):
            return self.env.timeout(10)
        @do(Work)
        def fcn(self,event):
            return Block
        Block = State('Block')
        @function(Block)
        def blockk(self):
            req = self.connections['after'].put([1])
            return req
        @do(Block)
        def blockk(self,event):
            return Starve
        return [Starve,Work,Block]
    def build_c(self):
        self.Store = Store(self.env,1)
        
class ServerWithQueueV1(Server):
    def __init__(self,env,name,capacity):
        super().__init__(env, name)
        self.capacity = capacity
    def build_c(self):
        self.Store = Store(self,env,self.capacity)
        
class ServerWithTwoQueues(Server):
    def __init__(self,env,name,capacityIn=1,capacityOut=1):
        self.capacityIn = capacityIn
        self.capacityOut = capacityOut
        super().__init__(env, name)
    def build(self):
        states = super().build()
        GetIn = State('GetIn',True)
        @function(GetIn)
        def q(self):
            return AllOf(self.env,[self.QueueIn.subscribe(),self.Store.subscribe(object())])
        @do(GetIn)
        def G(self,event):
            entity = event._events[0].confirm()
            event._events[1].item = entity
            return
        states.append(GetIn)
        return states
    def build_c(self):
        super().build_c()
        self.QueueIn = Store(env,self.capacityIn)
        self.QueueOut = Store(env,self.capacityOut)
        

class Generator(CHFSM):
    def build(self):
        Work = State('Work')
        @function(Work)
        def fcn(self):
            entity = [1]
            return self.connections['after'].put(entity)
        @do(Work)
        def do1(self):
            return Work()
        return [Work]
        

env = Environment()
a = ServerWithTwoQueues(env,'1')
a.QueueIn.put([1])
b = Store(env,1)
a.connections['after']=b
g = Generator(env, 'g')
g.connections['after'] = a
env.run(25)


        