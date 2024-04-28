from types import MethodType
from typing import List
from salabim import Component
from .supportFunctions import dotdict, get_class_dict
from .MachineState import MachineState
from .Transition import Transition

def do(instance):
    def decorator(f):
        f = MethodType(f, instance)
        setattr(instance, '_do', f)
        return f
    return decorator

class StateMachine(Component):
    def __init__(self, env, name:str=""):
        super().__init__(name=name)
        self.var = dotdict()
        self._states:List[MachineState] = list()
        self._current_state = None
        self._build_states()
    @property
    def state_types(self):
        return (state_type for state_type in get_class_dict(self.__class__).values() if hasattr(state_type,'__base__') and state_type.__base__ is MachineState and type(state_type) is type)
    @property
    def transitions_types(self):
        return (transition for transition in zip(get_class_dict(self.__class__).values(),get_class_dict(self.__class__).keys()) if type(transition[0]) is Transition)
    def start(self):
        [state.passivate() for state in self._states if state.initial_state == False]
        print('Warning: no initial state set in %s' %self) if not any([state.initial_state for state in self._states]) else None
    def _build_states(self):
        self._states = []
        for State in self.state_types:
            state = State()
            self._states.append(state)
            setattr(self,State.__name__,state)
            for y in State.__dict__.values():
                if hasattr(y,'__base__') and y.__base__.__name__ == 'CompositeState':
                    state._child_state_machine = y(self)    
        for state in self._states:
            state.set_parent_sm(self)
        # for transition in self.transitions_types:
        #     for state in self._states: 
        #         if type(state) is transition[0]._state:
        #             x = transition[0].add(state)
        #             setattr(self,transition[1],None)
        #             for target in self._states: 
        #                 if type(target) is transition[0]._target:
        #                     x._target = target
    def process(self):
        self.start()
    # def __repr__(self):
    #     return '<%s (%s object) at 0x%x>' % (self._name, type(self).__name__, id(self))
    # def name(self)->str:
    #     return self._name
    # @property
    # def current_state(self):
    #     return [state for state in self._states if state.is_alive]
    # @property
    # def is_alive(self):
    #     if self.current_state == []:
    #         return False
    #     else:
    #         return True
    # @classmethod
    # def _states_dict(cls,state):
    #     list_by_name = [s for s in self._states if s.name == state]
    #     if list_by_name is not []:
    #         return list_by_name[0]        
