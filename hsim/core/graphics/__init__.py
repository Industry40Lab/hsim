"""
Graphics Module for hsim

Provides visualization capabilities for discrete event simulations.
"""

from .graphics_mixin import GraphicsMixin, Shape

# Import renderers with optional dependencies
try:
    from .pygame_renderer import PygameRenderer, PygameRendererSync, PYGAME_AVAILABLE
except ImportError:
    PYGAME_AVAILABLE = False
    PygameRenderer = None
    PygameRendererSync = None

try:
    from .web_renderer import WebRenderer, FASTAPI_AVAILABLE as WEB_AVAILABLE
except ImportError:
    WEB_AVAILABLE = False
    WebRenderer = None

from .visualizer import Visualizer, visualize

__all__ = [
    'GraphicsMixin',
    'Shape',
    'PygameRenderer',
    'PygameRendererSync',
    'WebRenderer',
    'Visualizer',
    'visualize',
    'PYGAME_AVAILABLE',
    'WEB_AVAILABLE'
]
