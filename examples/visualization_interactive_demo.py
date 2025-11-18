"""
Interactive Visualization Demo for hsim

Showcases full interactive control features:
- Play/Pause/Step/Reset controls
- Variable speed control (0.5x to 5x)
- Real-time interaction while simulation runs
"""

import sys
import os
import random
import math

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
from hsim.core.graphics import (
    Shape, SimulationController,
    PygameRendererEnhanced, PYGAME_AVAILABLE
)


class BouncingAgent(Agent):
    """Agent that bounces around the screen."""

    class FSM:
        class Moving(State):
            def entry(self):
                # Initialize velocity if not set
                if not hasattr(self.agent, 'vx'):
                    self.agent.vx = random.uniform(-100, 100)
                    self.agent.vy = random.uniform(-100, 100)

            def do(self):
                # Update position
                dt = 0.05
                self.agent.x += self.agent.vx * dt
                self.agent.y += self.agent.vy * dt

                # Bounce off walls
                if self.agent.x < 0 or self.agent.x > 1100:
                    self.agent.vx = -self.agent.vx
                    self.agent.x = max(0, min(1100, self.agent.x))

                if self.agent.y < 0 or self.agent.y > 550:
                    self.agent.vy = -self.agent.vy
                    self.agent.y = max(0, min(550, self.agent.y))

        class Stopped(State):
            def entry(self):
                self.agent.set_color((150, 150, 150))

        Moving.add(TimeoutTransition(Stopped, 10.0))
        Stopped.add(TimeoutTransition(Moving, 2.0))

    def __init__(self, env, name, position, color, shape):
        super().__init__(
            env,
            name=name,
            position=position,
            dimensions=(30, 30),
            color=color,
            shape=shape,
            trail_length=50,
            trail_color=color,
            border_width=2
        )
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-100, 100)


def run_interactive_demo():
    """Run the interactive visualization demo."""
    print("=" * 70)
    print("hsim INTERACTIVE Visualization Demo")
    print("=" * 70)

    if not PYGAME_AVAILABLE:
        print("\n❌ ERROR: Pygame not available!")
        print("   Install with: pip install pygame")
        return 1

    # Create real-time environment
    env = RealTimeEnvironment(real_time=1.0)

    print("\n🎮 Creating interactive simulation...")

    # Create bouncing agents with different shapes and colors
    colors = [
        (255, 100, 100),  # Red
        (100, 255, 100),  # Green
        (100, 100, 255),  # Blue
        (255, 255, 100),  # Yellow
        (255, 100, 255),  # Magenta
        (100, 255, 255),  # Cyan
        (255, 165, 0),    # Orange
        (148, 0, 211),    # Purple
    ]

    shapes = [Shape.CIRCLE, Shape.RECTANGLE, Shape.TRIANGLE, Shape.DIAMOND,
              Shape.HEXAGON, Shape.STAR, Shape.CIRCLE, Shape.RECTANGLE]

    agents = []
    for i, (color, shape) in enumerate(zip(colors, shapes)):
        agent = BouncingAgent(
            env,
            name=f"Agent_{i+1}",
            position=(random.uniform(100, 1000), random.uniform(100, 450)),
            color=color,
            shape=shape
        )
        agents.append(agent)

    print(f"   ✓ Created {len(agents)} bouncing agents")

    # Create simulation controller
    print("\n🎛️  Creating simulation controller...")
    controller = SimulationController(
        env,
        step_size=0.05,  # Small steps for smooth animation
        max_time=None,   # Unlimited
        auto_start=True  # Start in running state
    )

    controller.start()
    print("   ✓ Controller started")

    # Create enhanced pygame renderer with controller
    print("\n🎨 Starting Pygame renderer with interactive controls...")
    renderer = PygameRendererEnhanced(
        env,
        controller=controller,
        width=1200,
        height=600,
        fps=60,
        show_trails=True,
        show_connections=False,
        show_minimap=True,
        show_stats=True
    )

    renderer.start()

    print("\n" + "=" * 70)
    print("✨ INTERACTIVE CONTROLS")
    print("=" * 70)
    print("\n🎮 Simulation Controls:")
    print("   SPACE       - Play/Pause simulation")
    print("   →           - Step forward one step")
    print("   Ctrl+R      - Reset simulation to start")
    print("\n⚡ Speed Controls:")
    print("   1           - 0.5x speed (slow motion)")
    print("   2           - 1.0x speed (normal)")
    print("   3           - 2.0x speed (fast)")
    print("   4           - 5.0x speed (very fast)")
    print("\n🖼️  View Controls:")
    print("   +/-         - Zoom in/out")
    print("   Right-drag  - Pan view")
    print("   Scroll      - Zoom")
    print("\n🎨 Layer Toggles:")
    print("   G           - Toggle grid")
    print("   T           - Toggle trails")
    print("   M           - Toggle minimap")
    print("   L           - Toggle labels")
    print("   S           - Toggle states")
    print("   I           - Toggle stats")
    print("\n📸 Other:")
    print("   F12         - Screenshot")
    print("   Click       - Select agent")
    print("   ESC         - Quit")
    print("=" * 70)

    print("\n▶️  Simulation is RUNNING")
    print("   Try pausing with SPACE and stepping with →")
    print("   Change speed with 1-4")
    print("   The simulation will run until you close the window\n")

    # Wait for renderer to close
    try:
        while renderer.running:
            import time
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n⏸️  Interrupted by user")

    print("\n🛑 Stopping controller and renderer...")
    controller.stop()
    renderer.stop()

    print("\n✅ Demo complete!")
    print(f"   Final simulation time: {env.now:.2f}s")
    print(f"   Steps executed: {controller.steps_executed}")

    return 0


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='hsim Interactive Visualization Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This demo showcases full interactive control over the simulation:
- Play/Pause/Step/Reset controls
- Variable speed (0.5x to 5x)
- Real-time interaction

Controls are shown in the window. Try pausing with SPACE and
stepping through the simulation with the arrow key!
        """
    )

    args = parser.parse_args()

    return run_interactive_demo()


if __name__ == "__main__":
    sys.exit(main())
