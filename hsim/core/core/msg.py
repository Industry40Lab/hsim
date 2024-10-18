if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))


from abc import abstractmethod
from heapq import heappop, heappush
import heapq
import types
from typing import Any, Callable, Iterable, OrderedDict, Tuple
from hsim.core.core.event import BaseEvent, RecurringEvent, Status

class Message():
    def __init__(self, env, content:Any=None, receiver:'MessageQueue'=None, sender=None, wait=False):
        self.env = env
        self.content = content
        self.receiver = receiver
        self.sender = sender
        self.receipts = OrderedDict()
        self.receipts["received"] = BaseEvent(env, action=self._on_received).add()
        self.receipts["read"] = BaseEvent(env, action=self._on_read).add()
        if receiver and not wait:
            receiver.receive(self)
    def send(self, receiver=None):
        receiver = receiver if receiver else self.receiver
        if receiver:
            receiver.receive(self)
        else:
            raise ValueError("No receiver specified")
    def cancel(self, receiver=None):
        receiver = receiver if receiver else self.receiver
        if receiver:
            receiver.cancel(self)
        else:
            raise ValueError("No receiver specified")
    def schedule(self):
        self.status = Status.SCHEDULED
        self._on_receipt()
    def _on_received(self):
        pass
    def _on_read(self):
        pass
    def receive(self):
        self.receipts["received"].trigger()
    def read(self):
        self.receipts["read"].trigger()
    def reset(self):
        self.receipts["received"].reset()
        self.receipts["read"].reset()
    def __lt__(self,other:'Message'):
        try:
            return self.content < other.content # compare content
        except AttributeError:
            return False
        

class MessageQueue:
    put, get = heappush, heappop
    def __init__(self, env):
        self.env = env
        self.queue = list()
        self.event = BaseEvent(env, action=self._on_receive).add()
        
    def _trigger(self):
        # self.event.action = self._on_receive
        self.event.trigger()
        
    def _reset(self):
        self.event.reset()
        
    def _put(self, message):
        heappush(self.queue, message)

    def receiveContent(self, content:Any, sender=None) -> Message:
        message = Message(self.env, content, receiver=self, sender=sender, wait=True)
        self.receive(message)
        return message

    def receive(self, message: Message):
        self._put(message)
        message.receive()
        self._trigger()
        
    def cancel(self, message: Message):
        try:
            self.queue.remove(message)
        except ValueError:
            print("Message not found in receiver, just deleting it")
            message.reset()
            [self.env.scheduler._queue.remove(message.receipts[key]) for key in message.receipts]
            del message
        
    def get(self)->Message:
        message = heappop(self.queue)
        message.read()
        return message
        
    def inspect(self, index=0):
        return self.queue[index]
        
    def _on_receive(self):
        self.on_receive()
        self._reset()
    
    @abstractmethod
    def on_receive(self):
        pass
    
    def __getitem__(self, index):
        return self.queue[index]
    
    def __repr__(self) -> str:
        content = f": {[f'{msg}:{msg.content}' for msg in self.queue]}" if self.queue else ""
        return f"<{self.__class__.__name__} object at {hex(id(self))}> ({len(self.queue)})" + content
    

class PriorityMessageQueue(MessageQueue):
    def __init__(self, env, capacity=None, priorityFcn:Callable[[Tuple[Message, Message]], bool]=lambda x,y: False):
        super().__init__(env, capacity=capacity)
        self._priorityFcn = priorityFcn

    def _put(self, msg:Message):
        msg.__lt__ = types.MethodType(self.priorityFcn, msg)
        heappush(self.queue, msg)
        msg.receive()
        self._trigger()
    @property
    def priorityFcn(self):
        return self._priorityFcn
    def changePriorityFcn(self, fcn:Callable[[Tuple[Message, Message]], bool]):
        self._priorityFcn = fcn
        for msg in self.queue:
            msg.__lt__ = types.MethodType(fcn, msg)
        heapq.heapify(self.queue)
        
class CallableList(list):
    def __init__(self, *args):
        for arg in args:
            if not callable(arg):
                raise TypeError("Arguments must be callable")
        super().__init__(args)
    def __setitem__(self, index, value):
        if not callable(value):
            raise TypeError("Arguments must be callable")
        super().__setitem__(index,value)
    def __call__(self, *args):
        if len(args) == 0:
            args = [() for _ in range(len(self))]
        elif len(args) != len(self):
            raise ValueError("Arguments do not match")
        for index, item in enumerate(self):
            item(*args[index])