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

from typing import Tuple, Dict, Any, Optional, List, Deque
from enum import Enum
from collections import deque
import time


class Shape(Enum):
    """Visual shape types for agents"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    STAR = "star"
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
        trail_length: int = 0,
        trail_color: Optional[Tuple[int, int, int]] = None,
        border_color: Optional[Tuple[int, int, int]] = None,
        border_width: int = 1,
        opacity: float = 1.0,
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
            trail_length: Number of trail points to keep (0 = no trail)
            trail_color: Color for trail (None = use agent color)
            border_color: Border color (None = black)
            border_width: Border width in pixels
            opacity: Opacity (0.0-1.0)
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

        # Trail tracking
        self.trail_length = trail_length
        self.trail_color = trail_color if trail_color else color
        self.trail_points: Deque[Tuple[float, float, float]] = deque(maxlen=trail_length if trail_length > 0 else None)

        # Enhanced visual properties
        self.border_color = border_color if border_color else (0, 0, 0)
        self.border_width = border_width
        self.opacity = opacity

        # Animation state
        self._last_position = list(position)
        self._velocity = [0.0, 0.0]

        # Selection state
        self.selected = False
        self.highlighted = False

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

    def move_to(self, x: float, y: float, record_trail: bool = True):
        """
        Move to absolute position.

        Args:
            x: Target x coordinate
            y: Target y coordinate
            record_trail: Whether to record this position in the trail
        """
        if hasattr(self, 'position'):
            # Record trail if enabled
            if record_trail and hasattr(self, 'trail_points') and self.trail_length > 0:
                current_time = time.time()
                self.trail_points.append((self.position[0], self.position[1], current_time))

            # Update velocity for animation
            if hasattr(self, '_last_position'):
                self._velocity[0] = x - self.position[0]
                self._velocity[1] = y - self.position[1]
                self._last_position = list(self.position)

            self.position[0] = x
            self.position[1] = y

    def move_by(self, dx: float, dy: float, record_trail: bool = True):
        """
        Move by relative offset.

        Args:
            dx: Change in x
            dy: Change in y
            record_trail: Whether to record this position in the trail
        """
        if hasattr(self, 'position'):
            self.move_to(self.position[0] + dx, self.position[1] + dy, record_trail)

    def set_color(self, color: Tuple[int, int, int]):
        """Set RGB color."""
        self.color = color

    def set_trail_color(self, color: Tuple[int, int, int]):
        """Set trail color."""
        if hasattr(self, 'trail_color'):
            self.trail_color = color

    def clear_trail(self):
        """Clear the trail history."""
        if hasattr(self, 'trail_points'):
            self.trail_points.clear()

    def enable_trail(self, length: int = 50):
        """
        Enable trail tracking.

        Args:
            length: Maximum number of trail points
        """
        self.trail_length = length
        if not hasattr(self, 'trail_points'):
            self.trail_points = deque(maxlen=length)
        else:
            self.trail_points = deque(self.trail_points, maxlen=length)

    def disable_trail(self):
        """Disable trail tracking."""
        self.trail_length = 0
        if hasattr(self, 'trail_points'):
            self.trail_points.clear()

    def hide(self):
        """Hide the agent from rendering."""
        if hasattr(self, 'visible'):
            self.visible = False

    def show(self):
        """Show the agent in rendering."""
        if hasattr(self, 'visible'):
            self.visible = True

    def select(self):
        """Mark agent as selected."""
        if hasattr(self, 'selected'):
            self.selected = True

    def deselect(self):
        """Mark agent as not selected."""
        if hasattr(self, 'selected'):
            self.selected = False

    def highlight(self):
        """Highlight the agent."""
        if hasattr(self, 'highlighted'):
            self.highlighted = True

    def unhighlight(self):
        """Remove highlight from agent."""
        if hasattr(self, 'highlighted'):
            self.highlighted = False

    def get_graphics_dict(self) -> Dict[str, Any]:
        """
        Get all graphics properties as a dictionary.

        Returns:
            Dictionary containing all visual properties
        """
        if not hasattr(self, '_graphics_initialized') or not self._graphics_initialized:
            return {}

        data = {
            'position': self.position,
            'dimensions': self.dimensions,
            'color': self.color,
            'shape': self.shape.value if isinstance(self.shape, Shape) else self.shape,
            'rotation': self.rotation,
            'visible': self.visible,
            'label': self.label,
            'custom_properties': self.custom_properties
        }

        # Add optional properties if they exist
        if hasattr(self, 'trail_points') and self.trail_length > 0:
            data['trail'] = list(self.trail_points)
            data['trail_color'] = self.trail_color

        if hasattr(self, 'border_color'):
            data['border_color'] = self.border_color
            data['border_width'] = self.border_width

        if hasattr(self, 'opacity'):
            data['opacity'] = self.opacity

        if hasattr(self, 'selected'):
            data['selected'] = self.selected

        if hasattr(self, 'highlighted'):
            data['highlighted'] = self.highlighted

        return data
