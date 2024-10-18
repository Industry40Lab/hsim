if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
    

from typing import Callable, Iterable, Union
from warnings import warn
import numpy as np
from pymulate import Server, Generator, Terminator, forwardItemB2S
from hsim.core.fsm.FSM import FSM
from hsim.core.fsm.states import Pseudostate, State
from hsim.core.fsm.transitions import MessageTransition, TimeoutTransition, EventTransition
from hsim.core.core.env import Environment
from hsim.core.agent.agent import Agent
from hsim.core.agent.q import Queue

class UnreliableMachine(Server):
    def __init__(self, env, name=None, serviceTime=1, serviceTimeFunction=None, failure_rate=0.1, TTRfcn:Callable=lambda *args: args[0] if hasattr(args,"__len__") else args, TTRvalue:Iterable[Union[float,int]]=(1,)):
        super().__init__(env, name, serviceTime, serviceTimeFunction)
        self.var.failure_rate = failure_rate
        self.var.TTR = {"fcn":TTRfcn,"value":TTRvalue}
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
                self.transitions[0].timeout = self.var.TTR["fcn"](*self.var.TTR["value"])
        class PS1(Pseudostate):
            def control(self):
                if np.random.rand() < self.var.failure_rate:
                    return self.Failed,
                else:
                    return self.Working,
                
        S2W=MessageTransition.define(Starving, PS1)
        F2W=TimeoutTransition.define(Failed, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)
        
        W2B.on_transition = lambda self: forwardItemB2S(self,self.var.item)
        B2S.on_transition = lambda self: self._fsm._agent.store.get() if self._fsm._agent.store else None



        
def test1():
    env = Environment()
    a = UnreliableMachine(env,failure_rate=0.99)
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