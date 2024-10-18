from collections import OrderedDict
from copy import deepcopy
from typing import Any, Callable, Iterable, List, Union
import numpy as np
import logging

from hsim.core.core.event import ConditionEvent, BaseEvent, DelayEvent, TimedEvent
from hsim.core.core.env import Environment
from hsim.core.core.msg import Message, MessageQueue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Transition:
    def __init__(self, fsm, source:'State', target:'State', guard:Union[Union[float, int], str, Callable[[], bool], None]=None):
        self._fsm = fsm
        self._env = fsm._env
        self.source = source
        self.target = target
        self.guard = guard
        self.event = None
    def start(self):
        self.on_start()
        env, guard = self._env, self._guard
        if isinstance(guard, (float, int)):
            self.event = TimedEvent(env, time=guard, action=self)
        elif isinstance(guard, Callable):
            self.event = ConditionEvent(env, condition=guard, action=self)
        elif guard is not None:
            self.event = BaseEvent(env, action=self)
        else:
            self.event = BaseEvent(env, action=self)
    def stop(self):
        self.event.cancel(safe=False)
    def _on_transition(self):
        self.on_transition()
    def on_start(self):
        pass
    def _on_start(self):
        self.on_start()
    def on_transition(self):
        pass
    def __call__(self):
        print(f"{self._fsm} transitioning from {self.source.name} to {self.target.name}")
        self.source.stop()
        self._on_transition()
        self.target.start()
    @classmethod
    def define(cls, source, target):
        class Transition(cls):
            pass
        Transition.__name__ = cls.__name__
        Transition._sourceStateClass = source
        Transition._targetStateClass = target
        return Transition
    def __override__(obj):
        z = {key: value for key, value in obj.__class__.__dict__.items() if not callable(value) and not key.startswith('__')}
        for key, value in z.items():
            setattr(obj, key, value)
        return obj
    def __getattr__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self,name)
        except AttributeError as e1:
            if name == 'fsm' or name[:2] == "__":
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from e1
            try:
                return getattr(object.__getattribute__(self,'_fsm'),name)
            except AttributeError as e2:
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from e2

        
class TimeoutTransition(Transition):
    def __init__(self, fsm, source:'State', target:'State', timeout:Union[float, int] = 0):
        super().__init__(fsm, source, target)
        self.timeout = timeout
    def start(self):
        self.event = DelayEvent(self._env, self.timeout, action=self).add()

class MessageTransition(Transition):
    _message = None
    def __init__(self, fsm, source:'State', target:'State', message:Any=None):
        super().__init__(fsm, source, target)
        self.message = self._message if message is None else message
    def start(self):
        self.event = BaseEvent(self._env, action=self).add()
    def interpret(self, message):
        return self.message == message.content or self.message is None


class EventTransition(Transition):
    """Incomplete"""
    def __init__(self, fsm, source:'State', target:'State', event=None):
        super().__init__(fsm,  source, target)
        self.event = BaseEvent(self._env, action=self).add() if event is None else event
    def start(self):
        self.event.cancel()
        self.event.add()
        
        
class ConditionTransition(Transition):
    _condition = lambda *args : True
    def __init__(self, fsm, source:'State', target:'State', condition:Callable[[], bool] = None):
        super().__init__(fsm,  source, target)
        self.condition = self._condition if condition is None else condition 
    def start(self):
        self.event = ConditionEvent(self._env, condition=self.condition, action=self).add()
    def verify(self) -> bool:
        return self.event.verify()

        
from .states import State
from .FSM import FSM