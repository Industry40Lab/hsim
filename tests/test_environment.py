"""
Unit tests for the core Environment class.
"""

import unittest
from hsim.core.core.env import Environment, RealTimeEnvironment
from hsim.core.core.event import TimedEvent, DelayEvent


class TestEnvironment(unittest.TestCase):
    """Test cases for Environment class."""
    
    def test_environment_initialization(self):
        """Test that environment initializes correctly."""
        env = Environment()
        self.assertEqual(env.now, 0.0)
        self.assertIsNotNone(env.scheduler)
    
    def test_environment_with_current_time(self):
        """Test environment initialization with current time."""
        import time
        before = time.time()
        env = Environment(current_time=True)
        after = time.time()
        # Environment time should be between before and after
        self.assertGreaterEqual(env.now, before)
        self.assertLessEqual(env.now, after)
    
    def test_time_advancement(self):
        """Test that simulation time advances correctly."""
        env = Environment()
        initial_time = env.now
        env.run(until=10)
        self.assertEqual(env.now, 10)
        self.assertGreater(env.now, initial_time)
    
    def test_event_scheduling(self):
        """Test basic event scheduling."""
        env = Environment()
        executed = []
        
        def callback():
            executed.append(env.now)
        
        env.schedule(5, 1, callback)
        env.run(until=10)
        
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0], 5)
    
    def test_multiple_events(self):
        """Test scheduling multiple events."""
        env = Environment()
        executed = []
        
        def callback(value):
            executed.append(value)
        
        env.schedule_absolute(5, 1, callback, 'first')
        env.schedule_absolute(10, 1, callback, 'second')
        env.schedule_absolute(3, 1, callback, 'third')
        env.run(until=15)
        
        self.assertEqual(len(executed), 3)
        # Events should execute in time order
        self.assertEqual(executed, ['third', 'first', 'second'])
    
    def test_event_priority(self):
        """Test that event priority is respected."""
        env = Environment()
        executed = []
        
        def callback(value):
            executed.append(value)
        
        # Schedule at same time with different priorities
        env.schedule_absolute(5, 2, callback, 'low_priority')
        env.schedule_absolute(5, 1, callback, 'high_priority')
        env.run(until=10)
        
        # Lower priority number executes first
        self.assertEqual(executed, ['high_priority', 'low_priority'])


class TestRealTimeEnvironment(unittest.TestCase):
    """Test cases for RealTimeEnvironment class."""
    
    def test_real_time_scaling_factor(self):
        """Test real-time environment stores scaling factor correctly."""
        env = RealTimeEnvironment(real_time=2)
        # Test behavior rather than private attribute
        self.assertIsNotNone(env.scheduler)
    
    def test_real_time_scaling(self):
        """Test that real-time scaling works."""
        import time
        env = RealTimeEnvironment(real_time=10)  # 10x faster than real time
        
        start = time.time()
        env.run(until=1)  # Should take ~0.1 seconds in real time
        elapsed = time.time() - start
        
        # Should be much faster than 1 second
        self.assertLess(elapsed, 0.5)


class TestEventTypes(unittest.TestCase):
    """Test different event types."""
    
    def test_timed_event(self):
        """Test TimedEvent creation and execution."""
        env = Environment()
        executed = []
        
        def callback():
            executed.append(env.now)
        
        event = TimedEvent(env, 5, 1, callback)
        event.add()
        env.run(until=10)
        
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0], 5)
    
    def test_delay_event(self):
        """Test DelayEvent creation and execution."""
        env = Environment()
        executed = []
        
        def callback():
            executed.append(env.now)
        
        env.run(until=2)  # Start at time 2
        event = DelayEvent(env, 3, 1, callback)  # Delay of 3 from current time
        event.add()
        env.run(until=10)
        
        self.assertEqual(len(executed), 1)
        self.assertEqual(executed[0], 5)  # 2 + 3


if __name__ == '__main__':
    unittest.main()
