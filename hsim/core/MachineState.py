from __future__ import annotations
from typing import Iterable
from salabim import State, Component

class MachineState(Component,State):
    initial_state = False
    def __init__(self, name: str = "", trigger: bool = False, **kwargs):
        State.__init__(self, name, trigger, **kwargs)
        Component.__init__(self, name)
        self._transitions:Iterable["Transitions"] = list() # type: ignore
    def _do(self)->None:
        pass
    def process(self):
        self._do()
        return
        triggers = [t._trigger for t in self._transitions]
        self.wait(triggers)
        # get trigger triggered, in order
        # evaluate condition
        # perform action
        # return new_state
    def set_parent_sm(self, sm:"StateMachine") -> None: # type: ignore
        self.sm = sm
    def __call__(self) -> None:
        self.activate()