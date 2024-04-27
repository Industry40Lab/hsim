# -*- coding: utf-8 -*-


from typing import Iterable, List, Any, Optional, Callable
import logging 
# from simpy import Process, Interrupt, Event
# from simpy.events import PENDING, Initialize, Interruption
# from .core import Environment, dotdict, Interruption, method_lambda
from salabim import Environment
import salabim as sim
from .core import dotdict, method_lambda
import types
from .stores import Store, Subscription
from collections import OrderedDict
import warnings
import pandas as pd
import copy
import dill

def do(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        setattr(instance, '_do', f)
        return f
    return decorator

def on_entry(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        instance._entry_callbacks.append(f)
        return f
    return decorator

def on_exit(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        instance._exit_callbacks.append(f)
        return f
    return decorator

def on_interrupt(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        instance._interrupt_callbacks.append(f)
        return f
    return decorator

def trigger(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        instance._trigger = f
        return f
    return decorator

def action(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        instance._action = f
        return f
    return decorator

def get_class_dict(par):
    z=dict()
    for cls in par.__mro__:
        if cls.__name__ == 'CHFSM':
            break
        z = {**cls.__dict__, **z}
    return z

def trackObj(sm):
    entity = None
    items = []
    if hasattr(sm,'var'):
        if hasattr(sm.var,'entity'):
            entity = sm.var.entity
    if hasattr(sm,'Store'):
        pass
    elif hasattr(sm,'Store'):
        pass
    return entity, items

class Timeout(sim.Component):
    def __init__(self, name="", timeout=0):
        self.timeout = timeout
        self.value = sim.State()
        super().__init__()
        self.process()
    def process(self):
        self.hold(self.timeout)
        self.value.trigger(True)
    
class StateMachine(sim.Component):
    def __init__(self, env, name=None):
        self.env = env
        self.var = dotdict()
        if name==None:
            self._name = str('0x%x' %id(self))
        else:
            self._name = name
        self._current_state = None
        self._build_states()
        self.activate()
        # self.env.add_object(self)
    def _get_transitions(self):
        return (transition for transition in zip(get_class_dict(self.__class__).values(),get_class_dict(self.__class__).keys()) if type(transition[0]) is Transition)
    def _get_state_types(self):
        return (state_type for state_type in get_class_dict(self.__class__).values() if hasattr(state_type,'__base__') and state_type.__base__ is State and type(state_type) is type)
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
        super().interrupt()
    def stop(self):
        return self.interrupt()
    def _build_states(self):
        self._states = []
        for State in self._get_state_types():
            state = State()
            self._states.append(state)
            setattr(self,State.__name__,state)
            for y in State.__dict__.values():
                if hasattr(y,'__base__') and y.__base__.__name__ == 'CompositeState':
                    state._child_state_machine = y(self)    
        for state in self._states:
            state.set_parent_sm(self)
        for transition in self._get_transitions():
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
    def _states_dict(cls,state):
        list_by_name = [s for s in self._states if s.name == state]
        if list_by_name is not []:
            return list_by_name[0]        
    
class CompositeState(StateMachine):
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

class State(sim.Component):
    def __init__(self):
        self._name = self.__class__.__name__
        self._time = None
        self._entry_callbacks = []
        self._exit_callbacks = []
        self._child_state_machine = None
        self._interrupt_callbacks = []
        self.sm = None
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
        if self._child_state_machine and self._child_state_machine == parent_sm:
            raise ValueError("child_sm and parent_sm must be different")
        self.sm = parent_sm
    def _on_entry(self):
        for callback in self._entry_callbacks:
            callback()
    def _on_exit(self):
        for callback in self._exit_callbacks:
            callback()
    def _on_interrupt(self):
        for callback in self._interrupt_callbacks:
            callback()
    def interrupt(self):
        super().interrupt()
        raise InterruptedError
    def process(self):
        self._on_entry()
        self._do()
        triggers = [transition._trigger() for transition in self._transitions]
        try:
            self.wait(triggers)
            # action transition
            # trigger transitions
            self._on_exit()
        except InterruptedError:
            self._on_interrupt()

class CHFSM(StateMachine):
    def __init__(self,env,name=None):
        super().__init__(env,name)
        self._list_messages()
        self.connections = dict()
    def build(self):
        pass
    def _associate(self):
        for state in self._states:
            state.connections = self.connections
            state.var = self.var
            for message in self._messages:
                setattr(state,message,self._messages[message])
    def _list_messages(self):
        self._messages = OrderedDict()
        temp=list(self.__dict__.keys())
        self.build()
        for i in list(self.__dict__.keys()):
            if i not in temp:
                self._messages[i] = getattr(self,i)

class Transition(sim.State):
    @classmethod
    def copy(cls, state, target=None, trigger=None, condition=None, action=None):
        class Transition(cls):
            _state = state
            _target = target
            if trigger is not None:
                _trigger = trigger
            if action is not None:
                _action = action
            _condition_eval = condition
        return Transition
    def add(self,state):
        new = copy.deepcopy(self)
        state._transitions.append(new)
        new._state = state
        return new
    def __init__(self, state, target=None, trigger=None, condition=None, action=None):
        self._state = state
        self._target = target
        self._trigger = trigger if trigger in [sim.State,Iterable[sim.State]] else sim.State(value=True)
        self._action = action if callable(action) else lambda self: None
        self._condition = condition if type(condition) is sim.State else sim.State(value=True)
    def __getattr__(self, attr):
        try:
            return object.__getattribute__(self,attr)
        except:
            try:
                return getattr(object.__getattribute__(self,'_state'),attr)
            except:
                raise AttributeError()
    def _trigger(self):
        pass
    def _action(self):
        return None
    def _otherwise(self):
        return self()
 
class Pseudostate(State):
    def __init__(self):
        pass
    def _resume(self,event):
        events = list()
        for transition in self._transitions:
            transition._state = self._state
            event = transition()
            events.append(event)



    
