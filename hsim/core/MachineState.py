from __future__ import annotations
from salabim import State, Component

class MachineState(Component,State):
    initial_state = False
    def __init__(self, name: str = "", trigger: bool = False, **kwargs):
        State.__init__(self, name, trigger, **kwargs)
        Component.__init__(self, name)
    def _do(self):
        pass
    def process(self):
        return self._do()
    def set_parent_sm(self, sm:"StateMachine") -> None: # type: ignore
        self.sm = sm
    def __call__(self) -> None:
        self.activate()