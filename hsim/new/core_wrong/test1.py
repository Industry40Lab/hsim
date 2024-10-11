import sched
import threading
import time
import asyncio
import sched
import time
import asyncio
from typing import Callable, Iterable, Union

import numpy as np

class Event:
    def __init__(self, clock, callbacks:Union[Callable, Iterable[Callable], None]=None):
        self.clock = clock
        self._event = asyncio.Event()
        if callbacks is Iterable:
            for cb in callbacks:
                self._event.add_callback(callbacks)
        elif callbacks is Callable:
            self._event.add_callback(callbacks)
    def trigger(self):
        self._event.set()
        print(f"Event triggered at simulated time {self.clock.current_time}")
    async def wait(self):
        await self._event.wait()
    def __getstate__(self):
        state = self.__dict__.copy()
        if '_event' in state and '_loop' in state['_event'].__dict__:
            state['_event'].__dict__['_loop'] = None
        return state
    def __setstate__(self, state):
        self.__dict__.update(state)

class Scheduler(sched.scheduler):
    def __init__(self, env, timefunc, delayfunc):
        self.env = env
        super().__init__(timefunc, delayfunc)
        self._lock = threading.RLock()
    def __getstate__(self):
        state = self.__dict__.copy()
        state['_lock'] = None
        return state
    def __setstate__(self, state):
        self.__dict__.update(state)
        self._lock = threading.RLock()
        self.timefunc = self._env._get_time

class Environment:
    _termination : asyncio.Event
    def __init__(self):
        self.scheduler = Scheduler(env=self, timefunc=self._get_time, delayfunc=self.delay)
        self.current_time = 0
        self._objects = []
    def _get_time(self):
        return self.current_time
    @property
    def now(self):
        return self.current_time
    def delay(self, duration):
        time.sleep(duration)
    def advance_time(self, seconds):
        self.current_time += seconds
        self.scheduler.run(blocking=False)
    def end_simulation(self):
        self._termination.set()
    def check_conditions(self):
        for event in self.scheduler.queue:
            event.check() if isinstance(event, ConditionEvent) else None
    async def run(self, until):
        self._termination = asyncio.Event()
        self.scheduler.enter(until, 1, self.end_simulation)
        while not self._termination.is_set():
            if self.scheduler.queue:
                next_event_time = self.scheduler.queue[0].time
                time_to_advance = next_event_time - self.current_time
            else:
                print(f"No more events to process at time {self.now}")
                break
            self.advance_time(time_to_advance)
            print(f"Simulated time: {self.current_time}")
            await asyncio.sleep(0)  # Yield control to allow other tasks to run
      
class var:
    def __init__(self, initial_value=None):
        self._value = initial_value
        self._callbacks = []
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, new_value):
        self._value = new_value
        if hasattr(self, "_clock"):
            self._callback()
    def __imatmul__(self, other):
        self.value = other
        return self
    def _callback(self):
        self._clock.check_conditions()

class Timeout(Event):
    def __init__(self, env, timeout):
        super().__init__(env)
        self.timeout = timeout
        self.clock.scheduler.enterabs(env.now + timeout, 1, self.trigger_timeout)
        print(f"Timeout set for {timeout} seconds at simulated time {self.clock.current_time}")
    def trigger_timeout(self):
        self._event.set()
        print(f"Timeout of {self.timeout} seconds reached at simulated time {self.clock.current_time}")
    async def wait(self):
        await self._event.wait()
        self._event.clear()

class ConditionEvent(Event):
    def __init__(self, clock, condition: Callable[[], bool], callbacks: Union[Callable, Iterable[Callable], None] = None):
        super().__init__(clock, callbacks)
        self._condition = condition

    def check(self):
        if self.condition():
            self.trigger()

    async def wait(self):
        await self._event.wait()

class Message(Event):
    def __init__(self, clock, message, destination):
        super().__init__(clock, callbacks=None)
        self.message = message

    def trigger(self):
        super().trigger()
        print(f"Message: {self.message}")

def class_binder(self, cls):
    def wrapper(*args, **kwargs):
        return cls(self, *args, **kwargs)
    return wrapper        


        
if __name__ == "__main__":
    try: 
        async def test():
            env = Environment()
            # Create a Timeout event with a 5-second timeout
            timeout = Timeout(env, 5)
            # Run the simulated clock until a specified time and wait for its completion
            await env.run(until=10)
            await env.run(until=15)
            print("Environment has completed running.")
        asyncio.run(test())
    except Exception as e:
        print(e)
        print("Error in test")
