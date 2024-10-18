from hsim.core.CHFSM.FSM import FSM


class CompositeState(FSM):
    def __init__(self, parent_state, name=None):
        if name==None:
            self._name = str('0x%x' %id(self))
        else:
            self._name = name
        self._current_state = None
        self.parent_state = parent_state
        self.env = self.parent_state.env 
    def start(self):
        self._build_states()
        super().start()
