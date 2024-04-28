from __future__ import annotations
import copy
from types import MethodType
from typing import Callable, Iterable, Union
from salabim import State, Component

class Transition(State):
    @classmethod
    def copy(cls, state:"MachineState", target:"MachineState"=None, trigger:State=None, condition=None, action=None): # type: ignore
        class Transition(cls):
            _state = state
            _target = target
            if trigger is not None:
                _trigger = trigger
            if action is not None:
                _action = action
            _condition_eval = condition
        return Transition
    def add(self,state):
        new = copy.deepcopy(self)
        state._transitions.append(new)
        new._state = state
        return new
    def __init__(self, state:"MachineState", target:"MachineState"|None=None, trigger:Union[State, Iterable[State]]=None, condition=None, action=None): # type: ignore
        self._state = state
        self._target = target
        self._trigger: Union[State, Iterable[State]] = trigger if isinstance(trigger, (State,Iterable)) else None #State(value=True)
        self._action: Callable = action if callable(action) else lambda self: None
        self._condition = condition if isinstance(condition, State) else None #State(value=True)

def action(instance):
    def decorator(f):
        f = MethodType(f, instance)
        setattr(instance, '_action', f)
        return f
    return decorator