# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:15:38 2022

@author: Lorenzo
"""

from typing import List, Any, Optional, Callable
import logging 
from simpy import Process, Interrupt
from simpy.events import PENDING, Initialize, Interruption
from core import Environment
import types
from stores import Store
from collections import OrderedDict


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
        setattr(instance, '_do', f)
        return f
    return decorator


# class StateMachine(StateMachine):
@staticmethod
def set_state(name,initial_state=False):
    state=State(name)
    setattr(StateMachine,name,state)
    StateMachine.add_state(state,initial_state)
        # return State
        
class StateMachine(object):
    def __init__(self, env, name):
        self.env = env
        self._name = name
        self._states: List[State] = []
        self._initial_state = None
        self._current_state = None
        states = self.build()
        for state in states:
            setattr(self, state._name, state)
        self.copy_states()
        self.start()
        self.env.add_object(self)
    def start(self):
        for state in self._states:
            if state.initial_state == True:
                state.start()
    def interrupt(self):
        for state in self._states:
            if state.is_alive:
                state.interrupt()
    def stop(self):
        return self.interrupt()
    def build(self):
        return []
    def add_state(self, state, initial_state = False):
        if state in self._states:
            print(1)
            # raise ValueError("attempting to add same state twice")
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
        self._parent_state_machine = None
        self._interrupt_callbacks = []
        self.env = None
        self._generator = None
        self._function = None
        self.initial_state = initial_state
        self.callbacks = []
    def __repr__(self):
        return '<%s (State) object at 0x%x>' % (self._name, id(self))
    def __call__(self):
        return self.start()
    @property
    def name(self):
        return self.name()
    def set_composite_state(self, CompositeState):
        sm = CompositeState(self.env, 'Prova', parent_state=self) #was parent_state=True
        # sm.parent_state = self
        self._child_state_machine = sm
    def set_parent_sm(self, parent_sm):
        if not isinstance(parent_sm, StateMachine):
            raise TypeError("parent_sm must be the type of StateMachine")
        if self._child_state_machine and self._child_state_machine == parent_sm:
            raise ValueError("child_sm and parent_sm must be different")
        self._parent_state_machine = parent_sm
        self.env = parent_sm.env
    def start(self):
        logging.debug(f"Entering {self._name}")
        for callback in self._entry_callbacks:
            callback()
        if self._child_state_machine is not None:
            self._child_state_machine.start()
        self._do_start()
    def stop(self):
        logging.debug(f"Exiting {self._name}")
        for callback in self._exit_callbacks:
            callback()
        if self._child_state_machine is not None:
            self._child_state_machine.stop()
    def _do_start(self):
        self.callbacks = []
        self._value = PENDING
        self._generator = self._function
        self._target = Initialize(self.env, self)
    def interrupt(self):
        if self.is_alive:
            super().interrupt()
            # for event in self.env._queue:
            #     for callback in event[-1].callbacks:
            #         if callback == self._resume:
            #             event[-1].callbacks.remove(callback)
            for callback in self._interrupt_callbacks:
                callback()
            if self._child_state_machine is not None:
                self._child_state_machine.stop()
        else:
            print('Warning - interrupted state was not active')
    # def safe_generator(self,generator):
    #     try:
    #         yield from generator
    #     except Interrupt:
    #         for event in self.env._queue: 
    #             if event[-1] == self._target:
    #                 self.env._queue.remove(event)
    #         for callback in self._interrupt_callback:
    #             callback()
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
                        raise StopIteration
                    if event is None:
                        event = Initialize(self.env,self)
                        break
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
    def __init__(self,env,name):
        super().__init__(env,name)
        # self.message_ports = self.create_ports()
        # for port in self.message_ports:
        #     setattr(self, port._name, port)
        temp=list(self.__dict__.keys())
        self.message_ports()
        self.messages = OrderedDict()
        for i in list(self.__dict__.keys()):
            if i not in temp:
                self.messages[i] = getattr(self,i)
    def message_ports(self):
        pass
        
                
class Boh(StateMachine):
    def build(self):
        Idle = State('Idle',True)
        @function(Idle)
        def printt(self):
            print('%s is Idle' %self._parent_state_machine._name)
            return self.env.timeout(10)
        @do(Idle)
        def todo(self,Event):
            print('%s waited 10s' %self._parent_state_machine._name)
        @on_exit(Idle)
        def print_ciao(self):
            print('Idle state exit')
        @on_interrupt(Idle)
        def interrupted_ok(self):
            print('%s idle state interrupted ok'  %self._parent_state_machine._name)
        class Idle_SM(CompositeState):
            Sub = State('Sub',True)
            @function(Sub)
            def printt(self):
                print('%s will print this something in 20 s'  %self._parent_state_machine._name)
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

class Boh2(StateMachine):
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
# Idle = State('Idle')
# @function(Idle)
# def test(self):
#     print('Test working')
#     yield self.env.timeout(1)
#     print('FAIL')    
# @on_exit(Idle)
# def print_ciao(self):
#     print('ciao')

     
# class Environment(Environment):
#     state = BoundClass(State)


# env = Environment()
# Idle.env = env
# Idle.start()
# env.run(0.5)
# Idle.interrupt()
# env.run(0.6)

# env.run(50)

if 1:
    env = Environment()
    foo = Boh2(env,1)
    env.run(20)
    foo.interrupt()
    # for i in range(10):
    #     env.step()
    env.run(200)
    
if 1:
    env = Environment()
    foo = Boh(env,'Foo 1')
    foo2 = Boh(env,'Foo 2')

    env.run(11)
    
    foo.interrupt()
    env.run(30)

    
# def Composite(instance):
#     def decorator(f):
#         setattr(instance, '_child_state_machine', f)
#         return f
#     return decorator
    
