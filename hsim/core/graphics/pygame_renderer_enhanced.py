"""
Enhanced Pygame Renderer for hsim Simulations

Advanced real-time visualization with trails, minimap, agent selection,
connection lines, performance stats, and more.
"""

import threading
from typing import Optional, Tuple, List, Dict, Any, Set
from collections import OrderedDict
import time
import math

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from hsim.core.graphics import GraphicsMixin, Shape
from hsim.core.graphics.simulation_controller import SimulationController, SimulationState


class PygameRendererEnhanced:
    """
    Enhanced Pygame renderer with advanced features.

    Features:
    - Agent trails/paths
    - FPS counter and performance stats
    - Agent selection and info display
    - Connection lines between agents
    - Minimap for navigation
    - Configurable visual layers
    - Screenshot capability
    - Smooth zoom and pan
    - Agent highlighting on hover

    Args:
        env: Simulation environment
        width: Window width in pixels
        height: Window height in pixels
        fps: Target frames per second
        title: Window title
        show_trails: Show agent movement trails
        show_connections: Show connection lines between agents
        show_minimap: Show minimap overview
        show_stats: Show FPS and stats
        show_grid: Display grid lines
        show_labels: Show agent labels
        show_states: Show FSM states
    """

    def __init__(
        self,
        env,
        controller: Optional[SimulationController] = None,
        width: int = 1200,
        height: int = 800,
        fps: int = 60,
        title: str = "hsim Simulation (Enhanced)",
        background_color: Tuple[int, int, int] = (245, 245, 250),
        show_trails: bool = True,
        show_connections: bool = True,
        show_minimap: bool = True,
        show_stats: bool = True,
        show_grid: bool = True,
        show_labels: bool = True,
        show_states: bool = True,
        show_controls: bool = True,
        grid_spacing: int = 50
    ):
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required. Install with: pip install pygame")

        self.env = env
        self.controller = controller
        self.width = width
        self.height = height
        self.fps = fps
        self.title = title
        self.background_color = background_color

        # Layer toggles
        self.show_trails = show_trails
        self.show_connections = show_connections
        self.show_minimap = show_minimap
        self.show_stats = show_stats
        self.show_grid = show_grid
        self.show_labels = show_labels
        self.show_states = show_states
        self.show_controls = show_controls
        self.grid_spacing = grid_spacing

        # Rendering state
        self.running = False
        self.screen = None
        self.clock = None
        self.font = None
        self.font_small = None
        self.font_large = None
        self.thread = None

        # Camera/viewport
        self.camera_offset = [0, 0]
        self.zoom = 1.0
        self.zoom_target = 1.0
        self.zoom_smooth = 0.15

        # Selection
        self.selected_agent = None
        self.hovered_agent = None

        # Performance tracking
        self.frame_times = []
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.current_fps = 0

        # Agent count cache
        self.agent_count = 0

    def start(self):
        """Start the renderer in a separate thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._render_loop, daemon=True)
        self.thread.start()
        print(f"Enhanced Pygame renderer started ({self.width}x{self.height} @ {self.fps} FPS)")

    def stop(self):
        """Stop the renderer and close the window."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def _init_pygame(self):
        """Initialize Pygame components."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)
        self.font_large = pygame.font.Font(None, 36)

    def _render_loop(self):
        """Main rendering loop."""
        self._init_pygame()

        while self.running:
            frame_start = time.time()

            # Handle events
            self._handle_events()

            # Smooth zoom
            self.zoom += (self.zoom_target - self.zoom) * self.zoom_smooth

            # Clear screen
            self.screen.fill(self.background_color)

            # Draw layers (back to front)
            if self.show_grid:
                self._draw_grid()

            if self.show_connections:
                self._draw_connections()

            if self.show_trails:
                self._draw_trails()

            self._draw_agents()

            if self.show_minimap:
                self._draw_minimap()

            if self.show_stats:
                self._draw_stats()

            self._draw_selected_agent_info()
            self._draw_controls()

            # Draw pause overlay if paused
            if self.controller and self.controller.is_paused:
                self._draw_pause_overlay()

            # Update display
            pygame.display.flip()

            # Track performance
            frame_time = time.time() - frame_start
            self.frame_times.append(frame_time)
            if len(self.frame_times) > 60:
                self.frame_times.pop(0)

            self.frame_count += 1
            if time.time() - self.last_fps_update >= 1.0:
                self.current_fps = self.frame_count
                self.frame_count = 0
                self.last_fps_update = time.time()

            self.clock.tick(self.fps)

        pygame.quit()

    def _handle_events(self):
        """Handle user input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keypress(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._handle_click(mouse_pos)
                elif event.button == 4:  # Scroll up
                    self.zoom_target = min(5.0, self.zoom_target * 1.1)
                elif event.button == 5:  # Scroll down
                    self.zoom_target = max(0.1, self.zoom_target / 1.1)

            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[2]:  # Right mouse drag
                    self.camera_offset[0] += event.rel[0]
                    self.camera_offset[1] += event.rel[1]

        # Update hovered agent
        self.hovered_agent = self._get_agent_at_pos(mouse_pos)

    def _handle_keypress(self, key):
        """Handle keyboard input."""
        # Simulation controls (if controller available)
        if self.controller:
            if key == pygame.K_SPACE:
                if self.controller.is_running:
                    self.controller.pause()
                else:
                    self.controller.play()
            elif key == pygame.K_PERIOD or key == pygame.K_RIGHT:
                self.controller.step(1)
            elif key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.controller.reset()
            elif key == pygame.K_1:
                self.controller.set_speed(0.5)
            elif key == pygame.K_2:
                self.controller.set_speed(1.0)
            elif key == pygame.K_3:
                self.controller.set_speed(2.0)
            elif key == pygame.K_4:
                self.controller.set_speed(5.0)

        # View controls
        if key == pygame.K_ESCAPE:
            if self.selected_agent:
                self.selected_agent = None
            else:
                self.running = False
        elif key == pygame.K_PLUS or key == pygame.K_EQUALS:
            self.zoom_target = min(5.0, self.zoom_target * 1.2)
        elif key == pygame.K_MINUS:
            self.zoom_target = max(0.1, self.zoom_target / 1.2)

        # Layer toggles
        elif key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif key == pygame.K_t:
            self.show_trails = not self.show_trails
        elif key == pygame.K_c:
            self.show_connections = not self.show_connections
        elif key == pygame.K_m:
            self.show_minimap = not self.show_minimap
        elif key == pygame.K_l:
            self.show_labels = not self.show_labels
        elif key == pygame.K_s:
            self.show_states = not self.show_states
        elif key == pygame.K_i:
            self.show_stats = not self.show_stats
        elif key == pygame.K_F12:
            self.screenshot()

    def _handle_click(self, pos):
        """Handle mouse click for agent selection."""
        agent = self._get_agent_at_pos(pos)
        if agent:
            self.selected_agent = agent
            if hasattr(agent, 'select'):
                # Deselect all
                for a in self.env._agents.values():
                    if hasattr(a, 'deselect'):
                        a.deselect()
                # Select clicked agent
                agent.select()
        else:
            self.selected_agent = None

    def _get_agent_at_pos(self, pos) -> Optional[Any]:
        """Get agent at screen position."""
        if not hasattr(self.env, '_agents'):
            return None

        # Check in reverse order (top to bottom)
        for agent in reversed(list(self.env._agents.values())):
            if not isinstance(agent, GraphicsMixin):
                continue
            if not hasattr(agent, '_graphics_initialized') or not agent._graphics_initialized:
                continue
            if not agent.visible:
                continue

            x = int((agent.x + self.camera_offset[0]) * self.zoom)
            y = int((agent.y + self.camera_offset[1]) * self.zoom)
            w = int(agent.width * self.zoom)
            h = int(agent.height * self.zoom)

            if agent.shape == Shape.CIRCLE:
                r = int(agent.radius * self.zoom)
                dist = math.sqrt((pos[0] - (x + r))**2 + (pos[1] - (y + r))**2)
                if dist <= r:
                    return agent
            else:
                if x <= pos[0] <= x + w and y <= pos[1] <= y + h:
                    return agent

        return None

    def _draw_grid(self):
        """Draw background grid."""
        grid_color = (220, 220, 225)
        spacing = int(self.grid_spacing * self.zoom)

        if spacing < 10:  # Don't draw if too small
            return

        # Vertical lines
        start_x = int(self.camera_offset[0] * self.zoom) % spacing
        for x in range(start_x, self.width, spacing):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, self.height), 1)

        # Horizontal lines
        start_y = int(self.camera_offset[1] * self.zoom) % spacing
        for y in range(start_y, self.height, spacing):
            pygame.draw.line(self.screen, grid_color, (0, y), (self.width, y), 1)

    def _draw_connections(self):
        """Draw connection lines between agents."""
        if not hasattr(self.env, '_agents'):
            return

        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin):
                continue
            if not hasattr(agent, 'connections'):
                continue
            if not agent.visible:
                continue

            x1 = int((agent.x + agent.width/2 + self.camera_offset[0]) * self.zoom)
            y1 = int((agent.y + agent.height/2 + self.camera_offset[1]) * self.zoom)

            for conn_agents in agent.connections.values():
                # Handle both single agent and iterable of agents
                if not hasattr(conn_agents, '__iter__'):
                    conn_agents = [conn_agents]

                for conn_agent in conn_agents:
                    if not isinstance(conn_agent, GraphicsMixin):
                        continue
                    if not conn_agent.visible:
                        continue

                    x2 = int((conn_agent.x + conn_agent.width/2 + self.camera_offset[0]) * self.zoom)
                    y2 = int((conn_agent.y + conn_agent.height/2 + self.camera_offset[1]) * self.zoom)

                    # Draw line
                    pygame.draw.line(self.screen, (150, 150, 160), (x1, y1), (x2, y2), 1)

    def _draw_trails(self):
        """Draw agent movement trails."""
        if not hasattr(self.env, '_agents'):
            return

        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin):
                continue
            if not hasattr(agent, 'trail_points') or not agent.trail_points:
                continue
            if not agent.visible:
                continue

            points = []
            for px, py, _ in agent.trail_points:
                x = int((px + self.camera_offset[0]) * self.zoom)
                y = int((py + self.camera_offset[1]) * self.zoom)
                points.append((x, y))

            if len(points) >= 2:
                # Draw trail with fading alpha
                trail_color = agent.trail_color if hasattr(agent, 'trail_color') else agent.color
                for i in range(len(points) - 1):
                    alpha = int(255 * (i + 1) / len(points))
                    color = (*trail_color, alpha)

                    # Create surface for alpha
                    if i < len(points) - 1:
                        start, end = points[i], points[i + 1]
                        pygame.draw.line(self.screen, trail_color[:3], start, end, 2)

    def _draw_agents(self):
        """Draw all agents."""
        if not hasattr(self.env, '_agents'):
            return

        self.agent_count = 0

        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin):
                continue
            if not hasattr(agent, '_graphics_initialized') or not agent._graphics_initialized:
                continue
            if not agent.visible:
                continue

            self.agent_count += 1

            x = int((agent.x + self.camera_offset[0]) * self.zoom)
            y = int((agent.y + self.camera_offset[1]) * self.zoom)
            w = int(agent.width * self.zoom)
            h = int(agent.height * self.zoom)

            # Determine colors
            color = agent.color
            border_color = agent.border_color if hasattr(agent, 'border_color') else (0, 0, 0)
            border_width = int(agent.border_width * self.zoom) if hasattr(agent, 'border_width') else max(1, int(2 * self.zoom))

            # Highlight if selected or hovered
            if agent == self.selected_agent or agent == self.hovered_agent:
                border_color = (255, 200, 0)
                border_width = max(3, int(4 * self.zoom))

            # Draw shape
            self._draw_shape(agent.shape, x, y, w, h, color, border_color, border_width)

            # Draw label
            if self.show_labels and agent.label and self.zoom > 0.5:
                label_surface = self.font_small.render(agent.label, True, (0, 0, 0))
                self.screen.blit(label_surface, (x + 2, y + h + 2))

            # Draw state
            if self.show_states and self.zoom > 0.5:
                if hasattr(agent, 'stateMachine') and hasattr(agent.stateMachine, 'current_state'):
                    if agent.stateMachine.current_state:
                        state_text = f"[{agent.stateMachine.current_state.name}]"
                        state_surface = self.font_small.render(state_text, True, (80, 80, 80))
                        self.screen.blit(state_surface, (x + 2, y - 16))

    def _draw_shape(self, shape, x, y, w, h, color, border_color, border_width):
        """Draw a shape."""
        if shape == Shape.RECTANGLE:
            pygame.draw.rect(self.screen, color, (x, y, w, h))
            pygame.draw.rect(self.screen, border_color, (x, y, w, h), border_width)

        elif shape == Shape.CIRCLE:
            r = int(w / 2)
            pygame.draw.circle(self.screen, color, (x + r, y + r), r)
            pygame.draw.circle(self.screen, border_color, (x + r, y + r), r, border_width)

        elif shape == Shape.TRIANGLE:
            points = [(x + w // 2, y), (x, y + h), (x + w, y + h)]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, border_color, points, border_width)

        elif shape == Shape.DIAMOND:
            points = [(x + w // 2, y), (x + w, y + h // 2), (x + w // 2, y + h), (x, y + h // 2)]
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, border_color, points, border_width)

        elif shape == Shape.HEXAGON:
            cx, cy = x + w // 2, y + h // 2
            r = min(w, h) // 2
            points = []
            for i in range(6):
                angle = math.pi / 3 * i
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, border_color, points, border_width)

        elif shape == Shape.STAR:
            cx, cy = x + w // 2, y + h // 2
            r_outer = min(w, h) // 2
            r_inner = r_outer // 2
            points = []
            for i in range(10):
                r = r_outer if i % 2 == 0 else r_inner
                angle = math.pi / 5 * i - math.pi / 2
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, border_color, points, border_width)

    def _draw_minimap(self):
        """Draw minimap overview."""
        map_size = 150
        map_margin = 10
        map_x = self.width - map_size - map_margin
        map_y = map_margin

        # Background
        pygame.draw.rect(self.screen, (255, 255, 255, 200), (map_x, map_y, map_size, map_size))
        pygame.draw.rect(self.screen, (100, 100, 100), (map_x, map_y, map_size, map_size), 2)

        if not hasattr(self.env, '_agents') or not self.env._agents:
            return

        # Find bounds
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')

        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin) or not hasattr(agent, '_graphics_initialized'):
                continue
            min_x = min(min_x, agent.x)
            min_y = min(min_y, agent.y)
            max_x = max(max_x, agent.x + agent.width)
            max_y = max(max_y, agent.y + agent.height)

        if min_x == float('inf'):
            return

        # Add padding
        padding = 50
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        world_w = max_x - min_x
        world_h = max_y - min_y
        scale = min((map_size - 4) / world_w, (map_size - 4) / world_h)

        # Draw agents on minimap
        for agent in self.env._agents.values():
            if not isinstance(agent, GraphicsMixin) or not agent.visible:
                continue

            mx = map_x + 2 + int((agent.x - min_x) * scale)
            my = map_y + 2 + int((agent.y - min_y) * scale)
            ms = max(2, int(3 * scale))

            pygame.draw.circle(self.screen, agent.color, (mx, my), ms)

    def _draw_stats(self):
        """Draw performance stats."""
        y_offset = 10
        stats = [
            f"FPS: {self.current_fps}",
            f"Time: {self.env.now:.2f}",
            f"Agents: {self.agent_count}",
            f"Zoom: {self.zoom:.2f}x",
        ]

        # Add controller stats if available
        if self.controller:
            status = self.controller.get_status()
            state_emoji = {
                'running': '▶️',
                'paused': '⏸️',
                'stopped': '⏹️',
                'stepping': '⏭️',
            }
            emoji = state_emoji.get(status['state'], '')
            stats.insert(1, f"{emoji} {status['state'].upper()}")
            stats.insert(3, f"Speed: {status['speed']:.1f}x")

        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            stats.append(f"Frame: {avg_frame_time*1000:.1f}ms")

        for stat in stats:
            text = self.font_small.render(stat, True, (60, 60, 60))
            bg_rect = text.get_rect()
            bg_rect.topleft = (10, y_offset)
            bg_rect.inflate_ip(8, 4)
            pygame.draw.rect(self.screen, (255, 255, 255, 200), bg_rect)
            self.screen.blit(text, (10, y_offset))
            y_offset += 20

    def _draw_selected_agent_info(self):
        """Draw info panel for selected agent."""
        if not self.selected_agent:
            return

        agent = self.selected_agent
        panel_width = 250
        panel_x = self.width - panel_width - 10
        panel_y = 180

        # Background
        pygame.draw.rect(self.screen, (255, 255, 255, 230), (panel_x, panel_y, panel_width, 200))
        pygame.draw.rect(self.screen, (100, 100, 100), (panel_x, panel_y, panel_width, 200), 2)

        # Agent info
        y_offset = panel_y + 10
        info = [
            f"Selected: {agent.label or 'Agent'}",
            f"Position: ({agent.x:.1f}, {agent.y:.1f})",
            f"Color: RGB{agent.color}",
            f"Shape: {agent.shape.value}",
        ]

        if hasattr(agent, 'stateMachine') and agent.stateMachine.current_state:
            info.append(f"State: {agent.stateMachine.current_state.name}")

        if hasattr(agent, 'connections'):
            info.append(f"Connections: {sum(1 if not hasattr(c, '__iter__') else len(c) for c in agent.connections.values())}")

        for line in info:
            text = self.font_small.render(line, True, (0, 0, 0))
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 20

    def _draw_controls(self):
        """Draw control instructions."""
        if self.controller:
            controls = [
                "SPACE: Play/Pause | →: Step | Ctrl+R: Reset",
                "1-4: Speed (0.5x, 1x, 2x, 5x) | ESC: Quit",
                "G: Grid | T: Trails | C: Connections | M: Minimap",
                "L: Labels | S: States | I: Stats | F12: Screenshot",
                "Right-drag: Pan | Scroll: Zoom | Click: Select"
            ]
        else:
            controls = [
                "SPACE: Pause | ESC: Deselect/Quit | +/-: Zoom",
                "G: Grid | T: Trails | C: Connections | M: Minimap",
                "L: Labels | S: States | I: Stats | F12: Screenshot",
                "Right-drag: Pan | Scroll: Zoom | Click: Select"
            ]

        y_offset = self.height - (len(controls) * 18 + 10)
        for control in controls:
            text = self.font_small.render(control, True, (100, 100, 100))
            self.screen.blit(text, (10, y_offset))
            y_offset += 18

    def _draw_pause_overlay(self):
        """Draw pause overlay in center of screen."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Pause text
        pause_text = self.font_large.render("⏸ PAUSED", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(self.width // 2, self.height // 2))

        # Background for text
        bg_rect = text_rect.inflate(40, 20)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 3, border_radius=10)

        self.screen.blit(pause_text, text_rect)

        # Instructions
        instruction = self.font_small.render("Press SPACE to resume | → to step", True, (200, 200, 200))
        inst_rect = instruction.get_rect(center=(self.width // 2, self.height // 2 + 40))
        self.screen.blit(instruction, inst_rect)

    def screenshot(self, filename: Optional[str] = None):
        """Save a screenshot."""
        if not self.screen:
            return

        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"hsim_screenshot_{timestamp}.png"

        pygame.image.save(self.screen, filename)
        print(f"Screenshot saved: {filename}")
