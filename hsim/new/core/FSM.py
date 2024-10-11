from collections import OrderedDict
from typing import Any, Callable, Iterable, List, Union
import numpy as np
import logging

from event import ConditionEvent, BaseEvent, TimedEvent
from env import Environment
from msg import Message, MessageQueue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FSM:
    def __init__(self, env):
        self._env = env
        env._objects.append(self)
        self._states:List['State'] = []
        self._transitions:List['Transition'] = []
        self._messages:MessageQueue = MessageQueue(env)
        self.add_state(get_class_dict(self, State))
        self.add_transition(get_class_dict(self, Transition))
    def start(self):
        for state in self._states:
            state.start() if state.initial_state else None
    def stop(self):
        for state in self._states:
            state.stop()
    def add_state(self, state:Union["State", Iterable["State"]]):
        if isinstance(state, State):
            self._states.append(state)
        elif isinstance(state, type):
            initial_state = state.initial_state if hasattr(state, 'initial_state') else False
            self._states.append(state(state.__name__,self,initial_state))
        elif isinstance(state, Iterable):
            for s in state:
                self.add_state(s)
    def add_transition(self, transition:Union["Transition", Iterable["Transition"]]):
        if isinstance(transition, Transition):
            self._transitions.append(transition)
        elif isinstance(transition, Iterable):
            if len(transition) == 0:
                return
            elif isinstance(transition[0], Transition):
                for t in transition:
                    self._transitions.append(t)
            elif isinstance(transition[0], type):
                for t in transition:
                    source, target = self.states[t._sourceStateClass.__name__], self.states[t._targetStateClass.__name__]
                    self._transitions.append(t(self, source, target).__override__())
    def receive(self, message):
        self._messages.receive(message)
        self._on_receive(message)
    def guard_message(self):
        msg = self._messages.get()
        for transition in self._transitions:
            if transition.source in self.current_state and isinstance(transition, MessageTransition) and transition.interpret(msg):
                transition.event.trigger()
    def _on_receive(self, message):
        self.guard_message()
    @property
    def state_list(self):
        return self._states
    @property
    def transitions(self):
        return self._transitions
    @property
    def current_state(self):
        return [state for state in self._states if state.active]
    @property
    def states(self):
        return {state.name: state for state in self._states}
    @property
    def transitionsFrom(self):
        return {name: [transition for transition in self._transitions if transition.source == source] for name, source in self.states.items()}
    @property
    def transitionsTo(self):
        return {name: [transition for transition in self._transitions if transition.target == target] for name, target in self.states.items()}
    def __getattr__(self, name: str) -> Any:
        try:
            return object.__getattribute__(self,name)
        except AttributeError as e1:
            if name == '_agent' or name[:2] == "__":
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from e1
            try:
                return getattr(object.__getattribute__(self,'_agent'),name)
            except AttributeError as e2:
                raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from e2

def get_class_dict(par, sub, txt = "FSM"):
    for cls in par.__class__.__mro__:
        if cls.__name__ == txt:
            break
    cls = [cls for cls in par.__class__.__mro__][0]
    z = {**cls.__dict__, **dict()}
    return [x for x in z.values() if hasattr(x,'__base__') and (x.__base__ is sub or (hasattr(x.__base__,'__base__') and x.__base__.__base__ is sub)) and type(x) is type]
        


from transitions import Transition, MessageTransition
from states import State