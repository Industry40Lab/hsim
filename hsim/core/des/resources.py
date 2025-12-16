if __name__ == "__main__":
    import sys
    import os
    try:
        sys.path.append("/".join(os.path.abspath(__file__).split("/")[:os.path.abspath(__file__).split("/").index("hsim")+1]))
    except:
        sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
    

from typing import Callable, Iterable, Union
from warnings import warn
import numpy as np
from hsim.core.des.assembly import Assembly
from hsim.core.des.frame import Frame
from hsim.core.des.pymulate import Server, Generator, Terminator, forwardItemB2S, Buffer
from hsim.core.fsm.FSM import FSM
from hsim.core.fsm.states import Pseudostate, State
from hsim.core.fsm.transitions import MessageTransition, TimeoutTransition, EventTransition
from hsim.core.core.env import Environment
from hsim.core.agent.agent import Agent
from hsim.core.agent.q import Queue
from hsim.core.des.manual import ManualStation
from hsim.core.core.obs import ObservableVariable

class UnreliableMachine(Server):
    def __init__(self, env, name=None, serviceTime=1, serviceTimeFunction=None, failure_rate=0.1, TTRfcn:Callable=lambda *args: args[0] if hasattr(args,"__len__") else args, TTRvalue:Iterable[Union[float,int]]=1):
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
                self.transitions[0].timeout = self.var.TTR["fcn"](self.var.TTR["value"])
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

class Quality:
    def __init__(self, function:callable=np.random.rand, threshold=0, *args):
        self.function = function
        self.threshold = threshold
        self.args = args
    def __call__(self)->bool:
        return self.function(*self.args) < self.threshold

class QualityMachine(Server):
    def __init__(self, env, name=None, serviceTime=1, serviceTimeFunction=None, quality=Quality()):
        super().__init__(env, name, serviceTime, serviceTimeFunction)
        self.quality:Callable[[],bool] = quality
    def forwardItemB2S(self,item):
        try:
            if self.quality():
                _, msg = self.give(self.connections["next"], item)
                msg.receipts["received"].action = self.stateMachine.transitionsFrom["Blocking"][0]
            else:
                if "quality" in self.connections.keys():
                    _, msg = self.give(self.connections["quality"], item)
                    msg.receipts["received"].action = self.stateMachine.transitionsFrom["Blocking"][0]
                else:
                    if not hasattr(self,"_terminator"):
                        self._terminator = Terminator(self.env,"Terminator")
                    _, msg = self.give(self._terminator, item)
                    msg.receipts["received"].action = self.stateMachine.transitionsFrom["Blocking"][0]
        except AttributeError as e:
            warn(RuntimeWarning(e))
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

        W2B.on_transition = lambda self: self.forwardItemB2S(self.var.item)
        B2S.on_transition = lambda self: self._fsm._agent.store.get() if self._fsm._agent.store else None

class ServerDoubleBuffer(Frame):
    def __init__(self, env, name, serviceTime=1, serviceTimeFunction=None, inputBufferCapacity=1, outputBufferCapacity=1, inputPorts=1, outputPorts=1, inputStoreNames="", outputStoreNames=""):
        self.inputBufferCapacity = inputBufferCapacity
        self.outputBufferCapacity = outputBufferCapacity
        self.serviceTime = serviceTime
        self.serviceTimeFunction = serviceTimeFunction
        super().__init__(env, name, inputPorts, outputPorts, inputStoreNames, outputStoreNames)
    def define(self):
        A = Buffer(self.env,"InputBuffer",capacity=self.inputBufferCapacity)
        B = Server(self.env,"Server",serviceTime=self.serviceTime,serviceTimeFunction=self.serviceTimeFunction)
        C = Buffer(self.env,"OutputBuffer",capacity=self.outputBufferCapacity)
        self.input_ports[0].connections["next"] = A
        A.connections["next"] = B
        B.connections["next"] = C
        C.connections["next"] = self.output_ports[0]
        return {A, B, C}


class QualityServerDoubleBuffer(Frame):
    def __init__(self, env, name, qualityThreshold=0, serviceTime=1, serviceTimeFunction=None, inputBufferCapacity=1, outputBufferCapacity=1, inputPorts=1, outputPorts=1, inputStoreNames="", outputStoreNames=""):
        self.inputBufferCapacity = inputBufferCapacity
        self.outputBufferCapacity = outputBufferCapacity
        self.serviceTime = serviceTime
        self.serviceTimeFunction = serviceTimeFunction
        self.qualityThreshold = qualityThreshold
        super().__init__(env, name, inputPorts, outputPorts, inputStoreNames, outputStoreNames)
    def define(self):
        A = Buffer(self.env,"InputBuffer",capacity=self.inputBufferCapacity)
        B = QualityMachine(self.env,"Server",serviceTime=self.serviceTime,serviceTimeFunction=self.serviceTimeFunction,quality=Quality(threshold=self.qualityThreshold))
        C = Buffer(self.env,"OutputBuffer",capacity=self.outputBufferCapacity)
        self.input_ports[0].connections["next"] = A
        A.connections["next"] = B
        B.connections["next"] = C
        C.connections["next"] = self.output_ports[0]
        return {A, B, C}


