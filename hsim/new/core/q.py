from heapq import heappush
from typing import Any, Callable, Tuple, Union
import numpy as np
from agent import Agent
from msg import MessageQueue, Message, PriorityMessageQueue
from event import ConditionEvent

class Queue(MessageQueue):
    def __init__(self, env, capacity=None):
        super().__init__(env)
        self.capacity = capacity if capacity > 0 else np.inf
        
    def take(self, agent:Agent) -> tuple[ConditionEvent, Message]:
        msg:Message = Message(self.env, content=agent, receiver=self, wait=True)
        event = ConditionEvent(self.env, action=self._put, condition=self._capacity_condition, arguments=(msg,)).add()
        event.verify()
        return event, msg
        
    def _put(self, msg:Message):
        agent:Agent = msg.content
        msg.reset()
        heappush(self.queue, msg)
        msg.receive()
        self._trigger()
    
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
        self.queue.remove(msg) 
        
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