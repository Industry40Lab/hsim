"""
Enhanced Web-based Renderer for hsim Simulations

Modern browser-based visualization with WebSocket streaming,
interactive controls, agent trails, selection, and real-time stats.
"""

import asyncio
import json
import threading
from typing import Optional, Set, Dict, Any
from pathlib import Path
import time

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    WebSocket = object
    WebSocketDisconnect = Exception

from hsim.core.graphics import GraphicsMixin, Shape


class WebRendererEnhanced:
    """
    Enhanced web-based renderer with advanced features.

    Features:
    - Real-time WebSocket updates
    - Interactive controls (play/pause/step/speed)
    - Agent selection and info panel
    - Movement trails
    - Connection lines
    - Performance stats
    - Smooth zoom and pan
    - Beautiful modern UI

    Args:
        env: Simulation environment
        port: Server port
        host: Server host
        update_rate: Updates per second
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
        title: Page title
    """

    def __init__(
        self,
        env,
        port: int = 8000,
        host: str = "localhost",
        update_rate: int = 30,
        canvas_width: int = 1200,
        canvas_height: int = 800,
        title: str = "hsim Simulation (Enhanced)"
    ):
        if not FASTAPI_AVAILABLE:
            raise ImportError("fastapi and uvicorn required. Install with: pip install fastapi uvicorn websockets")

        self.env = env
        self.port = port
        self.host = host
        self.update_rate = update_rate
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.title = title

        # WebSocket connections
        self.active_connections: Set[WebSocket] = set()

        # Server state
        self.app = None
        self.server_thread = None
        self.running = False

        # Performance tracking
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.current_fps = 0

        self._setup_app()

    def _setup_app(self):
        """Set up FastAPI application."""
        self.app = FastAPI(title=self.title)

        @self.app.get("/", response_class=HTMLResponse)
        async def get_viewer():
            return self._get_html()

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.add(websocket)
            try:
                # Send initial state
                await self._send_state(websocket)

                # Handle messages
                while True:
                    data = await websocket.receive_text()
                    await self._handle_client_message(websocket, data)

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

    def start(self):
        """Start the web server."""
        if self.running:
            return

        self.running = True

        # Start server thread
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        # Start update loop
        threading.Thread(target=self._update_loop, daemon=True).start()

        print(f"Enhanced web renderer started at http://{self.host}:{self.port}")
        print("Open the URL in your browser to view the simulation")

    def stop(self):
        """Stop the web server."""
        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=2.0)

    def _run_server(self):
        """Run the FastAPI server."""
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="warning")

    def _update_loop(self):
        """Periodically send updates to clients."""
        update_interval = 1.0 / self.update_rate

        while self.running:
            if self.active_connections:
                state = self._get_simulation_state()
                self._broadcast(state)

                # Update FPS counter
                self.frame_count += 1
                if time.time() - self.last_fps_update >= 1.0:
                    self.current_fps = self.frame_count
                    self.frame_count = 0
                    self.last_fps_update = time.time()

            time.sleep(update_interval)

    def _get_simulation_state(self) -> Dict[str, Any]:
        """Get current simulation state."""
        agents_data = []

        if hasattr(self.env, '_agents'):
            for name, agent in self.env._agents.items():
                if not isinstance(agent, GraphicsMixin):
                    continue
                if not hasattr(agent, '_graphics_initialized') or not agent._graphics_initialized:
                    continue
                if not agent.visible:
                    continue

                agent_data = {
                    'name': str(name),
                    'position': agent.position,
                    'dimensions': agent.dimensions,
                    'color': agent.color,
                    'shape': agent.shape.value if isinstance(agent.shape, Shape) else agent.shape,
                    'rotation': agent.rotation,
                    'label': agent.label,
                }

                # Add optional properties
                if hasattr(agent, 'border_color'):
                    agent_data['borderColor'] = agent.border_color
                if hasattr(agent, 'border_width'):
                    agent_data['borderWidth'] = agent.border_width
                if hasattr(agent, 'selected') and agent.selected:
                    agent_data['selected'] = True

                # Add trail
                if hasattr(agent, 'trail_points') and agent.trail_length > 0:
                    agent_data['trail'] = [[x, y] for x, y, _ in agent.trail_points]
                    if hasattr(agent, 'trail_color'):
                        agent_data['trailColor'] = agent.trail_color

                # Add connections
                if hasattr(agent, 'connections'):
                    connections = []
                    for conn_agents in agent.connections.values():
                        if not hasattr(conn_agents, '__iter__'):
                            conn_agents = [conn_agents]
                        for conn_agent in conn_agents:
                            if isinstance(conn_agent, GraphicsMixin):
                                connections.append(str(conn_agent.name if hasattr(conn_agent, 'name') else id(conn_agent)))
                    agent_data['connections'] = connections

                # Add state
                if hasattr(agent, 'stateMachine') and hasattr(agent.stateMachine, 'current_state'):
                    if agent.stateMachine.current_state:
                        agent_data['state'] = agent.stateMachine.current_state.name

                agents_data.append(agent_data)

        return {
            'time': self.env.now,
            'agents': agents_data,
            'fps': self.current_fps
        }

    def _broadcast(self, message: Dict[str, Any]):
        """Send message to all connected clients."""
        if not self.active_connections:
            return

        json_message = json.dumps(message)
        disconnected = set()

        for connection in self.active_connections:
            try:
                asyncio.run(connection.send_text(json_message))
            except Exception:
                disconnected.add(connection)

        self.active_connections -= disconnected

    async def _send_state(self, websocket: WebSocket):
        """Send current state to a specific client."""
        state = self._get_simulation_state()
        await websocket.send_text(json.dumps(state))

    async def _handle_client_message(self, websocket: WebSocket, message: str):
        """Handle messages from clients."""
        try:
            data = json.loads(message)
            command = data.get('command')

            if command == 'get_state':
                await self._send_state(websocket)
            elif command == 'select_agent':
                agent_name = data.get('agent')
                # Handle agent selection (broadcast to all clients)
                if hasattr(self.env, '_agents') and agent_name in self.env._agents:
                    agent = self.env._agents[agent_name]
                    if hasattr(agent, 'select'):
                        # Deselect all
                        for a in self.env._agents.values():
                            if hasattr(a, 'deselect'):
                                a.deselect()
                        # Select target
                        agent.select()

        except json.JSONDecodeError:
            pass

    def _get_html(self) -> str:
        """Generate enhanced HTML viewer page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.title}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
            max-width: 1400px;
            width: 100%;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header h1 {{
            font-size: 24px;
            font-weight: 600;
        }}

        .status {{
            padding: 6px 12px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            background: #4ade80;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .main-content {{
            display: flex;
            gap: 20px;
            padding: 20px;
        }}

        .canvas-container {{
            flex: 1;
            position: relative;
        }}

        #canvas {{
            border: 2px solid #e5e7eb;
            background: #f9fafb;
            border-radius: 12px;
            display: block;
            width: 100%;
            cursor: grab;
        }}

        #canvas:active {{
            cursor: grabbing;
        }}

        .controls {{
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }}

        .btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .btn-primary {{
            background: #667eea;
            color: white;
        }}

        .btn-primary:hover {{
            background: #5568d3;
            transform: translateY(-1px);
        }}

        .btn-secondary {{
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
        }}

        .btn-secondary:hover {{
            background: #f0f1ff;
        }}

        .toggle-group {{
            display: flex;
            gap: 5px;
            background: white;
            padding: 4px;
            border-radius: 8px;
        }}

        .toggle-btn {{
            padding: 6px 12px;
            border: none;
            background: transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}

        .toggle-btn.active {{
            background: #667eea;
            color: white;
        }}

        .sidebar {{
            width: 300px;
            background: #f9fafb;
            padding: 20px;
            border-radius: 12px;
            overflow-y: auto;
            max-height: calc(100vh - 200px);
        }}

        .stats-panel {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}

        .stats-panel h3 {{
            font-size: 16px;
            margin-bottom: 12px;
            color: #374151;
        }}

        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f3f4f6;
        }}

        .stat-row:last-child {{
            border-bottom: none;
        }}

        .stat-label {{
            color: #6b7280;
            font-size: 14px;
        }}

        .stat-value {{
            color: #111827;
            font-weight: 600;
            font-size: 14px;
        }}

        .agent-info {{
            background: white;
            padding: 15px;
            border-radius: 8px;
        }}

        .agent-info h3 {{
            font-size: 16px;
            margin-bottom: 12px;
            color: #374151;
        }}

        .no-selection {{
            color: #9ca3af;
            font-size: 14px;
            text-align: center;
            padding: 20px;
        }}

        .legend {{
            font-size: 12px;
            color: #6b7280;
            padding: 15px 0;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
        }}

        .legend-icon {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid #d1d5db;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.title}</h1>
            <div class="status">
                <div class="status-dot"></div>
                <span id="connection-status">Connected</span>
            </div>
        </div>

        <div class="main-content">
            <div class="canvas-container">
                <canvas id="canvas" width="{self.canvas_width}" height="{self.canvas_height}"></canvas>

                <div class="controls">
                    <div class="toggle-group">
                        <button class="toggle-btn active" id="toggle-grid" onclick="toggleLayer('grid')">Grid</button>
                        <button class="toggle-btn active" id="toggle-trails" onclick="toggleLayer('trails')">Trails</button>
                        <button class="toggle-btn active" id="toggle-connections" onclick="toggleLayer('connections')">Links</button>
                        <button class="toggle-btn active" id="toggle-labels" onclick="toggleLayer('labels')">Labels</button>
                        <button class="toggle-btn active" id="toggle-states" onclick="toggleLayer('states')">States</button>
                    </div>

                    <button class="btn btn-secondary" onclick="resetView()">
                        🎯 Reset View
                    </button>

                    <button class="btn btn-secondary" onclick="screenshot()">
                        📸 Screenshot
                    </button>
                </div>
            </div>

            <div class="sidebar">
                <div class="stats-panel">
                    <h3>📊 Simulation Stats</h3>
                    <div class="stat-row">
                        <span class="stat-label">Time</span>
                        <span class="stat-value" id="sim-time">0.00</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">FPS</span>
                        <span class="stat-value" id="fps">{self.update_rate}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Agents</span>
                        <span class="stat-value" id="agent-count">0</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Zoom</span>
                        <span class="stat-value" id="zoom-level">1.0x</span>
                    </div>
                </div>

                <div class="agent-info">
                    <h3>🎯 Selected Agent</h3>
                    <div id="agent-details" class="no-selection">
                        Click on an agent to view details
                    </div>
                </div>

                <div class="legend">
                    <strong>Controls:</strong>
                    <div class="legend-item">🖱️ Drag to pan</div>
                    <div class="legend-item">🔍 Scroll to zoom</div>
                    <div class="legend-item">👆 Click to select agent</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        // State
        let agents = [];
        let simTime = 0;
        let zoom = 1.0;
        let offsetX = 0;
        let offsetY = 0;
        let selectedAgent = null;
        let currentFps = 0;

        // Layer toggles
        let showGrid = true;
        let showTrails = true;
        let showConnections = true;
        let showLabels = true;
        let showStates = true;

        // WebSocket
        const ws = new WebSocket(`ws://${{window.location.host}}/ws`);

        ws.onopen = () => {{
            document.getElementById('connection-status').textContent = 'Connected';
        }};

        ws.onclose = () => {{
            document.getElementById('connection-status').textContent = 'Disconnected';
        }};

        ws.onmessage = (event) => {{
            const data = JSON.parse(event.data);
            simTime = data.time;
            agents = data.agents;
            currentFps = data.fps || {self.update_rate};

            document.getElementById('sim-time').textContent = simTime.toFixed(2);
            document.getElementById('fps').textContent = currentFps;
            document.getElementById('agent-count').textContent = agents.length;
            document.getElementById('zoom-level').textContent = zoom.toFixed(1) + 'x';

            render();
        }};

        // Rendering
        function render() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw grid
            if (showGrid) {{
                drawGrid();
            }}

            // Draw connections
            if (showConnections) {{
                drawConnections();
            }}

            // Draw trails
            if (showTrails) {{
                drawTrails();
            }}

            // Draw agents
            drawAgents();
        }}

        function drawGrid() {{
            ctx.strokeStyle = '#e5e7eb';
            ctx.lineWidth = 1;
            const spacing = 50 * zoom;

            for (let x = offsetX % spacing; x < canvas.width; x += spacing) {{
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }}

            for (let y = offsetY % spacing; y < canvas.height; y += spacing) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }}
        }}

        function drawTrails() {{
            agents.forEach(agent => {{
                if (!agent.trail || agent.trail.length < 2) return;

                const trailColor = agent.trailColor || agent.color;
                ctx.strokeStyle = `rgb(${{trailColor[0]}},${{trailColor[1]}},${{trailColor[2]}})`;
                ctx.lineWidth = 2;
                ctx.globalAlpha = 0.6;

                ctx.beginPath();
                agent.trail.forEach((point, i) => {{
                    const x = point[0] * zoom + offsetX;
                    const y = point[1] * zoom + offsetY;
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }});
                ctx.stroke();
                ctx.globalAlpha = 1.0;
            }});
        }}

        function drawConnections() {{
            agents.forEach(agent => {{
                if (!agent.connections) return;

                const x1 = agent.position[0] * zoom + offsetX + (agent.dimensions[0] * zoom) / 2;
                const y1 = agent.position[1] * zoom + offsetY + (agent.dimensions[1] * zoom) / 2;

                agent.connections.forEach(connName => {{
                    const connAgent = agents.find(a => a.name === connName);
                    if (!connAgent) return;

                    const x2 = connAgent.position[0] * zoom + offsetX + (connAgent.dimensions[0] * zoom) / 2;
                    const y2 = connAgent.position[1] * zoom + offsetY + (connAgent.dimensions[1] * zoom) / 2;

                    ctx.strokeStyle = '#9ca3af';
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x2, y2);
                    ctx.stroke();
                }});
            }});
        }}

        function drawAgents() {{
            agents.forEach(agent => {{
                const x = agent.position[0] * zoom + offsetX;
                const y = agent.position[1] * zoom + offsetY;
                const w = agent.dimensions[0] * zoom;
                const h = (agent.dimensions[1] || agent.dimensions[0]) * zoom;

                const [r, g, b] = agent.color;
                ctx.fillStyle = `rgb(${{r}},${{g}},${{b}})`;

                const borderColor = agent.selected ? '#fbbf24' : (agent.borderColor ? `rgb(${{agent.borderColor.join(',')}})` : '#000');
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = agent.selected ? 3 : (agent.borderWidth || 1);

                // Draw shape
                drawShape(agent.shape, x, y, w, h);

                // Draw label
                if (showLabels && agent.label && zoom > 0.5) {{
                    ctx.fillStyle = '#000';
                    ctx.font = '12px sans-serif';
                    ctx.fillText(agent.label, x + 2, y + h + 14);
                }}

                // Draw state
                if (showStates && agent.state && zoom > 0.5) {{
                    ctx.fillStyle = '#6b7280';
                    ctx.font = '11px sans-serif';
                    ctx.fillText(`[${{agent.state}}]`, x + 2, y - 5);
                }}
            }});
        }}

        function drawShape(shape, x, y, w, h) {{
            ctx.beginPath();

            if (shape === 'rectangle') {{
                ctx.rect(x, y, w, h);
            }} else if (shape === 'circle') {{
                ctx.arc(x + w/2, y + w/2, w/2, 0, Math.PI * 2);
            }} else if (shape === 'triangle') {{
                ctx.moveTo(x + w/2, y);
                ctx.lineTo(x, y + h);
                ctx.lineTo(x + w, y + h);
                ctx.closePath();
            }} else if (shape === 'diamond') {{
                ctx.moveTo(x + w/2, y);
                ctx.lineTo(x + w, y + h/2);
                ctx.lineTo(x + w/2, y + h);
                ctx.lineTo(x, y + h/2);
                ctx.closePath();
            }} else if (shape === 'hexagon') {{
                const cx = x + w/2, cy = y + h/2, r = Math.min(w, h) / 2;
                for (let i = 0; i < 6; i++) {{
                    const angle = Math.PI / 3 * i;
                    const px = cx + r * Math.cos(angle);
                    const py = cy + r * Math.sin(angle);
                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }}
                ctx.closePath();
            }} else if (shape === 'star') {{
                const cx = x + w/2, cy = y + h/2;
                const outerR = Math.min(w, h) / 2, innerR = outerR / 2;
                for (let i = 0; i < 10; i++) {{
                    const r = i % 2 === 0 ? outerR : innerR;
                    const angle = Math.PI / 5 * i - Math.PI / 2;
                    const px = cx + r * Math.cos(angle);
                    const py = cy + r * Math.sin(angle);
                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }}
                ctx.closePath();
            }}

            ctx.fill();
            ctx.stroke();
        }}

        // Interaction
        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            zoom = Math.max(0.1, Math.min(5, zoom * delta));
            render();
        }});

        let isDragging = false, lastX, lastY;

        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            // Check for agent click
            const clicked = getAgentAtPos(mx, my);
            if (clicked) {{
                selectAgent(clicked);
            }} else {{
                isDragging = true;
                lastX = e.clientX;
                lastY = e.clientY;
            }}
        }});

        canvas.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                offsetX += e.clientX - lastX;
                offsetY += e.clientY - lastY;
                lastX = e.clientX;
                lastY = e.clientY;
                render();
            }}
        }});

        canvas.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        function getAgentAtPos(mx, my) {{
            for (let i = agents.length - 1; i >= 0; i--) {{
                const agent = agents[i];
                const x = agent.position[0] * zoom + offsetX;
                const y = agent.position[1] * zoom + offsetY;
                const w = agent.dimensions[0] * zoom;
                const h = (agent.dimensions[1] || agent.dimensions[0]) * zoom;

                if (agent.shape === 'circle') {{
                    const dx = mx - (x + w/2);
                    const dy = my - (y + w/2);
                    if (Math.sqrt(dx*dx + dy*dy) <= w/2) return agent;
                }} else {{
                    if (mx >= x && mx <= x + w && my >= y && my <= y + h) return agent;
                }}
            }}
            return null;
        }}

        function selectAgent(agent) {{
            selectedAgent = agent;
            agents.forEach(a => a.selected = (a === agent));

            // Update info panel
            const details = document.getElementById('agent-details');
            details.innerHTML = `
                <div class="stat-row">
                    <span class="stat-label">Name</span>
                    <span class="stat-value">${{agent.label || agent.name}}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Position</span>
                    <span class="stat-value">(${{agent.position[0].toFixed(1)}}, ${{agent.position[1].toFixed(1)}})</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Shape</span>
                    <span class="stat-value">${{agent.shape}}</span>
                </div>
                ${{agent.state ? `
                <div class="stat-row">
                    <span class="stat-label">State</span>
                    <span class="stat-value">${{agent.state}}</span>
                </div>` : ''}}
            `;

            // Send selection to server
            ws.send(JSON.stringify({{command: 'select_agent', agent: agent.name}}));

            render();
        }}

        function toggleLayer(layer) {{
            const btn = document.getElementById(`toggle-${{layer}}`);
            switch(layer) {{
                case 'grid': showGrid = !showGrid; break;
                case 'trails': showTrails = !showTrails; break;
                case 'connections': showConnections = !showConnections; break;
                case 'labels': showLabels = !showLabels; break;
                case 'states': showStates = !showStates; break;
            }}
            btn.classList.toggle('active');
            render();
        }}

        function resetView() {{
            zoom = 1.0;
            offsetX = 0;
            offsetY = 0;
            render();
        }}

        function screenshot() {{
            const link = document.createElement('a');
            link.download = `hsim_${{Date.now()}}.png`;
            link.href = canvas.toDataURL();
            link.click();
        }}

        // Initial render
        render();
    </script>
</body>
</html>
        """
