from __future__ import annotations
from enum import Enum, auto
from typing import Any, Callable, Iterable, List, Optional, Union
from warnings import warn

import numpy as np

class Status(Enum):
    PENDING = auto()
    SCHEDULED = auto()
    TRIGGERED = auto()
    PROCESSED = auto()
    
class BaseEvent():
    def __init__(self, env: 'Environment', priority: Union[float,int]=1, action: Union[Iterable[Callable[..., Any]], Callable[..., Any]] = object, arguments: Any = [], **kwargs: Any): # type: ignore
        self.env = env
        self.sequence = next(env.scheduler._sequence_generator)
        self.time = np.inf
        self.priority = priority
        self._status : Status = Status.PENDING
        self.action = action
        self.arguments = arguments
        # self.action = attachAction(action, arguments, **kwargs)
        self.kwargs = kwargs
    def add(self) -> BaseEvent:
        self.env.scheduler.enter(self)
        return self
    def reset(self) -> BaseEvent:
        self.cancel(safe=False)
        self.time = np.inf
        self._status = Status.PENDING
        return self.add()
    def cancel(self, safe=True) -> None:
        try:
            self.env.scheduler.cancel(self)
        except ValueError as e:
            if self.triggered and safe:
                raise ValueError("Cannot cancel processed event")
    def add_action(self, action:Callable, arguments: Any = []) -> None:
        if action is object:
            self.action, self.arguments = list(), list()
        elif not isinstance(action, Iterable):
            self.action, self.arguments = [self.action], [self.arguments]
        if isinstance(action, Iterable):
            if len(action) != len(arguments):
                raise ValueError("Arguments should be provided for each action")
            else:
                for a,b in zip(action, arguments):
                    self.action.append(a), self.arguments.append(b)
        else:
            self.action.append(action), self.arguments.append([arguments])
    def schedule(self, time=None) -> BaseEvent:
        self.time = time if time else self.time
        self._status = Status.SCHEDULED
        return self
    def trigger(self) -> None:
        self._status = Status.TRIGGERED
        if self.time == np.inf:
            self.time = self.env.now
            self.priority = 0
            self.env.scheduler.heapify()
            # self.env.scheduler.enter(self)
    def process(self) -> None:
        self._status = Status.PROCESSED
    @property
    def status(self):
        return self._status
    @property
    def pending(self) -> bool:
        return self.status == Status.PENDING
    @property
    def scheduled(self) -> bool:
        return self.status == Status.SCHEDULED
    @property
    def triggered(self) -> bool:
        return self.status == Status.TRIGGERED
    @property
    def processed(self) -> bool:
        return self.status == Status.PROCESSED
    def __lt__(self, other: BaseEvent) -> bool:
        return (self.time, self.priority, self.sequence) < (other.time, other.priority, other.sequence)
    def __le__(self, other: BaseEvent) -> bool:
        if not isinstance(other, BaseEvent):
            return NotImplemented
        return (self.time, self.priority, self.sequence) <= (other.time, other.priority, other.sequence)
    def __eq__(self, other: BaseEvent) -> bool:
        if not isinstance(other, BaseEvent):
            return NotImplemented
        return (self.time, self.priority, self.sequence) == (other.time, other.priority, other.sequence)
    def __ne__(self, other: BaseEvent) -> bool:
        if not isinstance(other, BaseEvent):
            return NotImplemented
        return (self.time, self.priority, self.sequence) != (other.time, other.priority, other.sequence)
    def __gt__(self, other: BaseEvent) -> bool:
        if not isinstance(other, BaseEvent):
            return NotImplemented
        return (self.time, self.priority, self.sequence) > (other.time, other.priority, other.sequence)
    def __ge__(self, other: BaseEvent) -> bool:
        if not isinstance(other, BaseEvent):
            return NotImplemented
        return (self.time, self.priority, self.sequence) >= (other.time, other.priority, other.sequence)
    
    
