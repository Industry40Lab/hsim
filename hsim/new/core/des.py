from typing import Iterable, Union
from q import LockedQueue, PriorityQueue, Queue
from states import State
from FSM import FSM
from msg import Message
from event import ConditionEvent
from agent import Agent, FSM

class DESBlock(Agent):
    __queueType = "standard" # "priority", "locked"
    Next : Union[Agent,Iterable[Agent]]
    def __init__(self,env,name=None,capacity=1) -> None:
        super().__init__(env,name)
        if self.__queueType == "standard":
            self.store:Queue = Queue(env,capacity=capacity)
        elif self.__queueType == "priority":
            self.store = PriorityQueue(env)
        elif self.__queueType == "locked":
            self.store = LockedQueue(env)
        else:
            raise ValueError(f"Queue type {self.__queueType} is not recognized.")
        self.store.on_receive = self.on_receive
    def take(self,item) -> tuple[ConditionEvent, Message]:
        return self.store.take(item)
    def give(self, other, item) -> tuple[ConditionEvent, Message]:
        return other.take(item)
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
    __lockedQueue__ = True



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
        
