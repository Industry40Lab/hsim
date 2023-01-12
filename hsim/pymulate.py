# -*- coding: utf-8 -*-

from chfsm import CHFSM, State, Transition, add_states, trigger, action, Pseudostate
from chfsm import do
from stores import Store, Box
from core import Environment, Event
from simpy import AllOf, AnyOf
from simpy.events import PENDING 
import types
import numpy as np
from collections.abc import Iterable
from copy import deepcopy

# %% add
def calculateServiceTime(self,entity=None,attribute='serviceTime'):
    if self.var.serviceTimeFunction == None:
        if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
            return self.var.serviceTime
        elif self.var.serviceTime == None:
            time = getattr(entity,attribute)
            if type(time) is dict:
                time = time[self.name]
            return time
        elif len(self.var.serviceTime)==0:
            time = getattr(entity,attribute)
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
                time = getattr(entity,attribute)
                if type(time) is dict:
                    time = time[self.name]
                return self.var.serviceTimeFunction(time)
        except:
            pass
        if len(self.var.serviceTime)==0:
            return self.var.serviceTimeFunction()
        elif len(self.var.serviceTime)>0:
            return self.var.serviceTimeFunction(*self.var.serviceTime)

def getState(name:str,states):
    return next(state for state in states if state.name is name)

