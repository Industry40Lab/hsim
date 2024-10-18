if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

    
from typing import Union
from hsim.core.agent.q import Queue
from hsim.core.fsm.transitions import ConditionTransition, MessageTransition, TimeoutTransition, EventTransition
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.core.env import Environment
from hsim.core.agent.agent import Agent, FSM
from warnings import warn
from pymulate import Server, Store

class ManualStation(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None) -> None:
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.connections["operator"] = None 
    def add_operator(self,operator):
        self.connections["operator"] = operator
        self.receiveContent("Operator")
    class FSM(Server.FSM):
        class Starving(State):
            initial_state=True
        class Idle(State):
            pass
        class Working(State):
            def on_enter(self):
                self.var.item, self.var.message = self.store.inspect()
        class Blocking(State):
            pass
        S2I=MessageTransition.define(Server.FSM.Starving, Idle)
        I2W=MessageTransition.define(Idle, Server.FSM.Working)
        I2W._message = "Operator"
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)

        def onW2B(self):
            try:
                _, msg = self.give(self.connections["next"], self._agent.var.item)
                self.connections["operator"].free()
                self.connections["operator"] = None
                msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
            except AttributeError as e:
                warn(RuntimeWarning(e))
        W2B.on_transition = onW2B
     

class Operator(Agent):
    def __init__(self,env,name=None) -> None:
        super().__init__(env,name)
        self.connections["stations"] = list()
    def free(self):
        self.receiveContent("free")
    class FSM(FSM):
        def _on_receive(self, message):
            station = message.content
            self.current_state
            return super()._on_receive(message)
        class Sleep(State):
            initial_state=True
        class Working(State):
            pass
        
        S2W=ConditionTransition.define(Sleep, Working)
        S2W._condition = lambda self: self.pick() and any([s.stateMachine.current_state[0].name == "Idle" for s in self._agent.connections["stations"]])
        S2W.on_transition = lambda self: self.pick().add_operator(self._agent)
        W2I=MessageTransition.define(Working, Sleep)
        W2I._message = "free"
        
    def pick(self) -> Union[ManualStation,None]:
        for s in reversed(self.connections["stations"]):
            if s.stateMachine.current_state[0].name == "Idle":
                return s
        return None
        


    
def test1():
    env = Environment()
    a = ManualStation(env)
    b = Store(env)
    q = Queue(env,10)
    op = Operator(env)
    a.connections["next"] = b
    b.connections["next"] = q
    op.connections["stations"].append(a)
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1)
    env.run(20)
    # a.stateMachine.receiveContent("operator enters")
    env.run(30)
    
    x2 = Agent(env,"test2")
    a.take(x2)
    env.run(30)
    

if __name__ == "__main__":

    test1()