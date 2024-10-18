from hsim.core.CHFSM.state import State
from hsim.core.CHFSM.transition import Transition
from hsim.core.CHFSM.utilities.getClassDict import getClassDict
from hsim.core.core import dotdict


class FSM():
    def __init__(self, env, name=None):
        self.env = env
        self.var = dotdict()
        if name==None:
            self._name = str('0x%x' %id(self))
        else:
            self._name = name
        self._current_state = None
        self._build_states()
        self.start()
        self.env.add_object(self)


    # def __getattr__(self,attr):
    #     for state in object.__getattribute__(self,'_states'):
    #         if state._name == attr:
    #             return state
    #     raise AttributeError()
    def __repr__(self):
        return '<%s (%s object) at 0x%x>' % (self._name, type(self).__name__, id(self))
    def start(self):
        for state in self._states:
            if state.initial_state == True:
                state.start()
        if not any([state.initial_state for state in self._states]):
            print('Warning: no initial state set in %s' %self)
    def interrupt(self):
        for state in self._states:
            state.interrupt()
    def stop(self):
        return self.interrupt()
    def _build_states(self):
        self._states = []
        for x in getClassDict(self.__class__).values():
            if hasattr(x,'__base__') and x.__base__ is State and type(x) is type:
                state = x()
                self._states.append(state)
                setattr(self,x.__name__,state)
                for y in x.__dict__.values():
                    if hasattr(y,'__base__') and y.__base__.__name__ == 'CompositeState':
                        state._child_state_machine = y(self)    
        for state in self._states:
            state.set_parent_sm(self)
        for transition in zip(getClassDict(self.__class__).values(),getClassDict(self.__class__).keys()):
            if type(transition[0]) is Transition:
            # if hasattr(transition[0],'__base__') and transition[0].__base__ is Transition:
                # x è Transition
                for state in self._states: 
                    if type(state) is transition[0]._state:
                        x = transition[0].add(state)
                        setattr(self,transition[1],None)
                        for target in self._states: 
                            if type(target) is transition[0]._target:
                                x._target = target

    @property
    def name(self):
        return self._name
    @property
    def current_state(self):
        return [state for state in self._states if state.is_alive]
    @property
    def is_alive(self):
        if self.current_state == []:
            return False
        else:
            return True
    @classmethod
    def _states_dict(self,state):
        list_by_name = [s for s in self._states if s.name == state]
        if list_by_name is not []:
            return list_by_name[0]