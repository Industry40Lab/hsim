import logging
from simpy import Process
from simpy.events import PENDING, Initialize, Interruption
from hsim.core.CHFSM.utilities.trackObj import trackObj
from hsim.core.core import method_lambda


class State(Process):
    def __init__(self):
        self._name = self.__class__.__name__
        self._time = None
        self._entry_callbacks = []
        self._exit_callbacks = []
        self._child_state_machine = None
        self.sm = None
        self._interrupt_callbacks = []
        if not hasattr(self,'_do'):
            self._do = lambda self: None
        if not hasattr(self,'initial_state'):
            self.initial_state = False
        self.callbacks = []
        self._value = None
        self._transitions = list()
    def _do(self):
        pass
    def __getattr__(self,attr):
        try:
            return object.__getattribute__(self,attr)
        except:
            pass
        try:
            return getattr(object.__getattribute__(self,'sm'),attr)
        except:
            raise AttributeError()
    def __repr__(self):
        return '<%s (State) object at 0x%x>' % (self._name, id(self))
    def __call__(self):
        return self.start()
    @property
    def name(self):
        return self._name
    def set_composite_state(self, compositeState):
        compositeState.parent_state = self
        self._child_state_machine = compositeState
    def set_parent_sm(self, parent_sm):
        # if not isinstance(parent_sm, FSM):
        #     raise TypeError("parent_sm must be the type of FSM")
        if self._child_state_machine and self._child_state_machine == parent_sm:
            raise ValueError("child_sm and parent_sm must be different")
        self.sm = parent_sm
    def start(self):
        logging.debug(f"Entering {self._name}")
        # self._last_state_record = [self.sm,self.sm._name,self,self._name,self.env.now,None]
        self._last_state_record = [self.sm,self.sm._name,self,self._name,*trackObj(self.sm),self.env.now,None]
        self.env.state_log.append(self._last_state_record)
        for callback in self._entry_callbacks:
            callback()
        if self._child_state_machine is not None:
            self._child_state_machine.start()
        self._do_start()
    def stop(self):
        logging.debug(f"Exiting {self._name}")
        self._last_state_record[-1] = self.env.now
        for callback in self._exit_callbacks:
            callback()
        if self._child_state_machine is not None:
            self._child_state_machine.stop()
        self._do_stop()
    def _do_start(self):
        self.callbacks = []
        self._value = PENDING
        self._target = Initialize(self.env, self)
    def _do_stop(self):
        self._value = None
    def interrupt(self):
        if self.is_alive:
            Interruption(self, None)
            for callback in self._interrupt_callbacks:
                callback()
            if self._child_state_machine is not None:
                self._child_state_machine.stop()
        else:
            print('Warning - interrupted state was not active')
    def _resume(self, event):
        self.env._active_proc = self
        if isinstance(event,Initialize):
            method_lambda(self,self._do)
            events = list()
            for transition in self._transitions:
                # transition._state = self
                event = transition()
                events.append(event)
        else:
            for transition in self._transitions:
                transition.cancel()
            if event is None:
                event = self
                self._do_start()
                return
            elif isinstance(event,State):
                self.stop()
                event()
            elif isinstance(event,Interruption):
                event = None
                self._ok = True
                self._value = None
                self.callbacks = []
                self.env.schedule(self)
        self._target = event
        self.env._active_proc = None
