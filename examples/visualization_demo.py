"""
Visualization Demo for hsim

Demonstrates real-time visualization with both Pygame and Web renderers.
Shows agents moving through a simple manufacturing system.
"""

import sys
import os

# Add hsim to path
abs_path = os.path.abspath(__file__)
parts = abs_path.split(os.sep)
if "hsim" in parts:
    hsim_index = parts.index("hsim")
    hsim_path = os.sep.join(parts[:hsim_index + 1])
    if hsim_path not in sys.path:
        sys.path.append(hsim_path)

from hsim.core.core.env import RealTimeEnvironment
from hsim.core.agent.agent import Agent
from hsim.core.fsm.FSM import State, TimeoutTransition
from hsim.core.graphics import Shape, visualize, PYGAME_AVAILABLE, WEB_AVAILABLE
import random


class MovingAgent(Agent):
    """Agent that moves across the screen."""

    class FSM:
        """State machine for movement."""

        class Idle(State):
            def entry(self):
                print(f"{self.agent.name} is idle")

        class Moving(State):
            def entry(self):
                # Set random target position
                self.agent.target_x = random.uniform(100, 700)
                self.agent.target_y = random.uniform(100, 500)

            def do(self):
                # Move towards target
                dx = self.agent.target_x - self.agent.x
                dy = self.agent.target_y - self.agent.y
                dist = (dx**2 + dy**2)**0.5

                if dist > 5:
                    speed = 50  # pixels per second
                    dt = 0.1  # approximate time step
                    self.agent.x += (dx / dist) * speed * dt
                    self.agent.y += (dy / dist) * speed * dt

        class Processing(State):
            def entry(self):
                print(f"{self.agent.name} is processing")
                # Change color during processing
                self.agent.set_color((255, 150, 0))

            def exit(self):
                # Restore original color
                self.agent.set_color(self.agent.original_color)

        # Transitions
        Idle.add(TimeoutTransition(Moving, 1.0))
        Moving.add(TimeoutTransition(Processing, 3.0))
        Processing.add(TimeoutTransition(Moving, 2.0))

    def __init__(self, env, name, position, color, shape=Shape.RECTANGLE):
        super().__init__(
            env,
            name=name,
            position=position,
            dimensions=(40, 40),
            color=color,
            shape=shape
        )
        self.target_x = position[0]
        self.target_y = position[1]
        self.original_color = color


class StationAgent(Agent):
    """Static station agent."""

    class FSM:
        """Simple state machine."""

        class Idle(State):
            def entry(self):
                self.agent.set_color((150, 150, 150))

        class Active(State):
            def entry(self):
                self.agent.set_color((0, 200, 0))

        Idle.add(TimeoutTransition(Active, 2.0))
        Active.add(TimeoutTransition(Idle, 2.0))

    def __init__(self, env, name, position):
        super().__init__(
            env,
            name=name,
            position=position,
            dimensions=(60, 60),
            color=(150, 150, 150),
            shape=Shape.RECTANGLE
        )


def run_demo(renderer_mode='auto', duration=60):
    """
    Run the visualization demo.

    Args:
        renderer_mode: 'pygame', 'web', or 'auto'
        duration: Simulation duration in seconds
    """
    print("=" * 60)
    print("hsim Visualization Demo")
    print("=" * 60)

    # Create real-time environment (2x speed for faster demo)
    env = RealTimeEnvironment(real_time=2.0)

    # Create static stations
    stations = [
        StationAgent(env, "Station_A", position=(100, 100)),
        StationAgent(env, "Station_B", position=(400, 100)),
        StationAgent(env, "Station_C", position=(700, 100)),
        StationAgent(env, "Station_D", position=(100, 400)),
        StationAgent(env, "Station_E", position=(700, 400)),
    ]

    # Create moving agents with different shapes and colors
    colors = [
        (255, 100, 100),  # Red
        (100, 100, 255),  # Blue
        (100, 255, 100),  # Green
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
    ]

    shapes = [Shape.CIRCLE, Shape.RECTANGLE, Shape.TRIANGLE, Shape.DIAMOND, Shape.CIRCLE]

    moving_agents = []
    for i, (color, shape) in enumerate(zip(colors, shapes)):
        agent = MovingAgent(
            env,
            name=f"Agent_{i+1}",
            position=(200 + i * 50, 250),
            color=color,
            shape=shape
        )
        moving_agents.append(agent)

    print(f"\nCreated {len(stations)} stations and {len(moving_agents)} moving agents")
    print(f"Environment: RealTimeEnvironment (2x speed)")
    print(f"Renderer: {renderer_mode}")

    # Start visualization
    print("\nStarting visualization...")
    viz = visualize(
        env,
        mode=renderer_mode,
        width=800,
        height=600,
        fps=30,
        title="hsim Visualization Demo"
    )

    if renderer_mode == 'web' or (renderer_mode == 'auto' and not PYGAME_AVAILABLE):
        print("\n" + "=" * 60)
        print("Web renderer started!")
        print("Open your browser to: http://localhost:8000")
        print("=" * 60)

    # Run simulation
    print(f"\nRunning simulation for {duration} seconds...")
    print("Press Ctrl+C to stop early")

    try:
        env.run(until=duration)
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")

    # Stop visualization
    print("\nStopping visualization...")
    viz.stop()

    print("\nDemo complete!")
    print(f"Final simulation time: {env.now:.2f}")


def main():
    """Main entry point with command line argument parsing."""
    import argparse

    parser = argparse.ArgumentParser(description='hsim Visualization Demo')
    parser.add_argument(
        '--renderer',
        choices=['pygame', 'web', 'auto'],
        default='auto',
        help='Renderer to use (default: auto)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=60,
        help='Simulation duration in seconds (default: 60)'
    )

    args = parser.parse_args()

    # Check availability
    print("\nAvailable renderers:")
    print(f"  - Pygame: {'✓' if PYGAME_AVAILABLE else '✗ (install with: pip install pygame)'}")
    print(f"  - Web: {'✓' if WEB_AVAILABLE else '✗ (install with: pip install fastapi uvicorn websockets)'}")
    print()

    if not PYGAME_AVAILABLE and not WEB_AVAILABLE:
        print("ERROR: No visualization backend available!")
        print("Install at least one:")
        print("  pip install pygame")
        print("  pip install fastapi uvicorn websockets")
        return

    run_demo(renderer_mode=args.renderer, duration=args.duration)


if __name__ == "__main__":
    main()
