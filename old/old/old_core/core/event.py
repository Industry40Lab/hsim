from simpy import Event
from simpy.events import PENDING

class Event(Event):
    def restart(self):
        self._value = PENDING
        self.callbacks = []