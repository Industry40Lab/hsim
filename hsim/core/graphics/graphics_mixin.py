"""
Graphics Mixin for Agents

Provides visual properties (position, dimensions, color, shape) for agents
that need to be visualized in simulations.

Usage:
    class Agent(GraphicsMixin, ABC):
        def __init__(self, env, name="", **kwargs):
            super().__init__(env, name)
            self.init_graphics(**kwargs)
"""

from typing import Tuple, Dict, Any, Optional
from enum import Enum


class Shape(Enum):
    """Visual shape types for agents"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    CUSTOM = "custom"


class GraphicsMixin:
    """
    Mixin class that adds visual properties to agents.

    Attributes:
        position: (x, y) coordinates in simulation space
        dimensions: (width, height) for rectangles or (radius,) for circles
        color: RGB tuple (0-255) or hex string
        shape: Visual shape type
        rotation: Rotation angle in degrees (0-360)
        visible: Whether the agent should be rendered
        label: Optional text label to display
        custom_properties: Dictionary for renderer-specific properties
    """

    def __init__(self):
        """Initialize with default graphics properties."""
        self._graphics_initialized = False

    def init_graphics(
        self,
        position: Tuple[float, float] = (0, 0),
        dimensions: Tuple[float, ...] = (20, 20),
        color: Tuple[int, int, int] = (100, 100, 255),
        shape: Shape = Shape.RECTANGLE,
        rotation: float = 0.0,
        visible: bool = True,
        label: Optional[str] = None,
        **custom_properties: Any
    ):
        """
        Initialize graphics properties.

        Args:
            position: (x, y) coordinates
            dimensions: Size tuple (width, height) or (radius,)
            color: RGB tuple (0-255 each)
            shape: Visual shape type
            rotation: Rotation in degrees
            visible: Visibility flag
            label: Optional text label
            **custom_properties: Additional renderer-specific properties
        """
        self.position = list(position)  # Mutable for updates
        self.dimensions = dimensions
        self.color = color
        self.shape = shape
        self.rotation = rotation
        self.visible = visible
        self.label = label if label is not None else getattr(self, 'name', '')
        self.custom_properties = custom_properties
        self._graphics_initialized = True

    @property
    def x(self) -> float:
        """Get x coordinate."""
        return self.position[0] if hasattr(self, 'position') else 0

    @x.setter
    def x(self, value: float):
        """Set x coordinate."""
        if hasattr(self, 'position'):
            self.position[0] = value

    @property
    def y(self) -> float:
        """Get y coordinate."""
        return self.position[1] if hasattr(self, 'position') else 0

    @y.setter
    def y(self, value: float):
        """Set y coordinate."""
        if hasattr(self, 'position'):
            self.position[1] = value

    @property
    def width(self) -> float:
        """Get width."""
        return self.dimensions[0] if hasattr(self, 'dimensions') else 0

    @property
    def height(self) -> float:
        """Get height."""
        return self.dimensions[1] if hasattr(self, 'dimensions') and len(self.dimensions) > 1 else self.width

    @property
    def radius(self) -> float:
        """Get radius (for circular shapes)."""
        return self.dimensions[0] if hasattr(self, 'dimensions') else 0

    def move_to(self, x: float, y: float):
        """Move to absolute position."""
        if hasattr(self, 'position'):
            self.position[0] = x
            self.position[1] = y

    def move_by(self, dx: float, dy: float):
        """Move by relative offset."""
        if hasattr(self, 'position'):
            self.position[0] += dx
            self.position[1] += dy

    def set_color(self, color: Tuple[int, int, int]):
        """Set RGB color."""
        self.color = color

    def hide(self):
        """Hide the agent from rendering."""
        if hasattr(self, 'visible'):
            self.visible = False

    def show(self):
        """Show the agent in rendering."""
        if hasattr(self, 'visible'):
            self.visible = True

    def get_graphics_dict(self) -> Dict[str, Any]:
        """
        Get all graphics properties as a dictionary.

        Returns:
            Dictionary containing all visual properties
        """
        if not hasattr(self, '_graphics_initialized') or not self._graphics_initialized:
            return {}

        return {
            'position': self.position,
            'dimensions': self.dimensions,
            'color': self.color,
            'shape': self.shape.value if isinstance(self.shape, Shape) else self.shape,
            'rotation': self.rotation,
            'visible': self.visible,
            'label': self.label,
            'custom_properties': self.custom_properties
        }