class SUMachine(ManualStation):
    def __init__(self,env,name=None,serviceTime=1,serviceTimeFunction=None,setupTime=1,setupTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.var.setupTime = setupTime
        self.var.setupTimeFunction = setupTimeFunction 
    class FSM(Server.FSM):
        class Starving(State):
            initial_state=True
        class Setup(State):
            def on_enter(self):
                self.transitions[0].timeout = self.calculateSetupTime()
        class Idle(State):
            pass
        class Working(State):
            def on_enter(self):
                self.var.item, self.var.message = self.store.inspect()
                self.transitions[0].timeout = self.calculateServiceTime(self.var.item)
        class Blocking(State):
            pass
        S2I=MessageTransition.define(Starving, Idle)
        I2SU=MessageTransition.define(Idle, Setup)
        I2SU._message = "Operator"
        SU2W=TimeoutTransition.define(Setup, Working)
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)

        def onSU2W(self):
            self.connections["operator"].free()
            self.connections["operator"] <<= None
        SU2W.on_transition = onSU2W
        def onW2B(self):
            try:
                _, msg = self.give(self.connections["next"], self._agent.var.item)
                msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
            except AttributeError as e:
                warn(RuntimeWarning(e))
        W2B.on_transition = onW2B 
        B2S.on_transition = lambda self: self._fsm._agent.store.get() if self._fsm._agent.store else None
        
class ManualAssembly(Assembly):
    def __init__(self,env:Environment,name=None,size=1,serviceTime=1,serviceTimeFunction=None,mainAgent:Union[int,type]=0,queueType:Union[Iterable[str],str]="standard") -> None:
        Assembly.__init__(self,env,name,size,serviceTime,serviceTimeFunction,mainAgent,queueType=queueType)
        self.connections["operator"] = ObservableVariable(None) 
    def add_operator(self,operator):
        self.connections["operator"] <<= operator
        self.receiveContent("Operator")
    def on_receive(self,i) -> None:
        if all(len(store.queue) > 0 for store in self.stores) and isinstance(self.stateMachine.current_state[0],self.FSM.Starving):
            self.stateMachine.transitionsFrom["Starving"][0]()
    class FSM(FSM):
        class Starving(State):
            initial_state=True
            def on_enter(self):
                if all(len(store.queue) > 0 for store in self.stores):
                    self.stateMachine.transitionsFrom["Starving"][0]()
        class Idle(State):
            pass
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

        S2I=MessageTransition.define(Starving, Idle)
        I2W=MessageTransition.define(Idle, Working)
        I2W._message = "Operator"
        W2B=TimeoutTransition.define(Working, Blocking)
        B2S=EventTransition.define(Blocking, Starving)
        
    
        def onW2B(self):
            try:
                _, msg = self.give(self.connections["next"], self._agent.var.item)
                self.connections["operator"]().free()
                self.connections["operator"] <<= None
                msg.receipts["received"].action = self.transitionsFrom["Blocking"][0]
            except AttributeError as e:
                warn(RuntimeWarning(e))
        W2B.on_transition = onW2B
        B2S.on_transition = lambda self: [msg.receive() for msg in self.var.msg]



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
    assert len(q) == 2
    
def test2():
    env = Environment()
    a = QualityMachine(env,serviceTime=1,quality=Quality(threshold=0.0099))
    q = Queue(env,10)
    a.connections["next"] = q
    env.run(10)
    x = Agent(env,"test")
    a.take(x)
    env.run(20)
    a.take(Agent(env,"test"))
    env.run(30)
    assert len(q) == 0, "Quality threshold already very low, just try again"
    
def test3():
    env = Environment()
    g = Generator(env, Agent, serviceTime=2)
    s = ServerDoubleBuffer(env, "S", serviceTime=1, inputBufferCapacity=1, outputBufferCapacity=8, inputPorts=1, outputPorts=1)
    q = Queue(env,10)
    g.connections["next"] = s.input_ports[0]
    s.output_ports[0].connections["next"] = q
    env.run(10)
    x = Agent(env,"test")
    s.take(x)
    env.run(20)
    s.take(Agent(env,"test"))
    env.run(30)
    assert len(q) == 10 and len(s.OutputBuffer.store) == 6 and s.Server.stateMachine.current_state[0].name == "Starving"

def test4():
    env = Environment()
    g = Generator(env, Agent, serviceTime=2)
    s = QualityServerDoubleBuffer(env, "S", qualityThreshold=0.6, serviceTime=1, inputBufferCapacity=1, outputBufferCapacity=8, inputPorts=1, outputPorts=1)
    q = Queue(env,10)
    g.connections["next"] = s.input_ports[0]
    s.output_ports[0].connections["next"] = q
    env.run(30)
    assert len(q) + len(s.Server._terminator.store) + len(s.OutputBuffer.store) == 14
    
def test5():
    env = Environment()
    g = Generator(env, Agent, serviceTime=2)
    a = SUMachine(env)
    t = Terminator(env)
    op = Operator(env)
    a.connections["next"] = t
    g.connections["next"] = a
    op.connections["stations"].append(a)
    env.run(10)
    env.run(30)
    assert len(t.store) == 13
    
def test6():
    env = Environment()
    g1 = Generator(env, Agent, serviceTime=0.51)
    g2 = Generator(env, Agent, serviceTime=2)
    b = Buffer(env, capacity=10)
    a = ManualAssembly(env,size=2,serviceTime=1)
    t = Terminator(env)
    op = Operator(env)
    g2.connections["next"] = b
    b.connections["next"] = a.toStore(0)
    a.toStore(1).take(Agent(env))
    g1.connections["next"] = a.toStore(1)
    a.connections["next"] = t
    op.connections["stations"].append(a)
    env.run(100)
    env.run(50)
    assert len(t.store) == 1
    
if __name__ == "__main__":
    from hsim.core.des.pymulate import Generator
    from hsim.core.des.manual import Operator
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    print("Tests completed.")