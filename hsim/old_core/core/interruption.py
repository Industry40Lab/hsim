from simpy.events import PENDING, Interruption
from hsim.core.core.event import Event

class Interruption(Interruption):
    def _interrupt(self, event: Event) -> None:
        if self.process._value is not PENDING:
            return
        # self.process._target.callbacks.remove(self.process._resume)
        self.process._resume(self)
