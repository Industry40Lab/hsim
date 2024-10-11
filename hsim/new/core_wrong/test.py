import unittest
import numpy as np
from event import Event, Status
from env import Environment

class TestEvent(unittest.TestCase):
    def setUp(self):
        self.env = Environment()

    def test_event_initialization(self):
        event = Event(self.env, time=15, priority=1, action=print, argument=("Hello, World!",))
        self.assertEqual(event.time, 15)
        self.assertEqual(event.priority, 1)
        self.assertEqual(event._status, Status.PENDING)
        self.assertEqual(event.action, print)

    def test_event_initialization_with_infinite_time(self):
        event = Event(self.env, time=np.inf, priority=1, action=print, argument=("Hello, World!",))
        self.assertEqual(event._status, Status.TRIGGERED)

    def test_event_schedule(self):
        event = Event(self.env, time=15, priority=1, action=print, argument=("Hello, World!",))
        event.schedule()
        self.assertIn(event, self.env.scheduler.queue)

if __name__ == '__main__':
    unittest.main()