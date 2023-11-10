# -*- coding: utf-8 -*-
from sys import path
path.append('../')

from pymulate import Transition, State, Environment, ServerWithBuffer, Server, Queue, Terminator, Store
import pandas as pd
from itertools import permutations

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
        self.data = pd.read_excel("C:/Users/Lorenzo/Dropbox (DIG)/Ricerca/GEORGIA TECH/ShuffleCenter/ShuffleCenter 2022_12_29_copy/Shuffle Bot Movement Speed Matrix.xlsx",sheet_name=2,index_col=0)
        pass #read_excel
    def __call__(self,entity):
        t_empty = self.data.iloc[entity[0].__abs__(),entity[1].__abs__()]
        t_full = self.data.iloc[entity[1].__abs__(),entity[2].__abs__()]
        return t_empty + t_full
calc = Calc()

class Robot(Server):
    def __init__(self,env,controller,name=None,serviceTime=None,serviceTimeFunction=calc):
        self.controller = controller
        self.position = 1
        self.C=list()
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
            self.C.append([self.var.entity[0],self.env.now])
            self.controller.put(self)
    T1=Transition.copy(Starving, Server.Working, lambda self: self.var.request)
    T2=Transition.copy(Server.Working, Blocking, lambda self: self.env.timeout(calc(self.var.entity)))
    T3=Transition.copy(Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())

def runLocal(matrix):
    if matrix == []:
        return 0
    env = Environment()
    t = Terminator(env)
    c = Controller(env)
    r = Robot(env,c)
    r.Next = t
    # process matrix
    for i in matrix:
        r.put(i)
    # run            
    env.run(3600)
    # report
    env.state_log2=pd.DataFrame(env.state_log)
    C = r.C
    C.sort(key=lambda x: x[0])
    return C

def getWL(C):
    cmax = max([c[1] for c in C])
    print(cmax)
    return cmax

def getSlack(C,rTimes):
    res = [rT[2]-(rT[1]+C[1]) for C,rT in zip(C, rTimes)]
    slack = 0
    for r in res:
        if r>0:
            slack += 1/r
        else:
            slack += 1000
    return slack

def bruteTSP(matrix,rTimes,objective):
    res = list()
    for m in permutations(matrix):
        C = runLocal(matrix)
        res.append([getWL(C),getSlack(C,rTimes)])
        #get index of minimum
        index = 0
        return [i[0] for i in list(permutations(matrix))[index]]
    
        
   
# %%    

env = Environment()
t = Terminator(env)
c = Controller(env)
r = Robot(env,c)
r.Next = t

# process matrix
for i in matrix:
    r.put(i)
env.run(200)



