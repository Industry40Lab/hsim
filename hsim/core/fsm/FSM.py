if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))


from collections import OrderedDict
from typing import Any, Callable, Iterable, List, Type, Union
import numpy as np
import logging

from hsim.core.core.event import ConditionEvent, BaseEvent, TimedEvent
from hsim.core.core.env import Environment
from hsim.core.core.msg import Message, MessageQueue

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
        self._pseudostates:List['Pseudostate'] = []
        self.add_element(get_class_dict(self, State))
        self.add_element(get_class_dict(self, Pseudostate))
        self.add_element(get_class_dict(self, Transition))
        self.active, self.startable, self.stoppable = False, True, True
    def start(self):
        for state in self._states:
            state.start() if state.initial_state else None
        self.active = True
    def stop(self):
        for state in self._states:
            state.stop()
        self.active = False
    def add_element(self, element: Union["State", "Transition", "Pseudostate", Type, Iterable]):
        if isinstance(element, Iterable):
            for e in element:
                self.add_element(e)
        elif not isinstance(element, type):
            if isinstance(element, State):
                self._states.append(element)
            elif isinstance(element, Transition):
                self._transitions.append(element)
            elif isinstance(element, Pseudostate):
                self._pseudostates.append(element)
        elif isinstance(element, type):
            if issubclass(element, State):
                initial_state = getattr(element, 'initial_state', False)
                self.add_element(element(element.__name__, self, initial_state))
            elif issubclass(element, Transition):
                source, target = self.statesps[element._sourceStateClass.__name__], self.statesps[element._targetStateClass.__name__]
                self.add_element(element(self, source, target).__override__())
            elif issubclass(element, Pseudostate):
                self.add_element(element(element.__name__, self))
                
    def receive(self, message):
        self._messages.receive(message)
        self._on_receive(message)
    def receiveContent(self, content, sender=None) -> Message:
        msg:Message = Message(self._env, content, sender=sender, receiver=self, wait=True)
        self.receive(msg)
        return msg
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
    @property
    def transitionsFromTo(self):
        return {(source, target): [transition for transition in self._transitions if transition.source == source and transition.target == target] for source in self.states for target in self.states}
    @property
    def pseudostates(self):
        return {state.name: state for state in self._pseudostates}
    @property
    def statesps(self):
        d = {state.name: state for state in self._states}
        d.update({state.name: state for state in self._pseudostates})
        return d
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

def get_class_dict(par, sub):
    cls = [cls for cls in par.__class__.__mro__][0]
    z = {**cls.__dict__, **dict()}
    return [x for x in z.values() if hasattr(x,'__base__') and (x.__base__ is sub or (hasattr(x.__base__,'__base__') and x.__base__.__base__ is sub)) and type(x) is type]
        


from .transitions import Transition, MessageTransition
from .states import State, Pseudostate