# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, CompositeState
from chfsm import function, do, on_entry, on_exit, on_interrupt
from stores import Store, Box
from core import Environment, Event
from simpy import AllOf, AnyOf
from simpy.events import PENDING 
import types
import numpy as np
from collections.abc import Iterable

class Server(CHFSM):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
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
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=1):
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
        self.QueueIn = Store(self.env,self.capacityIn)
    def put(self,item):
        return self.QueueIn.put(item)
    def subscribe(self,item):
        return self.QueueIn.subscribe(item)

class ServerDoubleBuffer(ServerWithBuffer):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=1,capacityOut=1):
        self.capacityOut = capacityOut
        super().__init__(env,name,serviceTime,serviceTimeFunction,capacityIn)
    def build_c(self):
        super().build_c()
        self.QueueOut = Store(self.env,self.capacityOut)
    def build(self):
        states = super().build()
        Block = states.pop(-2)
        Starve = states[0]
        GetOut = State('GetOut',True)
        @function(GetOut)
        def q(self):
            return AllOf(self.env,[self.QueueOut.subscribe(),self.connections['after'].subscribe(object())])
        @do(GetOut)
        def G(self,event):
            check = all(event.check() for event in event._events)
            if check:
                entity = event._events[0].confirm()
                event._events[1].item = entity
                event._events[1].confirm()
            return
        states.append(GetOut)
        @function(Block)
        def blockk(self):
            req = self.QueueOut.put(self.var.entity)
            return req
        @do(Block)
        def blockkk(self,event):
            self.var.request.confirm()
            return Starve
        states.append(Block)
        return states
        
class ManualStation(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
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
    def __init__(self, env, name=None, serviceTime=0,serviceTimeFunction=None,createEntity=None):
        super().__init__(env, name)
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        self.var.createEntity = createEntity
    def build(self):
        Create = State('Create',True)
        @function(Create)
        def fcn2(self):
            serviceTime = self.sm.calculateServiceTime(None)
            return self.env.timeout(serviceTime)
        @do(Create)
        def do2(self,event):
            try:
                self.var.entity = self.var.createEntity()
            except:
                self.var.entity = object()
            return Wait
        Wait = State('Wait')
        @function(Wait)
        def fcn(self):
            return self.connections['after'].put(self.var.entity)
            self.var.entity = None
        @do(Wait)
        def do1(self,event):
            return Create
        return [Create,Wait]        

class Operator(CHFSM):
    def __init__(self, env, name=None, station = []):
        super().__init__(env, name)
        self.var.station = station
        self.var.target = None
        self.var.Pause = env.event()
    def monitor(self):
        for station in reversed(self.var.station):
            if not station.var.operator and not station.var.WaitOperator.triggered:
                return station
        return
    def add_station(self,station):
        if station is Iterable:
            for s in station:
                self.var.station.append(s)
        else:
            self.var.station.append(station)
    def build(self):
        Idle = State('Idle',True)
        @function(Idle)
        def idleF(self):
            self.var.request = AnyOf(self.env,[station.var.NeedOperator for station in self.var.station])
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

class Queue(CHFSM):
    def __init__(self,env,name=None,capacity=None):
        if capacity==None:
            capacity = np.inf
        self.capacity = capacity
        super().__init__(env,name)
    def build_c(self):
        self.Queue = Store(env,self.capacity)
    def build(self):
        Forwarding = State('GetIn',True)
        @function(Forwarding)
        def q(self):
            return AllOf(self.env,[self.Queue.subscribe(),self.connections['after'].subscribe(object())])
        @do(Forwarding)
        def G(self,event):
            if all(event.check() for event in event._events):
                entity = event._events[0].confirm()
                event._events[1].item = entity
                event._events[1].confirm()
            return

class ManualStationWithCapacity(ManualStation):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacity=1):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.stop()
        self.var.capacity = capacity
        for i in range(self.var.capacity-1):
            states = self.build()
            for state in states:
                state._name += str(i)
                setattr(self, state._name, state)
        self.copy_states(True)
        self.associate()
        self.start()
    def copy_states(self,x=False):
        if x:
            super().copy_states()
            
class SwitchOut(CHFSM):
    def put(self,item):
        return self.Queue.put(item)
    def build_c(self):
        self.Queue = Box(self.env)
    def build(self):
        Work = State('Work',True)
        @function(Work)
        def W(self):
            self.var.requests = [after.subscribe(object()) for after in self.connections['after']]
            return AllOf(self.env,[self.Queue.subscribe(),*self.var.requests])
        @do(Work)
        def WW(self,event):
            if event._events[0].check() and any(event.check for event in self.var.requests):
                entity = event._events[0].confirm()
                for event in self.var.requests:
                    if event.check:
                        event.item = entity
                        event.confirm()
            return Work
        return [Work]

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



if False:
    env = Environment()
    a = ServerDoubleBuffer(env,'1',1,np.random.exponential)
    # a.put([1])
    # op = Operator(env, 'op1')
    # op.var.station = [a]
    b = Store(env,20)
    a.connections['after']=b
    g = Generator(env, 'g',0.5)
    g.connections['after'] = a
    env.run(20)


    import utils
    s = utils.stats(env)