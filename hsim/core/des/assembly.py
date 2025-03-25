if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

from abc import abstractmethod
import queue
from typing import Iterable, Union
from hsim.core.core.env import Environment
from hsim.core.des.des import TimedBlock, DESMulti
from hsim.core.agent.q import Queue
from hsim.core.agent.agent import Agent
from hsim.core.fsm.transitions import MessageTransition, TimeoutTransition, EventTransition
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.des.pymulate import forwardItemB2S, forwardItemEmpty




class Assembly(DESMulti, TimedBlock):
    def __init__(self,env,name=None,size=1,serviceTime=1,serviceTimeFunction=None,mainAgent:Union[int,type]=0) -> None:
        super().__init__(env,name,size,queueType="locked")
        self.var.serviceTime = serviceTime
        self.var.serviceTimeFunction = serviceTimeFunction
        self.var.mainAgent = mainAgent
        
    def on_receive(self,i) -> None:
        if all(len(store.queue) > 0 for store in self.stores):
            self.stateMachine.transitionsFrom["Starving"][0]()
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Working(State):
            def on_enter(self):
                mainAgent = self.var.mainAgent
                if type(mainAgent) == type:
                    self.var.item = mainAgent(self._env)
                else:
                    self.var.item, _ = self.stores[mainAgent].inspect()
                for store in self.stores:
                    store.get()
                self.transitions[0].timeout = self.calculateServiceTime(self.var.item)
        class Blocking(State):
            pass

        S2W=MessageTransition.define(Starving, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)

        W2B.on_transition = lambda self: forwardItemB2S(self,self.var.item)
        B2S.on_transition = lambda self: None

from hsim.core.des.pymulate import Buffer, EmptyBuffer
class Port(EmptyBuffer):
    def __init__(self,env,name=None):
        super().__init__(env,name,capacity=0)
    
    class FSM(FSM):
        class Starving(State):
            initial_state=True
        class Blocking(State):
            pass
        T1=MessageTransition.define(Starving, Blocking)
        T2=EventTransition.define(Blocking, Starving)
                
        T1.on_transition = lambda self: forwardItemEmpty(self)
        T2.on_transition = lambda self: self._fsm._agent.store.get()


from collections import OrderedDict
from itertools import islice
class Ports(OrderedDict[Port]):
    def __init__(self,env,name=""):
        self.name = name
        self.env = env
        
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.getPortByID(0)
    
    @property
    def ports(self):
        return (i for i in self.values())
    
    def getPortByID(self,id):
        return next(islice(self.ports,id,id+1))
    
    def addPort(self,name)-> Port:
        self[name] = Port(self.env,name)
        return self[name]
    

class Frame(Agent):
    def __init__(self, env, name, inputPorts = 1, outputPorts = 1, inputStoreNames="",outputStoreNames=""):
        super().__init__(env, name)
        # self.input_ports = DESMulti(env, name, inputPorts, queueType="locked", storeNames=inputStoreNames)
        # self.output_ports = DESMulti(env, name, outputPorts, queueType="locked", storeNames=outputStoreNames)
        self.input_ports = Ports(env,name="input")
        self.output_ports = Ports(env,name="output")
        for i in range(inputPorts):
            thisName = inputStoreNames[i] if inputStoreNames != "" else f"input{i}"
            setattr(self,thisName,self.input_ports.addPort(thisName))
        for i in range(outputPorts):
            thisName = outputStoreNames[i] if outputStoreNames != "" else f"output{i}"
            setattr(self,thisName,self.output_ports.addPort(thisName))
        agents = self.define()
        if agents is dict:
            for key, value in agents.items():
                value.name = self.name + "." + key
                setattr(self,key,value)
        else:
            assert any([a.name for a in agents]), "Missing sub-agents name definitions"
            for a in agents:
                thisName = a.name
                a.name = self.name + "." + thisName
                setattr(self,thisName,a) 
                
        # return {key:value for key,value in locals().items() if issubclass(type(value),Agent) and value is not self}
    @abstractmethod
    def define(self) -> Union[dict[Agent],Iterable[str]]:
        pass

    
def test1():
    env = Environment()
    a = Assembly(env,size=2)
    q = Queue(env,10)
    a.connections["next"] = q
    env.run(10)
    a.take(Agent(env,"test1"))
    a.take(Agent(env,"test2"),1)
    env.run(20)
    
def test2():
    env = Environment()
    g1 = Generator(env,Agent)
    g2 = Generator(env,Agent)
    a = Assembly(env)
    q = Queue(env,10)
    g1.connections["next"] = a
    g2.connections["next"] = a
    a.connections["next"] = q
    env.run(10)
    x1 = Agent(env,"test1")
    a.take(x1)
    env.run(20)
    x2 = Agent(env,"test2")
    a.take(x2)
    env.run(30)

def test3():
    env = Environment()
    g = Generator(env,Agent, serviceTime=1)
    q = EmptyBuffer(env,capacity=10)
    q2 = EmptyBuffer(env,capacity=10)
    s = Server(env,serviceTime=4.9)
    t = Terminator(env)
    g.connections["next"] = q
    q.connections["next"] = q2
    q2.connections["next"] = s
    s.connections["next"] = t
    env.run(1)
    env.run(20)
    print("Test 3 done")
    
def test4():
    env = Environment()
    class F1(Frame):
        def define(self):
            s = Server(self.env,"s",serviceTime=1)
            self.input_ports[0].connections["next"] = s
            s.connections["next"] = self.output_ports[0]
            return {s}
    a = F1(env,"F",inputPorts=1,outputPorts=1)
    g = Generator(env,Agent)
    t = Terminator(env)
    
    g.connections["next"] = a.input_ports[0]
    a.output_ports[0].connections["next"] = t
    env.run(30)
    print("done")
    
    
def test5():
    env = Environment()
    class F1(Frame):
        def define(self):
            A = Buffer(self.env,"A",capacity=2)
            B = Server(self.env,"B",serviceTime=1)
            self.input_ports[0].connections["next"] = A
            A.connections["next"] = B
            B.connections["next"] = self.output_ports[0]
            return {A, B}
    a = F1(env,"F",inputPorts=1,outputPorts=1)
    g = Generator(env,Agent)
    t = Terminator(env)
    
    g.connections["next"] = a.input_ports[0]
    a.output_ports[0].connections["next"] = t
    env.run(30)
    print("done")


def test6():
    env = Environment()
    class F1(Frame):
        def define(self):
            A = Buffer(self.env,"A",capacity=2)
            B = Server(self.env,"B",serviceTime=1)
            C = Buffer(self.env,"A",capacity=2)
            self.input_ports[0].connections["next"] = A
            A.connections["next"] = B
            B.connections["next"] = C
            C.connections["next"] = self.output_ports[0]
            return {A, B, C}
    a = F1(env,"F",inputPorts=1,outputPorts=1)
    g = Generator(env,Agent)
    t = Terminator(env)
    
    g.connections["next"] = a.input_ports[0]
    a.output_ports[0].connections["next"] = t
    env.run(30)
    print("done")
    
    
if __name__ == "__main__":
    from hsim.core.des.pymulate import Generator, Store, Server, Terminator, EmptyBuffer, Buffer
    # test1()
    # print("\n\n\n\n")
    # test2()
    # print("\n\n\n\n")
    # test3()
    # print("\n\n\n\n")
    # test4()
    # print("\n\n\n\n")
    # test5()
    print("\n\n\n\n")
    test6()