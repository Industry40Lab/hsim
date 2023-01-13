# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:15:38 2022

@author: Lorenzo
"""

from typing import List, Any, Optional, Callable
import logging 
from simpy import Process, Interrupt, Event
from simpy.events import PENDING, Initialize, Interruption
from core import Environment, dotdict, Interruption, method_lambda
import types
from stores import Store
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

@staticmethod
def set_state(name,initial_state=False):
    state=State(name)
    setattr(StateMachine,name,state)
    StateMachine.add_state(state,initial_state)

def add_states(sm,states):
    sm._states = states # [copy.deepcopy(state) for state in states] 
    
def get_class_dict(par):
    z=dict()
    for cls in par.__mro__:
        if cls.__name__ == 'CHFSM':
            break
        z = {**cls.__dict__, **z}
    return z
    
class StateMachine():
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
    def __getattr__(self,attr):
        for state in object.__getattribute__(self,'_states'):
            if state._name == attr:
                return state
        raise AttributeError()
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
        for x in get_class_dict(self.__class__).values():
            if hasattr(x,'__base__') and x.__base__ is State:
                state = x()
                self._states.append(state)
                setattr(self,x.__name__,state)
                for y in x.__dict__.values():
                    if hasattr(y,'__base__') and y.__base__.__name__ == 'CompositeState':
                        state._child_state_machine = y(self)    
        for state in self._states:
            state.set_parent_sm(self)
        for transition in zip(get_class_dict(self.__class__).values(),get_class_dict(self.__class__).keys()):
            if hasattr(transition[0],'__base__') and transition[0].__base__ is Transition:
                # x è Transition
                for state in self._states: 
                    if type(state) is transition[0]._state:
                        x = transition[0](state)
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
    def __getattr__(self,attr):
        try:
            sm = self.__getattribute__('sm')
            return getattr(sm,attr)
        except:
            return object.__getattribute__(self,attr)
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
        # if not isinstance(parent_sm, StateMachine):
        #     raise TypeError("parent_sm must be the type of StateMachine")
        if self._child_state_machine and self._child_state_machine == parent_sm:
            raise ValueError("child_sm and parent_sm must be different")
        self.sm = parent_sm
    def start(self):
        logging.debug(f"Entering {self._name}")
        self._last_state_record = [self.sm,self.sm._name,self,self._name,self.env.now,None]
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


class CHFSM(StateMachine):
    def __init__(self,env,name=None):
        super().__init__(env,name)
        self._list_messages()
        self.connections = dict()
    def __getattr__(self,attr):
        for state in object.__getattribute__(self,'_states'):
            if state._name == attr:
                return state
        if object.__getattribute__(self,'_messages').__contains__(attr):
            return object.__getattribute__(self,'_messages')[attr]
        raise AttributeError()
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

class Transition():
    @classmethod
    def copy(cls, state, target=None, trigger=None, condition=None, action=None):
        class Transition(cls):
            _state = state
            _target = target
            if trigger is not None:
                _trigger = trigger
            if action is not None:
                _action = action
        return Transition
    def __init__(self, state, target=None, trigger=None, condition=None, action=None):
        self._state = state
        # self._target = target
        # if trigger is not None:
        #     self._trigger = trigger
        # if action is not None:
        #     self._action = action
        state._transitions.append(self)
    def __getattr__(self,attr):
        try:
            state = self.__getattribute__('_state')
            try:
                return getattr(state,attr)
            except:
                sm = state.__getattribute__('sm')
                return getattr(sm,attr)
        except:
            return object.__getattribute__(self,attr)
    def _trigger(self):
        pass
    def _condition(self):
        return True
    def _action(self):
        return None
    def _otherwise(self):
        return self()
    def cancel(self):
        self._event._value = False
    def _evaluate(self,event):
        if self._event._value == False:
            return
        if method_lambda(self,self._condition):
            method_lambda(self,self._action)
            self._state._resume(self._target)
        else:
            self._otherwise()
    def __call__(self):
        if self._trigger is None:
            return self._evaluate(None)
            self._target._state = self._state
        self._event = method_lambda(self,self._trigger)
        if self._event == None:
            self._event = self.env.event()
            self._event.succeed()
            print('Missing trigger')
        try:
            self._event.callbacks.append(self._evaluate)
        except:
            self._event.callbacks = [self._evaluate]
        return self._event
 
class Pseudostate(State):
    def __init__(self):
        pass
    def _resume(self,event):
        events = list()
        for transition in self._transitions:
            transition._state = self._state
            event = transition()
            events.append(event)

# %% TESTS 

if __name__ == "__main__" and 1:
    '''
    class Boh(StateMachine):
        def build(self):
            Idle = State('Idle',True)
            @do(Idle)
            def printt(self):
                print('%s is Idle' %self.sm._name)
                return self.env.timeout(10)
            @do(Idle)
            def todo(self,Event):
                print('%s waited 10s' %self.sm._name)
            @on_exit(Idle)
            def print_ciao(self):
                print('Idle state exit')
            @on_interrupt(Idle)
            def interrupted_ok(self):
                print('%s idle state interrupted ok'  %self.sm._name)
            class Idle_SM(CompositeState):
                Sub = State('Sub',True)
                @do(Sub)
                def printt(self):
                    print('%s will print this something in 20 s'  %self.sm._name)
                    return self.env.timeout(20)
                @do(Sub)
                def todo(self,Event):
                    print('Printing this only once')
                    raise
                @on_exit(Sub)
                def print_ciao(self):
                    print('Substate exit')
            Idle.set_composite_state(Idle_SM)
            return [Idle]
    
    class Boh2(CHFSM):
        def build(self):
            Work = State('Work',True)
            @do(Work)
            def printt(self):
                print('Start working. Will finish in 10s')
                return self.env.timeout(10)
            @do(Work)
            def d(self,Event):
                print("Finished!")
                return Work
            @on_exit(Work)
            def exiting(self):
                print('Leaving working state')
            @on_entry(Work)
            def entering(self):
                print('Entering working state')
            return [Work]
        
    class Boh3(CHFSM):
        pass
    Work = State('Work',True)
    @do(Work)
    def printt(self):
        print('Start working. Will finish in 10s')
        return self.env.timeout(10)
    @do(Work)
    def d(self,Event):
        print("Finished!")
        return self.Work
    add_states(Boh3,[Work])
    
    class Boh4(CHFSM):
        pass
    Work = State('Work',True)
    Work._do = lambda self:print('Start working. Will finish in 10s')
    t = Transition(Work, None, lambda self: self.env.timeout(10))
    Work._transitions = [t]
    add_states(Boh4,[Work])
    
    '''
    class Boh5(CHFSM):
        class Work(State):
            initial_state=True
            _do = lambda self: print('Start working at %d. Will finish in 10s' %env.now)
            class WorkSM(CompositeState):
                class Work0(State):
                    initial_state=True
                    _do = lambda self:print('Inner SM start working at %d. Will finish in 5s' %env.now)
                T1=Transition.copy(Work0, None, lambda self: self.env.timeout(5))
        T1=Transition.copy(Work, None, lambda self: self.env.timeout(10))
    
    class Boh6(CHFSM):
        class Work(State):
            initial_state=True
            _do = lambda self: print('Start working at %d. Will finish in 10s' %self.env.now)
        class Rest(State):
            _do = lambda self: print('Start resting at %d. Will finish in 10s' %self.env.now)
        T1=Transition.copy(Work, Rest, lambda self: self.env.timeout(10))
        T2=Transition.copy(Rest, Work, lambda self: self.env.timeout(10))
    
    class Boh7(CHFSM):
        class Work(State):
            initial_state=True
            _do = lambda self: print('Start working at %d. Will finish in 10s' %self.env.now)
        class Rest(State):
            _do = lambda self: print('Start resting at %d. Will finish in 10s' %self.env.now)
        T1=Transition.copy(Work, Rest, lambda self: self.E,action=print(100))
        T1a=Transition.copy(Work, Rest, lambda self: self.E,action=print(100))
        T2=Transition.copy(Rest, Work, lambda self: self.env.timeout(10))
    
    
    
    # env = Environment()
    # foo = Boh6(env,1)
    # env.run(50)
    # foo.interrupt()
    # env.run(200)

    env = Environment()
    foo2 = Boh7(env,1)
    foo2.E = env.event()
    env.run(50)
    print('go')
    foo2.E.succeed()
    env.run(10)
    




    
