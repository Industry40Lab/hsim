if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

from abc import abstractmethod
from typing import Iterable, Union
from itertools import accumulate
from hsim.core.core.env import Environment
from hsim.core.agent.agent import Agent
from hsim.core.fsm.transitions import MessageTransition, EventTransition
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.des.pymulate import forwardItemEmpty
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
        self.input_ports = Ports(env,name="input")
        self.output_ports = Ports(env,name="output")
        for i in range(inputPorts):
            thisName = inputStoreNames[i] if inputStoreNames != "" else f"input{i}"
            thisPort = self.input_ports.addPort(thisName)
            thisPort._frame = self
            setattr(self,thisName,thisPort)
        for i in range(outputPorts):
            thisName = outputStoreNames[i] if outputStoreNames != "" else f"output{i}"
            thisPort = self.output_ports.addPort(thisName)
            thisPort._frame = self
            setattr(self,thisName,thisPort)
        self._agents = self.define()
        if self._agents is dict:
            for key, value in self._agents.items():
                value.name = self.name + "." + key
                setattr(self,key,value)
        else:
            assert any([a.name for a in self._agents]), "Missing sub-agents name definitions"
            for a in self._agents:
                thisName = a.name
                a.name = self.name + "." + thisName
                setattr(self,thisName,a)
                a._frame = self
        self._agents = [*self._agents,*self.input_ports.values(),*self.output_ports.values()]
                
        # return {key:value for key,value in locals().items() if issubclass(type(value),Agent) and value is not self}
    @abstractmethod
    def define(self) -> Union[dict[Agent],Iterable[str]]:
        pass
    def take(self,agent:Agent,id:int=0):
        return self.input_ports.getPortByID(id).take(agent)
    @property
    def _queue_history(self):
        data = [(-1,e[1]) for port in self.output_ports.values() for e in port.store._queue_history] + [(1,e[1]) for port in self.input_ports.values() for e in port.store._queue_history]
        data.sort(key=lambda x: x[1]) 
        cumulative_qty = list(accumulate(qty for qty, _ in data))
        return list(zip(cumulative_qty, (time for _, time in data)))

def test1():
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
    
def test2():
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
    
    
def test3():
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


def test4():
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
    from hsim.core.des.pymulate import Generator, Server, Terminator, EmptyBuffer, Buffer
    print("\n\n\n\n")
    test1()
    print("\n\n\n\n")
    test2()
    print("\n\n\n\n")
    test3()
    print("\n\n\n\n")
    test4()