# %% obj    
class Server(CHFSM):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        super().__init__(env,name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
    def build(self):
        self.Store = Store(self.env,1)
        
    class Starving(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Store.subscribe()
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request.read()
    class Blocking(State):
        pass
    T1=Transition.copy(Starving, Working, lambda self: self.var.request)
    T2=Transition.copy(Working, Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
    T3=Transition.copy(Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())


class ServerWithBuffer(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=np.inf):
        self.capacityIn = capacityIn
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def build(self):
        super().build()
        self.QueueIn = Store(self.env,self.capacityIn)
    class Retrieving(State):
        initial_state=True
        def _do(self):
            self.var.requestIn = self.QueueIn.subscribe()
    class Forwarding(State):
        def _do(self):
            self.var.entityIn = self.var.requestIn.read()
    TRF=Transition.copy(Retrieving,Forwarding,lambda self: self.var.requestIn)
    TFR=Transition.copy(Forwarding,Retrieving,lambda self: self.Store.put(self.var.entityIn),action=lambda self:self.var.requestIn.confirm())


class ServerDoubleBuffer(ServerWithBuffer):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=np.inf,capacityOut=np.inf):
        self.capacityOut = capacityOut
        super().__init__(env,name,serviceTime,serviceTimeFunction,capacityIn)
    def build(self):
        super().build()
        self.QueueOut = Store(self.env,self.capacityOut)
    class RetrievingOut(State):
        initial_state=True
        def _do(self):
            self.var.requestOut = self.QueueOut.subscribe()
    class ForwardingOut(State):
        def _do(self):
            self.var.entityOut = self.var.requestOut.read()
    TRFO=Transition.copy(RetrievingOut,ForwardingOut,lambda self: self.var.requestOut)
    TFRO=Transition.copy(ForwardingOut,RetrievingOut,lambda self: self.Next.put(self.var.entityOut),action=lambda self:self.var.requestOut.confirm())
    T3=Transition.copy(Server.Blocking, Server.Starving, lambda self: self.QueueOut.put(self.var.entity),action=lambda self: self.var.request.confirm())


class Generator(CHFSM):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        super().__init__(env,name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
    def createEntity(self):
        return object()
    class Sending(State):
        pass
    class Creating(State):
        initial_state=True
        def _do(self):
            self.var.entity = self.createEntity()
    T1=Transition.copy(Sending,Creating,lambda self: self.Next.put(self.var.entity))
    T2=Transition.copy(Creating,Sending,lambda self: self.env.timeout(self.calculateServiceTime(None)))

class Queue(CHFSM):
    def __init__(self, env, name=None, capacity=np.inf):
        self.capacity = capacity
        super().__init__(env,name)
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
    T1=Transition.copy(Retrieving,Forwarding,lambda self: self.var.request)
    T2=Transition.copy(Forwarding,Retrieving,lambda self: self.Next.put(self.var.entity),action=lambda self:self.var.request.confirm())


class ManualStation(Server):
    def build(self):
        super().build()
        self.WaitOperator = self.env.event()
        self.NeedOperator = self.env.event()
        self.Operators = Store(self.env)
    class Idle(State):
        pass
    T1=Transition.copy(Server.Starving, Idle, lambda self: self.var.request, action = lambda self: self.NeedOperator.succeed())
    T1b=Transition.copy(Idle, Server.Working, lambda self: self.WaitOperator, action = lambda self: [self.NeedOperator.restart(),self.WaitOperator.restart()])
    T2 = Transition.copy(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
    # @action(T2)
    def action(self):
        for op in self.Operators.items:
            op.Pause.succeed()
            self.Operators.items.remove(op)
    T2._action = action


class Operator(CHFSM):
    def __init__(self,env,name=None,station=[]):
        super().__init__(env, name)
        self.var.station = station
    def build(self):
        self.Pause = self.env.event()
    def select(self):
        for station in self.var.station:
            if station.NeedOperator.triggered and not station.WaitOperator.triggered:
                return station
    class Idle(State):
        initial_state=True
        def _do(self):
            self.var.request = AnyOf(self.env,[station.NeedOperator for station in self.var.station])
    class Working(State):
        def _do(self):
            self.var.target = self.select()
            self.var.target.WaitOperator.succeed()
            self.var.target.Operators.put(self.sm)
            self.Pause.restart()
    T1=Transition.copy(Idle, Working, lambda self: self.var.request)
    T2=Transition.copy(Working, Idle, lambda self: self.Pause)


class OutputSwitch(CHFSM):
    def build(self):
        self.Queue = Box(self.env)
    class Working(State):
        initial_state = True
        def _do(self):
            self.var.requestIn = self.Queue.subscribe()
            self.var.requestsOut = [next.subscribe(object()) for next in self.Next]
    W2W = Transition.copy(Working,Working,lambda self: AllOf(self.env,[self.var.requestIn,AnyOf(self.env,self.var.requestsOut)]))
    def action(self):
        entity = self.var.requestIn.read()
        for request in self.var.requestsOut:
            if request.check():
                request.item = entity
                request.confirm()
                break
        for request in self.var.requestsOut:
            if request.item is not entity:
                request.cancel()
        self.Queue.forward(entity)
    W2W._action = action
    
'''
class OutputSwitchC(CHFSM):
    def build(self):
        self.Queue = Box(self.env)
    def condition_check(self,item,target):
        return True
Retrieving = State('Retrieving',True)
Sending = State('Sending')
@do(Retrieving)
def f13(self):
    self.var.requestIn = self.Queue.subscribe()
R2S = Transition(Retrieving,Sending,lambda self: self.var.requestIn)
@do(Sending)
def f14(self):
    self.var.entity = self.var.requestIn.read()
    self.var.requestOut = [next.subscribe(self.var.entity) for next in self.Next if self.condition_check(self.var.entity,next)]
S2R = Transition(Sending,Retrieving,lambda self: AnyOf(self.env,self.var.requestIn))
@action(S2R)
def f15(self):
    for req in self.var.requestOut:
        if req.triggered:
            req.confirm()
        else:
            req.cancel()
Retrieving._transitions=[R2S]
Sending._transitions=[S2R]
OutputSwitchC._states = [Retrieving,Sending]

'''

class Router(CHFSM):
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.sent = []
    def build(self):
        self.Queue = Box(self.env)
    def condition_check(self,item,target):
        return True
    class Sending(State):
        initial_state = True
        def _do(self):
            self.sm.var.requestIn = self.sm.Queue.put_event
            self.sm.var.requestOut = [item for sublist in [[next.subscribe(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
            if self.sm.var.requestOut == []:
                self.sm.var.requestOut.append(self.sm.var.requestIn)
    S2S1 = Transition.copy(Sending,Sending,lambda self:self.var.requestIn)
    S2S2 = Transition.copy(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
    def action(self):
        self.Queue.put_event.restart()
    S2S1._action = action
    def action(self):
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
                    self.Queue.forward(request.item)
                    continue
    S2S2._action = action


'''

class Router0(CHFSM):
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.flag = 0
    def build(self):
        self.Queue = Box(self.env)
        self.Dummy = Store(self.env)
    def condition_check(self,item,target):
        return True
Sending = State('Sending',True)
@do(Sending)
def f121(self):
    self.sm.var.requestIn = self.sm.Queue.put_event
    if self.var.flag:
        self.var.flag = 0
        self.sm.var.requestOut = [item for sublist in [[next.put(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
    if self.sm.var.requestOut == []:
        self.sm.var.requestOut.append(self.sm.var.requestIn)
S2S1 = Transition(Sending,Sending,lambda self:self.var.requestIn)
S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
@action(S2S1)
def f131(self):
    self.Queue.put_event.restart()
    self.var.flag=1
@action(S2S2)
def f141(self):
    if not hasattr(self.var.requestOut[0],'item'):
        self.Queue.put_event.restart()
        return
    [self.Queue.forward(request.item) for request in self.var.requestOut if request.triggered]
    self.var.requestOut = [req for req in self.var.requestOut if not req.triggered]
Sending._transitions=[S2S1,S2S2]
Router0._states = [Sending]

'''

class StoreSelect(CHFSM):
    def build(self):
        self.Queue = Store(self.env)
    def condition_check(self,item,target):
        return True
    class Sending(State):
        initial_state = True
        def _do(self):
            self.var.requestIn = self.Queue.put_event
            self.var.requestOut = []
            for item in self.Queue.items:
                if self.condition_check(item,self.Next):
                    self.var.requestOut.append(self.Next.subscribe(item))
            if self.var.requestOut == []:
                self.var.requestOut = [self.var.requestIn]
    S2S1 = Transition.copy(Sending,Sending,lambda self:self.var.requestIn)
    S2S2 = Transition.copy(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
    def action(self):
        if hasattr(self.var.requestOut[0],'item'):
            for req in self.var.requestOut:
                req.cancel()
        self.Queue.put_event.restart()
    S2S1._action = action
    def action(self):
        if not hasattr(self.var.requestOut[0],'item'):
            return
        for request in self.var.requestOut:
            if request.check():
                request.confirm()
                self.var.requestOut.remove(request)
                self.Queue.items.remove(request.item)
                break
        for request in self.var.requestOut:
            request.cancel()
    S2S2.action = action

# %% TESTS

if __name__ == '__main__' and 1:
    env = Environment()
    a = Server(env,serviceTime=1)
    a.Next = Store(env,5)
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if a.current_state[0]._name == 'Blocking' and len(a.Next) == 5:
        print('OK server')
        
if __name__ == '__main__' and 1:
    env = Environment()
    b = ServerWithBuffer(env,serviceTime=1)
    b.Next = Store(env,5)
    for i in range(1,10):
        b.QueueIn.put(i)
    env.run(10)
    if b.current_state[0]._name == 'Blocking' and len(b.Next) == 5:
        print('OK server with buffer')

if __name__ == '__main__' and 1:
    env = Environment()
    a = ServerDoubleBuffer(env,serviceTime=1,capacityOut=5)
    a.Next = Store(env,5)
    for i in range(1,10):
        a.QueueIn.put(i)
    env.run(10)
    if a.current_state[0]._name == 'Starving' and len(a.Next) == 5 and len(a.QueueOut) == 4:
        print('OK server with 2 buffers')

if __name__ == '__main__':
    env = Environment()
    a = Generator(env,serviceTime=1)
    a.Next = Store(env,5)
    env.run(5)
    if len(a.Next) == 4:
        print('OK generator')
    env.run(10)
    if len(a.Next) == 5:
        print('OK generator 2x')
        
if __name__ == '__main__':
    env = Environment()
    a = Queue(env,capacity=4)
    a.Next = Store(env,5)
    for i in range(1,10):
        a.Store.put(i)
    env.run(10)
    if a.current_state[0]._name == 'Forwarding' and len(a.Next) == 5 and len(a.Store) == 4:
        print('OK queue')
        
if __name__ == '__main__':
    env = Environment()
    a = ManualStation(env,serviceTime=1)
    b = Operator(env,station=[a])
    a.Next = Store(env,5)
    for i in range(1,10):
        a.Store.put(i)
    env.run(10)
    if b.current_state[0]._name == 'Idle' and len(a.Next) == 5 and a.current_state[0]._name == 'Blocking':
        print('OK manual station')

if __name__ == '__main__':
    env = Environment()
    a = Server(env,serviceTime=1)
    b = OutputSwitch(env)
    c = Store(env,1)
    d = Store(env)
    a.Next = b.Queue
    b.Next = [c,d]
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if len(c) == 1 and len(d) == 5:
        print('OK switch')

if __name__ == '__main__':
    env = Environment()
    a = Server(env,serviceTime=1)
    b = Router(env)
    c = Store(env,1)
    d = Store(env)
    a.Next = b.Queue
    b.Next = [c,d]
    for i in range(1,7):
        b.Queue.put(i)
    env.run(20)
    if len(c) == 1 and len(d) == 5:
        print('OK router')

        
if __name__ == '__main__':
    env = Environment()
    b = Router(env)
    c = Store(env,1)
    d = Queue(env,capacity=3)
    e = Server(env,serviceTime = 5)
    f = Store(env)
    a.Next = b.Queue
    b.Next = [d.Store,c]
    d.Next = e.Store
    e.Next = f
    for i in range(1,10):
        b.Queue.put(i)
    env.run(20)
    if len(c) == 1 and len(d) == 3:
        print('OK router')
  

       
if __name__ == '__main__' and 0:
    env = Environment()
    a = Server(env,serviceTime=1)
    b = StoreSelect(env)
    c = Store(env,5)
    a.Next = b.Queue
    b.Next = c
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if len(c) == 5 and len(b.Queue) == 1:
        print('OK switch')
'''
# %% old





            
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
'''