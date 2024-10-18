if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))


from typing import Iterable, Union
from hsim.core.agent.q import LockedQueue, PriorityQueue, Queue
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.core.msg import Message
from hsim.core.core.event import ConditionEvent
from hsim.core.agent.agent import Agent, FSM

class DESBlock(Agent):
    __queueType = "standard" # "priority", "locked"
    Next : Union[Agent,Iterable[Agent]]
    def __init__(self,env,name=None,capacity=1, queueType="standard") -> None:
        super().__init__(env,name)
        if queueType == "standard":
            self.store:Queue = Queue(env,capacity=capacity)
        elif queueType == "priority":
            self.store = PriorityQueue(env,capacity=capacity)
        elif queueType == "locked":
            self.store = LockedQueue(env,capacity=capacity)
        else:
            raise ValueError(f"Queue type {self.__queueType} is not recognized.")
        self.store.on_receive = self.on_receive
    def take(self,item) -> tuple[ConditionEvent, Message]:
        return self.store.take(item)
    def give(self, other:Agent, item:Agent) -> tuple[ConditionEvent, Message]:
        return other.take(item)
    def post(self, item:Agent) -> tuple[ConditionEvent, Message]:
        return self.store.post(item)
    def on_receive(self) -> None:
        raise NotImplementedError(f"on_receive method is not implemented for {self}.")
    class FSM(FSM):
        class Empty(State):
            initial_state=True
            
class TimedBlock(Agent):
    def calculateServiceTime(self,entity=None,attribute='serviceTime'):
        if self.var.serviceTimeFunction == None:
            if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
                return self.var.serviceTime
            elif self.var.serviceTime == None:
                time = getattr(entity,attribute)
                if type(time) is dict:
                    time = time[self.name]
                return time
            elif len(self.var.serviceTime)==0:
                time = getattr(entity,attribute)
                if type(time) is dict:
                    time = time[self.name]
                return time
            elif len(self.var.serviceTime)>0:
                return self.var.serviceTime[0]
        elif self.var.serviceTimeFunction != None:
            if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
                return self.var.serviceTimeFunction(self.var.serviceTime)
            try:
                if self.var.serviceTime==None:
                    time = getattr(entity,attribute)
                    if type(time) is dict:
                        time = time[self.name]
                    return self.var.serviceTimeFunction(time)
            except:
                pass
            if len(self.var.serviceTime)==0:
                return self.var.serviceTimeFunction()
            elif len(self.var.serviceTime)>0:
                return self.var.serviceTimeFunction(*self.var.serviceTime)
            
class DESLocked(DESBlock):
    def __init__(self,env,name=None,capacity=1) -> None:
        super().__init__(env,name,capacity,queueType="locked")



def calculateServiceTime(self,entity=None,attribute='serviceTime'):
    if self.var.serviceTimeFunction == None:
        if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
            return self.var.serviceTime
        elif self.var.serviceTime == None:
            time = getattr(entity,attribute)
            if type(time) is dict:
                time = time[self.name]
            return time
        elif len(self.var.serviceTime)==0:
            time = getattr(entity,attribute)
            if type(time) is dict:
                time = time[self.name]
            return time
        elif len(self.var.serviceTime)>0:
            return self.var.serviceTime[0]
    elif self.var.serviceTimeFunction != None:
        if type(self.var.serviceTime)==int or type(self.var.serviceTime)==float:
            return self.var.serviceTimeFunction(self.var.serviceTime)
        try:
            if self.var.serviceTime==None:
                time = getattr(entity,attribute)
                if type(time) is dict:
                    time = time[self.name]
                return self.var.serviceTimeFunction(time)
        except:
            pass
        if len(self.var.serviceTime)==0:
            return self.var.serviceTimeFunction()
        elif len(self.var.serviceTime)>0:
            return self.var.serviceTimeFunction(*self.var.serviceTime)
        
