if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

    
import sched
from sortedcontainers import SortedList
import time
from typing import Any, Callable, Optional, Union
from collections import OrderedDict, deque

import numpy as np
from hsim.core.core.event import BaseEvent as Event, ConditionEvent, Status
from hsim.core.core.event import TimedEvent

DEBUG = False



class Scheduler(sched.scheduler):
    def __init__(self, timefunc: Callable[[], float], delayfunc: Callable[[float], None], env:'Environment'):
        super().__init__(timefunc, delayfunc)
        self._lock = Context()
        self._past = list()
        self._env = env
        self._queue = SortedList(key=lambda event: (event.time, event.priority, event.sequence))
        self._conditions = SortedList(key=lambda event: (event.time, event.priority, event.sequence))
    def enter(self, event: 'Event') -> 'Event':
        self._queue.add(event)
        return event
    def enterabs(self, time, priority, action=object, argument=(), kwargs=sched._sentinel) -> 'Event':
        if kwargs is sched._sentinel:
            kwargs = {}
        return self.enter(TimedEvent(self._env, time, priority, action, argument, **kwargs))
    def delay(self, delay, priority, action=object, argument=(), kwargs=sched._sentinel) -> 'Event':
        return self.enterabs(self.timefunc() + delay, priority, action, argument, kwargs)
    def late(self, priority, action, argument=(), kwargs=sched._sentinel):
        return self.enterabs(np.inf, priority, action, argument, kwargs)
    def run(self, blocking=True):
        delayfunc, timefunc, lock, past = self.delayfunc, self.timefunc, self._lock, self._past
        while self._queue:
            event = self._queue.pop(0)
            delayfunc(event.time - timefunc())
            if event.pending:
                event.time = np.inf
                event.schedule()
                self.enterevent(event)
            elif "StopSimulation" in event.kwargs:
                break
            else:
                if event._conditioned:
                    if not event.verify():
                        event._status, event.time = Status.CONDITIONED, np.inf
                        event.add()
                        continue
                event.trigger()
                self.execute(event)
                delayfunc(0)
                past.append(event)
                event.process()
            # Only check conditioned events in the queue
            self.check_conditioned_events()
    def check_conditioned_events(self):
        for cond_event in self._conditions:
            if cond_event.verify():
                break
    def execute(self,event):
        if callable(event.action):
            try:
                event.action(*event.arguments, **event.kwargs)
            except Exception as e:
                if DEBUG:
                    event.action(*event.arguments, **event.kwargs)
                    print(f"Error in event {event}: {e}. Action: {event.action}. Arguments: {event.arguments}")
                else:
                    raise e
        else:
            if len(event.arguments) == 0:
                event.arguments = [() for _ in range(len(event.action))]
            elif len(event.arguments) != len(event.action):
                raise ValueError("Arguments do not match")
            for index, action in enumerate(event.action):
                try:
                    action(*event.arguments[index], **event.kwargs)
                except Exception as e:
                    if DEBUG:
                        print(f"Error in event {event}: {e}. Action: {event.action}. Arguments: {event.arguments}")
                    else:
                        raise e 
    def cancel(self, event):
        self._queue.remove(event)
        
class Context:
    def __enter__(self):
        pass
    def __exit__(self,a,b,c):
        pass

class Counter():
    def __init__(self, value=0):
        super().__init__()
        self._value = value
    def __call__(self):
        return self.__next__()
    def __next__(self):
        self._value += 1
        return self._value
    def __repr__(self) -> str:
        return "Counter({self.val})".format(self._value)
    
class Environment:
    def __init__(self, real_time: Union[float,int,bool] = False, current_time: bool = False):
        self._now = 0.0 if not current_time else time.time()
        self._real_time = real_time if real_time is not True else 1.0
        self.scheduler = Scheduler(self._time, self._sleep, self)
        self._objects = list()
        self._agents = OrderedDict()
        self.counter = Counter()
        self._debug = DEBUG

    def _time(self) -> float:
        return time.time() if self._real_time else self._now

    def _sleep(self, delay: float) -> None:
        if self._real_time:
            time.sleep(delay/self._real_time)
        else:
            self._now += delay
    
    def add_agent(self, obj: Any) -> None:
        count = self.counter()
        key = obj.name if obj.name is not None else count
        self._agents[key] = obj
        
    def _activate_fsm(self) -> None:
        for ag in self._agents.values():
            ag.activate_fsm()

    @property
    def now(self) -> float:
        return self._time()

    def schedule(self, delay: float, priority: int, action: Callable[..., Any], *args: Any, **kwargs: Any) -> sched.Event:
        return self.scheduler.enter(delay, priority, action, args, kwargs)

    def schedule_absolute(self, time: float, priority: int, action: Callable[..., Any], *args: Any, **kwargs: Any) -> sched.Event:
        return self.scheduler.enterabs(time, priority, action, args, kwargs)

    def run(self, until: Optional[float] = None) -> None:
        self._activate_fsm()
        if until is not None:
            if until < self.now:
                until += self.now
            self.scheduler.enterabs(until, 0, kwargs={"StopSimulation": True})
        self.scheduler.run(blocking=True)

    def _stop_simulation(self) -> None:
        self.scheduler.queue.clear()

# Circular import to resolve type hinting