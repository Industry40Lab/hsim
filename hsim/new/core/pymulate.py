from typing import Iterable, Union
import numpy as np
from q import LockedQueue, PriorityQueue, Queue
import types
from transitions import ConditionTransition, MessageTransition, TimeoutTransition, EventTransition
from states import State
from FSM import FSM
from env import Environment
from msg import Message
from event import BaseEvent, ConditionEvent, wait
from agent import Agent, FSM
import dill
from warnings import warn

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
        
class DESBlock(Agent):
    __priorityQueue__, __lockedQueue__ = False, False
    Next : Union[Agent,Iterable[Agent]]
    def __init__(self,env,name=None,capacity=1) -> None:
        super().__init__(env,name)
        if self.__priorityQueue__:
            self.store = PriorityQueue(env)
        elif self.__lockedQueue__:
            self.store = LockedQueue(env)
        else:
            self.store:Queue = Queue(env,capacity=capacity)
        self.store.on_receive = self.on_receive
    def take(self,item) -> tuple[ConditionEvent, Message]:
        return self.store.take(item)
    def give(self, other, item) -> tuple[ConditionEvent, Message]:
        return other.take(item)
    def on_receive(self) -> None:
        raise NotImplementedError(f"on_receive method is not implemented for {self}.")
    class FSM(FSM):
        class Empty(State):
            initial_state=True
            
class DESLocked(DESBlock):
    __lockedQueue__ = True
    

class Server(DESBlock):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None) -> None:
        super().__init__(env,name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        setattr(self,'calculateServiceTime',types.MethodType(calculateServiceTime, self))
    def on_receive(self) -> None:
        self.stateMachine.transitionsFrom["Starving"][0]()
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Working(State):
            def on_enter(self):
                self.var.item, self.var.message = self.store.inspect()
        class Blocking(State):
            pass

        T1=MessageTransition.define(Starving, Working)
        T2=TimeoutTransition.define(Working, Blocking)
        T3=EventTransition.define(Blocking, Starving)

        def W2B(self):
            try:
                _, msg = self.give(self.Next, self._agent.var.item)
                msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
            except AttributeError as e:
                warn(RuntimeWarning(e))
        T2.on_transition = W2B
        T3.on_transition = lambda self: self._fsm._agent.store.get()
        

class Buffer(DESBlock):
    """
    Pushes first agent according to dispatching rule.
    """
    def __init__(self,env,name=None,capacity=np.inf):
        super().__init__(env,name)
    def on_receive(self):
        self.stateMachine.transitionsFrom["Starving"][0]()

    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Blocking(State):
            pass
        T1=MessageTransition.define(Starving, Blocking)
        T2=EventTransition.define(Blocking, Starving)
        def S2B(self):
            try:
                item, _ = self.store.inspect(index = -1) # get the last item
                _, msg = self.give(self.Next, item)
                msg.receipts["received"].action = (self.transitionsFrom["Blocking"][0],self._fsm._agent.Store.get())
            except Exception as e:
                warn(RuntimeWarning(e))
        T1.on_transition = S2B
        T2.on_transition = lambda self: self._fsm._agent.Store.get()


class Store(DESBlock):
    """
    Pushes every agent.
    
    Note: does not require a FSM.
    """
    def __init__(self,env,name=None,capacity=np.inf):
        super().__init__(env,name)
    def on_receive(self):
        self._forward_item()

    def _forward_item(self):
        item, _ = self.store.inspect(index = -1) # get the last item
        _, msg = self.give(self.Next, item)
        msg.receipts["received"].action = self.store.pull
        msg.receipts["received"].arguments = (item,)
        
    
# class Switch(Agent):
#     def __init__(self,env,name=None,capacity=np.inf):
#         super().__init__(env,name)
#         self.Store:Queue = LockedQueue(env,capacity)
#     def take(self,item):
#         return self.Store.take(item)
#     def give(self, other, item):
#         return other.take(item)
#     def on_receive(self):
#         self.stateMachine.transitionsFrom["Starving"][0]()
#     class FSM(FSM):
#         class Starving(State):
#             initial_state=True
#         class Blocking(State):
#             def on_enter(self) -> None:
#                 self.var.item = self.Store.inspect()
#                 try:
#                     next = self.Next
#                     self.give(next, self.fsm._agent.var.item)
#                     self.var.item.receipts["received"].action = self.transitionsFrom["Blocking"][0]
#                 except Exception as e:
#                     warn(RuntimeWarning(e))
#             def on_exit(self):
#                 self.Store.receive()


def test1():
    env = Environment()
    a = Server(env)
    q = Queue(env,10)
    # a.Next = q
    a.stateMachine.start()
    env.run(10)
    x = Agent(env,"test")
    a.take(x)
    env.run(20)
    a.take(Agent(env,"test"))
    env.run(30)
    
def test2():
    env = Environment()
    a = Server(env)
    b = Buffer(env)
    q = Queue(env,10)
    a.Next = b
    b.Next = q
    a.stateMachine.start()
    b.stateMachine.start()
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1)
    env.run(20)
    x2 = Agent(env,"test2")
    a.take(x2)
    env.run(30)
    
def test3():
    env = Environment()
    a = Server(env)
    b = Store(env)
    q = Queue(env,10)
    a.Next = b
    b.Next = q
    a.stateMachine.start()
    b.stateMachine.start()
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1)
    env.run(20)
    x2 = Agent(env,"test2")
    a.take(x2)
    env.run(30)
    
def test4():
    env = Environment()
    a = Switch(env)
    q1 = Queue(env,10)
    q2 = Queue(env,10)
    q1.Next = a
    a.Next = q2
    a.stateMachine.start()
    env.run(10)
    x = Agent(env,"test")
    q1.take(x)
    env.run(20)
    q1.take(Agent(env,"test"))
    env.run(30)
    

if __name__ == "__main__":
    test1()
    test2()
    test3()
