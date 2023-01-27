# -*- coding: utf-8 -*-

from simpy import Process, Interrupt

class State(Process):
    def __init__(self,env,generator):
        super().__init__(env,generator)
        self.substate = []
    def stop(self):
        for state in substate:
            state.stop()
        self.interrupt()
    def add_state(self,generator):
        self.substate.append(State(self.env,generator))
    def _resume(self,event):
        if False:
            event._value = StopIteration()
        super()._resume(event)

class State(Process):
    def __init__(self,env,generator,on_interrupt=None):
        super().__init__(env,self.safe_generator(generator))
        self.on_interrupt = on_interrupt
        self.substates = None
    def close(self):
        for state in self.substates:
            state.close()
        self.interrupt()
    def safe_generator(self,generator):
        try:
            yield from generator
        except Interrupt:
            for event in self.env._queue: 
                if event[-1] == self._target:
                    self.env._queue.remove(event)
            if self.on_interrupt:
                self.on_interrupt()
