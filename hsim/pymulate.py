# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, CompositeState
from chfsm import function, do, on_entry, on_exit, on_interrupt
from stores import Store
from core import Environment

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
            a = self.connections['after'].put(1)
            self.var.request.confirm()
            # if self.
        Block = State('Block')
        @function(Block)
        def block(self):
            pass
        @do(Block)
        def blockk(self):
            pass
        return [Starve,Work,Block]
    def build_c(self):
        self.Store = Store(self.env,1)
        
class Generator(CHFSM):
    def build(self):
        self.connections['after'].put(entity)
        Work = State('Work')
        @function
        def fcn(self):
            return self.env.timeout(10)
        @do
        def do(self):
            return self

env = Environment()
a1=CHFSM(env,1)
a = Server(env,'1')
a.Store.put([1])
b = Store(env)
a.connections['after']=b
# env.run(15)