# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 18:08:34 2023

@author: Lorenzo
"""

from pymulate import Environment, Server, Generator, Router, Terminator, StoreSelect, RouterNew
import numpy as np
import random as rnd
import pymulate
from chfsm import CHFSM, State, Transition
from stores import Store

class Server(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        self.WL = 0
        super().__init__(env,name,serviceTime,serviceTimeFunction)

    T2=Transition(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)),action=lambda self:self.var.entity.route.pop(0))

class Queue(CHFSM):
    def __init__(self, env, name=None, capacity=np.inf):
        self.capacity = capacity
        self.sortingFcn = None
        super().__init__(env,name)
    def sort(self):
        pass
    def put(self,item):
        if not hasattr(item,'entryTime'):
            item.entryTime = {}
        item.entryTime[self.name] = self.env.now
        self.sort()
        return self.Store.put(item)
    def subscribe(self,item):
        return self.Store.subscribe(item)
    def build(self):
        self.Store = Store(self.env,self.capacity)
    @property
    def items(self):
        return self.Store.items
    def __len__(self):
        return len(self.Store.items)
    class Retrieving(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Store.subscribe()
    class Forwarding(State):
        def _do(self):
            self.var.entity = self.var.request.read()
    T1=Transition(Retrieving,Forwarding,lambda self: self.var.request)
    T2=Transition(Forwarding,Retrieving,lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())

def erlang(mean):
    scale = mean/2
    x = np.random.gamma(2,scale)
    return x

class Entity():
    def __init__(self,ID=0,serviceTime={},createTime=None,dueDate=None):
        self.ID = ID
        self.serviceTime = serviceTime
        self.route = None
        self.createTime = createTime
        self.releaseTime = None
        self.completionTime = None
        self.dueDate = dueDate
    @property
    def load(self):
        count = 0
        y = dict()
        for key in self.serviceTime.keys():
            if self.serviceTime[key] > 0:
                count += 1
                y[key] = self.serviceTime[key]/count
            else:
                y[key] = 0               
        return y
        

class Generator(Generator):
    def __init__(self,env,name=None,serviceTime=1,serviceTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.count = 0
        self.flowshop = True
        self.N = 1
    def createEntity(self):
        self.count += 1
        T = dict()
        listOfMachineNames=['M'+str(i) for i in range(1,self.N+1)]
        for i in listOfMachineNames:
            T[i] = erlang(1*60)
        dueDate=self.env.now+np.random.uniform(30,45)
        entity = Entity(ID=self.count,serviceTime=T,createTime=self.env.now)
        x = rnd.sample(listOfMachineNames,rnd.randint(1,self.N))
        if self.flowshop:
            x.sort()
        x.sort()
        entity.route = x
        for machine in listOfMachineNames:
            if machine in entity.route:
                pass
            else:
                entity.serviceTime[machine]=0
        print(entity.ID)
        return entity

class Router(RouterNew):
    def condition_check(self,item,target):
        if len(item.route) == 0 and type(target) is Terminator:
            return True
        elif len(item.route)>0:
            if item.route[0][1:]==target._name[1:]:
                return True
        else:
            return False

def FIFO(itemList):
    if itemList != []:
        print(1)
    sortedList = itemList
    return sortedList

def SPT(itemList):
    sortedList = itemList
    return sortedList
    
def LPT(itemList):
    sortedList = itemList
    return sortedList

def Slack(itemList):
    sortedList = itemList
    return sortedList

def SlackOPN(itemList):
    sortedList = itemList
    return sortedList

def WL():
    pass
    # for each job
         # for each s in job.route
             # if pij/i[s] + Ws < Ns
                 # pass
             # else
                 # break
        # for each s in job.route
            #Ws += pij/i[s]

def CONWIP():
    pass

# 1 - order release
# 2 - dispatching rules

# %%  t2

env = Environment()

N=5
capIn = 5
capOut = 5

globals()['G']=Generator(env)
globals()['G'].N = N
globals()['G'].flowshop = False
globals()['Preshop'] = Queue(env,capacity=10)
globals()['R0'] = Router(env,'R0',capacity=2)

globals()['T'] = Terminator(env)
globals()['T']._name = 'terminator'

for i in range(1,N+1):
    globals()['Q'+str(i)] = Queue(env,'Q'+str(i),capacity=capIn)
    globals()['M'+str(i)] = Server(env,'M'+str(i))
    globals()['R'+str(i)] = Router(env,'R'+str(i),capacity=capOut)
    
# g.Next = globals()['R0']
globals()['G'].Next = globals()['Preshop']
globals()['Preshop'].Next = globals()['R0']

globals()['R0'].Next = list()
for i in range(1,N+1):
    globals()['R0'].Next.append(globals()['Q'+str(i)])

for i in range(1,N+1):
    globals()['Q'+str(i)].Next = globals()['M'+str(i)]
    globals()['M'+str(i)].Next = globals()['R'+str(i)]
    globals()['R'+str(i)].Next = list()
    globals()['R'+str(i)].Next.append(globals()['T'])
    for j in range(1,N+1):
        globals()['R'+str(i)].Next.append(globals()['Q'+str(j)])

np.random.seed(1)    
env.run(33600)




#%% t3
# env = Environment()

# N=3
# capIn = 5
# capOut = 5

# globals()['G']=Generator(env)
# globals()['G'].N = N
# globals()['G'].flowshop = True
# globals()['Preshop'] = Queue(env,capacity=10)
# # globals()['R0'] = Router(env)
# globals()['R0'] = Router(env,capacity=10)

# globals()['T'] = Terminator(env)
# globals()['T']._name = 'terminator'

# for i in range(1,N+1):
#     globals()['Q'+str(i)] = Queue(env,'Q'+str(i),capacity=capIn)
#     globals()['M'+str(i)] = Server(env,'M'+str(i))
#     globals()['Qout'+str(i)] = Queue(env,'Qout'+str(i),capacity=capOut)
#     globals()['R'+str(i)] = Router(env)
    
# # g.Next = globals()['R0']
# globals()['G'].Next = globals()['Preshop']
# globals()['Preshop'].Next = globals()['R0']

# globals()['R0'].Next = list()
# for i in range(1,N+1):
#     globals()['R0'].Next.append(globals()['Q'+str(i)])

# for i in range(1,N+1):
#     globals()['Q'+str(i)].Next = globals()['M'+str(i)]
#     globals()['M'+str(i)].Next = globals()['Qout'+str(i)]
#     globals()['Qout'+str(i)].Next = globals()['R'+str(i)]
#     globals()['R'+str(i)].Next = list()
#     globals()['R'+str(i)].Next.append(globals()['T'])
#     for j in range(1,N+1):
#         globals()['R'+str(i)].Next.append(globals()['Q'+str(j)])

# np.random.seed(1)    
# env.run(3600)
    

