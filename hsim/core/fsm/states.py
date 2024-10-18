if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

    
from abc import abstractmethod
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

class State:
    def __init__(self, name:str, fsm:'FSM', initial_state:bool=False):
        self.name = name
        self._fsm = fsm
        self._env = fsm._env
        self.initial_state = initial_state
        self._active = False
    def _on_enter(self):
        print(f"Entering {self.name} state")
        self.on_enter()
    def on_enter(self):
        pass
    def _on_exit(self):
        self.on_exit()
    def on_exit(self):
        pass
    def start(self):
        self._active = True
        self._on_enter()
        for transition in self.transitions:
            transition.start()
    def stop(self):
        self._active = False
        self._on_exit()
        for transition in self.transitions:
            transition.stop()
    def interrupt(self):
        pass
    async def __call__(self):
        self.start()
    @property
    def fsm(self):
        return self._fsm
    @property
    def transitions(self):
        return [t for t in self.fsm.transitions if t.source == self]
    @property
    def active(self):
        return self._active
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
    @property
    def transition(self, name:str):
        return {name:[transition for transition in self.transitions if transition.name == name]}
        

# needing pseudostate or multiple transitions=??
class Pseudostate:
    initial_state = False
    _active = False
    def __init__(self, name:str, fsm:'FSM'):
        self.name = name
        self._fsm = fsm
        self._env = fsm._env
    def start(self) -> None:
        targets:Iterable[Type] = [*self.control()]
        for target in targets:
            self.states[target.__name__].start()
    @abstractmethod    
    def control(self) -> Iterable[State]:
        if True:
            return self.fsm.Empty,
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



from hsim.core.fsm.transitions import Transition, MessageTransition
from hsim.core.fsm.FSM import FSM