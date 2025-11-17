"""
Pygame Renderer for hsim Simulations

Provides real-time visualization using Pygame for desktop applications.
Renders agents with their graphics properties in a window.
"""

import threading
from typing import Optional, Tuple, List, Dict, Any
from collections import OrderedDict
import time

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not installed. Install with: pip install pygame")

from hsim.core.graphics import GraphicsMixin, Shape


class PygameRenderer:
    """
    Real-time Pygame renderer for simulations.

    Runs in a separate thread to avoid blocking the simulation.
    Updates the display at a specified FPS while the simulation runs.

    Args:
        env: Simulation environment
        width: Window width in pixels
        height: Window height in pixels
        fps: Target frames per second
        title: Window title
        background_color: RGB background color
        show_time: Display simulation time
        show_grid: Display grid lines
    """

    def __init__(
        self,
        env,
        width: int = 800,
        height: int = 600,
        fps: int = 30,
        title: str = "hsim Simulation",
        background_color: Tuple[int, int, int] = (240, 240, 240),
        show_time: bool = True,
        show_grid: bool = True,
        grid_spacing: int = 50
    ):
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required for PygameRenderer. Install with: pip install pygame")

        self.env = env
        self.width = width
        self.height = height
        self.fps = fps
        self.title = title
        self.background_color = background_color
        self.show_time = show_time
        self.show_grid = show_grid
        self.grid_spacing = grid_spacing

        # Rendering state
        self.running = False
        self.paused = False
        self.screen = None
        self.clock = None
        self.font = None
        self.thread = None

        # Camera/viewport
        self.camera_offset = [0, 0]
        self.zoom = 1.0

    def start(self):
        """Start the renderer in a separate thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._render_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the renderer and close the window."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def _init_pygame(self):
        """Initialize Pygame components."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

    def _render_loop(self):
        """Main rendering loop (runs in separate thread)."""
        self._init_pygame()

        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.zoom *= 1.1
                    elif event.key == pygame.K_MINUS:
                        self.zoom /= 1.1

            # Clear screen
            self.screen.fill(self.background_color)

            # Draw grid
            if self.show_grid:
                self._draw_grid()

            # Draw agents
            self._draw_agents()

            # Draw UI overlay
            if self.show_time:
                self._draw_time()

            # Draw instructions
            self._draw_instructions()

            # Update display
            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()

    def _draw_grid(self):
        """Draw background grid."""
        grid_color = (200, 200, 200)
        spacing = int(self.grid_spacing * self.zoom)

        # Vertical lines
        for x in range(0, self.width, spacing):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height), 1)

        # Horizontal lines
        for y in range(0, self.height, spacing):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y), 1)

    def _draw_agents(self):
        """Draw all agents with graphics properties."""
        if not hasattr(self.env, '_agents'):
            return

        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin):
                continue

            if not hasattr(agent, '_graphics_initialized') or not agent._graphics_initialized:
                continue

            if not agent.visible:
                continue

            # Transform coordinates
            x = int((agent.x + self.camera_offset[0]) * self.zoom)
            y = int((agent.y + self.camera_offset[1]) * self.zoom)
            w = int(agent.width * self.zoom)
            h = int(agent.height * self.zoom)

            # Draw based on shape
            if agent.shape == Shape.RECTANGLE:
                pygame.draw.rect(self.screen, agent.color, (x, y, w, h))
                pygame.draw.rect(self.screen, (0, 0, 0), (x, y, w, h), 1)  # Border

            elif agent.shape == Shape.CIRCLE:
                r = int(agent.radius * self.zoom)
                pygame.draw.circle(self.screen, agent.color, (x + r, y + r), r)
                pygame.draw.circle(self.screen, (0, 0, 0), (x + r, y + r), r, 1)  # Border

            elif agent.shape == Shape.TRIANGLE:
                points = [
                    (x + w // 2, y),
                    (x, y + h),
                    (x + w, y + h)
                ]
                pygame.draw.polygon(self.screen, agent.color, points)
                pygame.draw.polygon(self.screen, (0, 0, 0), points, 1)  # Border

            elif agent.shape == Shape.DIAMOND:
                points = [
                    (x + w // 2, y),
                    (x + w, y + h // 2),
                    (x + w // 2, y + h),
                    (x, y + h // 2)
                ]
                pygame.draw.polygon(self.screen, agent.color, points)
                pygame.draw.polygon(self.screen, (0, 0, 0), points, 1)  # Border

            # Draw label
            if agent.label:
                label_surface = self.font.render(agent.label, True, (0, 0, 0))
                self.screen.blit(label_surface, (x + 2, y + h + 2))

            # Draw state if available
            if hasattr(agent, 'stateMachine') and hasattr(agent.stateMachine, 'current_state'):
                if agent.stateMachine.current_state:
                    state_text = f"[{agent.stateMachine.current_state.name}]"
                    state_surface = self.font.render(state_text, True, (100, 100, 100))
                    self.screen.blit(state_surface, (x + 2, y - 20))

    def _draw_time(self):
        """Draw simulation time."""
        time_text = f"Time: {self.env.now:.2f}"
        time_surface = self.font.render(time_text, True, (0, 0, 0))
        self.screen.blit(time_surface, (10, 10))

    def _draw_instructions(self):
        """Draw control instructions."""
        instructions = [
            "SPACE: Pause",
            "+/-: Zoom",
            "ESC: Quit"
        ]
        y_offset = self.height - 80
        for instruction in instructions:
            text_surface = self.font.render(instruction, True, (100, 100, 100))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25

    def screenshot(self, filename: str = "screenshot.png"):
        """Save a screenshot of the current view."""
        if self.screen:
            pygame.image.save(self.screen, filename)
            print(f"Screenshot saved to {filename}")


class PygameRendererSync:
    """
    Synchronous Pygame renderer (blocking).

    Use this version if you want to manually control rendering
    or integrate with the simulation loop directly.
    """

    def __init__(
        self,
        env,
        width: int = 800,
        height: int = 600,
        title: str = "hsim Simulation",
        background_color: Tuple[int, int, int] = (240, 240, 240)
    ):
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required. Install with: pip install pygame")

        self.env = env
        self.width = width
        self.height = height
        self.title = title
        self.background_color = background_color

        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.font = pygame.font.Font(None, 24)

    def render(self):
        """Render one frame (call this from your simulation loop)."""
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        # Clear and draw
        self.screen.fill(self.background_color)
        self._draw_agents()
        self._draw_time()
        pygame.display.flip()

        return True

    def _draw_agents(self):
        """Draw all agents."""
        if not hasattr(self.env, '_agents'):
            return

        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin) or not hasattr(agent, '_graphics_initialized'):
                continue
            if not agent._graphics_initialized or not agent.visible:
                continue

            x, y = int(agent.x), int(agent.y)
            w, h = int(agent.width), int(agent.height)

            if agent.shape == Shape.RECTANGLE:
                pygame.draw.rect(self.screen, agent.color, (x, y, w, h))
                pygame.draw.rect(self.screen, (0, 0, 0), (x, y, w, h), 1)

            elif agent.shape == Shape.CIRCLE:
                r = int(agent.radius)
                pygame.draw.circle(self.screen, agent.color, (x + r, y + r), r)
                pygame.draw.circle(self.screen, (0, 0, 0), (x + r, y + r), r, 1)

            if agent.label:
                label_surface = self.font.render(agent.label, True, (0, 0, 0))
                self.screen.blit(label_surface, (x + 2, y + h + 2))

    def _draw_time(self):
        """Draw simulation time."""
        time_text = f"Time: {self.env.now:.2f}"
        time_surface = self.font.render(time_text, True, (0, 0, 0))
        self.screen.blit(time_surface, (10, 10))

    def close(self):
        """Close the renderer."""
        pygame.quit()
