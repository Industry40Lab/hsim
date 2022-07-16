# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:15:38 2022

@author: Lorenzo
"""

from typing import List, Any, Optional, Callable
import logging 
from simpy import Process, Interrupt
from simpy.events import PENDING, Initialize, Interruption
from core import Environment, dotdict
import types
from stores import Store
from collections import OrderedDict
import warnings
import pandas as pd


def function(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        setattr(instance, '_function', f)
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

def prova(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        setattr(instance, '_generator', f)
        return f
    return decorator

def do(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        if f.__code__.co_argcount < 2:
            raise TypeError('Probably missing trigger event') 
        setattr(instance, '_do', f)
        return f
    return decorator

@staticmethod
def set_state(name,initial_state=False):
    state=State(name)
    setattr(StateMachine,name,state)
    StateMachine.add_state(state,initial_state)
        
class StateMachine(object):
    def __init__(self, env, name=None):
        self.env = env
        self.var = dotdict()
        if name==None:
            name = str('0x%x' %id(self))
        self._name = name
        self._states: List[State] = []
        self._initial_state = None
        self._current_state = None
        self._states = self.build()
        for state in self._states:
            state.set_parent_sm(self)
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
            print('Warning: no initial state set')
    def interrupt(self):
        for state in self._states:
            state.interrupt()
    def stop(self):
        return self.interrupt()
    def build(self):
        return []
    def add_state(self, state, initial_state = False):
        if state in self._states:
            raise ValueError("attempting to add same state twice")
        else:
            self._states.append(state)
            state.set_parent_sm(self)
        if not self._initial_state and initial_state:
            self._initial_state = state
    def copy_states(self):
        for element in dir(self):
            x = getattr(self, element)
            if type(x) == State:
                x.set_parent_sm(self)
                self.add_state(x)
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

class CompositeState(StateMachine):
    def __init__(self, env, name, parent_state):
        self.env = env
        self.parent_state = parent_state
        self._name = name
        self._states: List[State] = []
        self._initial_state = None
        self._current_state = None
    def start(self):
        self.env = self.parent_state.env
        self.copy_states()
        super().start()
    def copy_states(self):
        var = dir(self)
        for element in var:
            x = getattr(self, element)
            if type(x) == State and x is not self.parent_state:
                x.set_parent_sm(self)
                self.add_state(x)


class State(Process):
    def __init__(self, name, initial_state=False):
        self._name = name
        self._time = None
        self._entry_callbacks = []
        self._exit_callbacks = []
        self._child_state_machine = None
        self.sm = None
        self._interrupt_callbacks = []
        self._generator = None
        self._function = None
        self.initial_state = initial_state
        self.callbacks = []
        self._value = None
    def __getattr__(self,attr):
        try:
            sm = self.__getattribute__('sm')
            return sm.__getattribute__(attr)
        except:
            return object.__getattribute__(self,attr)
    def __repr__(self):
        return '<%s (State) object at 0x%x>' % (self._name, id(self))
    def __call__(self):
        return self.start()
    @property
    def name(self):
        return self._name
    def set_composite_state(self, CompositeState):
        sm = CompositeState(self.env, 'Prova', parent_state=self) #was parent_state=True
        self._child_state_machine = sm
    def set_parent_sm(self, parent_sm):
        if not isinstance(parent_sm, StateMachine):
            raise TypeError("parent_sm must be the type of StateMachine")
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
            super().interrupt()
            for callback in self._interrupt_callbacks:
                callback()
            if self._child_state_machine is not None:
                self._child_state_machine.stop()
        else:
            print('Warning - interrupted state was not active')
    def _resume(self, event):
        self.env._active_proc = self
        while True:
            try:
                if isinstance(event,Initialize):
                    event = self._function()
                elif event._ok:
                    try:
                        event = self._do(event)
                    except:
                        warnings.warn('Error in %s (%s)' %(self,self.sm))
                        raise StopIteration
                    if event is None:
                        event = self
                        self._do_start()
                        return
                    else:
                        event()
                        if type(event) is type(self):
                            self.stop()
                        else:
                            raise StopIteration
                elif isinstance(event,Interruption):
                    event = None
                    self._ok = True
                    self._value = None
                    self.callbacks = []
                    self.env.schedule(self)
                    break
                else:
                    event._defused = True
                    exc = type(event._value)(*event._value.args)
                    exc.__cause__ = event._value
                    event = self._generator.throw(exc)
                    warnings.warn('%s' %self)
            except StopIteration as e:
                event = None
                self._ok = True
                self._value = e.args[0] if len(e.args) else None
                self.callbacks = []
                self.env.schedule(self)
                self.stop()
                break
            except BaseException as e:
                event = None
                self._ok = False
                tb = e.__traceback__
                e.__traceback__ = tb.tb_next
                self._value = e
                self.callbacks = []
                self.env.schedule(self)
                break
            try:
                if event.callbacks is not None:
                    event.callbacks.append(self._resume)
                    break
            except AttributeError:
                if not hasattr(event, 'callbacks'):
                    msg = 'Invalid yield value "%s"' % event
                descr = self._generator #_describe_frame(self._generator.gi_frame)
                error = RuntimeError('\n%s%s' % (descr, msg))
                error.__cause__ = None
                raise error
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
        try:
            return self._messages[attr]
        except:
            pass
        raise AttributeError(str('%s has no attribute %s' %(self,attr)))
    def build_c(self):
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
        self.build_c()
        for i in list(self.__dict__.keys()):
            if i not in temp:
                self._messages[i] = getattr(self,i)
                
class Boh(StateMachine):
    def build(self):
        Idle = State('Idle',True)
        @function(Idle)
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
            @function(Sub)
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
        Work = State('Idle',True)
        @function(Work)
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
    

if __name__ == "__main__" and 1:
    env = Environment()
    foo = Boh2(env,1)
    foo.Idle
    env.run(20)
    foo.interrupt()
    # for i in range(10):
    #     env.step()
    env.run(200)
    import dill
    print(dill.pickles(foo))
    

if __name__ == "__main__" and False:
    env = Environment()
    foo = Boh(env,'Foo 1')
    foo2 = Boh(env,'Foo 2')
    env.run(11)
    
    foo.interrupt()
    env.run(30)


    
