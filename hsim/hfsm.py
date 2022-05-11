# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 16:15:38 2022

@author: Lorenzo
"""

from typing import List, Any, Optional, Callable
import logging 

'''
class State(object):

    def __init__(self, name, child_sm=None):
        self._name = name
        self._entry_callbacks: List[Callable[[Any], None]] = []
        self._exit_callbacks: List[Callable[[Any], None]] = []
        self._child_state_machine: Optional[StateMachine] = child_sm
        self._parent_state_machine: Optional[StateMachine] = None

    def __repr__(self):
        return f"State({self.name})"

    # def __eq__(self, other):
    #     if other.name == self._name:
    #         return True
    #     else:
    #         return False

    # def __ne__(self, other):
    #     return not self.__eq__(other)

    def __call__(self, data: Any):
        pass

    def on_entry(self, callback: Callable[[Any], None]):
        self._entry_callbacks.append(callback)

    def on_exit(self, callback: Callable[[], None]):
        self._exit_callbacks.append(callback)

    def set_child_sm(self, child_sm):
        if not isinstance(child_sm, StateMachine):
            raise TypeError("child_sm must be the type of StateMachine")
        if self._parent_state_machine and self._parent_state_machine == child_sm:
            raise ValueError("child_sm and parent_sm must be different")
        self._child_state_machine = child_sm

    def set_parent_sm(self, parent_sm):
        if not isinstance(parent_sm, StateMachine):
            raise TypeError("parent_sm must be the type of StateMachine")
        if self._child_state_machine and self._child_state_machine == parent_sm:
            raise ValueError("child_sm and parent_sm must be different")
        self._parent_state_machine = parent_sm
        self.env = parent_sm.env

    def start(self, data: Any):
        logging.debug(f"Entering {self._name}")
        for callback in self._entry_callbacks:
            callback(data)
        if self._child_state_machine is not None:
            self._child_state_machine.start(data)

    def stop(self, data: Any):
        logging.debug(f"Exiting {self._name}")
        for callback in self._exit_callbacks:
            callback(data)
        if self._child_state_machine is not None:
            self._child_state_machine.stop(data)

    def has_child_sm(self) -> bool:
        return True if self._child_state_machine else False

    @property
    def name(self):
        return self._name

    @property
    def child_sm(self):
        return self._child_state_machine

    @property
    def parent_sm(self):
        return self._parent_state_machine


class ExitState(State):

    def __init__(self, status="Normal"):
        self._name = "ExitState"
        self._status = status
        super().__init__(self._status + self._name)

    @property
    def status(self):
        return self._status


class Event(object):

    def __init__(self, name):
        self._name = name

    def __repr__(self):
        return f"Event={self._name}"

    def __eq__(self, other):
        if other.name == self._name:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def name(self):
        return self._name


class Transition(object):

    def __init__(self, event: Event, src: State, dst: State):
        self._event = event
        self._source_state = src
        self._destination_state = dst
        self._condition: Optional[Callable[[Any], bool]] = None
        self._action: Optional[Callable[[Any], None]] = None

    def __call__(self, data: Any):
        raise NotImplementedError

    def add_condition(self, callback: Callable[[Any], bool]):
        self._condition = callback

    def add_action(self, callback: Callable[[Any], Any]):
        self._action = callback

    @property
    def event(self):
        return self._event

    @property
    def source_state(self):
        return self._source_state

    @property
    def destination_state(self):
        return self._destination_state


class NormalTransition(Transition):

    def __init__(self, source_state: State, destination_state: State,
                 event: Event):
        super().__init__(event, source_state, destination_state)
        self._from = source_state
        self._to = destination_state

    def __call__(self, data: Any):
        if not self._condition or self._condition(data):
            logging.info(f"NormalTransition from {self._from} to {self._to} "
                         f"caused by {self._event}")
            if self._action:
                self._action(data)
            self._from.stop(data)
            self._to.start(data)

    def __repr__(self):
        return f"Transition {self._from} to {self._to} by {self._event}"


class SelfTransition(Transition):

    def __init__(self, source_state: State, event: Event):
        super().__init__(event, source_state, source_state)
        self._state = source_state

    def __call__(self, data: Any):
        if not self._condition or self._condition(data):
            logging.info(f"SelfTransition {self._state}")
            if self._action:
                self._action(data)
            self._state.stop(data)
            self._state.start(data)

    def __repr__(self):
        return f"SelfTransition on {self._state}"


class NullTransition(Transition):

    def __init__(self, source_state: State, event: Event):
        super().__init__(event, source_state, source_state)
        self._state = source_state

    def __call__(self, data: Any):
        if not self._condition or self._condition(data):
            logging.info(f"NullTransition {self._state}")
            if self._action:
                self._action(data)

    def __repr__(self):
        return f"NullTransition on {self._state}"


class StateMachine(object):

    def __init__(self, name):
        self._name = name
        self._states: List[State] = []
        self._transitions: List[Transition] = []
        self._initial_state: Optional[List[State]] = None
        self._current_state: Optional[List[State]] = None
        # self._exit_callback: Optional[Callable[[ExitState, Any], None]] = None
        # self._exit_state = ExitState()
        # self.add_state(self._exit_state)
        # self._exited = True
        
    def __eq__(self, other):
        if other.name == self._name:
            return True
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self._name



    def on_exit(self, callback):
        self._exit_callback = callback



    def add_state(self, state: State, initial_state: bool = False):
        if state in self._states:
            raise ValueError("attempting to add same state twice")
        self._states.append(state)
        state.set_parent_sm(self)
        if not self._initial_state and initial_state:
            self._initial_state = state

    def add_event(self, event: Event):
        self._events.append(event)

    def add_transition(self, src: State, dst: State, evt: Event) -> \
            Optional[Transition]:
        transition = None
        if src in self._states and dst in self._states and evt in self._events:
            transition = NormalTransition(src, dst, evt)
            self._transitions.append(transition)
        return transition

    def add_self_transition(self, state: State, evt: Event) -> \
            Optional[Transition]:
        transition = None
        if state in self._states and evt in self._events:
            transition = SelfTransition(state, evt)
            self._transitions.append(transition)
        return transition

    def add_null_transition(self, state: State, evt: Event) -> \
            Optional[Transition]:
        transition = None
        if state in self._states and evt in self._events:
            transition = NullTransition(state, evt)
            self._transitions.append(transition)
        return transition

    def trigger_event(self, evt: Event, data: Any = None,
                      propagate: bool = False):
        transition_valid = False
        if not self._initial_state:
            raise ValueError("initial state is not set")

        if self._current_state is None:
            raise ValueError("state machine has not been started")

        if propagate and self._current_state.has_child_sm():
            logging.debug(f"Propagating evt {evt} from {self} to "
                          f"{self._current_state.child_sm}")
            self._current_state.child_sm.trigger_event(evt, data, propagate)
        else:
            for transition in self._transitions:
                if transition.source_state == self._current_state and \
                        transition.event == evt:
                    self._current_state = transition.destination_state
                    transition(data)
                    if isinstance(self._current_state, ExitState) and \
                            self._exit_callback and not self._exited:
                        self._exited = True
                        self._exit_callback(self._current_state, data)
                    transition_valid = True
                    break
            if not transition_valid:
                logging.warning(f"Event {evt} is not valid in state "
                                f"{self._current_state}")

    # @property
    # def exit_state(self):
    #     return self._exit_state


'''



from simpy import Process, Interrupt
from simpy.core import BoundClass
from simpy.events import PENDING, Initialize, Interruption
from core import Environment
import sys

def addto(instance):
    def decorator(f):
        import types
        f = types.MethodType(f, instance)
        setattr(instance, f.__name__, f)
        return f
    return decorator

def Generator(instance):
    def decorator(f):
        import types
        f = types.MethodType(f, instance)
        setattr(instance, '_generator_function', f)
        return f
    return decorator

def on_entry(instance):
    def decorator(f):
        import types
        f = types.MethodType(f, instance)
        instance._entry_callbacks.append(f)
        return f
    return decorator

def on_exit(instance):
    def decorator(f):
        import types
        f = types.MethodType(f, instance)
        instance._exit_callbacks.append(f)
        return f
    return decorator

def on_interrupt(instance):
    def decorator(f):
        import types
        f = types.MethodType(f, instance)
        instance._interrupt_callbacks.append(f)
        return f
    return decorator

def prova(instance):
    def decorator(f):
        import types
        f = types.MethodType(f, instance)
        setattr(instance, '_generator', f)
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
        self._initial_state: Optional[List[State]] = None
        self._current_state: Optional[List[State]] = None
        self.copy_states()
        self.start()
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
    def add_state(self, state, initial_state: bool = False):
        if state in self._states:
            raise ValueError("attempting to add same state twice")
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
        self._initial_state: Optional[List[State]] = None
        self._current_state: Optional[List[State]] = None
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
        self._entry_callbacks: List[Callable[[Any], None]] = []
        self._exit_callbacks: List[Callable[[Any], None]] = []
        self._child_state_machine: Optional[StateMachine] = None
        self._parent_state_machine: Optional[StateMachine] = None
        self._interrupt_callbacks: List[Callable[[Any], None]] = []
        self.env = None
        self._generator = None
        self._generator_function = None
        self.initial_state = initial_state
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
        self._generator = self.safe_generator(self._generator_function())
        self._target = Initialize(self.env, self)
    def interrupt(self):
        super().interrupt()
        for callback in self._interrupt_callbacks:
            callback()
        if self._child_state_machine is not None:
            self._child_state_machine.stop()
    def safe_generator(self,generator):
        try:
            yield from generator
        except Interrupt:
            for event in self.env._queue: 
                if event[-1] == self._target:
                    self.env._queue.remove(event)
            for callback in self._interrupt_callback:
                callback()
    def _resume(self, event):
        self.env._active_proc = self
        while True:
            try:
                if event._ok:
                    event = self._generator.send(event._value)
                elif isinstance(event,Interruption):
                    event = None
                    self._ok = True
                    self._value = None
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
                self.env.schedule(self)
                self.stop()
                break
            except BaseException as e:
                event = None
                self._ok = False
                tb = e.__traceback__
                e.__traceback__ = tb.tb_next
                self._value = e
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

                
class Boh(StateMachine):
    pass
    # @prova(self)

    Idle = State('Idle',True)
    @Generator(Idle)
    def printt(self):
        yield self.env.timeout(10)
        print('Idle state print')
    @on_exit(Idle)
    def print_ciao(self):
        print('Idle state exit')
    @on_interrupt(Idle)
    def interrupted_ok(self):
        print('Idle state interrupted ok')
    class Idle_SM(CompositeState):
        Sub = State('Sub',True)
        @Generator(Sub)
        def printt(self):
            yield self.env.timeout(2)
            print('Substate print')
        @on_exit(Sub)
        def print_ciao(self):
            print('Substate exit')
    Idle.set_composite_state(Idle_SM)
     

Idle = State('Idle')
@Generator(Idle)
def test(self):
    print('Test working')
    yield self.env.timeout(1)
    print('FAIL')    
@on_exit(Idle)
def print_ciao(self):
    print('ciao')

     
# class Environment(Environment):
#     state = BoundClass(State)


# env = Environment()
# Idle.env = env
# Idle.start()
# env.run(0.5)
# Idle.interrupt()
# env.run(0.6)

# env.run(50)

env = Environment()
foo = Boh(env,1)
env.run(1)
foo.interrupt()
env.run(20)

@addto(Boh)
def print_ciao(self):
    print('ciao')
    
def Composite(instance):
    def decorator(f):
        setattr(instance, '_child_state_machine', f)
        return f
    return decorator
    