class TimedEvent(BaseEvent):
    def __init__(self, env: 'Environment', time: Union[float,int,None], priority: Union[float,int] = 1, action: Union[Iterable[Callable[..., Any]], Callable[..., Any]] = object, arguments: Any = [], **kwargs: Any): # type: ignore
        super().__init__(env, priority, action, arguments, **kwargs)
        self.time = time
        if self.time < self.env.now:
            raise ValueError("Event cannot be scheduled in the past")
        self._status : Status = Status.SCHEDULED if time < np.inf else Status.PENDING
    @classmethod
    def at(cls, env: 'Environment', time: Union[float,int], priority: Union[float,int] = 1) -> TimedEvent: # type: ignore
        return cls(env, time, priority)


class DelayEvent(BaseEvent):
    def __init__(self, env: 'Environment', delay: Union[float,int], priority: Union[float,int] = 1, action: Union[Iterable[Callable[..., Any]], Callable[..., Any]] = object, arguments: Any = [], **kwargs: Any): # type: ignore
        super().__init__(env, priority, action, arguments, **kwargs)
        self.time = delay + self.env.now
        self._status : Status = Status.SCHEDULED if delay < np.inf else Status.PENDING
    @classmethod
    def after(cls, env: 'Environment', delay: Union[float,int], priority: Union[float,int] = 1) -> TimedEvent: # type: ignore
        return cls(env, env.now + delay, priority)


class ConditionEvent(BaseEvent):
    def __init__(self, env: 'Environment', condition: Callable[[], bool], priority: Union[float,int] = 1, action:Union[Iterable[Callable[..., Any]], Callable[..., Any]]=object, arguments: Any = [], **kwargs: Any): # type: ignore
        super().__init__(env, priority,action, arguments, **kwargs)
        self.condition = condition
        self._status : Status = Status.PENDING

    def verify(self) -> bool:
        if self.condition():
            self.trigger()
            return True
        else:
            return False
            
class RecurringEvent(BaseEvent):
    def __init__(self, env: 'Environment', priority: float | int = 1, action: Iterable[Callable[..., Any]] | Callable[..., Any] = object, arguments: Any = [], **kwargs: Any): # type: ignore
        super().__init__(env, priority, action, arguments, **kwargs)
    def new(self) -> BaseEvent:
        new = BaseEvent(self.env, self.priority, self.action, self.arguments, **self.kwargs)
        self._children.append(new)
        new._parent = self
        return new
    def __iter__(self) -> BaseEvent:
        return self.new()
    
class AnyEvent(ConditionEvent):
    def __init__(self, env: 'Environment', events:Iterable[ConditionEvent], priority: Union[float,int] = 1, action:Union[Iterable[Callable[..., Any]], Callable[..., Any]]=object, **kwargs: Any): # type: ignore
        arguments = [event for event in events]
        condition = lambda: any([event.condition() for event in events])
        super().__init__(env, condition, priority, action, arguments, **kwargs)
        
        
class AllEvent(ConditionEvent):
    def __init__(self, env: 'Environment', events:Iterable[ConditionEvent], priority: Union[float,int] = 1, action:Union[Iterable[Callable[..., Any]], Callable[..., Any]]=object, **kwargs: Any): # type: ignore
        arguments = [event for event in events]
        condition = lambda: all([event.condition() for event in events])
        super().__init__(env, condition, priority, action, arguments, **kwargs)
        
    
def attachAction(action, arguments: List[Any] = []) -> Callable[..., Any]:
    return action
    if isinstance(action, Iterable):
        assert len(action) == len(arguments) or len(arguments) == 0, "Arguments should be provided for each action" # len(kwargs)
        def action_function(args: Any) -> None:
            for index, callback in enumerate(action):
                if len(arguments) > 0:
                    callback(*args[index])
                else:
                    callback()
        action = action_function
    return action

from functools import wraps
def wait(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        e, f = func(*args, **kwargs)
        if not isinstance(e, BaseEvent) or not callable(f):
            raise TypeError("Function must return an Event and a callable")
        e.action = f
        e.add()
        return e
    return wrapper


