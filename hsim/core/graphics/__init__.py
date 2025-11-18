"""
Graphics Module for hsim

Provides visualization capabilities for discrete event simulations.
"""

from .graphics_mixin import GraphicsMixin, Shape
from .simulation_controller import SimulationController, SimulationState, SimulationCommand

# Import renderers with optional dependencies
try:
    from .pygame_renderer import PygameRenderer, PygameRendererSync, PYGAME_AVAILABLE
    from .pygame_renderer_enhanced import PygameRendererEnhanced
except ImportError:
    PYGAME_AVAILABLE = False
    PygameRenderer = None
    PygameRendererSync = None
    PygameRendererEnhanced = None

try:
    from .web_renderer import WebRenderer, FASTAPI_AVAILABLE as WEB_AVAILABLE
    from .web_renderer_enhanced import WebRendererEnhanced
except ImportError:
    WEB_AVAILABLE = False
    WebRenderer = None
    WebRendererEnhanced = None

from .visualizer import Visualizer, visualize

__all__ = [
    'GraphicsMixin',
    'Shape',
    'SimulationController',
    'SimulationState',
    'SimulationCommand',
    'PygameRenderer',
    'PygameRendererSync',
    'PygameRendererEnhanced',
    'WebRenderer',
    'WebRendererEnhanced',
    'Visualizer',
    'visualize',
    'PYGAME_AVAILABLE',
    'WEB_AVAILABLE'
]
