import numpy as np
from core import Environment, State, Transition, CHFSM, Store, AllOf
from pymulate import Server, ServerWithBuffer, ServerDoubleBuffer, Generator, Queue, ManualStation, Operator, OutputSwitch, Router, StoreSelect

class MachineMIP(Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,failure_rate=0,TTR=60):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.var.failure_rate = failure_rate
        self.var.TTR = TTR
    class Fail(State):
        pass
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = self.Store.subscribe()
    T1 = 'ciao'
    S2F = Transition(Starving, Fail, lambda self: self.var.request, condition=lambda self: np.random.uniform() < self.var.failure_rate)
    S2W = Transition(Starving, Server.Working, lambda self: self.var.request)
    F2W = Transition(Fail, Server.Working, lambda self: self.env.timeout(self.var.TTR))
    T3=Transition(Server.Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())
        
class SwitchQualityMIP(CHFSM):
    def __init__(self, env, name=None):
        super().__init__(env,name)
        self.var.Trigger = env.event()
        self.var.quality_rate = 0.1
        self.var.requests = list()
    def build(self):
        self.Queue = Store(self.env)
    def put(self,item):
        return self.Queue.put(item)
    class Wait(State):
        initial_state=True
        def _do(self):
            self.var.request = self.Queue.subscribe()
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request.read()
            if np.random.uniform() < self.var.quality_rate:
                self.var.putRequest = self.Rework.put(self.var.entity)
            else:
                self.var.putRequest = self.Next.put(self.var.entity)
    T1 = Transition(Wait, Working, lambda self: self.var.request)
    T2 = Transition(Working,Wait,lambda self: self.var.putRequest,action = lambda self: self.var.request.confirm())


class FinalAssemblyManualMIP(ManualStation):
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = [self.Before1.subscribe(),self.Before2.get()]     
    S2I = Transition(Starving, ManualStation.Idle, lambda self: AllOf(self.env,self.var.request))
    def action(self):
        self.var.request = self.var.request[0]
        self.NeedOperator.succeed()
    S2I._action = action
    T3=Transition(ManualStation.Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())

    

    
class FinalAssemblyMIP(Server):
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = [self.connections['before1'].get(),self.connections['before2'].get()]
    class Working(State):
        def _do(self):
            self.var.entity = self.var.request._events[0].value
    S2W = Transition(Starving, Working, lambda self: AllOf(self.env,self.var.request))
    T2=Transition(Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))

  
class AutomatedMIP(ManualStation):
    class Setup(State):
        pass
    # class Working(State):
    #     pass
        # def _do(self,event):
        #     self.var.operator.var.Pause.succeed()
        #     self.var.operator = None
    T1b=Transition(ManualStation.Idle, Setup, lambda self: self.GotOperator,action=lambda self:self.NeedOperator.restart())
    T1c=Transition(Setup, ManualStation.Working, lambda self: self.env.timeout((0.1+np.random.uniform()/10) * self.sm.calculateServiceTime(self.var.request.read())))
    T2 = Transition(ManualStation.Working, ManualStation.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
    def action(self):
        self.GotOperator.restart()
        for op in self.Operators.items:
            op.Pause.succeed()
            self.Operators.items.remove(op)
    T2._action = action
    # T1=Transition(Server.Starving, Idle, lambda self: self.var.request, action = lambda self: self.NeedOperator.succeed())
    # T1b=Transition(Idle, Server.Working, lambda self: self.GotOperator)
    
    # T2 = Transition(Server.Working, Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)))
