# hsim Graphics & Visualization

Real-time visualization for hsim discrete event simulations.

## Overview

The graphics module provides real-time visualization capabilities for hsim simulations through two renderer backends:
- **Pygame**: Desktop window with keyboard controls
- **Web**: Browser-based with WebSocket streaming

## Quick Start

### 1. Install Dependencies

```bash
# For Pygame renderer
pip install pygame

# For Web renderer
pip install fastapi uvicorn websockets

# Or install both
pip install -r requirements-viz.txt
```

### 2. Add Graphics to Your Agents

Agents automatically inherit from `GraphicsMixin`:

```python
from hsim.core.core.env import RealTimeEnvironment
from hsim.core.agent.agent import Agent
from hsim.core.graphics import Shape

# Create environment with real-time scaling
env = RealTimeEnvironment(real_time=2.0)  # 2x speed

# Create agent with graphics properties
agent = Agent(
    env,
    name="MyAgent",
    position=(100, 100),      # (x, y) coordinates
    dimensions=(50, 50),      # (width, height)
    color=(100, 150, 255),    # RGB tuple
    shape=Shape.RECTANGLE     # RECTANGLE, CIRCLE, TRIANGLE, DIAMOND
)
```

### 3. Start Visualization

```python
from hsim.core.graphics import visualize

# Auto-select best available renderer
viz = visualize(env, mode='auto')

# Run simulation
env.run(until=100)

# Stop visualization
viz.stop()
```

## Renderers

### Pygame Renderer (Desktop)

**Features:**
- Real-time rendering in a desktop window
- Keyboard controls for zoom and pause
- Automatic camera tracking
- State display for agents with FSM

**Controls:**
- `SPACE`: Pause/Resume
- `+/-`: Zoom in/out
- `ESC`: Quit

**Example:**
```python
from hsim.core.graphics import PygameRenderer

renderer = PygameRenderer(
    env,
    width=800,
    height=600,
    fps=30,
    show_grid=True
)
renderer.start()
env.run(until=100)
renderer.stop()
```

### Web Renderer (Browser)

**Features:**
- Modern browser-based interface
- WebSocket real-time updates
- Mouse controls (drag to pan, scroll to zoom)
- Multiple simultaneous viewers
- No installation required on client

**Example:**
```python
from hsim.core.graphics import WebRenderer

renderer = WebRenderer(
    env,
    port=8000,
    canvas_width=800,
    canvas_height=600,
    update_rate=30
)
renderer.start()

print("Open browser to: http://localhost:8000")

env.run(until=100)
renderer.stop()
```

## GraphicsMixin API

All agents inherit graphics properties:

### Properties

```python
agent.position        # [x, y] list (mutable)
agent.x              # x coordinate
agent.y              # y coordinate
agent.dimensions     # (width, height) or (radius,)
agent.width          # width
agent.height         # height
agent.radius         # radius (for circles)
agent.color          # (r, g, b) tuple (0-255)
agent.shape          # Shape enum
agent.rotation       # degrees (0-360)
agent.visible        # bool
agent.label          # text label
```

### Methods

```python
# Movement
agent.move_to(x, y)          # Absolute position
agent.move_by(dx, dy)        # Relative offset

# Appearance
agent.set_color((r, g, b))   # Change color
agent.show()                 # Make visible
agent.hide()                 # Make invisible

# Data
agent.get_graphics_dict()    # Get all properties as dict
```

## Visualizer Helper

Simplest way to add visualization:

```python
from hsim.core.graphics import Visualizer

# Context manager (auto start/stop)
with Visualizer(env, mode='pygame') as viz:
    env.run(until=100)

# Or manual control
viz = Visualizer(env, mode='web', port=8000)
viz.start()
env.run(until=100)
viz.stop()
```

## Real-Time Simulation

Visualization requires real-time simulation:

```python
from hsim.core.core.env import RealTimeEnvironment

# Create real-time environment
env = RealTimeEnvironment(
    real_time=1.0    # Speed multiplier
)                    # 1.0 = real-time
                     # 2.0 = 2x speed
                     # 0.5 = half speed
```

## Shape Types

```python
from hsim.core.graphics import Shape

Shape.RECTANGLE  # Default
Shape.CIRCLE     # Round agents
Shape.TRIANGLE   # Triangular agents
Shape.DIAMOND    # Diamond-shaped agents
Shape.CUSTOM     # For custom rendering
```

## Example: Manufacturing Simulation

```python
from hsim.core.core.env import RealTimeEnvironment
from hsim.core.agent.agent import Agent
from hsim.core.graphics import Shape, visualize

# Setup
env = RealTimeEnvironment(real_time=2.0)

# Create stations
station1 = Agent(env, "Station_A",
    position=(100, 100),
    dimensions=(80, 80),
    color=(150, 150, 150),
    shape=Shape.RECTANGLE
)

# Create moving parts
part = Agent(env, "Part_1",
    position=(200, 200),
    dimensions=(30, 30),
    color=(100, 150, 255),
    shape=Shape.CIRCLE
)

# Animate movement
def move_part():
    part.move_to(400, 300)
    env.schedule(1.0, 0, move_part)

env.schedule(0, 0, move_part)

# Visualize
viz = visualize(env, mode='auto')
env.run(until=60)
viz.stop()
```

## Demo

Run the included demo:

```bash
# Pygame demo
python examples/visualization_demo.py --renderer pygame

# Web demo
python examples/visualization_demo.py --renderer web

# Auto-select
python examples/visualization_demo.py --renderer auto --duration 60
```

## Architecture

```
hsim/core/graphics/
├── __init__.py           # Module exports
├── graphics_mixin.py     # GraphicsMixin base class
├── pygame_renderer.py    # Pygame renderer
├── web_renderer.py       # FastAPI/WebSocket renderer
├── visualizer.py         # High-level helper
└── README.md            # This file
```

## Performance

- **Pygame**: 60+ FPS with 100+ agents
- **Web**: 30+ FPS with 50+ agents (network dependent)
- **Overhead**: <5% CPU for visualization thread

## Troubleshooting

### Pygame not available
```bash
pip install pygame
```

### Web renderer not available
```bash
pip install fastapi uvicorn websockets
```

### Agents not visible
```python
# Ensure graphics are initialized
agent.init_graphics(
    position=(100, 100),
    dimensions=(50, 50),
    color=(255, 100, 100)
)
```

### Simulation too fast/slow
```python
# Adjust real_time factor
env = RealTimeEnvironment(real_time=0.5)  # Slower
env = RealTimeEnvironment(real_time=5.0)  # Faster
```

## Future Enhancements

- [ ] 3D visualization
- [ ] Animation interpolation
- [ ] Trace/path rendering
- [ ] Statistics overlay
- [ ] Video export
- [ ] VR support

## License

Part of the hsim project.
