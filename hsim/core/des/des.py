if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))


from typing import Iterable, Union

import numpy as np
from hsim.core.agent.q import LockedQueue, PriorityQueue, Queue
from hsim.core.fsm.states import State
from hsim.core.fsm.FSM import FSM
from hsim.core.core.msg import Message
from hsim.core.core.event import ConditionEvent
from hsim.core.agent.agent import Agent, FSM
from hsim.core.core.env import Environment

def createQueue(env,capacity:int=1,queueType="standard"):
    if type(capacity) != int and capacity != np.inf:
        raise ValueError("Capacity must be an integer.")
    if capacity < 1:
        return LockedQueue(env,capacity=capacity)
    if queueType == "standard":
        return Queue(env,capacity=capacity)
    elif queueType == "priority":
        return PriorityQueue(env,capacity=capacity)
    elif queueType == "locked":
        return LockedQueue(env,capacity=capacity)
    else:
        raise ValueError(f"Queue type {queueType} is not recognized.")
    
class DESBase(Agent):
    Next : Union[Agent,Iterable[Agent]]
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
    
class DESBlock(DESBase):
    __queueType = "standard" # "priority", "locked"
    def __init__(self,env,name=None,capacity=1, queueType="standard") -> None:
        super().__init__(env,name)
        self.store = createQueue(env,capacity,queueType)
        self.store.on_receive = self.on_receive 
        
            
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
    __queueType = "locked"
    

class AgentMask(Agent):
    def __init__(self,original,masked:dict):
        for key in masked.keys():
            if key not in original.__dict__.keys():
                raise AttributeError(f"Attribute {key} does not exists in {original}.")
        self.original = original
        self.masked = masked
    def __getattribute__(self, name):
        mask = object.__getattribute__(self,"masked")
        if name in mask.keys():
            return mask[name]
        return object.__getattribute__(self,"original").__getattribute__("name")
    @classmethod
    def mask(cls,original,masked:dict):
        return cls(original,masked)


class DESMulti(DESBase):
    Next : Union[Agent,Iterable[Agent]]
    def __init__(self,env,name=None,size:int=1,capacity:Union[int,Iterable[int]]=1,queueType:Union[str,Iterable[str]]="standard",storeNames:Union[str,Iterable[str]]="") -> None:
        super().__init__(env,name)
        self.stores = list()
        for i in range(size):
            thisCapacity = capacity if type(capacity)==int else capacity[i]
            thisQueueType = queueType if type(queueType)==str else queueType[i]
            if type(storeNames)==str:
                thisStoreName = f"Store{i}" if storeNames == "" else f"{storeNames}{i}"
            else:
                thisStoreName = storeNames[i]
            setattr(self,thisStoreName,createQueue(env,capacity=thisCapacity,queueType=thisQueueType))
            self.stores += [getattr(self,thisStoreName)]
            self.stores[i].on_receive = lambda: self.on_receive(i)
        self.__queueType = queueType if type(queueType) == str else [i for i in queueType]
    @property
    def store(self):
        raise AttributeError("store is not a valid attribute for DESMulti.")
    def take(self,item,storeIndex:int=0) -> tuple[ConditionEvent, Message]:
        return self.stores[storeIndex].take(item)
    def post(self, item:Agent, storeIndex:int=0) -> tuple[ConditionEvent, Message]:
        return self.stores[storeIndex].post(item)
    def on_receive(self,storeIndex:int) -> None:
        raise NotImplementedError(f"on_receive method is not implemented for {self}.")
    def __getitem__(self, key):
        try:
            if type(key) == int:
                return self.stores[key]
            elif type(key) == str:
                return getattr(self,key)
        except:
            raise KeyError(f"Key {key} is not valid.")
                
    

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
        
if __name__ == "__main__":
    env = Environment()
    a = DESMulti(env,size=2)
    x = Agent(env)
    m = AgentMask.mask(x,{"no":"test"})
    print(m.store)
    a.take(x,1)
    env.run(10)
    print(1)