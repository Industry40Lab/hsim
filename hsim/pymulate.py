# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, Transition, add_states, trigger, Pseudostate
from chfsm import function, do
from stores import Store, Box
from core import Environment, Event
from simpy import AllOf, AnyOf
from simpy.events import PENDING 
import types
import numpy as np
from collections.abc import Iterable
from copy import deepcopy

# %% add
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
        try:
            if self.var.serviceTime==None:
                time = getattr(self.var.entity,attribute)
                if type(time) is dict:
                    time = time[self.name]
                return self.var.serviceTimeFunction(time)
        except:
            pass
        if len(self.var.serviceTime)==0:
            return self.var.serviceTimeFunction()
        elif len(self.var.serviceTime)>0:
            return self.var.serviceTimeFunction(*self.var.serviceTime)



# %% easy server    
class Server(CHFSM):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        super().__init__(env,name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
    def build(self):
        self.Store = Store(self.env,1)
        
Starving = State('Starving',True)
@function(Starving)
def f(self):
    self.var.request = self.Store.subscribe()
Working = State('Working') 
@function(Working)
def f(self):
    self.var.entity = self.var.request.read()
    # print('%d %s' %(self.env.now,self.var.entity))
Blocking = State('Blocking')
S2W = Transition(Starving, Working, lambda self: self.var.request)
W2B = Transition(Working, Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
B2S = Transition(Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())
Starving._transitions = [S2W]
Working._transitions = [W2B]
Blocking._transitions = [B2S]
Server._states = [Starving,Working,Blocking]


if __name__ == '__main__':
    env = Environment()
    a = Server(env,serviceTime=1)
    a.Next = Store(env,5)
    for i in range(1,6):
        a.Store.put(i)
    env.run(20)
    if type(a.current_state[0]) is type(Blocking) and len(a.Next) == 5:
        print('OK')

# %% server w/ buffer
class ServerWithBuffer(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=np.inf):
        self.capacityIn = capacityIn
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def build(self):
        super().build()
        self.QueueIn = Store(self.env,self.capacityIn)
Retrieving = State('Retrieving',True)
@function(Retrieving)
def f1(self):
    self.var.requestIn = self.QueueIn.subscribe()
Forwarding = State('Forwarding')
@function(Forwarding)
def f2(self):
    self.var.entityIn = self.var.requestIn.read()
r2f = Transition(Retrieving,Forwarding,lambda self: self.var.requestIn)
f2r = Transition(Forwarding,Retrieving,lambda self: self.Store.put(self.var.entityIn),action=lambda self:self.var.requestIn.confirm())
Retrieving._transitions = [r2f]
Forwarding._transitions = [f2r]
ServerWithBuffer._states = Server._states + [Retrieving,Forwarding]
if __name__ == '__main__':
    env = Environment()
    a = ServerWithBuffer(env,serviceTime=1)
    a.Next = Store(env,5)
    for i in range(1,10):
        a.QueueIn.put(i)
    env.run(10)
    if type(a.current_state[0]) is type(Blocking) and len(a.Next) == 5:
        print('OK')

# %% ServerDoubleBuffer

class ServerDoubleBuffer(ServerWithBuffer):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=np.inf,capacityOut=np.inf):
        self.capacityOut = capacityOut
        super().__init__(env,name,serviceTime,serviceTimeFunction,capacityIn)
    def build(self):
        super().build()
        self.QueueOut = Store(self.env,self.capacityOut)

RetrievingOut = State('RetrievingOut',True)
@function(RetrievingOut)
def f3(self):
    self.var.requestOut = self.QueueOut.subscribe()
ForwardingOut = State('ForwardingOut')
@function(ForwardingOut)
def f4(self):
    self.var.entityOut = self.var.requestOut.read()
r2fOut = Transition(RetrievingOut,ForwardingOut,lambda self: self.var.requestOut)
f2rOut = Transition(ForwardingOut,RetrievingOut,lambda self: self.Next.put(self.var.entityOut),action=lambda self:self.var.requestOut.confirm())
RetrievingOut._transitions = [r2fOut]
ForwardingOut._transitions = [f2rOut]


ServerDoubleBuffer._states = deepcopy(ServerWithBuffer._states)
Blocking = ServerDoubleBuffer._states_dict('Blocking')
B2S = Transition(Blocking, ServerDoubleBuffer._states_dict('Starving'), lambda self: self.QueueOut.put(self.var.entity),action=lambda self: self.var.request.confirm())
Blocking._transitions = [B2S]
ServerDoubleBuffer._states += [RetrievingOut,ForwardingOut]

if __name__ == '__main__':
    env = Environment()
    a = ServerDoubleBuffer(env,serviceTime=1,capacityOut=5)
    a.Next = Store(env,5)
    for i in range(1,10):
        a.QueueIn.put(i)
    env.run(10)
    if type(a.current_state[0]) is type(Blocking) and len(a.Next) == 5 and len(a.QueueOut) == 4:
        print('OK')

# %% generator

class Generator(CHFSM):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        super().__init__(env,name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
    def createEntity(self):
        return object()
Waiting = State('Waiting',True)
Sending = State('Sending')
@function(Waiting)
def f5(self):
    self.var.entity = self.createEntity()
W2S = Transition(Waiting,Sending,lambda self: self.Next.put(self.var.entity))
S2W = Transition(Sending,Waiting,lambda self: self.env.timeout(self.calculateServiceTime(None)))
Waiting._transitions = [W2S]
Sending._transitions = [S2W]

Generator._states = [Waiting,Sending]

if __name__ == '__main__':
    env = Environment()
    a = Generator(env,serviceTime=1)
    a.Next = Store(env,5)
    env.run(10)
    if type(a.current_state[0]) is type(Waiting) and len(a.Next) == 5:
        print('OK')

# %% old
raise BaseException('End')

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
            return AllOf(self.env,[self.QueueOut.subscribe(),self.sm.connections['after'].subscribe(('prova'))])
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
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.var.station = list()
        self.var.target = None
        self.var.Pause = env.event()
    def monitor(self):
        for station in reversed(self.var.station):
            if station.var.NeedOperator.triggered and not station.var.operator and not station.var.WaitOperator.triggered:
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
        self.Queue = Store(self.env,self.capacity)
    def build(self):
        Forwarding = State('GetIn',True)
        @function(Forwarding)
        def q(self):
            return AllOf(self.env,[self.Queue.subscribe(),self.connections['after'].subscribe([0])])
        @do(Forwarding)
        def G(self,event):
            if all(event.check() for event in event._events):
                entity = event._events[0].read()
                event._events[1].confirm(entity)
                event._events[0].confirm()
            return
        return [Forwarding]
    def put(self,item):
        return self.Queue.put(item)
    def subscribe(self,item=None):
        return self.Queue.subscribe(item)

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
    def subscribe(self,item=None):
        return self.Queue.subscribe(item)
    def build_c(self):
        self.Queue = Box(self.env)
    def build(self):
        Work = State('Work',True)
        @function(Work)
        def W(self):
            print(self.sm)
            self.var.requests = [after.subscribe(['prova 1']) for after in self.connections['after']]
            self.var.x = AllOf(self.env,[self.Queue.subscribe(),AnyOf(self.env,self.var.requests)])
            return self.var.x
        @do(Work)
        def WW(self,event):
            if event._events[0].check() and any([event.check() for event in self.var.requests]):
                entity = event._events[0].confirm()
                for event in self.var.requests:
                    if event.check():
                        event.item = entity
                        event.confirm()
                        self.var.requests.remove(event)
                        break
                for event in self.var.requests:
                    event.cancel()
            return
        return [Work]



class MachineMIP(Server):
    def build(self):
        Starve = State('Starve',True)
        @function(Starve)
        def starveF(self):
            self.var.request = self.Store.subscribe()
            return self.var.request
        @do(Starve)
        def starveDo(self,event):
            self.var.entity = event.read()
            if np.random.uniform() < self.var.failure_rate:
                return Fail
            return Work
        Fail = State('Fail')
        @function(Fail)
        def failF(self):
            return self.env.timeout(self.var.TTR)
        @do(Fail)
        def failDo(self,event):
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
            self.var.req = req
            return req
        @do(Block)
        def blockkk(self,event):
            self.var.request.confirm()
            return Starve
        return [Starve,Fail,Work,Block]
        
class SwitchQualityMIP(CHFSM):
    def __init__(self, env, name=None):
        super().__init__(env,name)
        self.var.Trigger = env.event()
        self.var.quality_rate = 0.1
        self.var.requests = list()
    def put(self,item):
        return self.Queue.put(item)
    def subscribe(self,item=None):
        return self.Queue.subscribe(item)
    def build_c(self):
        self.Queue = Store(self.env)
    def build(self):
        Wait = State('Wait',True)
        @function(Wait)
        def W(self):
            return self.Queue.get()
        @do(Wait)
        def WW(self,event):
            self.var.entity = event.value
            return Work
        Work = State('Work')
        @function(Work)
        def W0(self):
            if np.random.uniform() < self.var.quality_rate:
                return self.connections['rework'].put(self.var.entity)
            else:
                return self.connections['after'].put(self.var.entity)
        @do(Work)
        def WW0(self,event):
            return Wait
        return [Work,Wait]

class FinalAssemblyManualMIP(ManualStation):
    def build(self):
        Starve = State('Starve',True)
        @function(Starve)
        def starveF(self):
            self.var.request = [self.connections['before1'].get(),self.connections['before2'].get()]
            return AllOf(self.env,self.var.request)
        @do(Starve)
        def starveDo(self,event):
            self.var.entity = event._events[0].value
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
            # self.var.request.confirm()
            return Starve
        return [Starve,Idle,Work,Block]
    
class FinalAssemblyMIP(Server):
    def build(self):
        states = super().build()
        states.pop(0)
        Work = [state for state in states if state._name=='Work'][0]
        Starve = State('Starve',True)
        @function(Starve)
        def starveF(self):
            self.var.request = [self.connections['before1'].get(),self.connections['before2'].get()]
            return AllOf(self.env,self.var.request)
        @do(Starve)
        def starveDo(self,event):
            self.var.entity = event._events[0].value
            return Work
        states.insert(0,Starve)
        return states
    
class AutomatedMIP(ManualStation):
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
            return Setup
        Setup = State('Setup')
        @function(Setup)
        def suF(self):
            serviceTime = (0.1+np.random.uniform()/10) * self.sm.calculateServiceTime(self.var.entity)
            return self.env.timeout(serviceTime)
        @do(Setup)
        def suDo(self,event):
            self.var.operator.var.Pause.succeed()
            self.var.operator = None
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
        return [Starve,Idle,Setup,Work,Block]
    
if __name__ == "__main__":
    
    if 1:
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

    if False:
        env = Environment()
        g = Generator(env,serviceTime=1)
        b = Queue(env)
        c = Store(env)
        g.connections['after'] = b
        b.connections['after'] = c
        env.run(10)
        
    if False:
        env = Environment()
        g = Generator(env,serviceTime=1)
        b = ServerCoupledBuffer(env)
        c = Store(env)
        g.connections['after'] = b
        b.connections['after'] = c
        env.run(10)


    import utils
    s = utils.stats(env)
# %%
