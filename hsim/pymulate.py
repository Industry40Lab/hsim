# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, CompositeState
from chfsm import function, do, on_entry, on_exit, on_interrupt
from stores import Store

class Server(CHFSM):
    def build(self):
        Idle = State('Idle',True)
        @function(Idle)
        def sth(self):
            return self.store.subscribe()
        @do(Idle)
        def u(self):
            return Work
        Work = State('Work')
        return [Idle,Work]
    def create_messages(self):
        self.Store = Store(self.env,1)
        

