# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 18:08:34 2023

@author: Lorenzo
"""
from sys import path
path.append('../')

from pymulate import Environment, Server, Generator, Terminator, StoreSelect, RouterNew
import numpy as np
import random as rnd
import pymulate
from chfsm import CHFSM, State, Transition
from stores import Store
import types
from simpy import AnyOf
import pymoo
from math import ceil

def restart(env):
    L = [o for o in env._objects if hasattr(o,'_states')]
    for t in [o[-1].callbacks[0].__self__ for o in env._queue]:
        for o in [o for o in env._objects if hasattr(o,'_states')]:
            for s in o._states:
                if t in s._transitions:
                    if o in L:
                        L.remove(o)
                        continue
    for el in L:
        el.stop()
        el.start()

    

def forrun(env,time):
    while env.now < time:
        [o.start() for o in env._objects if hasattr(o,'current_state') and o.current_state == []]
        env.step()
class Server(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        self.WL = 0
        super().__init__(env,name,serviceTime,serviceTimeFunction)

    T2=Transition(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)),action=lambda self:(self.var.entity.route.pop(0),self.env.awakeCtrl.succeed() if not self.env.awakeCtrl.triggered else (self.env.awakeCtrl.restart(),self.env.awakeCtrl.succeed())))

class Queue(CHFSM):
    def __init__(self, env, name=None, capacity=np.inf):
        self.capacity = capacity
        self.sortingFcn = None
        self.DR = 'FIFO'
        super().__init__(env,name)
    def sort(self):
        if self.DR == 'FIFO':
            X = self.Store.items
            Y = [item.entryTime[self.name] for item in self.Store.items]
            self.Store.items = [x for _,x in sorted(zip(Y,X))]
        elif self.DR == 'SPT':
            X = self.Store.items
            Y = [sum(item.serviceTime.values()) for item in self.Store.items]
            self.Store.items = [x for _,x in sorted(zip(Y,X))]
        elif self.DR == 'LPT':
            X = self.Store.items
            Y = [-sum(item.serviceTime.values()) for item in self.Store.items]
            self.Store.items = [x for _,x in sorted(zip(Y,X))]
        elif self.DR == 'EDD':
            X = self.Store.items
            Y = [item.dueDate for item in self.Store.items]
            self.Store.items = [x for _,x in sorted(zip(Y,X))]
        elif self.DR == 'Slack':
            X = self.Store.items
            Y = [item.dueDate - self.env.now - sum([item.serviceTime[i] for i in item.route]) for item in self.Store.items]
            self.Store.items = [x for _,x in sorted(zip(Y,X))]
        elif self.DR == 'Slack/OPN':
            X = self.Store.items
            Y = [(item.dueDate - self.env.now - sum([item.serviceTime[i] for i in item.route]))/len(item.route) for item in self.Store.items]
            self.Store.items = [x for _,x in sorted(zip(Y,X))]
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
            self.var.r2 = self.Next.put(self.var.entity)
    T1=Transition(Retrieving,Forwarding,lambda self: self.var.request)
    # T2=Transition(Forwarding,Retrieving,lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())
    T2=Transition(Forwarding,Retrieving,lambda self: self.var.r2,action=lambda self: self.var.request.confirm())

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
        entity = Entity(ID=self.count,serviceTime=T,createTime=self.env.now,dueDate=dueDate)
        x = np.random.choice(listOfMachineNames,rnd.randint(1,self.N))
        if self.flowshop:
            x.sort()
        # x.sort()
        entity.route = x
        entity.route = [x[0]]
        for machine in listOfMachineNames:
            if machine in entity.route:
                pass
            else:
                entity.serviceTime[machine]=0
        return entity

class RShop(RouterNew):
    class Empty(State):
        pass
    def condition_check(self,item,target):
        if len(item.route) == 0 and type(target) is Terminator:
            return True
        elif len(item.route)>0:
            if item.route[0][1:]==target._name[1:]:
                return True
            else:
                return False
        else:
            return False
    S2E = Transition(RouterNew.Sending,Empty,lambda self:self.env.timeout(5))
    E2S = Transition(Empty,RouterNew.Sending,None)

'''        
class RNO(Router):
    def __init__(self, env, name=None,capacity=np.inf):
        self.released = 0
        self.CONWIP = 20
        self.terminator = None
        super().__init__(env, name,capacity)  
    def condition_check(self,item,target):
        #release control
        if self.released - len(self.terminator.items) < self.CONWIP:
            self.released += 1
            pass
        else:
            # pass
            return False          
        return super().condition_check(item,target)
    S2S3 = Transition(Router.Sending,Router.Sending,lambda self:self.env.awakeCtrl)
    # # S2S3 = Transition(Router.Sending,Router.Sending,lambda self:self.env.awakeCtrl,action = lambda self:self.env.awakeCtrl.restart())
    def action(self):
    #     self.Queue._trigger_put(self.env.event())
    #     self.Queue.put_event.restart()
        print(1)
        self.env.awakeCtrl.restart()
        # pass
        # self.released += 1
    S2S3._action = action
    # S2S4 = Transition(Router.Sending,Router.Sending,lambda self:self.env.timeout(10))
'''
class RPreShop(CHFSM):
    def __init__(self, env, name=None,capacity=np.inf):
        self.capacity = capacity
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.sent = []
        self.released = 0
        self.CONWIP = 20
        self.terminator = None
        self.DR = 'FIFO'
        self.putEvent = env.event()
    def build(self):
        self.Queue = Store(self.env,self.capacity)
    def sort(self):
        if self.DR == 'FIFO':
            X = self.Queue.items
            Y = [item.entryTime[self.name] for item in self.Queue.items]
            self.Queue.items = [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
        elif self.DR == 'SPT':
            X = self.Queue.items
            Y = [sum(item.serviceTime.values()) for item in self.Queue.items]
            self.Queue.items = [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
        elif self.DR == 'LPT':
            X = self.Queue.items
            Y = [-sum(item.serviceTime.values()) for item in self.Queue.items]
            self.Queue.items = [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
        elif self.DR == 'EDD':
            X = self.Queue.items
            Y = [item.dueDate for item in self.Queue.items]
            self.Queue.items = [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
        elif self.DR == 'Slack':
            X = self.Queue.items
            Y = [item.dueDate - self.env.now - sum([item.serviceTime[i] for i in item.route]) for item in self.Queue.items]
            self.Queue.items = [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
        elif self.DR == 'Slack/OPN':
            X = self.Queue.items
            Y = [(item.dueDate - self.env.now - sum([item.serviceTime[i] for i in item.route]))/len(item.route) for item in self.Queue.items]
            self.Queue.items = [x for _, x in sorted(zip(Y, X), key=lambda pair: pair[0])]
    def condition_check(self,item,target):
        if self.released - len(self.terminator.items) < self.CONWIP:
            pass
        else:
            return False
        if len(item.route) == 0 and type(target) is Terminator:
            return True
        elif len(item.route)>0:
            if item.route[0][1:]==target._name[1:]:
                return True
            else:
                return False
        else:
            return False
    def put(self,item):
        if not hasattr(item,'entryTime'):
            item.entryTime = {}
        item.entryTime[self.name] = self.env.now
        self.sort()
        if self.putEvent.triggered:
            self.putEvent.restart()
        self.putEvent.succeed()
        return self.Queue.put(item)
    class Sending(State):
        initial_state = True
        def _do(self):
            self.sm.putEvent.restart()
            self.sm.var.requestIn = self.sm.putEvent
            self.sm.var.requestOut = [item for sublist in [[next.subscribe(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
            if self.sm.var.requestOut == []:
                self.sm.var.requestOut.append(self.sm.var.requestIn)
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
    def action2(self):
        self.Queue._trigger_put(self.env.event())
        # if hasattr(self.Queue,'put_event'):
        #     if self.Queue.put_event.triggered:
        #         self.Queue.put_event.restart()
        #     self.Queue.put_event.succeed()
        # if len(self.Queue) < self.Queue.capacity and len(self.Queue.put_queue)>0:
        #     self.Queue._trigger_put(self.Queue.put_queue[0])
        if not hasattr(self.var.requestOut[0],'item'):
            # self.Queue.put_event.restart()
            return
        for request in self.var.requestOut:
            if not request.item in self.Queue.items:
                request.cancel()
                continue
            if request.triggered:
                if request.check():
                    request.confirm()
                    self.Queue.items.remove(request.item)
                    continue
    S2S2._action = action2
        
        
        
        
        
        
        
        
        
        
        
        
'''
        return self.Store.put(item)
    def build(self):
        self.Queue = Store(self.env,self.capacity)
    def condition_check(self,item,target):
        if self.released - len(self.terminator.items) < self.CONWIP:
            pass
        else:
            return False
        if len(item.route) == 0 and type(target) is Terminator:
            return True
        elif len(item.route)>0:
            if item.route[0][1:]==target._name[1:]:
                return True
            else:
                return False
        else:
            return False
    def put(self,item):
        return self.Queue.put(item)
    class Sending(State):
        initial_state = True
        def _do(self):
            self.sm.var.requestIn = [self.sm.Queue.put_event,self.env.awakeCtrl]
            self.sm.var.requestOut = [item for sublist in [[next.subscribe(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
            if self.sm.var.requestOut == []:
                self.sm.var.requestOut = self.sm.var.requestIn
    S2S1 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestIn))
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
    def action(self):
        self.Queue._trigger_put(self.env.event())
        self.Queue.put_event.restart()
        self.env.awakeCtrl.restart()
    S2S1._action = action
    def action2(self):
        self.Queue._trigger_put(self.env.event())
        if not hasattr(self.var.requestOut[0],'item'):
            self.Queue.put_event.restart()
            return
        for request in self.var.requestOut:
            if not request.item in self.Queue.items:
                request.cancel()
                continue
            if request.triggered:
                if request.check():
                    request.confirm()
                    self.Queue.items.remove(request.item)
                    self.sm.released += 1
                    continue
    S2S2._action = action2
'''
class Terminator(Terminator):
    def __init__(self, env, capacity=np.inf):
        super().__init__(env, capacity)
        self.register = list()
        self._name = 'terminator'
    def put(self, item):
        item.completionTime = self._env.now
        self.register.append(self._env.now)
        super().put(item)
    def subscribe(self,item):
        self.register.append(self._env.now)
        item.completionTime = self._env.now
        return super().subscribe(item)
    
# def WL(item):   
#     for s in item.route:
#         if item.load[s] + globals()[s] < globals()['N'][s]:
#             pass
#         else:
#             return False
#     for s in item.route:
#         Ws += pij/i[s]
#         return True



# %%  test system

env = Environment()
env.awakeCtrl = env.event()

N=5
capIn = 10
capOut = 5

globals()['G']=Generator(env)
globals()['G'].N = N
globals()['G'].flowshop = False
globals()['Preshop'] = Queue(env,'preshop',capacity=20)
globals()['R0'] = RPreShop(env,'R0',capacity=2)

globals()['T'] = Terminator(env)
globals()['T']._name = 'terminator'

globals()['R0'].terminator = globals()['T'] 

for i in range(1,N+1):
    globals()['Q'+str(i)] = Queue(env,'Q'+str(i),capacity=capIn)
    globals()['M'+str(i)] = Server(env,'M'+str(i))
    globals()['R'+str(i)] = RShop(env,'R'+str(i),capacity=capOut)
    
    
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
# env.run(3600)



def getbyname(List,name):
    for item in List:
        if item._name == name:
            return item


def main(flowshop=False,N=5,capIn=5,capOut=5):
    env = Environment()
    env.awakeCtrl = env.event()


    locals()['G']=Generator(env)
    locals()['G'].N = N
    locals()['G'].flowshop = flowshop
    locals()['Preshop'] = Queue(env,'preshop',capacity=30)
    locals()['R0'] = RPreShop(env,'R0',capacity=30)

    locals()['T'] = Terminator(env)
    locals()['T']._name = 'terminator'
    env._objects.append(locals()['T'])
    
    locals()['R0'].terminator = locals()['T'] 

    for i in range(1,N+1):
        locals()['Q'+str(i)] = Queue(env,'Q'+str(i),capacity=capIn)
        locals()['M'+str(i)] = Server(env,'M'+str(i))
        locals()['R'+str(i)] = RShop(env,'R'+str(i),capacity=capOut)
        
    # g.Next = locals()['R0']
    locals()['G'].Next = locals()['Preshop']
    locals()['Preshop'].Next = locals()['R0']

    locals()['R0'].Next = list()
    for i in range(1,N+1):
        locals()['R0'].Next.append(locals()['Q'+str(i)])

    for i in range(1,N+1):
        locals()['Q'+str(i)].Next = locals()['M'+str(i)]
        locals()['M'+str(i)].Next = locals()['R'+str(i)]
        locals()['R'+str(i)].Next = list()
        locals()['R'+str(i)].Next.append(locals()['T'])
        for j in range(1,N+1):
            locals()['R'+str(i)].Next.append(locals()['Q'+str(j)])
    
    return env
    # env.run(100)

class sys():
    def __init__(self,flowshop=False,N=5,capIn=5,capOut=5):
        env = Environment()
        env.awakeCtrl = env.event()
    
    
        self.G=Generator(env)
        self.G.N = N
        self.G.flowshop = flowshop
        self.Preshop = Queue(env,'preshop',capacity=30)
        self.R0 = RPreShop(env,'R0',capacity=30)
    
        self.T = Terminator(env)
        self.T._name = 'terminator'
        env._objects.append(self.T)
        
        self.R0.terminator = self.T 
    
        for i in range(1,N+1):
            setattr(self,'Q'+str(i),Queue(env,'Q'+str(i),capacity=capIn))
            setattr(self,'M'+str(i),Server(env,'M'+str(i)))
            setattr(self,'R'+str(i),RShop(env,'R'+str(i),capacity=capOut))
            
        # g.Next = self.R0
        self.G.Next = self.Preshop
        self.Preshop.Next = self.R0
    
        self.R0.Next = list()
        for i in range(1,N+1):
            self.R0.Next.append(getattr(self,'Q'+str(i)))
    
        for i in range(1,N+1):
            getattr(self,'Q'+str(i)).Next =  getattr(self,'M'+str(i))
            getattr(self,'M'+str(i)).Next =  getattr(self,'R'+str(i))
            getattr(self,'R'+str(i)).Next = list()
            getattr(self,'R'+str(i)).Next.append(getattr(self,'T'))
            for j in range(1,N+1):
                getattr(self,'R'+str(i)).Next.append(getattr(self,'Q'+str(j)))
        
        self.env=env
    # env.run(100)



# %%
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Real, Integer, Choice, Binary
from copy import deepcopy
import pandas as pd
from pymoo.algorithms.moo.nsga2 import RankAndCrowdingSurvival
from pymoo.core.mixed import MixedVariableGA
from pymoo.core.variable import Real, Integer
from pymoo.optimize import minimize
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.decomposition.weighted_sum import WeightedSum

class MixedVariableProblem(ElementwiseProblem):
    def __init__(self, env, time=3600, steps=1, N=5, **kwargs):
        self.env = env
        self.time = time
        self.steps = steps
        vars = {}
        for s in range(steps):
            for n in range(0,1+N):
                vars['dr_Q'+str(n)+'_'+str(s)]=Choice(options=['FIFO','SPT','LPT','EDD','Slack','Slack/OPN'])
        for s in range(steps):
            vars['wl_'+str(s)] = Integer(bounds=(10, 20))
        super().__init__(vars=vars, n_obj=1, **kwargs)
    def _evaluate(self, X, out, *args, **kwargs):
        env = deepcopy(self.env)
                
        # [o.start() for o in env._objects if type(o) in [RShop,RPreShop]]
        # c0 = len(getbyname(env._objects,'terminator').items)
        for step in range(self.steps):
            for obj in env._objects:
                if obj._name[0] == 'Q':
                    obj.DR = X['dr_'+obj._name+'_'+str(step)]
                elif obj._name == 'R0':
                    obj.DR = X['dr_'+'Q0'+'_'+str(step)]
                    obj.CONWIP = X['wl_'+str(step)]
                # elif obj._name == 'preshop':
                #     obj.items.pop(rnd.randint(0,-1+len(obj.items)))
            
            np.random.RandomState().set_state(globals()['rndState'])
            # print([obj for obj in env._objects if obj._name=='Q1'][0].DR , X['dr_'+'Q1'+'_'+str(step)])
            # t0=(env.now)
            env.run(env.now + self.time/self.steps)
            # t1=(env.now)
        T = getbyname(env._objects,'terminator')
        # c1 = len(getbyname(env._objects,'terminator').items)
        # print(c0,c1)#,t0,t1)
        items = [i for i in T.items if i.completionTime>(env.now-self.time)]

        TH = pd.DataFrame(T.register[-len(items):]).diff().mean()[0]
        Tardiness = 0
        for item in items:
            Tardiness += max(0,item.completionTime - item.dueDate)
        out["F"] = Tardiness


class MixedVariableProblemMulti(ElementwiseProblem):
    def __init__(self, env, time=3600, steps=1, N=5, **kwargs):
        self.env = env
        self.time = time
        self.steps = steps
        vars = {}
        for s in range(steps):
            for n in range(0,1+N):
                vars['dr_Q'+str(n)+'_'+str(s)]=Choice(options=['FIFO','SPT','LPT','EDD','Slack','Slack/OPN'])
        for s in range(steps):
            vars['wl_'+str(s)] = Integer(bounds=(10, 20))
        super().__init__(vars=vars, n_obj=2, **kwargs)
    def _evaluate(self, X, out, *args, **kwargs):
        e2 = deepcopy(self.env)
        # [o.start() for o in env._objects if type(o) in [RShop,RPreShop]]
        # c0 = len(getbyname(env._objects,'terminator').items)
        for step in range(self.steps):
            for obj in env._objects:
                if obj._name[0] == 'Q':
                    obj.DR = X['dr_'+obj._name+'_'+str(step)]
                elif obj._name == 'R0':
                    obj.DR = X['dr_'+'Q0'+'_'+str(step)]
                    obj.CONWIP = X['wl_'+str(step)]
            
            np.random.RandomState().set_state(globals()['rndState'])
            # print([obj for obj in env._objects if obj._name=='Q1'][0].DR , X['dr_'+'Q1'+'_'+str(step)])
            # t0=(env.now)
            e2.run(e2.now + self.time/self.steps)
            # t1=(env.now)
        T = getbyname(e2._objects,'terminator')
        # c1 = len(getbyname(env._objects,'terminator').items)
        # print(c0,c1,t0,t1)
        items = [i for i in T.items if i.completionTime>(e2.now-self.time)]

        TH = pd.DataFrame(T.register[-len(items):]).diff().mean()[0]
        # TH = 3600/pd.DataFrame(T.register[-len(items):]).diff().mean()[0]

        Tardiness = 0
        for item in T.items:
            Tardiness += max(0,item.completionTime - item.dueDate)
        Tardiness = Tardiness/1000
        out["F"] = [Tardiness, TH]

class Problem(ElementwiseProblem):
    def __init__(self,env,time=3600,steps=1,N=5,**kwargs):
        self.env = env
        self.time = time
        self.steps = steps
        self.N = N
        self.options = ['FIFO','SPT','LPT','EDD','Slack','Slack/OPN']
        self.WIPbounds = [15,30]
        n_var = (N+1)*steps*len(self.options) + 1
        super().__init__(n_var=n_var, n_obj=2, xl=0.0, xu=1.0)
    def _evaluate(self, x, out, *args, **kwargs):
        # separate
        e2 = deepcopy(self.env)
        X=dict()
        dr=iter([self.options[i] for i in np.floor(x[:-1]*6).astype(int)])
        for s in range(self.steps):
            for n in range(0,1+self.N):
                X['dr_Q'+str(n)+'_'+str(s)]=next(dr)
        for s in range(self.steps):
            X['wl_'+str(s)] = np.round(x[-1]*(self.WIPbounds[1]-self.WIPbounds[0])+self.WIPbounds[0]).astype(int)
        
        for step in range(self.steps):
            for obj in env._objects:
                if obj._name[0] == 'Q':
                    obj.DR = X['dr_'+obj._name+'_'+str(step)]
                elif obj._name == 'R0':
                    obj.DR = X['dr_'+'Q0'+'_'+str(step)]
                    obj.CONWIP = X['wl_'+str(step)]
        
        np.random.RandomState().set_state(globals()['rndState'])
        e2.run(e2.now+self.time/self.steps)
    
        T = getbyname(e2._objects,'terminator')
        TH = pd.DataFrame(T.register).diff().mean()[0]
        Tardiness = 0
        for item in T.items:
            Tardiness += max(0,item.completionTime - item.dueDate)
        out["F"] = Tardiness, TH


np.random.seed(1)
rndState = np.random.RandomState().get_state()
env = main(N=6)

if 0:
    problem = MixedVariableProblem(env)
    algorithm = MixedVariableGA(pop=2)
    res = minimize(problem,algorithm,termination=('n_gen', 5),seed=1,verbose=True)


def optim(env,time,steps,N):
    problem = MixedVariableProblem(env,time,steps,N)
    algorithm = MixedVariableGA(pop_size=20)
    res = minimize(problem,
                   algorithm,
                   termination=('n_gen', 5),
                   seed=1,
                   verbose=True)
    return res

def optim2(env,time,steps,N):
    problem = Problem(env,time,steps,N)
    algorithm = NSGA2(pop=5)
    res = minimize(problem,
                   algorithm,
                   termination=('n_gen', 10),
                   seed=1,
                   verbose=True)
    return res

def optim12(env,time,steps,N):
    problem = MixedVariableProblemMulti(env,time,steps,N)
    algorithm = MixedVariableGA(pop_size=20, survival=RankAndCrowdingSurvival())
    res = minimize(problem,
                   algorithm,
                   termination=('n_gen', 2),
                   seed=1,
                   verbose=True)
    return res



# print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))

# %% 
# np.random.seed(1)
# s= sys()
# s.env.run(100)
# np.random.seed(1)
# s2=deepcopy(s)
# s2.env.run(7200)
# print(s.T.items.__len__(),s2.T.items.__len__())
# s2.R0.Queue._trigger_put(s2.env.event())


#deepcopy run non va prova a usare una classe
Tardiness1 = list()
TH1 = list()
for exp in range(10):
    N = 6
    flowshop = False
    np.random.seed(exp)
    rndState = np.random.RandomState().get_state()
    env = main(flowshop,N)
    
    for i in range(12):
        res = optim12(env,N=N,time=900,steps=3)
        if False:
            X = res.X
        else:
            dm = WeightedSum()
            weights = np.array([0.5, 0.5])
            I = dm(res.F, weights).argmin()
            X = res.pop[I].X
        for obj in env._objects:
            if obj._name[0] == 'Q':
                obj.DR = X['dr_'+obj._name+'_'+str(0)]
            elif obj._name == 'R0':
                obj.CONWIP = X['wl_'+str(0)]
                obj.DR = X['dr_'+'Q0'+'_'+str(0)]
        
        np.random.RandomState().set_state(rndState)
        env.run(env.now+300)
        rndState = np.random.RandomState().get_state()
    T=getbyname(env._objects, 'terminator')
    Tardiness = 0
    for item in T.items:
        Tardiness += max(0,item.completionTime - item.dueDate)
    Tardiness1.append(Tardiness)
    TH = 3600/pd.DataFrame(T.register[-len(T.items):]).diff().mean()[0]
    TH1.append(TH)
    print(Tardiness,TH)


# %%
TH2 = list()
Tardiness2=list()
for exp in range(1):
    N=6
    flowshop = False
    np.random.seed(1)
    env = main(N=N, flowshop=False)
    env.run(100)
    res = optim12(env,time=3600,steps=1,N=N)
    if False:
        X = res.X
    else:
        dm = WeightedSum()
        weights = np.array([0.5, 0.5])
        I = dm(res.F, weights).argmin()
        X = res.pop[I].X
    for obj in env._objects:
        if obj._name[0] == 'Q':
            obj.DR = X['dr_'+obj._name+'_'+str(0)]
        elif obj._name == 'R0':
            obj.CONWIP = X['wl_'+str(0)]
            obj.DR = X['dr_'+'Q0'+'_'+str(0)]
    np.random.seed(1)
    env.run(3600)
    T=getbyname(env._objects, 'terminator')
    Tardiness = 0
    for item in T.items:
        Tardiness += max(0,item.completionTime - item.dueDate)
    TH = 3600/pd.DataFrame(T.register[-len(T.items):]).diff().mean()[0]
    TH2.append(TH)
    Tardiness2.append(Tardiness)
    print(Tardiness,TH)
