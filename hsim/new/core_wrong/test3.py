import sched
import threading
import time
from typing import Callable, Iterable, Union


class Event:
    def __init__(self, env, callbacks: Union[Callable, Iterable[Callable], None] = None):
        self._event = threading.Event()
        self.env = env
        self._callbacks = callbacks if callbacks is not None else []
        self.timeout = None

    def trigger(self):
        self._event.set()
        print(f"Event triggered at simulated time {self.env.current_time}")
        if isinstance(self._callbacks, Iterable):
            for cb in self._callbacks:
                cb()
        elif callable(self._callbacks):
            self._callbacks()

    def wait(self):
        self._event.wait()

    def is_set(self):
        return self._event.is_set()

    def clear(self):
        self._event.clear()

    def schedule(self, timeout=None):
        self.timeout = timeout
        self.env.schedule_event(self)

class Scheduler(sched.scheduler):
    def __init__(self, timefunc, delayfunc):
        super().__init__(timefunc, delayfunc)

class Environment:
    def __init__(self):
        self.scheduler = Scheduler(timefunc=self._get_time, delayfunc=self.delay)
        self.current_time = 0
        self._condition_events = []
        self._end_event = None

    def _get_time(self):
        return self.current_time

    @property
    def now(self):
        return self.current_time

    def delay(self, duration):
        time.sleep(0)  # Yield control without actual delay

    def schedule_event(self, event):
        if isinstance(event, ConditionEvent):
            self._condition_events.append(event)
        elif event.timeout is not None:
            self.scheduler.enterabs(event.timeout + self.now, 1, event.trigger)
        
        if isinstance(event, TimeoutEvent) and self._end_event is None:
            self._end_event = event

    def run(self):
        while not (self._end_event and self._end_event.is_set()):
            if not self.scheduler.empty():
                next_event_time, _, _, _ = self.scheduler.queue[0]
                self.current_time = next_event_time
                self.scheduler.run(blocking=False)
            else:
                break

            # Check and potentially trigger condition events
            for event in self._condition_events:
                event.check()

        print(f"Simulation completed at time {self.current_time}")

class TimeoutEvent(Event):
    def __init__(self, env, timeout):
        super().__init__(env)
        self.timeout = timeout
        print(f"Timeout set for {timeout} seconds at simulated time {self.env.current_time}")
        self.schedule(timeout)

class ConditionEvent(Event):
    def __init__(self, env, condition: Callable[[], bool]):
        super().__init__(env)
        self._condition = condition
        self.schedule()

    def check(self):
        if self._condition():
            self.trigger()


if __name__ == "__main__":
    
        env = Environment()
        
        # Create a Timeout event to end the simulation
        end_simulation = TimeoutEvent(env, 10)
        
        # Create another Timeout event
        timeout = TimeoutEvent(env, 5)
        
        # Create a ConditionEvent
        condition = ConditionEvent(env, lambda: env.now >= 3)
        
        # Run the simulation
        env.run()
        
    