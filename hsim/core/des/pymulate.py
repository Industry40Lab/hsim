from warnings import warn
from typing import Callable
import numpy as np
import types
if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
from hsim.core.agent.q import Queue
from hsim.core.fsm.transitions import MessageTransition, TimeoutTransition, EventTransition
from hsim.core.fsm.states import Pseudostate, State
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
        class No(Pseudostate):
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

        T1.on_transition = lambda self: forwardItemB2S(self,self.store.inspect(index = -1))
        T2.on_transition = lambda self: self._fsm._agent.store.get()


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
        _, msg = self.give(self.connections["next"], item)
        msg.receipts["received"].action = self.store.pull
        msg.receipts["received"].arguments = (item,)


class Generator(DESBlock, TimedBlock):
    """Generates agents.
    Args:
        agent_function: Callable[[],Agent] - function that generates agents.
    """
    def __init__(self, env, name=None, agent_function:Callable[[],Agent]=None, serviceTime=None, serviceTimeFunction=None):
        super().__init__(env, name)
        self.agent_function = types.MethodType(agent_function, self)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
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
        item, _ = self.store.inspect(index = -1) # get the last item
        item.deactivate_fsm()

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
    

if __name__ == "__main__":
    test1()
    test2()
    test3()
