from warnings import warn
from typing import Callable, Union
import numpy as np
import types
if __name__ == "__main__":
    import sys
    import os
    try:
        sys.path.append("/".join(os.path.abspath(__file__).split("/")[:os.path.abspath(__file__).split("/").index("hsim")+1]))
    except:
        sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
from hsim.core.agent.q import Queue
from hsim.core.fsm.transitions import MessageTransition, TimeoutTransition, EventTransition
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.core.env import Environment
from hsim.core.agent.agent import Agent, FSM
from hsim.core.des.des import DESBlock, TimedBlock


def forwardItemB2S(self,item):
    try:
        _, msg = self.give(self.connections["next"], item)
        msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
    except AttributeError as e:
        warn(RuntimeWarning(e))


class Server(DESBlock, TimedBlock):
    def __init__(self,env,name=None,serviceTime=1,serviceTimeFunction=None) -> None:
        super().__init__(env,name)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
    def on_receive(self) -> None:
        self.stateMachine.transitionsFrom["Starving"][0]()
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Working(State):
            def on_enter(self):
                self.var.item, self.var.message = self.store.inspect()
                self.transitions[0].timeout = self.calculateServiceTime(self.var.item)
        class Blocking(State):
            pass

        S2W=MessageTransition.define(Starving, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)

        W2B.on_transition = lambda self: forwardItemB2S(self,self.var.item)
        B2S.on_transition = lambda self: self._fsm._agent.store.get() if self._fsm._agent.store else None
        

class Buffer(DESBlock):
    """
    Pushes first agent according to dispatching rule.
    """
    def __init__(self,env,name=None,capacity=np.inf):
        super().__init__(env,name,capacity)
    def on_receive(self):
        self.stateMachine.transitionsFrom["Starving"][0]()

    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Blocking(State):
            pass
        T1=MessageTransition.define(Starving, Blocking)
        T2=EventTransition.define(Blocking, Starving)

        T1.on_transition = lambda self: forwardItemB2S(self,self.store.inspect(index = -1)[0])
        T2.on_transition = lambda self: self._fsm._agent.store.get()


class Store(DESBlock):
    """
    Pushes every agent.
    
    Note: does not require a FSM.
    """
    def __init__(self,env,name=None,capacity=np.inf):
        super().__init__(env,name,capacity=capacity)
    def on_receive(self):
        self._forward_item()

    def _forward_item(self):
        item, _ = self.store.inspect(index = -1) # get the last item
        _, msg = self.give(self.connections["next"], item)
        msg.receipts["received"].action = self.store.pull
        msg.receipts["received"].arguments = (item,)
        
def forwardItemEmpty(self):
    item, oldMsg = self.store.inspect(index = -1)
    _, msg = self.give(self.connections["next"], item)
    if oldMsg.receipts["received"].action is None:
        msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
    elif isinstance(oldMsg.receipts["received"].action,list):
        msg.receipts["received"].action = oldMsg.receipts["received"].action + [self.transitionsFrom["Blocking"][0] ]
    else:
        msg.receipts["received"].action = [oldMsg.receipts["received"].action, self.transitionsFrom["Blocking"][0]]


class EmptyBuffer(DESBlock):
    _alwaysEmpty = True
    def __init__(self,env,name=None,capacity=np.inf):
        super().__init__(env,name,capacity,queueType="locked")
    def on_receive(self):
        self.stateMachine.transitionsFrom["Starving"][0]()
    
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Blocking(State):
            pass
        T1=MessageTransition.define(Starving, Blocking)
        T2=EventTransition.define(Blocking, Starving)
                
        T1.on_transition = lambda self: forwardItemEmpty(self)
        T2.on_transition = lambda self: self._fsm._agent.store.get()

    


class Generator(DESBlock, TimedBlock):
    """Generates agents.
    Args:
        agent_function: Callable[[],Agent] - function that generates agents.
    """
    def __init__(self, env, name=None, agent_function:Union[Callable[[],Agent],Agent]=Agent, serviceTime=0, serviceTimeFunction=None):
        super().__init__(env, name)
        if not callable(agent_function):
            raise ValueError("Agent function must be a callable or an Agent class")
        elif isinstance(agent_function,type):
            self.agent_function = types.MethodType(lambda self: Agent(self.env), self)
        else:
            self.agent_function = types.MethodType(agent_function, self) 
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        self.stateMachine.transitionsFrom["Starving"][0].timeout = self.calculateServiceTime()
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Blocking(State):
            pass
        T1=TimeoutTransition.define(Starving, Blocking)
        T2=EventTransition.define(Blocking, Starving)

        
        T1.on_transition = lambda self: forwardItemB2S(self,self.agent_function())
        T2.on_transition = lambda self: None


class Terminator(DESBlock):
    """
    Terminates agent.
    
    Note: does not require a FSM.
    """
    def __init__(self,env,name=None):
        super().__init__(env,name,capacity=np.inf)
    def on_receive(self):
        self._terminate_item()

    def _terminate_item(self):
        item, msg = self.store.inspect(index = -1) # get the last item
        item.deactivate_fsm()
        
def example_agent_function(obj):
    return Agent(obj.env)

def test1():
    env = Environment()
    a = Server(env)
    q = Queue(env,10)
    a.connections["next"] = q
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
    a.connections["next"] = b
    b.connections["next"] = q
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
    a.connections["next"] = b
    b.connections["next"] = q
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1)
    env.run(20)
    x2 = Agent(env,"test2")
    a.take(x2)
    env.run(30)
    
def test4():
    env = Environment()
    g = Generator(env,"",example_agent_function,serviceTime=10)
    t = Terminator(env)
    g.connections["next"] = t
    env.run(100)
    
    
def test5():
    env = Environment()
    g = Generator(env,"",Agent,serviceTime=10)
    t = Terminator(env)
    g.connections["next"] = t
    env.run(100)

def test5():
    env = Environment()
    g = Generator(env,"",Agent,serviceTime=10)
    q1 = Buffer(env,capacity=2)
    q2 = Buffer(env,capacity=2)
    t = Terminator(env)
    g.connections["next"] = q1
    q1.connections["next"] = q2
    q2.connections["next"] = t
    env.run(100)
    
def test5():
    env = Environment()
    g = Generator(env,"",Agent,serviceTime=10)
    s1 = Server(env,serviceTime=10)
    s2 = Server(env,serviceTime=10)
    t = Terminator(env)
    g.connections["next"] = s1
    s1.connections["next"] = s2
    s2.connections["next"] = t
    env.run(100)
    
def test6():
    env = Environment()
    g = Generator(env,"",Agent,serviceTime=10)
    b0 = EmptyBuffer(env,capacity=1)
    b1 = Buffer(env,capacity=2)
    s = Server(env,serviceTime=10)
    t = Terminator(env)
    g.connections["next"] = b0
    b0.connections["next"] = b1
    b1.connections["next"] = s
    s.connections["next"] = t
    env.run(100)
    
def test7():
    env = Environment()
    g = Generator(env,"",Agent,serviceTime=1)
    b = Buffer(env,capacity=2)
    s = Server(env,serviceTime=10)
    t = Terminator(env)
    g.connections["next"] = b
    b.connections["next"] = s
    s.connections["next"] = t
    env.run(100)
    
if __name__ == "__main__":
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
