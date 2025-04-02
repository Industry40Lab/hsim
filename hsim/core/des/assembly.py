if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

from typing import Iterable, Union
from hsim.core.core.env import Environment
from hsim.core.des.des import TimedBlock, DESMulti
from hsim.core.agent.q import Queue
from hsim.core.agent.agent import Agent
from hsim.core.fsm.transitions import MessageTransition, TimeoutTransition, EventTransition
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.des.pymulate import forwardItemB2S


class Assembly(DESMulti, TimedBlock):
    def __init__(self,env,name=None,size=1,serviceTime=1,serviceTimeFunction=None,mainAgent:Union[int,type]=0,queueType:Union[Iterable[str],str]="locked") -> None:
        super().__init__(env,name,size,queueType=queueType)
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        self.var.mainAgent = mainAgent
        
    def on_receive(self,i) -> None:
        if all(len(store.queue) > 0 for store in self.stores) and isinstance(self.stateMachine.current_state[0],self.FSM.Starving):
            self.stateMachine.transitionsFrom["Starving"][0]()
    class FSM(FSM):
        class Starving(State):
            initial_state=True
            def on_enter(self):
                if all(len(store.queue) > 0 for store in self.stores):
                    self.stateMachine.transitionsFrom["Starving"][0]()
        class Working(State):
            def on_enter(self):
                mainAgent = self.var.mainAgent
                if type(mainAgent) == type:
                    self.var.item = mainAgent(self._env)
                else:
                    self.var.item, _ = self.stores[mainAgent].inspect()
                self.var.msg = list()
                for store in self.stores:
                    msg = store.get()
                    self.var.msg.append(msg)
                self.transitions[0].timeout = self.calculateServiceTime(self.var.item)
        class Blocking(State):
            pass

        S2W=MessageTransition.define(Starving, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)

        W2B.on_transition = lambda self: forwardItemB2S(self,self.var.item)
        B2S.on_transition = lambda self: [msg.receive() for msg in self.var.msg]


           
def test1():
    env = Environment()
    a = Assembly(env,size=2)
    q = Queue(env,10)
    a.connections["next"] = q
    env.run(10)
    a.take(Agent(env,"test1"))
    a.take(Agent(env,"test2"),1)
    env.run(20)
    assert len(q) == 1 and a.stateMachine.current_state[0].name == "Starving"
    
def test2():
    env = Environment()
    g1 = Generator(env,Agent)
    a = Assembly(env)
    q = Queue(env,10)
    g1.connections["next"] = a
    a.connections["next"] = q
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1)
    env.run(20)
    x2 = Agent(env,"test2")
    a.take(x2)
    env.run(30)
    assert len(q) == 10 and a.stateMachine.current_state[0].name == "Blocking"
    
    
def test3():
    env = Environment()
    g1 = Generator(env,Agent)
    a = Assembly(env,size=2)
    q = Queue(env,10)
    g1.connections["next"] = a
    a.connections["next"] = q
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1,0)
    env.run(20)
    x2 = Agent(env,"test2")
    a.take(x2,1)
    env.run(30)
    assert len(q) == 1 and a.stateMachine.current_state[0].name == "Starving"
    
    
def test4():
    env = Environment()
    g1 = Generator(env,"g1",Agent)
    g2 = Generator(env,"g2",Agent,serviceTime=5)
    a = Assembly(env,size=2,queueType=["locked","standard"])
    q = Queue(env,10)
    g1.connections["next"] = a
    g2.connections["next"] = a.toStore(1)
    a.connections["next"] = q
    env.run(30)
    assert len(q) == 5 and a.stateMachine.current_state[0].name == "Starving"
    
if __name__ == "__main__":
    from hsim.core.des.pymulate import Generator
    # test1()
    # print("\n\n\n\n")
    # test2()
    # print("\n\n\n\n")
    test4()
    print("\n\n\n\n")
