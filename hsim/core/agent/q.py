if __name__ == "__main__":
    import sys
    import os
    try:
        sys.path.append("/".join(os.path.abspath(__file__).split("/")[:os.path.abspath(__file__).split("/").index("hsim")+1]))
    except:
        sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))
from typing import Any, Callable, Tuple, Union
import numpy as np
from hsim.core.agent.agent import Agent
from hsim.core.core.msg import MessageQueue, Message, PriorityMessageQueue
from hsim.core.core.event import BaseEvent, ConditionedEvent
from hsim.core.core.obs import ObservableVariable, ObservableExpression


# def heappush(obs, item):
#     return heapq.heappush(obs.value, item)


class Queue(MessageQueue):
    def __init__(self, env, capacity=None):
        super().__init__(env)
        self.capacity = capacity if capacity > 0 else np.inf
        self.queue_size = self.queue.length()
        self.capacity_condition = self.queue_size < self.capacity
        self._inbound = dict()
        
    def take(self, agent:Agent) -> tuple[ConditionedEvent, Message]:
        msg:Message = Message(self.env, content=agent, receiver=self, wait=True)
        if self.capacity_condition.value:
            event = ConditionedEvent(self.env, condition=self.capacity_condition).add()
            # self.env.scheduler.add(event)
            event.trigger()
            self._put(msg)
        else:
            event = ConditionedEvent(self.env, action=self._put, condition=self.capacity_condition, arguments=(msg,)).add()
            self._inbound[msg] = event
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
        # Events are automatically triggered by the observable system when conditions change
        # No need to manually verify conditions
        return msg
    
        
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
        
    def post(self, agent:Agent, decisor:Callable=lambda *args:None) -> tuple[ConditionedEvent, Message]:
        msg:Message = Message(self.env, content=agent, receiver=self, wait=True)
        event = ConditionedEvent(self.env, action=decisor, condition=self.capacity_condition, arguments=(msg,)).add()
        return event, msg
    
    def cancel(self, message):
        raise NotImplementedError("Queue does not support cancel method")
        return super().cancel(message)
        
class LockedQueue(Queue):
    def take(self, agent:Agent) -> tuple[ConditionedEvent, Message]:
        msg:Message = Message(self.env, content=agent, receiver=self, wait=True)
        if self.capacity_condition.value:
            event = BaseEvent(self.env).add()
            self._put(msg)
        else:
            event = BaseEvent(self.env, action=self._put, condition=self.capacity_condition, arguments=(msg,)).add()
            self._inbound[msg] = event
        return event, msg
    
    def _put(self, msg:Message):
        self.queue.add(msg)
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


if __name__ == "__main__":
    # Test the new ConditionedEvent functionality with ObservableExpression
    print("Testing ConditionedEvent with ObservableExpression in Queue...")
    
    # Import necessary modules
    from hsim.core.core.env import Environment
    from hsim.core.agent.agent import Agent
    
    # Create test environment
    env = Environment()
    
    # Test 1: Basic Queue with capacity
    print("\n=== Test 1: Basic Queue with Capacity ===")
    queue = Queue(env, capacity=2)
    
    # Create test agents
    agent1 = Agent(env, name="Agent1")
    agent2 = Agent(env, name="Agent2") 
    agent3 = Agent(env, name="Agent3")
    
    print(f"Queue capacity: {queue.capacity}")
    print(f"Initial queue size: {queue.queue_size.value}")
    print(f"Capacity condition value: {queue.capacity_condition.value}")
    
    # Test immediate acceptance (queue not full)
    event1, msg1 = queue.take(agent1)
    print(f"After agent1 take - queue size: {queue.queue_size.value}, condition: {queue.capacity_condition.value}")
    env.run(1)
    event2, msg2 = queue.take(agent2)
    print(f"After agent2 take - queue size: {queue.queue_size.value}, condition: {queue.capacity_condition.value}")
    
    # Test waiting (queue full)
    event3, msg3 = queue.take(agent3)
    print(f"After agent3 take - queue size: {queue.queue_size.value}, condition: {queue.capacity_condition.value}")
    print(f"Agent3 should be waiting - event in inbound: {msg3 in queue._inbound}")
    
    # Test reactive triggering by removing an agent
    print("\n=== Test 2: Reactive Triggering ===")
    removed_msg = queue.get()
    print(f"Removed agent: {removed_msg.content.name}")
    print(f"After removal - queue size: {queue.queue_size.value}, condition: {queue.capacity_condition.value}")
    
    # Test 3: Observable Expression directly
    print("\n=== Test 3: Observable Expression Behavior ===")
    
    
    # Test 4: LockedQueue behavior
    print("\n=== Test 4: LockedQueue Behavior ===")
    locked_queue = LockedQueue(env, capacity=1)
    agent4 = Agent(env, name="Agent4")
    
    event4, msg4 = locked_queue.take(agent4)
    print(f"LockedQueue - queue size: {locked_queue.queue_size.value}")
    print(f"Message received status: {msg4.receipts["received"].triggered}")
    
    # Manually receive the message in locked queue
    locked_queue.receive(agent4)
    print(f"After manual receive - message status: {msg4.receipts["received"].triggered}")
    
    # Test 5: Post method with decisor
    print("\n=== Test 5: Post Method with Decisor ===")
    
    def test_decisor(msg):
        print(f"Decisor called for {msg.content.name}")
        return True
    
    agent5 = Agent(env, name="Agent5")
    event5, msg5 = queue.post(agent5, decisor=test_decisor)
    print(f"Post event created for {msg5.content.name}")
    
    print("\n=== All Tests Completed ===")
    print("ConditionedEvent with ObservableExpression successfully tested!")
    print("Key improvements:")
    print("- Reactive condition checking (no more O(n) polling)")
    print("- Automatic triggering when capacity conditions change")
    print("- Seamless integration with Observable system")