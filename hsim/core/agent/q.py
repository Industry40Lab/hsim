if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))


from heapq import heappush
from typing import Any, Callable, Tuple, Union
import numpy as np
from hsim.core.agent.agent import Agent
from hsim.core.core.msg import MessageQueue, Message, PriorityMessageQueue
from hsim.core.core.event import ConditionEvent, VerifiableEvent

class Queue(MessageQueue):
    def __init__(self, env, capacity=None):
        super().__init__(env)
        self.capacity = capacity if capacity > 0 else np.inf
        self._inbound = dict()
        
    def take(self, agent:Agent) -> tuple[ConditionEvent, Message]:
        msg:Message = Message(self.env, content=agent, receiver=self, wait=True)
        event = VerifiableEvent(self.env, action=self._put, condition=self._capacity_condition, arguments=(msg,)).add()
        self._inbound[msg] = event
        event.verify()
        return event, msg
        
    def _put(self, msg:Message):
        agent:Agent = msg.content
        self._inbound.pop(msg, None)
        msg.reset()
        super()._put(msg)
        # heappush(self.queue, msg)
        msg.receive()
        self._trigger()
        
    def get(self, msg=None) -> Message:
        if msg:
            self.queue.remove(msg)
            self._log_out(msg)
            return msg
        else:
            msg = super().get()
        for e in self._inbound.values():
            e.verify()
        return msg
    
    def _capacity_condition(self):
        return len(self.queue) < self.capacity
        
    def receive(self, *args, **kwargs):
        return
        raise NotImplementedError("Queue does not support receive method")
    
    def inspect(self, index=0) -> tuple[Union[Agent,Any],Message]:
        msg = super().inspect(index)
        return msg.content, msg
    
    def pull(self, other : Union[Agent,Message]):
        if isinstance(other, Agent):
            try:
                msg = [msg for msg in self.queue if msg.content == other][0]
            except IndexError:
                raise ValueError("Agent not in queue")
        else:
            msg = other
        self.get(msg)
        
    def post(self, agent:Agent, decisor:Callable=lambda *args:None) -> tuple[ConditionEvent, Message]:
        msg:Message = Message(self.env, content=agent, receiver=self, wait=True)
        event = ConditionEvent(self.env, action=decisor, condition=self._capacity_condition, arguments=(msg,)).add()
        event.verify()
        return event, msg
    
    def cancel(self, message):
        raise NotImplementedError("Queue does not support cancel method")
        return super().cancel(message)
        
class LockedQueue(Queue):
    def _put(self, msg:Message):
        heappush(self.queue, msg)
        self._trigger()
        # does not receive
    
    def receive(self, agent:Agent=None):
        if agent is None:
            msg = self.get()
            agent = msg.content
        else:
            try:
                msg = [msg for msg in self.queue if msg.content == agent][0]
                agent = agent
            except IndexError:
                raise ValueError("Agent not in queue")
        # msg.reset()
        msg.receive()
        # self._trigger()
        
class PriorityQueue(Queue, PriorityMessageQueue):
    def __init__(self, env, capacity=None, priorityFcn:Callable[[Tuple[Message, Message]], bool]=lambda x,y: False):
        super().__init__(env, capacity=capacity)
        self._priorityFcn = priorityFcn