from __future__ import annotations

import sched
import time
from typing import Any, Callable, Optional, List

SimTime = float
EventPriority = int

URGENT: EventPriority = 1
NORMAL: EventPriority = 2

class Event:
    def __init__(self, env: Environment, scheduler_event: sched.Event):
        self.env = env
        self._scheduler_event = scheduler_event
        self.callbacks: List[Callable[[], None]] = []
        self._value: Any = None
        self._ok: bool = True

    def cancel(self) -> None:
        self.env._scheduler.cancel(self._scheduler_event)

    def succeed(self, value: Any = None) -> Event:
        self._ok = True
        self._value = value
        return self

    def fail(self, exception: Exception) -> Event:
        self._ok = False
        self._value = exception
        return self

    @property
    def value(self) -> Any:
        return self._value

    @property
    def ok(self) -> bool:
        return self._ok

class Environment:
    def __init__(self, initial_time: SimTime = 0):
        self._now = initial_time
        self._scheduler = sched.scheduler(self._time, self._advance_time)
        self._stop_at: Optional[SimTime] = None

    def _time(self) -> SimTime:
        return self._now

    def _advance_time(self, duration: SimTime) -> None:
        self._now += duration

    @property
    def now(self) -> SimTime:
        return self._now

    def event(self) -> Event:
        return Event(self, self._scheduler.enter(0, NORMAL, lambda: None))

    def timeout(self, delay: SimTime, value: Any = None) -> Event:
        event = self.event()
        
        def action() -> None:
            event.succeed(value)
            for callback in event.callbacks:
                callback()

        self._scheduler.enter(delay, NORMAL, action)
        return event

    def schedule(self, delay: SimTime, priority: EventPriority, action: Callable[[], None]) -> Event:
        scheduler_event = self._scheduler.enter(delay, priority, action)
        return Event(self, scheduler_event)

    def run(self, until: Optional[SimTime] = None) -> None:
        if until is not None:
            self._stop_at = self._now + until
            self._scheduler.enterabs(self._stop_at, URGENT, lambda: self._scheduler.empty())

        self._scheduler.run()

    def step(self) -> SimTime:
        try:
            return self._scheduler.run(False)
        except sched.scheduler.empty:
            return 0

    def peek(self) -> Optional[SimTime]:
        try:
            return self._scheduler.queue[0].time - self._now
        except IndexError:
            return None

    def call_at(self, time: SimTime, action: Callable[[], None]) -> Event:
        return self.schedule(time - self._now, NORMAL, action)

    def call_later(self, delay: SimTime, action: Callable[[], None]) -> Event:
        return self.schedule(delay, NORMAL, action)

    def all_of(self, events: List[Event]) -> Event:
        all_event = self.event()
        remaining = len(events)

        def check() -> None:
            nonlocal remaining
            remaining -= 1
            if remaining == 0:
                all_event.succeed()
                for callback in all_event.callbacks:
                    callback()

        for event in events:
            event.callbacks.append(check)

        return all_event

    def any_of(self, events: List[Event]) -> Event:
        any_event = self.event()

        def check() -> None:
            if not any_event.ok:
                any_event.succeed()
                for callback in any_event.callbacks:
                    callback()

        for event in events:
            event.callbacks.append(check)

        return any_event
    

env = Environment()

def print_time(env: Environment, name: str) -> None:
    print(f"{name} executed at {env.now}")

env.call_later(5, lambda: print_time(env, "Event A"))
env.call_later(2, lambda: print_time(env, "Event B"))

env.run(until=10)