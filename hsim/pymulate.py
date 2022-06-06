# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, CompositeState
from chfsm import function, do, on_entry, on_exit, on_interrupt
from stores import Store
from core import Environment, Event
from simpy import AllOf, AnyOf
from simpy.events import PENDING 
import types
import numpy as np

class Server(CHFSM):
    def __init__(self,env,name,serviceTime=None,serviceTimeFunction=None):
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
        super().__init__(env, name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
    def build(self):
        Starve = State('Starve',True)
        @function(Starve)
        def starveF(self):
            self.var.request = self.Store.subscribe()
            return self.var.request
        @do(Starve)
        def starveDo(self,event):
            self.var.entity = event.read()
            return Work
        Work = State('Work')
        @function(Work)
        def workF(self):
            serviceTime = self.sm.calculateServiceTime(self.var.entity)
            return self.env.timeout(serviceTime)
        @do(Work)
        def workDo(self,event):
            return Block
        Block = State('Block')
        @function(Block)
        def blockk(self):
            req = self.connections['after'].put(self.var.entity)
            return req
        @do(Block)
        def blockkk(self,event):
            self.var.request.confirm()
            return Starve
        return [Starve,Work,Block]
    def build_c(self):
        self.Store = Store(self.env,1)
    def put(self,item):
        return self.Store.put(item)
    def subscribe(self,item):
        return self.Store.subscribe(item)
    
        
class ServerWithBuffer(Server):
    def __init__(self,env,name,serviceTime=None,serviceTimeFunction=None,capacityIn=1):
        self.capacityIn = capacityIn
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def build(self):
        states = super().build()
        GetIn = State('GetIn',True)
        @function(GetIn)
        def q(self):
            return AllOf(self.env,[self.QueueIn.subscribe(),self.Store.subscribe(object())])
        @do(GetIn)
        def G(self,event):
            if all(event.check() for event in event._events):
                entity = event._events[0].confirm()
                event._events[1].item = entity
                event._events[1].confirm()
            return
        states.append(GetIn)
        return states
    def build_c(self):
        super().build_c()
        self.QueueIn = Store(env,self.capacityIn)
    def put(self,item):
        return self.QueueIn.put(item)
    def subscribe(self,item):
        return self.QueueIn.subscribe(item)
        
class AssemblyStation(Server):
    def __init__(self,env,name,serviceTime=None,serviceTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.var.operator = list()
        self.var.NeedOperator = env.event()
        self.var.WaitOperator = env.event()
    def build(self):
        Starve = State('Starve',True)
        @function(Starve)
        def starveF(self):
            self.var.request = self.Store.subscribe()
            return self.var.request
        @do(Starve)
        def starveDo(self,event):
            self.var.entity = event.read()
            return Idle
        Idle = State('Idle')
        @function(Idle)
        def idlef(self):
            self.var.NeedOperator.succeed()
            return self.var.WaitOperator
        @do(Idle)
        def idledo(self,event):
            self.var.NeedOperator.restart()
            self.var.WaitOperator.restart()
            return Work
        Work = State('Work')
        @function(Work)
        def workF(self):
            serviceTime = self.sm.calculateServiceTime(self.var.entity)
            return self.env.timeout(serviceTime)
        @do(Work)
        def workDo(self,event):
            self.var.operator.var.Pause.succeed()
            self.var.operator = None
            return Block
        Block = State('Block')
        @function(Block)
        def blockk(self):
            req = self.connections['after'].put(self.var.entity)
            return req
        @do(Block)
        def blockkk(self,event):
            self.var.request.confirm()
            return Starve
        return [Starve,Idle,Work,Block]
        
class Generator(CHFSM):
    def build(self):
        Work = State('Work',True)
        @function(Work)
        def fcn(self):
            entity = [1]
            return self.connections['after'].put(entity)
        @do(Work)
        def do1(self,event):
            return Work
        return [Work]        


class Operator(CHFSM):
    def __init__(self, env, name, station = []):
        super().__init__(env, name)
        self.var.station = station
        self.var.target = None
        self.var.Pause = env.event()
    def monitor(self):
        for station in reversed(self.var.station):
            if not station.var.operator and not station.var.WaitOperator.triggered:
                return station
        return
    def build(self):
        Idle = State('Idle',True)
        @function(Idle)
        def idleF(self):
            self.var.request = AnyOf(env,[station.var.NeedOperator for station in self.var.station])
            return self.var.request
        @do(Idle)
        def idleDo(self,event):
            self.var.target = self.sm.monitor()
            if self.var.target is not None:
                return Work
            else:
                return
        Work = State('Work')
        @function(Work)
        def workF(self):
            self.var.target.var.operator = self.sm
            self.var.target.var.WaitOperator.succeed()
            self.var.Pause.restart()
            return self.var.Pause
        @do(Work)
        def workDo(self,event):
            return Idle
        return [Idle,Work]


def calculateServiceTime(self,entity,attribute='serviceTime'):
    if self.var.serviceTimeFunction == None:
        if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
            return self.var.serviceTime
        elif self.var.serviceTime == None:
            time = getattr(self.var.entity,attribute)
            if type(time) is dict:
                time = time[self.name]
            return time
        elif len(self.var.serviceTime)==0:
            time = getattr(self.var.entity,attribute)
            if type(time) is dict:
                time = time[self.name]
            return time
        elif len(self.var.serviceTime)>0:
            return self.var.serviceTime[0]
    elif self.var.serviceTimeFunction != None:
        if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
            return self.var.serviceTimeFunction(self.var.serviceTime)
        elif self.var.serviceTime==None:
            time = getattr(self.var.entity,attribute)
            if type(time) is dict:
                time = time[self.name]
            return self.var.serviceTimeFunction(time)
        elif len(self.var.serviceTime)==0:
            return self.var.serviceTimeFunction()
        elif len(self.var.serviceTime)>0:
            return self.var.serviceTimeFunction(*self.var.serviceTime)




env = Environment()
a = AssemblyStation(env,'1',1,np.random.exponential)
# a.put([1])
op = Operator(env, 'op1')
op.var.station = [a]
b = Store(env,20)
a.connections['after']=b
g = Generator(env, 'g')
g.connections['after'] = a
env.run(25)


        