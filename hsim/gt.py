# -*- coding: utf-8 -*-

from pymulate import Transition, State, Environment, ServerWithBuffer, Server, Queue, Terminator, Store

matrix = [[0, 7, 2], [1, 7, 5], [2, 7, 3], [3, 1, 2]]

class Controller(Server):
    def __init__(self,env,name=None,serviceTime=0,serviceTimeFunction=None):
        self.strategy = 'EDD'
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def sort(self,queue):
        pass
    class Starving(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Store.subscribe()
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request.read()
            self.sort(self.var.entity.Store) #sort Robot queue
    T2=Transition.copy(Working, Starving, lambda self: self.env.timeout(0),action=lambda self: self.var.request.confirm())
    T1=Transition.copy(Starving, Working, lambda self: self.var.request)

class Calc():
    def __init__(self):
        pass #read_excel
    def __call__(self,entity):
        t_empty = 2
        t_full = 1
        return t_empty + t_full
calc = Calc()

class Robot(Server):
    def __init__(self,env,controller,name=None,serviceTime=None,serviceTimeFunction=calc):
        self.controller = controller
        self.position
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def build(self):
        self.Store = Store(self.env)
    class Starving(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Store.subscribe()
    class Blocking(State):
        def _do(self):
            self.position = self.var.entity[-1] # set robot position
            self.controller.put(self)
    T1=Transition.copy(Starving, Server.Working, lambda self: self.var.request)
    T2=Transition.copy(Server.Working, Blocking, lambda self: self.env.timeout(calc(self.var.entity)))
    T3=Transition.copy(Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())

def runLocal(tEnd,matrix):
    env = Environment()
    t = Terminator(env)
    c = Controller(env)
    r = Robot(env,c)
    r.Next = t
    
    # process matrix
    for i in matrix:
        r.put(i)
    env.run(tEnd)
   

# %%    

env = Environment()
t = Terminator(env)
c = Controller(env)
r = Robot(env,c)
r.Next = t

# process matrix
for i in matrix:
    r.put(i)
env.run(20)