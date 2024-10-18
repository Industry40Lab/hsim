from hsim.core.CHFSM.state import State


class Pseudostate(State):
    def __init__(self):
        pass
    def _resume(self,event):
        events = list()
        for transition in self._transitions:
            transition._state = self._state
            event = transition()
            events.append(event)