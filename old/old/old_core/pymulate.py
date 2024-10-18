# -*- coding: utf-8 -*-

from .chfsm import CHFSM, State, Transition, Pseudostate
from .stores import Store, Box
from .core import Environment, Event
from simpy import AllOf, AnyOf
import types
import numpy as np

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
    def put(self,item):
        return self.Store.put(item)  
    def subscribe(self,item):
        return self.Store.subscribe(item)
    class Starving(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Store.subscribe()
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request.read()
    class Blocking(State):
        pass
    T1=Transition(Starving, Working, lambda self: self.var.request)
    T2=Transition(Working, Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
    T3=Transition(Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())

class MiniServer(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self._group = None
    @property
    def Next(self):
        return self._group.Next
    T2=Transition(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))

    
class ParallelServer():
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacity=1):
        self.env = env
        self.name = name
        self._capacity = capacity
        # self.Next = None
        self.switch = OutputSwitch(env)
        self.servers = []
        self.switch.Next = self.servers
        for i in range(capacity):
            self.servers.append(MiniServer(env,name,serviceTime,serviceTimeFunction))
            self.servers[i]._group = self
    def __len__(self):
        return sum([len(server.Store.items) for server in self.servers])         
    def put(self,item):
        return self.switch.Queue.put(item)  
    def subscribe(self,item):
        return self.switch.Queue.subscribe(item)  
    @property
    def current_state(self):
        return [server.current_state for server in self.servers]

class ServerWithBuffer(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacityIn=np.inf):
        self.capacityIn = capacityIn
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def build(self):
        super().build()
        self.QueueIn = Store(self.env,self.capacityIn)
    def put(self,item):
        return self.QueueIn.put(item)
    class Retrieving(State):
        initial_state=True
        def _do(self):
            self.var.requestIn = self.QueueIn.subscribe()
    class Forwarding(State):
        def _do(self):
            self.var.entityIn = self.var.requestIn.read()
    TRF=Transition(Retrieving,Forwarding,lambda self: self.var.requestIn)
    TFR=Transition(Forwarding,Retrieving,lambda self: self.Store.put(self.var.entityIn),action=lambda self:self.var.requestIn.confirm())


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
    TRFO=Transition(RetrievingOut,ForwardingOut,lambda self: self.var.requestOut)
    TFRO=Transition(ForwardingOut,RetrievingOut,lambda self: self.Next.put(self.var.entityOut),action=lambda self:self.var.requestOut.confirm())
    T3=Transition(Server.Blocking, Server.Starving, lambda self: self.QueueOut.put(self.var.entity),action=lambda self: self.var.request.confirm())

class Conveyor(CHFSM):
    def __init__(self,env,name=None,length=1,speed=1):
        super().__init__(env,name)
        self.servers = list()
        # class MiniServer(Server):
        #     @property
        #     def Next(self):
        #         return self._group.Next
        for i in range(length):
            self.servers.append(Server(env,serviceTime=speed))
        self.servers[-1] = MiniServer(env,serviceTime=speed)
        self.servers[-1]._group=self
        for i in range(length-1):
            self.servers[i].Next = self.servers[i+1]
    class Working(State):
        initial_state = True
    def build(self):
        self.Queue = Box(self.env)        
    @property
    def items(self):
        return [server.Store.items for server in self.servers]
    def put(self,item):
        return self.servers[0].put(item)
    def subscribe(self,item):
        return self.servers[0].subscribe(item)
    def __len__(self):
        return sum(len(server.Store.items) for server in self.servers)
        
            
            
        
        

class Generator(CHFSM):
    def __init__(self,env,name=None,serviceTime=1,serviceTimeFunction=None):
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
    T1=Transition(Sending,Creating,lambda self: self.Next.put(self.var.entity))
    T2=Transition(Creating,Sending,lambda self: self.env.timeout(self.calculateServiceTime(None)))

class Terminator(Store):
    pass

class Queue(CHFSM):
    def __init__(self, env, name=None, capacity=np.inf):
        self.capacity = capacity
        super().__init__(env,name)
    def put(self,item):
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

class Queue2(Queue):
    T2=Transition(Queue.Forwarding,Queue.Retrieving,lambda self: self.Next.subscribe(self.var.entity),action=lambda self: self.var.request.confirm())

class ManualStation(Server):
    def build(self):
        super().build()
        self.GotOperator = self.env.event()
        self.NeedOperator = self.env.event()
        self.Operators = Store(self.env)
    class Idle(State):
        pass
    T1=Transition(Server.Starving, Idle, lambda self: self.var.request, action = lambda self: self.NeedOperator.succeed())
    T1b=Transition(Idle, Server.Working, lambda self: self.GotOperator)
    T2 = Transition(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
    def action(self):
        self.NeedOperator.restart()
    T1b._action = action
    def action(self):
        self.GotOperator.restart()
        for op in self.Operators.items:
            op.Pause.succeed()
            self.Operators.items.remove(op)
    T2._action = action


class Operator(CHFSM):
    def __init__(self,env,name=None,station=[]):
        super().__init__(env, name)
        self.var.station = list()
        self.var.target = None
    def build(self):
        self.Pause = self.env.event()
    def select(self):
        for station in self.var.station[::-1]:
            if station.NeedOperator.triggered and not station.GotOperator.triggered:
                return station
    class Idle(State):
        initial_state=True
        def _do(self):
            self.var.request = AnyOf(self.env,[station.NeedOperator for station in self.var.station])
    class Working(State):
        def _do(self):
            self.var.target = self.select()
            if self.var.target:
                self.var.target.GotOperator.succeed()
                self.var.target.Operators.put(self.sm)
                self.Pause.restart()
            elif not any([station.NeedOperator.triggered for station in self.var.station]):
                if self.Pause.triggered:
                    self.Pause.restart()
                self.Pause.succeed()
            # da qui in poi pericolo
            elif self.var.target is None:
                if self.Pause.triggered:
                    self.Pause.restart()
                self.Pause.succeed()
            # fino a qui pericolo
    T1=Transition(Idle, Working, lambda self: self.var.request)
    T2=Transition(Working, Idle, lambda self: self.Pause)


class OutputSwitch(CHFSM):
    def build(self):
        self.Queue = Box(self.env)
    class Working(State):
        initial_state = True
        def _do(self):
            self.var.requestIn = self.Queue.subscribe()
            self.var.requestsOut = [next.subscribe(object()) for next in self.Next]
    W2W = Transition(Working,Working,lambda self: AllOf(self.env,[self.var.requestIn,AnyOf(self.env,self.var.requestsOut)]))
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
    def put(self,item):
        return self.Queue.put(item)
    def subscribe(self,item):
        return self.Queue.subscribe(item)
    
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
    def put(self,item):
        return self.Queue.put(item)
    class Sending(State):
        initial_state = True
        def _do(self):
            self.sm.var.requestIn = self.sm.Queue.put_event
            self.sm.var.requestOut = [item for sublist in [[next.subscribe(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
            if self.sm.var.requestOut == []:
                self.sm.var.requestOut.append(self.sm.var.requestIn)
    S2S1 = Transition(Sending,Sending,lambda self:AnyOf(self.env,[self.var.requestIn]))
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
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
    
class RouterNew(CHFSM):
    def __init__(self, env, name=None,capacity=np.inf):
        self.capacity = capacity
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.sent = []
        self.putEvent = env.event()
    def build(self):
        self.Queue = Store(self.env,self.capacity)
    def condition_check(self,item,target):
        return True
    def put(self,item):
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
    # S2S1 = Transition(Sending,Sending,lambda self:AnyOf(self.env,[self.var.requestIn]))
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut),condition=lambda self:self.var.requestOut != [])
    #new
    # class Waiting(State):
    #     pass
    # S2W = Transition(Sending,Waiting,lambda self:AllOf(self.env,self.var.requestOut))
    # W2S = Transition(Waiting,Sending,lambda self:AnyOf(self.env,[self.var.requestIn]))
    # def action0(self):
    #     pass
    #     # self.Queue._trigger_put(self.env.event())
    #     # self.Queue.put_event.restart()
    # W2S._action = action0
    #new
    # def action(self):
    #     self.Queue._trigger_put(self.env.event())
    #     self.Queue.put_event.restart()
    # S2S1._action = action
    def action2(self):
        # self.Queue._trigger_put(self.env.event())
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


class StoreSelect(CHFSM):
    def __init__(self, env, name=None,capacity=np.inf):
        self.capacity = capacity
        super().__init__(env, name)
    def build(self):
        self.Queue = Store(self.env,self.capacity)
    def put(self,item):
        return self.Queue.put(item)
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
    S2S1 = Transition(Sending,Sending,lambda self:self.var.requestIn)
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut))
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
    S2S2._action = action
    
class Gate(CHFSM):
    def build(self):
        self.Queue = Box(self.env)
        self.Input = Store(self.env)
    class Closed(State):
        pass
    class Open(State):
        pass
    
# class QueueSorted(Queue):
#     def sort(self):
#         pass
#     def put(self,item):
#         self.sort()
#         return self.Store.put(item)

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
    b = Operator(env)
    b.var.station=[a]
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

if __name__ == '__main__' and 1 and True:
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

if __name__ == '__main__' and 1 and False:
    env = Environment()
    a = Queue(env)
    b = ServerDoubleBuffer(env,serviceTime=1,capacityOut=5)
    a.Next = b
    b.Next = Store(env,5)
    for i in range(1,10):
        a.put(i)
    env.run(10)
    if a.current_state[0]._name == 'Starving' and len(a.Next) == 5 and len(a.QueueOut) == 4:
        print('OK server with 2 buffers')


# %% old

'''     
  
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

'''
# %% MIP
class MachineMIP(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,failure_rate=0,TTR=60):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.var.failure_rate = failure_rate
        self.var.TTR = TTR
    class Fail(State):
        pass
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = self.Store.subscribe()
    T1 = 'ciao'
    S2F = Transition(Starving, Fail, lambda self: self.var.request, condition=lambda self: np.random.uniform() < self.var.failure_rate)
    S2W = Transition(Starving, Server.Working, lambda self: self.var.request)
    F2W = Transition(Fail, Server.Working, lambda self: self.env.timeout(self.var.TTR))
    T3=Transition(Server.Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())


if __name__ == '__main__' and 1:
    env = Environment()
    a = MachineMIP(env,serviceTime=1,failure_rate=1,TTR=3)
    a.Next = Store(env,10)
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if a.current_state[0]._name == 'Working' and len(a.Next) == 4:
        print('OK server') 

        
class SwitchQualityMIP(CHFSM):
    def __init__(self, env, name=None):
        super().__init__(env,name)
        self.var.Trigger = env.event()
        self.var.quality_rate = 0.1
        self.var.requests = list()
    def build(self):
        self.Queue = Store(self.env)
    def put(self,item):
        return self.Queue.put(item)
    class Wait(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Queue.subscribe()
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request.read()
            if np.random.uniform() < self.var.quality_rate:
                self.var.putRequest = self.Rework.put(self.var.entity)
            else:
                self.var.putRequest = self.Next.put(self.var.entity)
    T1 = Transition(Wait, Working, lambda self: self.var.request)
    T2 = Transition(Working,Wait,lambda self: self.var.putRequest,action = lambda self: self.var.request.confirm())


class FinalAssemblyManualMIP(ManualStation):
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = [self.Before1.subscribe(),self.Before2.get()]     
    S2I = Transition(Starving, ManualStation.Idle, lambda self: AllOf(self.env,self.var.request))
    def action(self):
        self.var.request = self.var.request[0]
        self.NeedOperator.succeed()
    S2I._action = action
    T3=Transition(ManualStation.Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())

    

    
class FinalAssemblyMIP(Server):
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = [self.connections['before1'].get(),self.connections['before2'].get()]
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request._events[0].value
    S2W = Transition(Starving, Working, lambda self: AllOf(self.env,self.var.request))
    T2=Transition(Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))

  
class AutomatedMIP(ManualStation):
    class Setup(State):
        pass
    # class Working(State):
    #     pass
        # def _do(self,event):
        #     self.var.operator.var.Pause.succeed()
        #     self.var.operator = None
    T1b=Transition(ManualStation.Idle, Setup, lambda self: self.GotOperator,action=lambda self:self.NeedOperator.restart())
    T1c=Transition(Setup, ManualStation.Working, lambda self: self.env.timeout((0.1+np.random.uniform()/10) * self.sm.calculateServiceTime(self.var.request.read())))
    T2 = Transition(ManualStation.Working, ManualStation.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
    def action(self):
        self.GotOperator.restart()
        for op in self.Operators.items:
            op.Pause.succeed()
            self.Operators.items.remove(op)
    T2._action = action
    # T1=Transition(Server.Starving, Idle, lambda self: self.var.request, action = lambda self: self.NeedOperator.succeed())
    # T1b=Transition(Idle, Server.Working, lambda self: self.GotOperator)
    
    # T2 = Transition(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))


    
if False and __name__ == "__main__":
    
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
    
