"""
Web-based Renderer for hsim Simulations

Provides real-time visualization using FastAPI, WebSockets, and HTML5 Canvas.
Modern, browser-based visualization with smooth animations and interactivity.
"""

import asyncio
import json
import threading
from typing import Optional, Set, Dict, Any
from pathlib import Path

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # Create dummy types for type hints when fastapi not available
    WebSocket = object
    WebSocketDisconnect = Exception
    print("Warning: fastapi/uvicorn not installed. Install with: pip install fastapi uvicorn websockets")

from hsim.core.graphics import GraphicsMixin, Shape


class WebRenderer:
    """
    Real-time web-based renderer for simulations.

    Runs a FastAPI server with WebSocket support for real-time updates.
    Clients connect via browser to view the simulation.

    Args:
        env: Simulation environment
        port: Server port
        host: Server host
        update_rate: Updates per second to send to clients
        canvas_width: Canvas width in pixels
        canvas_height: Canvas height in pixels
    """

    def __init__(
        self,
        env,
        port: int = 8000,
        host: str = "localhost",
        update_rate: int = 30,
        canvas_width: int = 800,
        canvas_height: int = 600,
        title: str = "hsim Simulation"
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
        self.update_task = None

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

                # Keep connection alive and handle messages
                while True:
                    data = await websocket.receive_text()
                    # Handle client commands (pause, reset, etc.)
                    await self._handle_client_message(websocket, data)

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

    def start(self):
        """Start the web server in a separate thread."""
        if self.running:
            return

        self.running = True

        # Start server thread
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        self.server_thread.start()

        # Start update loop
        threading.Thread(target=self._update_loop, daemon=True).start()

        print(f"Web renderer started at http://{self.host}:{self.port}")

    def stop(self):
        """Stop the web server."""
        self.running = False
        if self.server_thread:
            self.server_thread.join(timeout=2.0)

    def _run_server(self):
        """Run the FastAPI server."""
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="warning")

    def _update_loop(self):
        """Periodically send updates to all connected clients."""
        import time
        update_interval = 1.0 / self.update_rate

        while self.running:
            if self.active_connections:
                state = self._get_simulation_state()
                self._broadcast(state)

            time.sleep(update_interval)

    def _get_simulation_state(self) -> Dict[str, Any]:
        """Get current simulation state as JSON-serializable dict."""
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

                # Add state information if available
                if hasattr(agent, 'stateMachine') and hasattr(agent.stateMachine, 'current_state'):
                    if agent.stateMachine.current_state:
                        agent_data['state'] = agent.stateMachine.current_state.name

                agents_data.append(agent_data)

        return {
            'time': self.env.now,
            'agents': agents_data
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

        # Remove disconnected clients
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

        except json.JSONDecodeError:
            pass

    def _get_html(self) -> str:
        """Generate HTML viewer page."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.title}</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            padding: 20px;
            max-width: 1000px;
        }}
        h1 {{
            margin: 0 0 20px 0;
            color: #333;
            font-size: 24px;
        }}
        #canvas {{
            border: 2px solid #333;
            background: #f5f5f5;
            border-radius: 8px;
            display: block;
        }}
        .controls {{
            margin-top: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
        }}
        .status {{
            padding: 8px 15px;
            background: #e8f5e9;
            border-radius: 5px;
            font-size: 14px;
            color: #2e7d32;
        }}
        .status.disconnected {{
            background: #ffebee;
            color: #c62828;
        }}
        .info {{
            margin-top: 15px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
            font-size: 14px;
            color: #666;
        }}
        .time-display {{
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
            padding: 10px;
            background: #f0f4ff;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.title}</h1>
        <canvas id="canvas" width="{self.canvas_width}" height="{self.canvas_height}"></canvas>
        <div class="controls">
            <div class="time-display">Time: <span id="time">0.00</span></div>
            <div class="status" id="status">Connecting...</div>
        </div>
        <div class="info">
            <strong>Controls:</strong> Scroll to zoom • Drag to pan • Real-time updates at {self.update_rate} FPS
        </div>
    </div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const statusEl = document.getElementById('status');
        const timeEl = document.getElementById('time');

        // Visualization state
        let agents = [];
        let simTime = 0;
        let zoom = 1.0;
        let offsetX = 0;
        let offsetY = 0;

        // WebSocket connection
        const ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onopen = () => {{
            statusEl.textContent = 'Connected';
            statusEl.className = 'status';
        }};

        ws.onclose = () => {{
            statusEl.textContent = 'Disconnected';
            statusEl.className = 'status disconnected';
        }};

        ws.onmessage = (event) => {{
            const data = JSON.parse(event.data);
            simTime = data.time;
            agents = data.agents;
            timeEl.textContent = simTime.toFixed(2);
            render();
        }};

        // Render function
        function render() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw grid
            ctx.strokeStyle = '#ddd';
            ctx.lineWidth = 1;
            for (let x = 0; x < canvas.width; x += 50 * zoom) {{
                ctx.beginPath();
                ctx.moveTo(x + offsetX, 0);
                ctx.lineTo(x + offsetX, canvas.height);
                ctx.stroke();
            }}
            for (let y = 0; y < canvas.height; y += 50 * zoom) {{
                ctx.beginPath();
                ctx.moveTo(0, y + offsetY);
                ctx.lineTo(canvas.width, y + offsetY);
                ctx.stroke();
            }}

            // Draw agents
            agents.forEach(agent => {{
                const x = agent.position[0] * zoom + offsetX;
                const y = agent.position[1] * zoom + offsetY;
                const w = agent.dimensions[0] * zoom;
                const h = (agent.dimensions[1] || agent.dimensions[0]) * zoom;

                // Set color
                const [r, g, b] = agent.color;
                ctx.fillStyle = `rgb(${{r}},${{g}},${{b}})`;
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;

                // Draw based on shape
                if (agent.shape === 'rectangle') {{
                    ctx.fillRect(x, y, w, h);
                    ctx.strokeRect(x, y, w, h);
                }} else if (agent.shape === 'circle') {{
                    ctx.beginPath();
                    ctx.arc(x + w/2, y + w/2, w/2, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.stroke();
                }} else if (agent.shape === 'triangle') {{
                    ctx.beginPath();
                    ctx.moveTo(x + w/2, y);
                    ctx.lineTo(x, y + h);
                    ctx.lineTo(x + w, y + h);
                    ctx.closePath();
                    ctx.fill();
                    ctx.stroke();
                }} else if (agent.shape === 'diamond') {{
                    ctx.beginPath();
                    ctx.moveTo(x + w/2, y);
                    ctx.lineTo(x + w, y + h/2);
                    ctx.lineTo(x + w/2, y + h);
                    ctx.lineTo(x, y + h/2);
                    ctx.closePath();
                    ctx.fill();
                    ctx.stroke();
                }}

                // Draw label
                ctx.fillStyle = '#000';
                ctx.font = '12px sans-serif';
                if (agent.label) {{
                    ctx.fillText(agent.label, x + 2, y + h + 14);
                }}

                // Draw state
                if (agent.state) {{
                    ctx.fillStyle = '#666';
                    ctx.fillText(`[${{agent.state}}]`, x + 2, y - 5);
                }}
            }});
        }}

        // Zoom with mouse wheel
        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            zoom *= delta;
            zoom = Math.max(0.1, Math.min(5, zoom));
            render();
        }});

        // Pan with mouse drag
        let isDragging = false;
        let lastX, lastY;

        canvas.addEventListener('mousedown', (e) => {{
            isDragging = true;
            lastX = e.clientX;
            lastY = e.clientY;
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

        // Initial render
        render();
    </script>
</body>
</html>
        """
