"""
Simulation Controller for Interactive Control

Provides play/pause/step/reset/speed control over simulations.
Coordinates between renderers and the simulation environment.
"""

import threading
import queue
import time
import copy
from typing import Optional, Callable, Any, Dict
from enum import Enum


class SimulationState(Enum):
    """Current state of the simulation."""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    RESETTING = "resetting"


class SimulationCommand(Enum):
    """Commands that can be sent to the controller."""
    PLAY = "play"
    PAUSE = "pause"
    STEP = "step"
    RESET = "reset"
    STOP = "stop"
    SET_SPEED = "set_speed"
    GOTO_TIME = "goto_time"


class SimulationController:
    """
    Controls simulation execution with play/pause/step/reset.

    Runs the simulation in a separate thread and accepts commands
    from renderers or other sources.

    Args:
        env: Simulation environment
        step_size: Time step for each simulation step (default: 0.1)
        max_time: Maximum simulation time (default: None for unlimited)
        on_reset: Optional callback when simulation resets

    Example:
        controller = SimulationController(env, step_size=0.1)
        controller.start()

        # From renderer or UI
        controller.send_command(SimulationCommand.PAUSE)
        controller.send_command(SimulationCommand.STEP)
        controller.send_command(SimulationCommand.PLAY)
        controller.set_speed(2.0)  # 2x speed

        controller.stop()
    """

    def __init__(
        self,
        env,
        step_size: float = 0.1,
        max_time: Optional[float] = None,
        on_reset: Optional[Callable] = None,
        auto_start: bool = False
    ):
        self.env = env
        self.step_size = step_size
        self.max_time = max_time
        self.on_reset = on_reset

        # Control state
        self.state = SimulationState.STOPPED
        self.speed_multiplier = getattr(env, '_real_time', 1.0)
        self.target_time = 0.0

        # Command queue (thread-safe)
        self.command_queue: queue.Queue = queue.Queue()

        # Thread control
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Initial state snapshot for reset
        self._initial_state = None
        self._capture_initial_state()

        # Statistics
        self.steps_executed = 0
        self.last_step_time = 0.0

        if auto_start:
            self.state = SimulationState.RUNNING

    def _capture_initial_state(self):
        """Capture initial state for reset functionality."""
        try:
            # Store initial time and agent states
            self._initial_state = {
                'time': self.env.now,
                'agents': {},
            }

            # Capture agent positions and states if they have graphics
            if hasattr(self.env, '_agents'):
                for name, agent in self.env._agents.items():
                    agent_state = {}

                    if hasattr(agent, 'position'):
                        agent_state['position'] = list(agent.position)

                    if hasattr(agent, 'color'):
                        agent_state['color'] = agent.color

                    if hasattr(agent, 'visible'):
                        agent_state['visible'] = agent.visible

                    if hasattr(agent, 'trail_points'):
                        agent.clear_trail()

                    self._initial_state['agents'][name] = agent_state

        except Exception as e:
            print(f"Warning: Could not capture initial state: {e}")

    def start(self):
        """Start the simulation controller thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the simulation controller."""
        self.running = False
        self.state = SimulationState.STOPPED
        if self.thread:
            self.thread.join(timeout=2.0)

    def send_command(self, command: SimulationCommand, **kwargs):
        """
        Send a command to the simulation controller.

        Args:
            command: The command to execute
            **kwargs: Additional arguments for the command
        """
        self.command_queue.put((command, kwargs))

    def play(self):
        """Resume simulation."""
        self.send_command(SimulationCommand.PLAY)

    def pause(self):
        """Pause simulation."""
        self.send_command(SimulationCommand.PAUSE)

    def step(self, steps: int = 1):
        """Step simulation forward by N steps."""
        self.send_command(SimulationCommand.STEP, steps=steps)

    def reset(self):
        """Reset simulation to initial state."""
        self.send_command(SimulationCommand.RESET)

    def set_speed(self, multiplier: float):
        """
        Set simulation speed multiplier.

        Args:
            multiplier: Speed multiplier (1.0 = normal, 2.0 = 2x speed)
        """
        self.send_command(SimulationCommand.SET_SPEED, multiplier=multiplier)

    def goto_time(self, target_time: float):
        """
        Jump to specific simulation time.

        Args:
            target_time: Target simulation time
        """
        self.send_command(SimulationCommand.GOTO_TIME, time=target_time)

    @property
    def is_running(self) -> bool:
        """Check if simulation is currently running."""
        return self.state == SimulationState.RUNNING

    @property
    def is_paused(self) -> bool:
        """Check if simulation is paused."""
        return self.state == SimulationState.PAUSED

    def get_status(self) -> Dict[str, Any]:
        """Get current controller status."""
        return {
            'state': self.state.value,
            'time': self.env.now,
            'speed': self.speed_multiplier,
            'steps': self.steps_executed,
            'max_time': self.max_time,
        }

    def _simulation_loop(self):
        """Main simulation control loop."""
        # Activate FSMs once
        if hasattr(self.env, '_activate_fsm'):
            self.env._activate_fsm()

        while self.running:
            # Process commands
            self._process_commands()

            # Execute simulation step if running
            if self.state == SimulationState.RUNNING:
                self._execute_step()

            elif self.state == SimulationState.STEPPING:
                self._execute_step()
                self.state = SimulationState.PAUSED

            # Small sleep to prevent CPU spinning
            time.sleep(0.001)

    def _process_commands(self):
        """Process all pending commands."""
        while not self.command_queue.empty():
            try:
                command, kwargs = self.command_queue.get_nowait()
                self._handle_command(command, kwargs)
            except queue.Empty:
                break

    def _handle_command(self, command: SimulationCommand, kwargs: Dict):
        """Handle a single command."""
        with self._lock:
            if command == SimulationCommand.PLAY:
                self.state = SimulationState.RUNNING

            elif command == SimulationCommand.PAUSE:
                self.state = SimulationState.PAUSED

            elif command == SimulationCommand.STEP:
                steps = kwargs.get('steps', 1)
                for _ in range(steps):
                    if self.state == SimulationState.PAUSED:
                        self.state = SimulationState.STEPPING

            elif command == SimulationCommand.RESET:
                self._reset_simulation()

            elif command == SimulationCommand.STOP:
                self.running = False

            elif command == SimulationCommand.SET_SPEED:
                multiplier = kwargs.get('multiplier', 1.0)
                self.speed_multiplier = max(0.1, min(10.0, multiplier))

                # Update environment speed if it's RealTimeEnvironment
                if hasattr(self.env, '_real_time'):
                    self.env._real_time = self.speed_multiplier

            elif command == SimulationCommand.GOTO_TIME:
                target_time = kwargs.get('time', 0)
                self._goto_time(target_time)

    def _execute_step(self):
        """Execute one simulation step."""
        try:
            current_time = self.env.now
            target_time = current_time + self.step_size

            # Check max time
            if self.max_time and target_time > self.max_time:
                self.state = SimulationState.PAUSED
                return

            # Execute events up to target time
            self._run_until(target_time)

            self.steps_executed += 1
            self.last_step_time = time.time()

        except Exception as e:
            print(f"Error in simulation step: {e}")
            self.state = SimulationState.PAUSED

    def _run_until(self, until_time: float):
        """
        Run simulation until specified time.

        This manually processes events from the scheduler.
        """
        if not hasattr(self.env, 'scheduler'):
            return

        scheduler = self.env.scheduler

        while scheduler._queue and self.running:
            # Peek at next event
            if not scheduler._queue:
                break

            event = scheduler._queue[0]

            # Stop if event is beyond target time
            if event.time > until_time:
                break

            # Pop and process event
            event = scheduler._queue.pop(0)

            if getattr(event, "_canceled", False):
                continue

            if event.time == float('inf'):
                continue

            # Update environment time for virtual environments
            if hasattr(self.env, '_now'):
                self.env._now = event.time

            # Handle event
            if event.pending:
                event.time = float('inf')
                event.schedule()
                scheduler.enter(event)
            else:
                if event._conditioned:
                    if not event.verify():
                        event._status = event.Status.CONDITIONED if hasattr(event, 'Status') else 'CONDITIONED'
                        event.time = float('inf')
                        event.add()
                        continue

                event.trigger()
                scheduler.execute(event)
                scheduler._past.append(event)
                event.process()

            # Check conditioned events
            scheduler.check_conditioned_events()

        # Update time to target even if no events
        if hasattr(self.env, '_now'):
            self.env._now = min(until_time, self.env.now)

    def _reset_simulation(self):
        """Reset simulation to initial state."""
        if not self._initial_state:
            print("Warning: No initial state captured, cannot reset")
            return

        try:
            # Clear event queue
            if hasattr(self.env, 'scheduler'):
                self.env.scheduler._queue.clear()
                self.env.scheduler._past.clear()

            # Reset time
            if hasattr(self.env, '_now'):
                self.env._now = self._initial_state['time']

            # Restore agent states
            if hasattr(self.env, '_agents'):
                for name, agent in self.env._agents.items():
                    if name in self._initial_state['agents']:
                        saved_state = self._initial_state['agents'][name]

                        if 'position' in saved_state and hasattr(agent, 'position'):
                            agent.position = list(saved_state['position'])

                        if 'color' in saved_state and hasattr(agent, 'color'):
                            agent.color = saved_state['color']

                        if 'visible' in saved_state and hasattr(agent, 'visible'):
                            agent.visible = saved_state['visible']

                        if hasattr(agent, 'trail_points'):
                            agent.clear_trail()

            # Reactivate FSMs
            if hasattr(self.env, '_activate_fsm'):
                self.env._activate_fsm()

            # Reset statistics
            self.steps_executed = 0

            # Call user callback
            if self.on_reset:
                self.on_reset()

            self.state = SimulationState.PAUSED

        except Exception as e:
            print(f"Error resetting simulation: {e}")

    def _goto_time(self, target_time: float):
        """Jump to specific simulation time."""
        current_time = self.env.now

        if target_time < current_time:
            # Going backwards - need to reset and replay
            self._reset_simulation()
            current_time = self.env.now

        # Fast-forward to target time
        while current_time < target_time and self.running:
            step = min(self.step_size, target_time - current_time)
            self._run_until(current_time + step)
            current_time = self.env.now
