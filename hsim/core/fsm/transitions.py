if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))


from typing import Any, Callable, Union
import logging
from hsim.core.core.event import ConditionEvent, BaseEvent, DelayEvent, TimedEvent, ConditionedEvent

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
        else:
            self.event = BaseEvent(env, action=self)
    def stop(self):
        self.event.cancel(safe=False) if self.event is not None and not self.event.triggered else None 
    def _on_transition(self):
        self.on_transition()
    def on_start(self):
        pass
    def _on_start(self):
        self.on_start()
    def on_transition(self):
        pass
    def __call__(self):
        None if not self._env._debug else print(f"{self._fsm} transitioning from {self.source.name} to {self.target.name} at time {self._env.now}")
        self._fsm.log_transition(self.source, self.target)  # Log the transition
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
        self._condition = condition if condition is not None else self._condition
        self._condition_created = False  # Track if we've created the ObservableExpression yet
    def start(self):
        # Only create the condition ONCE - the first time start() is called
        # After that, reuse the same ObservableExpression to maintain notification chain
        if not self._condition_created:
            if callable(self._condition) or self.condition is None:
                # Call _condition() - Python automatically binds self for class attribute lambdas
                self.condition = self._condition() if callable(self._condition) else self._condition
            self._condition_created = True
            print(f"[FIRST START] Created condition for {self._fsm}: id={id(self.condition)}")
        else:
            print(f"[REUSE] Reusing existing condition for {self._fsm}: id={id(self.condition)}")
        self.event = ConditionedEvent(self._env, condition=self.condition, action=self).add()
        # CRITICAL: If condition is already True, trigger immediately
        # recalc() won't fire because _stored_value hasn't changed
        if self.condition:
            print(f"[IMMEDIATE] Condition already True, triggering event at {self._env.now}")
            self.event.trigger()
    def __call__(self):
        print(f"[DEBUG] ConditionTransition.__call__ at time {self._env.now}: condition={bool(self.condition)}, {self.source.name}->{self.target.name}, FSM={self._fsm}")
        if self.condition:
            super().__call__()
        else:
            # Race condition: create new event for the same condition
            # Call .add() to properly register with scheduler and set condition._event
            print(f"[RACE] Creating new event for existing condition id={id(self.condition)}")
            self.event = ConditionedEvent(self._env, condition=self.condition, action=self).add()

from .states import State