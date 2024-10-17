
from typing import Callable, Iterable, Union
from warnings import warn
import numpy as np
from pymulate import Server, Generator, Terminator
from FSM import FSM
from states import Pseudostate, State
from transitions import MessageTransition, TimeoutTransition, EventTransition
from env import Environment
from agent import Agent
from q import Queue

class UnreliableMachine(Server):
    def __init__(self, env, name=None, serviceTime=1, serviceTimeFunction=None, failure_rate=0.1, TTRfcn:Callable=lambda self,*args: self.var.TTR[0], TTRvalue:Iterable[Union[float,int]]=(1,)):
        super().__init__(env, name, serviceTime, serviceTimeFunction)
        self.var.failure_rate = failure_rate
        self.var.TTR = TTRvalue
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Working(State):
            def on_enter(self):
                self.var.item, self.var.message = self.store.inspect()
                self.transitions[0].timeout = self.calculateServiceTime(self.var.item)
        class Blocking(State):
            pass
        class Failed(State):
            def on_enter(self):
                self.transitions[0].timeout = 10
        class PS1(Pseudostate):
            def control(self):
                if np.random.rand() < self.failure_rate:
                    return self.Failed,
                else:
                    return self.Working,
                
        S2W=MessageTransition.define(Starving, PS1)
        F2W=TimeoutTransition.define(Failed, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)
        
        def onW2B(self):
            try:
                _, msg = self.give(self.connections["next"], self._agent.var.item)
                msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
            except AttributeError as e:
                warn(RuntimeWarning(e))
        W2B.on_transition = onW2B
        B2S.on_transition = lambda self: self._fsm._agent.store.get() if self._fsm._agent.store else None
        
        
def test1():
    env = Environment()
    a = UnreliableMachine(env,failure_rate=0.9)
    q = Queue(env,10)
    a.connections["next"] = q
    env.run(10)
    x = Agent(env,"test")
    a.take(x)
    env.run(20)
    a.take(Agent(env,"test"))
    env.run(30)

if __name__ == "__main__":
    test1()