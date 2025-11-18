"""
Enhanced Visualization Demo for hsim

Showcases all advanced visualization features:
- Agent trails
- Connection lines
- Multiple shapes
- Agent selection
- Performance stats
- Interactive controls
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
from hsim.core.graphics import Shape, PYGAME_AVAILABLE, WEB_AVAILABLE


class RobotAgent(Agent):
    """Robot agent that moves between stations with trails."""

    class FSM:
        class Idle(State):
            def entry(self):
                self.agent.set_color((150, 150, 150))

        class MovingToStation(State):
            def entry(self):
                self.agent.set_color((100, 150, 255))
                # Pick random target station
                stations = [a for a in self.agent.env._agents.values()
                           if hasattr(a, 'is_station') and a.is_station]
                if stations:
                    self.agent.target_station = random.choice(stations)
                    self.agent.target_x = self.agent.target_station.x + 30
                    self.agent.target_y = self.agent.target_station.y + 30

            def do(self):
                if not hasattr(self.agent, 'target_x'):
                    return

                dx = self.agent.target_x - self.agent.x
                dy = self.agent.target_y - self.agent.y
                dist = math.sqrt(dx**2 + dy**2)

                if dist > 5:
                    speed = 80  # pixels per second
                    dt = 0.05
                    self.agent.x += (dx / dist) * speed * dt
                    self.agent.y += (dy / dist) * speed * dt

        class Processing(State):
            def entry(self):
                self.agent.set_color((255, 165, 0))

            def exit(self):
                self.agent.set_color((100, 150, 255))

        Idle.add(TimeoutTransition(MovingToStation, 0.5))
        MovingToStation.add(TimeoutTransition(Processing, 4.0))
        Processing.add(TimeoutTransition(MovingToStation, 2.0))

    def __init__(self, env, name, position):
        super().__init__(
            env,
            name=name,
            position=position,
            dimensions=(35, 35),
            color=(100, 150, 255),
            shape=Shape.CIRCLE,
            trail_length=100,  # Enable trails!
            trail_color=(100, 150, 255),
            border_width=2
        )
        self.target_x = position[0]
        self.target_y = position[1]
        self.target_station = None


class StationAgent(Agent):
    """Station agent with pulsing animation."""

    class FSM:
        class Idle(State):
            def entry(self):
                self.agent.set_color((180, 180, 180))

        class Active(State):
            def entry(self):
                self.agent.set_color((50, 200, 50))

        class Busy(State):
            def entry(self):
                self.agent.set_color((255, 100, 100))

        Idle.add(TimeoutTransition(Active, 3.0))
        Active.add(TimeoutTransition(Busy, 2.0))
        Busy.add(TimeoutTransition(Idle, 2.0))

    def __init__(self, env, name, position, shape=Shape.RECTANGLE):
        super().__init__(
            env,
            name=name,
            position=position,
            dimensions=(80, 80),
            color=(180, 180, 180),
            shape=shape,
            border_width=3,
            border_color=(50, 50, 50)
        )
        self.is_station = True


class ConveyorAgent(Agent):
    """Conveyor belt segment."""

    def __init__(self, env, name, position, width=100):
        super().__init__(
            env,
            name=name,
            position=position,
            dimensions=(width, 20),
            color=(100, 100, 120),
            shape=Shape.RECTANGLE,
            border_width=1
        )


def create_manufacturing_layout(env):
    """Create a realistic manufacturing layout."""

    # Create stations in a layout
    stations = []

    # Input station
    stations.append(StationAgent(env, "Input", (100, 100), Shape.HEXAGON))

    # Processing stations
    stations.append(StationAgent(env, "Station_A", (300, 100), Shape.RECTANGLE))
    stations.append(StationAgent(env, "Station_B", (500, 100), Shape.RECTANGLE))
    stations.append(StationAgent(env, "Station_C", (700, 200), Shape.DIAMOND))

    # Quality control
    stations.append(StationAgent(env, "QC", (900, 100), Shape.STAR))

    # Assembly stations
    stations.append(StationAgent(env, "Assembly_1", (300, 350), Shape.HEXAGON))
    stations.append(StationAgent(env, "Assembly_2", (500, 350), Shape.HEXAGON))

    # Output station
    stations.append(StationAgent(env, "Output", (900, 350), Shape.CIRCLE))

    # Storage
    stations.append(StationAgent(env, "Storage", (100, 350), Shape.DIAMOND))

    # Create conveyors (visual only)
    conveyors = [
        ConveyorAgent(env, "Conv_1", (180, 130), 100),
        ConveyorAgent(env, "Conv_2", (380, 130), 100),
        ConveyorAgent(env, "Conv_3", (580, 130), 100),
        ConveyorAgent(env, "Conv_4", (780, 180), 100),
    ]

    # Create robots with different colors
    robot_colors = [
        (100, 150, 255),  # Blue
        (255, 100, 150),  # Pink
        (150, 255, 100),  # Green
        (255, 200, 100),  # Orange
        (200, 100, 255),  # Purple
        (100, 255, 200),  # Cyan
    ]

    robots = []
    for i, color in enumerate(robot_colors):
        robot = RobotAgent(env, f"Robot_{i+1}", (150 + i * 100, 250))
        robot.set_trail_color(color)
        robot.set_color(color)
        robots.append(robot)

    # Create connections between stations (for visualization)
    stations[0].connections = {'next': stations[1]}
    stations[1].connections = {'next': stations[2]}
    stations[2].connections = {'next': stations[3]}
    stations[3].connections = {'next': stations[4]}
    stations[4].connections = {'assembly': [stations[5], stations[6]]}
    stations[5].connections = {'output': stations[7]}
    stations[6].connections = {'output': stations[7]}
    stations[8].connections = {'supply': [stations[0], stations[5], stations[6]]}

    return stations, robots, conveyors


def run_demo_enhanced(renderer='pygame', duration=120):
    """
    Run the enhanced visualization demo.

    Args:
        renderer: 'pygame' or 'web'
        duration: Simulation duration in seconds
    """
    print("=" * 70)
    print("hsim ENHANCED Visualization Demo")
    print("=" * 70)

    # Create real-time environment (1.5x speed)
    env = RealTimeEnvironment(real_time=1.5)

    print("\n🏭 Creating manufacturing layout...")
    stations, robots, conveyors = create_manufacturing_layout(env)

    print(f"   ✓ Created {len(stations)} stations")
    print(f"   ✓ Created {len(robots)} robots with trails")
    print(f"   ✓ Created {len(conveyors)} conveyor segments")
    print(f"   ✓ Total agents: {len(env._agents)}")

    # Start visualization
    print(f"\n🎨 Starting {renderer} renderer...")

    if renderer == 'pygame':
        from hsim.core.graphics import PygameRendererEnhanced
        viz = PygameRendererEnhanced(
            env,
            width=1200,
            height=600,
            fps=60,
            show_trails=True,
            show_connections=True,
            show_minimap=True,
            show_stats=True
        )
    else:  # web
        from hsim.core.graphics import WebRendererEnhanced
        viz = WebRendererEnhanced(
            env,
            port=8000,
            canvas_width=1200,
            canvas_height=600,
            update_rate=30
        )

    viz.start()

    if renderer == 'web':
        print("\n" + "=" * 70)
        print("🌐 Web renderer started!")
        print("   Open your browser to: http://localhost:8000")
        print("=" * 70)

    # Display features
    print("\n✨ Features enabled:")
    print("   • Agent movement trails (100 points)")
    print("   • Connection lines between stations")
    print("   • Agent selection (click to select)")
    print("   • Real-time performance stats")
    print("   • Minimap for navigation (Pygame)")
    print("   • Multiple shapes (circle, rectangle, diamond, hexagon, star)")
    print("   • Interactive zoom and pan")
    print("   • Configurable layers")

    if renderer == 'pygame':
        print("\n⌨️  Pygame Controls:")
        print("   SPACE: Pause     | ESC: Quit")
        print("   +/-: Zoom        | Right-drag: Pan")
        print("   G: Toggle Grid   | T: Toggle Trails")
        print("   C: Toggle Connections | M: Toggle Minimap")
        print("   L: Toggle Labels | S: Toggle States")
        print("   I: Toggle Stats  | F12: Screenshot")
        print("   Click: Select agent")
    else:
        print("\n🖱️  Web Controls:")
        print("   Drag: Pan        | Scroll: Zoom")
        print("   Click: Select agent")
        print("   Buttons: Toggle layers, screenshot, reset view")

    print(f"\n▶️  Running simulation for {duration} seconds...")
    print("   Press Ctrl+C to stop early\n")

    try:
        env.run(until=duration)
    except KeyboardInterrupt:
        print("\n⏸️  Simulation interrupted by user")

    print("\n🛑 Stopping visualization...")
    viz.stop()

    print("\n✅ Demo complete!")
    print(f"   Final simulation time: {env.now:.2f}s")
    print(f"   Robots completed: {len([r for r in robots if hasattr(r, 'stateMachine')])} cycles")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='hsim Enhanced Visualization Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python visualization_demo_enhanced.py --renderer pygame
  python visualization_demo_enhanced.py --renderer web --duration 180
        """
    )
    parser.add_argument(
        '--renderer',
        choices=['pygame', 'web'],
        default='pygame' if PYGAME_AVAILABLE else 'web',
        help='Renderer to use'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=120,
        help='Simulation duration in seconds (default: 120)'
    )

    args = parser.parse_args()

    # Check availability
    print("\n📦 Available renderers:")
    print(f"   Pygame: {'✓ Available' if PYGAME_AVAILABLE else '✗ Not installed (pip install pygame)'}")
    print(f"   Web: {'✓ Available' if WEB_AVAILABLE else '✗ Not installed (pip install fastapi uvicorn websockets)'}")

    if not PYGAME_AVAILABLE and not WEB_AVAILABLE:
        print("\n❌ ERROR: No visualization backend available!")
        print("   Install one of:")
        print("   • pip install pygame")
        print("   • pip install fastapi uvicorn websockets")
        return 1

    if args.renderer == 'pygame' and not PYGAME_AVAILABLE:
        print(f"\n❌ ERROR: Pygame not available. Install with: pip install pygame")
        return 1

    if args.renderer == 'web' and not WEB_AVAILABLE:
        print(f"\n❌ ERROR: Web renderer not available.")
        print("   Install with: pip install fastapi uvicorn websockets")
        return 1

    run_demo_enhanced(renderer=args.renderer, duration=args.duration)
    return 0


if __name__ == "__main__":
    sys.exit(main())
