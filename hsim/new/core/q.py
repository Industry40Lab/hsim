from heapq import heappush
import numpy as np
from agent import Agent
from msg import MessageQueue
from event import ConditionEvent

class Queue(MessageQueue):
    def __init__(self, env, capacity=None):
        super().__init__(env)
        self.capacity = capacity if capacity > 0 else np.inf
        
    def take(self, agent:Agent) -> ConditionEvent:
        event = ConditionEvent(self.env, action=self._put, condition=self._capacity_condition, arguments=(agent,)).add()
        event.verify()
        return event
        
    def _put(self, agent:Agent):
        agent.reset()
        heappush(self.queue, agent)
        agent.receive()
        self._trigger()
    
    def _capacity_condition(self):
        return len(self.queue) < self.capacity
        
    def receive(self, *args, **kwargs):
        raise NotImplementedError("Queue does not support receive method")
    
class LockedQueue(Queue):
    def _put(self, agent:Agent):
        heappush(self.queue, agent)
        # does not self trigger
        # does not receive
    
    def receive(self, agent:Agent=None):
        if agent is None:
            agent = self.get()
        agent.reset()
        agent.receive()
        self._trigger()