"""
High-level Visualizer for hsim Simulations

Provides a simple interface to start visualization with either Pygame or Web renderer.
"""

from typing import Optional, Literal
from hsim.core.graphics import (
    PygameRenderer, PygameRendererSync, WebRenderer,
    PYGAME_AVAILABLE, WEB_AVAILABLE
)


class Visualizer:
    """
    High-level visualization manager.

    Simplifies starting and managing visualization for simulations.

    Example:
        env = RealTimeEnvironment(real_time=2.0)
        # ... create agents with graphics properties ...

        viz = Visualizer(env, mode='pygame')
        viz.start()
        env.run(until=100)
        viz.stop()
    """

    def __init__(
        self,
        env,
        mode: Literal['pygame', 'web', 'auto'] = 'auto',
        width: int = 800,
        height: int = 600,
        fps: int = 30,
        title: str = "hsim Simulation",
        **kwargs
    ):
        """
        Initialize visualizer.

        Args:
            env: Simulation environment
            mode: Renderer type ('pygame', 'web', or 'auto')
            width: Display width
            height: Display height
            fps: Frames/updates per second
            title: Window/page title
            **kwargs: Additional renderer-specific options
        """
        self.env = env
        self.mode = mode
        self.renderer = None

        # Auto-detect best available renderer
        if mode == 'auto':
            if PYGAME_AVAILABLE:
                mode = 'pygame'
            elif WEB_AVAILABLE:
                mode = 'web'
            else:
                raise ImportError(
                    "No visualization backend available. "
                    "Install pygame: pip install pygame OR "
                    "Install web renderer: pip install fastapi uvicorn websockets"
                )

        # Create renderer
        if mode == 'pygame':
            if not PYGAME_AVAILABLE:
                raise ImportError("pygame not available. Install with: pip install pygame")
            self.renderer = PygameRenderer(
                env, width=width, height=height, fps=fps, title=title, **kwargs
            )
        elif mode == 'web':
            if not WEB_AVAILABLE:
                raise ImportError("Web renderer not available. Install with: pip install fastapi uvicorn websockets")
            port = kwargs.pop('port', 8000)
            update_rate = kwargs.pop('update_rate', fps)
            self.renderer = WebRenderer(
                env, port=port, canvas_width=width, canvas_height=height,
                update_rate=update_rate, title=title, **kwargs
            )
        else:
            raise ValueError(f"Unknown renderer mode: {mode}")

    def start(self):
        """Start the visualization."""
        if self.renderer:
            self.renderer.start()
            print(f"Visualization started ({self.mode} mode)")

    def stop(self):
        """Stop the visualization."""
        if self.renderer:
            self.renderer.stop()
            print("Visualization stopped")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def visualize(
    env,
    mode: Literal['pygame', 'web', 'auto'] = 'auto',
    width: int = 800,
    height: int = 600,
    fps: int = 30,
    **kwargs
):
    """
    Quick helper to start visualization.

    Args:
        env: Simulation environment
        mode: Renderer type
        width: Display width
        height: Display height
        fps: Frame rate
        **kwargs: Additional renderer options

    Returns:
        Visualizer instance (already started)
    """
    viz = Visualizer(env, mode=mode, width=width, height=height, fps=fps, **kwargs)
    viz.start()
    return viz
