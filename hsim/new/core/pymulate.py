from typing import Callable
import numpy as np
from q import Queue
import types
from transitions import MessageTransition, TimeoutTransition, EventTransition
from states import State
from FSM import FSM
from env import Environment
from agent import Agent, FSM
from warnings import warn
from des import DESBlock, TimedBlock


class Server(DESBlock, TimedBlock):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None) -> None:
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
        class Blocking(State):
            pass

        S2W=MessageTransition.define(Starving, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)

        def onW2B(self):
            try:
                _, msg = self.give(self.connections["next"], self._agent.var.item)
                msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
            except AttributeError as e:
                warn(RuntimeWarning(e))
        W2B.on_transition = onW2B
        B2S.on_transition = lambda self: self._fsm._agent.store.get()
        

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
                _, msg = self.give(self.connections["next"], item)
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
        T1=MessageTransition.define(Starving, Blocking)
        T2=EventTransition.define(Blocking, Starving)
        def S2B(self):
            try:
                item = self.agent_function()
                _, msg = self.give(self.connections["next"], item)
                msg.receipts["received"].action = (self.transitionsFrom["Blocking"][0],self._fsm._agent.Store.get())
            except Exception as e:
                warn(RuntimeWarning(e))
        T1.on_transition = S2B
        T2.on_transition = lambda self: self._fsm._agent.Store.get()


class Terminator(DESBlock):
    """
    Terminates agent.
    
    Note: does not require a FSM.
    """
    def __init__(self,env,name=None,capacity=np.inf):
        super().__init__(env,name)
    def on_receive(self):
        self._terminate_item()

    def _terminate_item(self):
        warn(NotImplementedError("The _terminate_item method is not implemented yet."))

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
