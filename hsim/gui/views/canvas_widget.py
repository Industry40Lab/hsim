"""
Model Canvas - Main workspace for drag-drop block design
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from hsim.gui.models.model import SimulationModel, Block, Connection, Position, Size, FSM, State, Transition
from hsim.gui.models.block_definitions import BlockType, get_block_definition
from hsim.gui.items.block_item import BlockItem  # Use new version
from hsim.gui.items.connection_item import ConnectionItem
from hsim.gui.items.port_item import PortItem
from hsim.gui.items.fsm_item import FSMItem
import uuid


class CanvasWidget(QGraphicsView):
    """Canvas for designing simulation models"""

    selection_changed = pyqtSignal(object)  # Emits selected block
    block_double_clicked = pyqtSignal(str)  # Emits block ID
    model_changed = pyqtSignal()  # Emits when model changes
    mode_changed = pyqtSignal(str)  # Emits "main" or "agent_internal"

    # Grid settings
    GRID_SIZE = 20  # Snap grid size in pixels

    def __init__(self, model: SimulationModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # Enable rubber band selection for multi-select
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

        # State
        self.block_items = {}  # block_id -> BlockItem
        self.connection_items = {}  # connection_id -> ConnectionItem
        self.create_mode = None  # Block type to create on click
        self.connection_mode = False
        self.connection_from = None
        self.grid_visible = True
        self.grid_snap = True  # Enable grid snapping by default
        self.zoom_level = 1.0
        
        # Clipboard for copy/paste
        self.clipboard = []  # List of copied block data

        # Canvas mode (main process flow or agent internal FSM view)
        self.current_mode = "main"  # "main" or "agent_internal"
        self.current_agent_id = None  # ID of agent being edited in internal view
        self.current_fsm = None  # FSM being displayed in internal view (backward compat)
        self.selected_fsm_id = None  # Currently selected FSM for adding states
        self.fsm_items = {}  # fsm_id -> FSMItem (visual FSM containers)
        self.state_items = {}  # state_id -> StateItem (in FSM view)
        self.transition_items = {}  # transition_id -> TransitionItem (in FSM view)

        # Scene stack for nested agent editing
        self.scene_stack = []  # Stack of (scene, mode, agent_id, fsm) tuples
        self.main_scene = self.scene  # Save reference to main scene

        self.setup_scene()
        self.setup_view()
        self.load_model()

    def on_port_click_started(self, block_id, port_name):
        """Handle click-started connection from a port (click-click behaviour)"""
        # Use same internal state as drag-started: store tuple (block_id, port_name)
        self.connection_mode = True
        self.connection_from = (block_id, port_name)
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Show status message
        from_block = self.model.get_block_by_id(block_id)
        if from_block:
            window = self._get_main_window()
            if window:
                window.statusBar().showMessage(
                    f"Creating connection from '{from_block.name}' - Click target block"
                )

    def setup_scene(self):
        """Setup the graphics scene"""
        # Set scene size
        self.scene.setSceneRect(0, 0, 2000, 2000)

        # Set background
        self.scene.setBackgroundBrush(QBrush(QColor("#F9FAFB")))

    def setup_view(self):
        """Setup the view"""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setAcceptDrops(True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Connect scene selection changed signal
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def load_model(self):
        """Load model into canvas"""
        # Clear existing items
        self.scene.clear()
        self.block_items.clear()
        self.connection_items.clear()

        # Add blocks
        for block_id, block in self.model.blocks.items():
            self.add_block_item(block)

        # Add connections
        # model.connections is a dict mapping id->Connection
        for connection in self.model.connections.values():
            self.add_connection_item(connection)

    def set_model(self, model: SimulationModel):
        """Set a new model"""
        self.model = model
        self.load_model()

    def add_block_item(self, block: Block):
        """Add a block item to the canvas (V2 with ports)"""
        item = BlockItem(block)

        # Connect signals
        item.signals.double_clicked.connect(self.on_block_double_clicked)
        item.signals.properties_requested.connect(self.on_block_properties_requested)
        item.signals.deleted.connect(self.on_block_deleted)

        # Connect port signals for drag-drop connections
        for port_name, port in item.ports.items():
            port.signals.connection_drag_started.connect(self.on_port_drag_started)
            port.signals.connection_drag_ended.connect(self.on_port_drag_ended)
            # Click-click behaviour: start connection by clicking an output port
            if hasattr(port.signals, 'connection_clicked'):
                port.signals.connection_clicked.connect(self.on_port_click_started)

        self.scene.addItem(item)
        self.block_items[block.id] = item

    def add_connection_item(self, connection: Connection):
        """Add a connection item to the canvas"""
        from_item = self.block_items.get(connection.from_block)
        to_item = self.block_items.get(connection.to_block)

        if from_item and to_item:
            item = ConnectionItem(connection, from_item, to_item)
            item.signals.deleted.connect(self.on_connection_deleted)

            self.scene.addItem(item)
            self.connection_items[connection.id] = item

    def on_block_double_clicked(self, block_id):
        """Handle block double-click"""
        self.block_double_clicked.emit(block_id)

    def on_block_properties_requested(self, block):
        """Handle block properties request"""
        self.selection_changed.emit(block)

    def on_block_deleted(self, block_id):
        """Handle block deletion"""
        # Remove from scene
        item = self.block_items.get(block_id)
        if item:
            self.scene.removeItem(item)
            del self.block_items[block_id]

        # Remove from model
        self.model.remove_block(block_id)

        # Remove associated connections (already handled by model.remove_block)
        # But we need to remove the visual items
        connections_to_remove = []
        for conn_id, conn_item in self.connection_items.items():
            if (conn_item.connection.from_block == block_id or
                conn_item.connection.to_block == block_id):
                self.scene.removeItem(conn_item)
                connections_to_remove.append(conn_id)

        for conn_id in connections_to_remove:
            del self.connection_items[conn_id]

    def on_connection_deleted(self, connection_id):
        """Handle connection deletion"""
        # Remove from scene
        item = self.connection_items.get(connection_id)
        if item:
            self.scene.removeItem(item)
            del self.connection_items[connection_id]

        # Remove from model
        self.model.remove_connection(connection_id)

    def on_selection_changed(self):
        """Handle scene selection changes"""
        selected_items = self.scene.selectedItems()

        # Find first selected block
        for item in selected_items:
            # Check if item is BlockItem or has BlockItem parent
            if isinstance(item, BlockItem):
                self.selection_changed.emit(item.block)
                return
            elif hasattr(item, 'parentItem') and isinstance(item.parentItem(), BlockItem):
                self.selection_changed.emit(item.parentItem().block)
                return

        # No block selected, clear properties
        self.selection_changed.emit(None)

    def on_port_drag_started(self, block_id, port_name):
        """Handle port drag start"""
        self.connection_mode = True
        self.connection_from = (block_id, port_name)
        # Could draw preview line here

    def on_port_drag_ended(self, from_block_id, from_port_name, target_port):
        """Handle port drag end - create connection if valid target"""
        if not target_port or not isinstance(target_port, PortItem):
            self.connection_mode = False
            self.connection_from = None
            return

        # Get target block and port
        to_block_id = target_port.block_id
        to_port_name = target_port.port_name

        # Validate connection (output -> input)
        if from_block_id == to_block_id:
            # Can't connect to self
            self.connection_mode = False
            self.connection_from = None
            return

        if target_port.port_type != "input":
            # Can only connect to input ports
            self.connection_mode = False
            self.connection_from = None
            return

        # Create connection
        conn = Connection(
            id=str(uuid.uuid4()),
            from_block=from_block_id,
            to_block=to_block_id,
            label=from_port_name  # Use port name as label
        )
        self.model.add_connection(conn)

        # Create visual connection
        self.add_connection_item(conn)

        # Show feedback
        from_block = self.model.get_block_by_id(from_block_id)
        to_block = self.model.get_block_by_id(to_block_id)
        if from_block and to_block:
            window = self._get_main_window()
            if window:
                window.statusBar().showMessage(
                    f"Connected {from_block.name} → {to_block.name}"
                )

        self.connection_mode = False
        self.connection_from = None

    def set_create_mode(self, block_type: str):
        """Set mode to create a block on next click"""
        self.create_mode = block_type
        self.setCursor(Qt.CursorShape.CrossCursor)

    def select_block(self, block_id: str):
        """Select a block on the canvas"""
        # Clear current selection
        self.scene.clearSelection()

        # Select the block item
        if block_id in self.block_items:
            block_item = self.block_items[block_id]
            block_item.setSelected(True)

            # Center view on block
            self.centerOn(block_item)

    def _get_main_window(self):
        """Get main window through parent hierarchy"""
        widget = self.parent()
        while widget and not hasattr(widget, 'statusBar'):
            widget = widget.parent()
        return widget

    def snap_to_grid(self, x, y):
        """Snap coordinates to grid"""
        if self.grid_snap:
            x = round(x / self.GRID_SIZE) * self.GRID_SIZE
            y = round(y / self.GRID_SIZE) * self.GRID_SIZE
        return x, y

    def start_connection_mode(self, from_block_id: str):
        """Start connection creation mode"""
        # Accept either a block id string or a tuple/list (block_id, port_name)
        self.connection_mode = True
        self.connection_from = from_block_id
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Show status message
        # Resolve block id for messaging
        resolved_from = from_block_id[0] if isinstance(from_block_id, (tuple, list)) else from_block_id
        from_block = self.model.get_block_by_id(resolved_from)
        if from_block:
            window = self._get_main_window()
            if window:
                window.statusBar().showMessage(
                    f"Creating connection from '{from_block.name}' - Click target block"
                )

    def complete_connection(self, to_block_id: str):
        """Complete connection creation"""
        if not self.connection_from:
            self.cancel_connection_mode()
            return

        # Support connection_from being either a block_id (str) or a tuple (block_id, port_name)
        from_block_id = self.connection_from[0] if isinstance(self.connection_from, (tuple, list)) else self.connection_from

        if to_block_id == from_block_id:
            self.cancel_connection_mode()
            return

        # Create connection in model
        conn = Connection(
            id=str(uuid.uuid4()),
            from_block=from_block_id,
            to_block=to_block_id,
            label="next"
        )
        self.model.add_connection(conn)

        # Create visual connection item
        self.add_connection_item(conn)

        # Exit connection mode
        self.cancel_connection_mode()

        # Show status
        from_block = self.model.get_block_by_id(self.connection_from)
        to_block = self.model.get_block_by_id(to_block_id)
        if from_block and to_block:
            window = self._get_main_window()
            if window:
                window.statusBar().showMessage(
                    f"Connected '{from_block.name}' → '{to_block.name}'"
                )

    def cancel_connection_mode(self):
        """Cancel connection creation mode"""
        self.connection_mode = False
        self.connection_from = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        window = self._get_main_window()
        if window:
            window.statusBar().showMessage("Ready")

    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.create_mode:
                scene_pos = self.mapToScene(event.pos())

                # Handle different creation modes
                if self.create_mode == "state":
                    self._create_state_at(scene_pos.x(), scene_pos.y())
                    self.create_mode = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return
                elif self.create_mode == "transition":
                    # Transition requires clicking two states
                    if not hasattr(self, 'transition_source_state'):
                        # First click - select source state
                        self._start_transition_creation(event.pos())
                    else:
                        # Second click - select target state and create transition
                        self._complete_transition_creation(event.pos())
                    return
                elif self.create_mode in ["input_port", "output_port"]:
                    self._create_port_at(event.pos())
                    self.create_mode = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return
                elif self.create_mode == "timeout_event":
                    # Timeout events are added to states, not placed on canvas
                    main_window = self._get_main_window()
                    if main_window:
                        main_window.statusBar().showMessage("Click a state to add timeout event", 3000)
                    # For now, just exit create mode
                    self.create_mode = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return
                elif self.create_mode == "connection":
                    # Connection mode uses port drag-drop (already implemented)
                    main_window = self._get_main_window()
                    if main_window:
                        main_window.statusBar().showMessage("Use port drag-drop for connections (already available)", 3000)
                    self.create_mode = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return
                elif self.create_mode == "fsm_container":
                    # Create FSM container
                    self._create_fsm_container_at(scene_pos.x(), scene_pos.y())
                    self.create_mode = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return
                else:
                    # Standard block creation
                    self.create_block_at(self.create_mode, scene_pos.x(), scene_pos.y())
                    self.create_mode = None
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                    return

            elif self.connection_mode:
                # Check if clicked on a block
                item = self.itemAt(event.pos())
                if item:
                    # Find the BlockItem (might be a child item)
                    block_item = item
                    while block_item and not isinstance(block_item, BlockItem):
                        block_item = block_item.parentItem()

                    if block_item and isinstance(block_item, BlockItem):
                        self.complete_connection(block_item.block.id)
                        return

                # Clicked on empty space - cancel connection
                self.cancel_connection_mode()
                return

        elif event.button() == Qt.MouseButton.RightButton and self.connection_mode:
            # Right-click cancels connection mode
            self.cancel_connection_mode()
            return

        super().mousePressEvent(event)

    def create_block_at(self, block_type: str, x: float, y: float):
        """Create a new block at the specified position"""
        try:
            block_def = get_block_definition(BlockType(block_type))
        except (ValueError, KeyError) as e:
            print(f"Error: Unknown block type '{block_type}': {e}")
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage(f"Error: Unknown block type '{block_type}'", 5000)
            return

        if not block_def:
            print(f"Error: No definition found for block type '{block_type}'")
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage(f"Error: No definition for '{block_type}'", 5000)
            return

        # Determine parent based on current view mode
        parent_id = None
        if self.current_mode == "agent_internal" and self.current_agent_id:
            parent_id = self.current_agent_id

        # Snap to grid
        x, y = self.snap_to_grid(x - 50, y - 40)  # Center on click, then snap

        # Create block data
        block = Block(
            id=str(uuid.uuid4()),
            type=block_type,
            name=f"{block_def.name} {len(self.model.blocks) + 1}",
            position=Position(x, y),
            size=Size(100, 80),
            properties={prop.name: prop.default for prop in block_def.properties},
            parent_id=parent_id
        )

        # All blocks are agents and have FSMs
        if block_def.has_fsm:
            from hsim.gui.models.model import State as FSMState, Transition
            fsm = FSM(
                id=str(uuid.uuid4()),
                name=f"{block.name} FSM",
                owner_block_id=block.id
            )

            # Create appropriate FSM states based on block type
            if block_type in ["server", "unreliable_machine", "quality_machine", "su_machine"]:
                # Server-like blocks: Idle → Busy cycle
                idle_state = FSMState(
                    id=str(uuid.uuid4()),
                    name="Idle",
                    position=Position(100, 100),
                    size=Size(120, 60),
                    is_initial=True,
                    on_enter="# Waiting for entity",
                    on_exit="",
                    color="#10B981"  # Green
                )
                busy_state = FSMState(
                    id=str(uuid.uuid4()),
                    name="Busy",
                    position=Position(300, 100),
                    size=Size(120, 60),
                    is_initial=False,
                    on_enter="# Processing entity",
                    on_exit="# Entity processed",
                    color="#F59E0B"  # Orange
                )
                fsm.add_state(idle_state)
                fsm.add_state(busy_state)

                # Add transitions
                to_busy = Transition(
                    id=str(uuid.uuid4()),
                    from_state=idle_state.id,
                    to_state=busy_state.id,
                    label="start_service",
                    transition_type="message"
                )
                to_idle = Transition(
                    id=str(uuid.uuid4()),
                    from_state=busy_state.id,
                    to_state=idle_state.id,
                    label="service_complete",
                    transition_type="timeout"
                )
                fsm.add_transition(to_busy)
                fsm.add_transition(to_idle)

            elif block_type == "buffer":
                # Buffer: Single state (passive storage)
                ready_state = FSMState(
                    id=str(uuid.uuid4()),
                    name="Ready",
                    position=Position(200, 100),
                    size=Size(120, 60),
                    is_initial=True,
                    on_enter="# Ready to store entities",
                    on_exit="",
                    color="#3B82F6"  # Blue
                )
                fsm.add_state(ready_state)

            elif block_type == "generator":
                # Generator: Generating state
                generating_state = FSMState(
                    id=str(uuid.uuid4()),
                    name="Generating",
                    position=Position(200, 100),
                    size=Size(120, 60),
                    is_initial=True,
                    on_enter="# Generate next entity",
                    on_exit="",
                    color="#10B981"  # Green
                )
                fsm.add_state(generating_state)

            else:
                # Default: Single Empty state
                empty_state = FSMState(
                    id=str(uuid.uuid4()),
                    name="Empty",
                    position=Position(200, 100),
                    size=Size(120, 60),
                    is_initial=True,
                    on_enter="",
                    on_exit="",
                    color="#6B7280"  # Gray
                )
                fsm.add_state(empty_state)

            block.fsm_id = fsm.id
            self.model.add_fsm(fsm)

        # Add to model
        self.model.add_block(block)

        # Add to parent's children list if this is a sub-agent
        if parent_id:
            parent_block = self.model.get_block_by_id(parent_id)
            if parent_block:
                parent_block.children.append(block.id)

        # Add to canvas
        self.add_block_item(block)

        # Emit model changed signal
        self.model_changed.emit()

    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Handle drag move"""
        event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop event (from palette)"""
        if event.mimeData().hasText():
            block_type = event.mimeData().text()
            scene_pos = self.mapToScene(event.position().toPoint())

            self.create_block_at(block_type, scene_pos.x(), scene_pos.y())
            event.acceptProposedAction()

    def contextMenuEvent(self, event):
        """Handle right-click on canvas"""
        # Check if clicked on an item
        item = self.itemAt(event.pos())
        if item:
            super().contextMenuEvent(event)
        else:
            # Show canvas context menu
            from PyQt6.QtWidgets import QMenu
            menu = QMenu(self)

            paste_action = menu.addAction("Paste")
            paste_action.setEnabled(False)  # TODO: Implement clipboard

            menu.addSeparator()

            select_all_action = menu.addAction("Select All")
            select_all_action.triggered.connect(self.select_all_blocks)

            menu.exec(event.globalPos())

    def select_all_blocks(self):
        """Select all blocks"""
        for item in self.block_items.values():
            item.setSelected(True)

    def copy_selected(self):
        """Copy selected blocks to clipboard"""
        selected_items = self.scene.selectedItems()
        self.clipboard = []
        
        for item in selected_items:
            if isinstance(item, BlockItem):
                block = item.block
                block_data = {
                    'type': block.type,
                    'name': block.name,
                    'position': {'x': block.position.x, 'y': block.position.y},
                    'size': {'width': block.size.width, 'height': block.size.height},
                    'properties': block.properties.copy() if block.properties else {}
                }
                self.clipboard.append(block_data)
        
        if self.clipboard:
            return len(self.clipboard)
        return 0
    
    def paste_from_clipboard(self):
        """Paste blocks from clipboard"""
        if not self.clipboard:
            return 0
        
        # Clear current selection
        for item in self.scene.selectedItems():
            item.setSelected(False)
        
        pasted_count = 0
        offset = 30  # Offset to avoid pasting on top of original
        
        for block_data in self.clipboard:
            # Create new block with offset position
            new_id = str(uuid.uuid4())
            position = Position(
                block_data['position']['x'] + offset,
                block_data['position']['y'] + offset
            )
            size = Size(
                block_data['size']['width'],
                block_data['size']['height']
            )
            
            # Generate unique name
            base_name = block_data['name']
            counter = 1
            new_name = f"{base_name}_copy"
            while any(b.name == new_name for b in self.model.blocks.values()):
                counter += 1
                new_name = f"{base_name}_copy{counter}"
            
            new_block = Block(
                id=new_id,
                type=block_data['type'],
                name=new_name,
                position=position,
                size=size,
                properties=block_data['properties'].copy()
            )
            
            # Add to model
            self.model.blocks[new_id] = new_block
            
            # Add to canvas
            self.add_block_to_canvas(new_block)
            
            # Select the new block
            if new_id in self.block_items:
                self.block_items[new_id].setSelected(True)
            
            pasted_count += 1
        
        if pasted_count > 0:
            self.model_changed.emit()
        
        return pasted_count

    def delete_selected(self):
        """Delete selected items"""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, BlockItem):
                self.on_block_deleted(item.block.id)
            elif isinstance(item, ConnectionItem):
                self.on_connection_deleted(item.connection.id)

    # Alignment operations
    def align_left(self):
        """Align selected blocks to the leftmost block"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 2:
            return
        
        # Find leftmost position
        min_x = min(item.pos().x() for item in selected_blocks)
        
        # Move all blocks to that x position
        for item in selected_blocks:
            item.setPos(min_x, item.pos().y())
            # Update model
            item.block.position.x = min_x
        
        self.model_changed.emit()
    
    def align_right(self):
        """Align selected blocks to the rightmost block"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 2:
            return
        
        # Find rightmost position (accounting for width)
        max_x = max(item.pos().x() + item.block.size.width for item in selected_blocks)
        
        # Move all blocks to that x position
        for item in selected_blocks:
            new_x = max_x - item.block.size.width
            item.setPos(new_x, item.pos().y())
            item.block.position.x = new_x
        
        self.model_changed.emit()
    
    def align_top(self):
        """Align selected blocks to the topmost block"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 2:
            return
        
        # Find topmost position
        min_y = min(item.pos().y() for item in selected_blocks)
        
        # Move all blocks to that y position
        for item in selected_blocks:
            item.setPos(item.pos().x(), min_y)
            item.block.position.y = min_y
        
        self.model_changed.emit()
    
    def align_bottom(self):
        """Align selected blocks to the bottommost block"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 2:
            return
        
        # Find bottommost position (accounting for height)
        max_y = max(item.pos().y() + item.block.size.height for item in selected_blocks)
        
        # Move all blocks to that y position
        for item in selected_blocks:
            new_y = max_y - item.block.size.height
            item.setPos(item.pos().x(), new_y)
            item.block.position.y = new_y
        
        self.model_changed.emit()
    
    def align_horizontal_center(self):
        """Align selected blocks to horizontal center"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 2:
            return
        
        # Calculate center y position
        min_y = min(item.pos().y() for item in selected_blocks)
        max_y = max(item.pos().y() + item.block.size.height for item in selected_blocks)
        center_y = (min_y + max_y) / 2
        
        # Move all blocks to center
        for item in selected_blocks:
            new_y = center_y - item.block.size.height / 2
            item.setPos(item.pos().x(), new_y)
            item.block.position.y = new_y
        
        self.model_changed.emit()
    
    def align_vertical_center(self):
        """Align selected blocks to vertical center"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 2:
            return
        
        # Calculate center x position
        min_x = min(item.pos().x() for item in selected_blocks)
        max_x = max(item.pos().x() + item.block.size.width for item in selected_blocks)
        center_x = (min_x + max_x) / 2
        
        # Move all blocks to center
        for item in selected_blocks:
            new_x = center_x - item.block.size.width / 2
            item.setPos(new_x, item.pos().y())
            item.block.position.x = new_x
        
        self.model_changed.emit()
    
    def distribute_horizontally(self):
        """Distribute selected blocks evenly horizontally"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 3:
            return
        
        # Sort by x position
        sorted_blocks = sorted(selected_blocks, key=lambda item: item.pos().x())
        
        # Calculate spacing
        first_x = sorted_blocks[0].pos().x()
        last_x = sorted_blocks[-1].pos().x()
        total_space = last_x - first_x
        num_gaps = len(sorted_blocks) - 1
        spacing = total_space / num_gaps
        
        # Distribute
        for i, item in enumerate(sorted_blocks[1:-1], start=1):
            new_x = first_x + spacing * i
            item.setPos(new_x, item.pos().y())
            item.block.position.x = new_x
        
        self.model_changed.emit()
    
    def distribute_vertically(self):
        """Distribute selected blocks evenly vertically"""
        selected_blocks = [item for item in self.scene.selectedItems() if isinstance(item, BlockItem)]
        if len(selected_blocks) < 3:
            return
        
        # Sort by y position
        sorted_blocks = sorted(selected_blocks, key=lambda item: item.pos().y())
        
        # Calculate spacing
        first_y = sorted_blocks[0].pos().y()
        last_y = sorted_blocks[-1].pos().y()
        total_space = last_y - first_y
        num_gaps = len(sorted_blocks) - 1
        spacing = total_space / num_gaps
        
        # Distribute
        for i, item in enumerate(sorted_blocks[1:-1], start=1):
            new_y = first_y + spacing * i
            item.setPos(item.pos().x(), new_y)
            item.block.position.y = new_y
        
        self.model_changed.emit()

    # View operations
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level *= 1.2
        self.setTransform(self.transform().scale(1.2, 1.2))

    def zoom_out(self):
        """Zoom out"""
        self.zoom_level /= 1.2
        self.setTransform(self.transform().scale(1/1.2, 1/1.2))

    def zoom_reset(self):
        """Reset zoom to 100%"""
        self.resetTransform()
        self.zoom_level = 1.0

    def set_grid_visible(self, visible):
        """Set grid visibility"""
        self.grid_visible = visible
        self.viewport().update()

    def drawBackground(self, painter, rect):
        """Draw background with grid"""
        super().drawBackground(painter, rect)

        if self.grid_visible:
            # Draw grid
            grid_size = 20
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)

            pen = QPen(QColor("#E5E7EB"), 1)
            painter.setPen(pen)

            # Vertical lines
            x = left
            while x < rect.right():
                painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
                x += grid_size

            # Horizontal lines
            y = top
            while y < rect.bottom():
                painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
                y += grid_size

    def enter_agent_view(self, block_id: str):
        """Enter agent internal view - show FSMs, states, and sub-agents"""
        block = self.model.get_block_by_id(block_id)
        if not block:
            return

        # Push current scene state onto stack
        self.scene_stack.append((
            self.scene,
            self.current_mode,
            self.current_agent_id,
            self.selected_fsm_id
        ))

        # Create NEW scene for this agent's internal view
        agent_scene = QGraphicsScene()
        agent_scene.setSceneRect(0, 0, 2000, 2000)
        agent_scene.setBackgroundBrush(QBrush(QColor("#F5F3FF")))  # Slight purple tint

        # Switch to new scene
        self.setScene(agent_scene)
        self.scene = agent_scene

        # Update mode
        self.current_mode = "agent_internal"
        self.current_agent_id = block_id
        # Set current_fsm to first FSM for backward compatibility
        self.current_fsm = self.model.get_fsm_by_id(block.fsm_id) if block.fsm_id else None
        self.selected_fsm_id = block.fsm_id  # Auto-select first FSM if exists

        # Clear items from previous view
        self.state_items.clear()
        self.transition_items.clear()
        self.fsm_items.clear()

        # Load all FSM containers for this agent
        self._load_agent_fsms(block)

        # Load sub-agents as blocks (AnyLogic style)
        self._load_sub_agents(block)

        # Show ports at boundaries (interface layer)
        self._load_agent_ports(block)

        # Emit mode change signal
        self.mode_changed.emit("agent_internal")

        # Update status
        main_window = self._get_main_window()
        if main_window:
            main_window.statusBar().showMessage(f"Editing {block.name} internal view - Press ESC to return")

    def exit_agent_view(self):
        """Exit agent internal view - return to previous view"""
        if not self.scene_stack:
            return

        # Pop previous scene from stack
        previous_scene, previous_mode, previous_agent_id, previous_selected_fsm = self.scene_stack.pop()

        # Current scene will be garbage collected, no need to manually clear
        # This prevents the rendering issues from leftover items

        # Switch back to previous scene
        self.setScene(previous_scene)
        self.scene = previous_scene

        # Restore mode
        self.current_mode = previous_mode
        self.current_agent_id = previous_agent_id
        self.selected_fsm_id = previous_selected_fsm
        # Restore current_fsm for backward compatibility
        self.current_fsm = self.model.get_fsm_by_id(previous_selected_fsm) if previous_selected_fsm else None

        # Clear items (they belong to the discarded scene)
        self.state_items.clear()
        self.transition_items.clear()
        self.fsm_items.clear()

        # Emit mode change signal
        self.mode_changed.emit(self.current_mode)

        # Update status
        main_window = self._get_main_window()
        if main_window:
            if self.current_mode == "main":
                main_window.statusBar().showMessage("Returned to main view")
            else:
                # Returned to a nested agent view
                block = self.model.get_block_by_id(self.current_agent_id)
                if block:
                    main_window.statusBar().showMessage(f"Returned to {block.name} view")

    def _load_fsm_graphics(self):
        """Load FSM states and transitions as graphics items"""
        if not self.current_fsm:
            return

        from hsim.gui.items.state_item import StateItem
        from hsim.gui.items.transition_item import TransitionItem

        # Clear existing FSM graphics
        self.state_items.clear()
        self.transition_items.clear()

        # Create state items
        for state_id, state in self.current_fsm.states.items():
            state_item = StateItem(state)
            state_item.setPos(state.position.x, state.position.y)

            # Connect signals
            state_item.signals.position_changed.connect(
                lambda sid=state_id: self._on_fsm_state_moved(sid)
            )
            state_item.signals.selected.connect(self._on_fsm_state_selected)
            state_item.signals.deleted.connect(self._on_fsm_state_deleted)

            self.scene.addItem(state_item)
            self.state_items[state_id] = state_item

        # Create transition items
        for transition in self.current_fsm.transitions:
            if transition.from_state in self.state_items and transition.to_state in self.state_items:
                from_item = self.state_items[transition.from_state]
                to_item = self.state_items[transition.to_state]

                trans_item = TransitionItem(transition, from_item, to_item)

                # Connect state movements to transition update (FIX for Issue #1)
                from_item.signals.position_changed.connect(
                    lambda *args, t=trans_item: t.update_path()
                )
                to_item.signals.position_changed.connect(
                    lambda *args, t=trans_item: t.update_path()
                )

                trans_item.signals.selected.connect(self._on_fsm_transition_selected)
                trans_item.signals.deleted.connect(self._on_fsm_transition_deleted)
                trans_item.signals.properties_requested.connect(self._on_fsm_transition_properties)

                self.scene.addItem(trans_item)
                # Store by transition id if available, otherwise by from->to pair
                trans_key = transition.id if hasattr(transition, 'id') else f"{transition.from_state}->{transition.to_state}"
                self.transition_items[trans_key] = trans_item

    def _load_agent_ports(self, block):
        """Load agent ports at boundaries in internal view"""
        from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
        from PyQt6.QtGui import QFont

        # Get scene dimensions
        scene_rect = self.scene.sceneRect()
        width = scene_rect.width()
        height = scene_rect.height()

        # Get block's ports from main scene
        if block.id in self.block_items:
            block_item = self.block_items[block.id]

            # Create port visualizations at scene boundaries
            for port_name, port in block_item.ports.items():
                # Create visual port indicator
                port_radius = 20
                port_item = QGraphicsEllipseItem(-port_radius, -port_radius, port_radius * 2, port_radius * 2)

                # Color based on port type
                if port.port_type == "input":
                    port_item.setBrush(QBrush(QColor("#3B82F6")))  # Blue
                    port_item.setPen(QPen(QColor("white"), 3))
                    # Position on left boundary
                    port_item.setPos(100, height / 2)
                    label_text = f"IN: {port_name}"
                else:
                    port_item.setBrush(QBrush(QColor("#10B981")))  # Green
                    port_item.setPen(QPen(QColor("white"), 3))
                    # Position on right boundary
                    port_item.setPos(width - 100, height / 2)
                    label_text = f"OUT: {port_name}"

                port_item.setZValue(5)
                port_item.setToolTip(f"Agent {port.port_type} port: {port_name}")
                self.scene.addItem(port_item)

                # Add label
                label = QGraphicsTextItem(label_text)
                label.setDefaultTextColor(QColor("white"))
                font = QFont()
                font.setPointSize(10)
                font.setBold(True)
                label.setFont(font)

                # Position label near port
                if port.port_type == "input":
                    label.setPos(100 + port_radius + 5, height / 2 - 10)
                else:
                    label.setPos(width - 100 - label.boundingRect().width() - port_radius - 5, height / 2 - 10)

                label.setZValue(5)
                self.scene.addItem(label)

    def _create_fsm_container_at(self, x, y):
        """Create a new FSM container at the specified position"""
        if self.current_mode != "agent_internal" or not self.current_agent_id:
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("FSM containers can only be created inside an agent view", 5000)
            return

        # Snap to grid
        x, y = self.snap_to_grid(x, y)

        # Create FSM data model
        fsm = FSM(
            id=str(uuid.uuid4()),
            name=f"FSM_{len(self.model.fsms) + 1}",
            owner_block_id=self.current_agent_id,
            position=Position(x, y),
            size=Size(400, 300)
        )

        # Add to model
        self.model.add_fsm(fsm)

        # Add FSM ID to owner block's list
        owner_block = self.model.get_block_by_id(self.current_agent_id)
        if owner_block:
            if fsm.id not in owner_block.fsm_ids:
                owner_block.fsm_ids.append(fsm.id)

        # Create visual item
        fsm_item = FSMItem(fsm)
        fsm_item.signals.selected.connect(self._on_fsm_selected)
        fsm_item.signals.properties_requested.connect(self._on_fsm_properties_requested)
        fsm_item.signals.deleted.connect(self._on_fsm_deleted)

        self.scene.addItem(fsm_item)
        self.fsm_items[fsm.id] = fsm_item

        # Auto-select this FSM
        self.selected_fsm_id = fsm.id
        fsm_item.setSelected(True)

        main_window = self._get_main_window()
        if main_window:
            main_window.statusBar().showMessage(f"Created FSM: {fsm.name}. States will be added to this FSM.", 3000)

        self.model_changed.emit()

    def _on_fsm_selected(self, fsm_id):
        """Handle FSM selection - this FSM becomes the target for new states"""
        self.selected_fsm_id = fsm_id
        main_window = self._get_main_window()
        if main_window:
            fsm = self.model.get_fsm_by_id(fsm_id)
            if fsm:
                main_window.statusBar().showMessage(f"Selected FSM: {fsm.name}. New states will be added here.", 2000)

    def _on_fsm_properties_requested(self, fsm):
        """Handle request to edit FSM properties"""
        # TODO: Show FSM properties in properties panel
        main_window = self._get_main_window()
        if main_window:
            # For now, just show in properties panel
            if hasattr(main_window.properties_panel, 'show_fsm_properties'):
                main_window.properties_panel.show_fsm_properties(fsm)

    def _on_fsm_deleted(self, fsm_id):
        """Handle FSM deletion"""
        if fsm_id in self.fsm_items:
            fsm_item = self.fsm_items[fsm_id]
            self.scene.removeItem(fsm_item)
            del self.fsm_items[fsm_id]

        # Remove from model
        if fsm_id in self.model.fsms:
            fsm = self.model.fsms[fsm_id]
            # Remove from owner block
            if fsm.owner_block_id:
                owner_block = self.model.get_block_by_id(fsm.owner_block_id)
                if owner_block and fsm_id in owner_block.fsm_ids:
                    owner_block.fsm_ids.remove(fsm_id)
            del self.model.fsms[fsm_id]

        # Deselect if this was the selected FSM
        if self.selected_fsm_id == fsm_id:
            self.selected_fsm_id = None

        self.model_changed.emit()

    def _load_agent_fsms(self, owner_block):
        """Load all FSM containers for this agent"""
        # Load all FSMs that belong to this agent
        for fsm_id in owner_block.fsm_ids:
            fsm = self.model.get_fsm_by_id(fsm_id)
            if fsm:
                # Create FSM container item
                fsm_item = FSMItem(fsm)
                fsm_item.signals.selected.connect(self._on_fsm_selected)
                fsm_item.signals.properties_requested.connect(self._on_fsm_properties_requested)
                fsm_item.signals.deleted.connect(self._on_fsm_deleted)

                self.scene.addItem(fsm_item)
                self.fsm_items[fsm.id] = fsm_item

                # Load states and transitions for this FSM
                self._load_fsm_states_and_transitions(fsm)

    def _load_fsm_states_and_transitions(self, fsm):
        """Load states and transitions for a specific FSM"""
        from hsim.gui.items.state_item import StateItem
        from hsim.gui.items.transition_item import TransitionItem

        # Load states
        for state in fsm.states.values():
            state_item = StateItem(state)
            state_item.setPos(state.position.x, state.position.y)

            # Connect signals
            state_item.signals.position_changed.connect(
                lambda sid, x, y: self._on_fsm_state_moved(sid)
            )
            state_item.signals.selected.connect(self._on_fsm_state_selected)
            state_item.signals.deleted.connect(self._on_fsm_state_deleted)

            self.scene.addItem(state_item)
            self.state_items[state.id] = state_item

        # Load transitions
        for transition in fsm.transitions:
            from_state_item = self.state_items.get(transition.from_state)
            to_state_item = self.state_items.get(transition.to_state)

            if from_state_item and to_state_item:
                transition_item = TransitionItem(transition, from_state_item, to_state_item)
                transition_item.signals.properties_requested.connect(
                    lambda t: self._on_transition_properties_requested(t)
                )

                self.scene.addItem(transition_item)
                self.transition_items[transition.id] = transition_item

    def _load_sub_agents(self, parent_block):
        """Load sub-agents as blocks inside parent (AnyLogic style)"""
        for child_id in parent_block.children:
            child_block = self.model.get_block_by_id(child_id)
            if child_block:
                # Create block item for this sub-agent
                self.add_block_item(child_block)

        # Also load connections between sub-agents
        for connection in self.model.connections.values():
            # Only show connections between blocks in this agent
            from_block = self.model.get_block_by_id(connection.from_block)
            to_block = self.model.get_block_by_id(connection.to_block)

            if (from_block and to_block and
                from_block.parent_id == parent_block.id and
                to_block.parent_id == parent_block.id):
                # Both blocks are children of this agent
                self.add_connection_item(connection)

    def _create_state_at(self, x, y):
        """Create a new FSM state at the specified position"""
        # Check if there's a selected FSM
        if not self.selected_fsm_id:
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("No FSM selected. Create or select an FSM container first.", 5000)
            return

        # Get the selected FSM
        current_fsm = self.model.get_fsm_by_id(self.selected_fsm_id)
        if not current_fsm:
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("Selected FSM not found", 5000)
            return

        # Snap to grid
        x, y = self.snap_to_grid(x - 60, y - 30)  # Center on click, then snap

        # Create new state
        state = State(
            id=str(uuid.uuid4()),
            name=f"State{len(current_fsm.states) + 1}",
            position=Position(x, y),
            size=Size(120, 60),
            is_initial=len(current_fsm.states) == 0,  # First state is initial
            on_enter="# Enter actions",
            on_exit="# Exit actions",
            color="#3B82F6"  # Blue
        )

        # Add to FSM model
        current_fsm.add_state(state)

        # Create visual item
        from hsim.gui.items.state_item import StateItem
        state_item = StateItem(state)
        state_item.setPos(state.position.x, state.position.y)

        # Connect signals
        state_item.signals.position_changed.connect(
            lambda sid=state.id: self._on_fsm_state_moved(sid)
        )
        state_item.signals.selected.connect(self._on_fsm_state_selected)
        state_item.signals.deleted.connect(self._on_fsm_state_deleted)

        self.scene.addItem(state_item)
        self.state_items[state.id] = state_item

        # Emit model changed
        self.model_changed.emit()

        main_window = self._get_main_window()
        if main_window:
            main_window.statusBar().showMessage(f"Created state: {state.name}", 2000)

    def _start_transition_creation(self, click_pos):
        """Start transition creation by selecting source state"""
        item = self.itemAt(click_pos)

        # Find StateItem
        from hsim.gui.items.state_item import StateItem
        state_item = item
        while state_item and not isinstance(state_item, StateItem):
            state_item = state_item.parentItem() if hasattr(state_item, 'parentItem') else None

        if state_item and isinstance(state_item, StateItem):
            self.transition_source_state = state_item.state.id
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage(f"Transition from '{state_item.state.name}' - Click target state", 5000)
        else:
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("Click on a state to start transition", 3000)

    def _complete_transition_creation(self, click_pos):
        """Complete transition creation by selecting target state"""
        item = self.itemAt(click_pos)

        # Find StateItem
        from hsim.gui.items.state_item import StateItem
        state_item = item
        while state_item and not isinstance(state_item, StateItem):
            state_item = state_item.parentItem() if hasattr(state_item, 'parentItem') else None

        if state_item and isinstance(state_item, StateItem):
            target_state_id = state_item.state.id

            if target_state_id == self.transition_source_state:
                main_window = self._get_main_window()
                if main_window:
                    main_window.statusBar().showMessage("Cannot create self-transition", 3000)
                delattr(self, 'transition_source_state')
                self.create_mode = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return

            # Create transition
            from hsim.gui.models.model import Transition
            import uuid

            transition = Transition(
                id=str(uuid.uuid4()),
                from_state=self.transition_source_state,
                to_state=target_state_id,
                label="condition",
                transition_type="condition"
            )

            self.current_fsm.add_transition(transition)

            # Create visual item
            from hsim.gui.items.transition_item import TransitionItem
            source_item = self.state_items.get(self.transition_source_state)
            target_item = self.state_items.get(target_state_id)

            if source_item and target_item:
                transition_item = TransitionItem(transition, source_item, target_item)
                transition_item.signals.deleted.connect(self._on_fsm_transition_deleted)
                transition_item.signals.properties_requested.connect(self._on_fsm_transition_properties)

                self.scene.addItem(transition_item)
                self.transition_items[transition.id] = transition_item

                # Emit model changed
                self.model_changed.emit()

                main_window = self._get_main_window()
                if main_window:
                    source_name = self.current_fsm.states[self.transition_source_state].name
                    target_name = self.current_fsm.states[target_state_id].name
                    main_window.statusBar().showMessage(f"Created transition: {source_name} → {target_name}", 2000)

            # Clean up
            delattr(self, 'transition_source_state')
            self.create_mode = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("Click on a state to complete transition", 3000)

    def _create_port_at(self, click_pos):
        """Create a new port on a block"""
        item = self.itemAt(click_pos)

        # Find BlockItem
        from hsim.gui.items.block_item import BlockItem
        block_item = item
        while block_item and not isinstance(block_item, BlockItem):
            block_item = block_item.parentItem() if hasattr(block_item, 'parentItem') else None

        if block_item and isinstance(block_item, BlockItem):
            block = block_item.block
            port_type = "input" if self.create_mode == "input_port" else "output"

            # Count existing ports of this type
            port_count = sum(1 for p in block_item.ports.values() if p.port_type == port_type)
            port_name = f"{port_type}{port_count + 1}"

            # Add port to block item (this will create the visual port)
            block_item.add_port(port_name, port_type)

            # Emit model changed
            self.model_changed.emit()

            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage(f"Added {port_type} port '{port_name}' to {block.name}", 2000)
        else:
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("Click on a block to add port", 3000)

    def _on_fsm_state_moved(self, state_id):
        """Handle FSM state movement"""
        if self.current_fsm and state_id in self.current_fsm.states and state_id in self.state_items:
            state = self.current_fsm.states[state_id]
            item = self.state_items[state_id]
            state.position.x = item.pos().x()
            state.position.y = item.pos().y()

    def _on_fsm_state_selected(self, state_id):
        """Handle FSM state selection"""
        if self.current_fsm and state_id in self.current_fsm.states:
            state = self.current_fsm.states[state_id]
            # Show state properties in properties panel
            main_window = self._get_main_window()
            if main_window and hasattr(main_window, 'properties_panel'):
                main_window.properties_panel.show_state_properties(state)

    def _on_fsm_state_deleted(self, state_id):
        """Handle FSM state deletion"""
        if self.current_fsm:
            self.current_fsm.remove_state(state_id)
            self._load_fsm_graphics()

    def _on_fsm_transition_selected(self, transition_id):
        """Handle FSM transition selection"""
        if self.current_fsm:
            # Find transition by ID
            transition = None
            for trans in self.current_fsm.transitions:
                trans_key = trans.id if hasattr(trans, 'id') else f"{trans.from_state}->{trans.to_state}"
                if trans_key == transition_id:
                    transition = trans
                    break

            if transition:
                # Show transition properties in properties panel
                main_window = self._get_main_window()
                if main_window and hasattr(main_window, 'properties_panel'):
                    main_window.properties_panel.show_transition_properties(transition)

    def _on_fsm_transition_deleted(self, transition_id):
        """Handle FSM transition deletion"""
        if self.current_fsm:
            self.current_fsm.remove_transition(transition_id)
            self._load_fsm_graphics()

    def _on_fsm_transition_properties(self, transition):
        """Handle FSM transition properties request"""
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'properties_panel'):
            main_window.properties_panel.show_transition_properties(transition)

    def create_fsm_state(self):
        """Create a new state in the current FSM"""
        if not self.current_fsm:
            return

        from hsim.gui.models.model import State, Position, Size
        import uuid

        # Create new state with unique name
        state_count = len(self.current_fsm.states)
        state_name = f"State_{state_count + 1}"

        # Position new state in center of view
        view_center = self.viewport().rect().center()
        scene_pos = self.mapToScene(view_center)

        state = State(
            id=str(uuid.uuid4()),
            name=state_name,
            position=Position(x=scene_pos.x() - 50, y=scene_pos.y() - 25),  # Center the 100x50 state
            size=Size(width=100, height=50),
            color="#6366F1",  # Indigo
            is_initial=len(self.current_fsm.states) == 0  # First state is initial
        )

        self.current_fsm.add_state(state)
        self._load_fsm_graphics()

        # Select the new state
        if state.id in self.state_items:
            self.state_items[state.id].setSelected(True)

    def create_fsm_transition(self):
        """Create a transition between two selected states"""
        if not self.current_fsm:
            return

        # Find selected states
        selected_states = [item for item in self.scene.selectedItems()
                          if hasattr(item, 'state')]

        if len(selected_states) != 2:
            # Show message in status bar via main window
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage(
                    "Select exactly 2 states to create a transition", 3000
                )
            return

        from hsim.gui.models.model import Transition
        import uuid

        from_state = selected_states[0].state
        to_state = selected_states[1].state

        # Check if transition already exists
        for trans in self.current_fsm.transitions:
            if trans.from_state == from_state.id and trans.to_state == to_state.id:
                main_window = self._get_main_window()
                if main_window:
                    main_window.statusBar().showMessage(
                        f"Transition from {from_state.name} to {to_state.name} already exists", 3000
                    )
                return

        transition = Transition(
            id=str(uuid.uuid4()),
            from_state=from_state.id,
            to_state=to_state.id,
            condition="true",  # Default condition
            label=""
        )

        self.current_fsm.add_transition(transition)
        self._load_fsm_graphics()

    def keyPressEvent(self, event):
        """Handle key presses"""
        from PyQt6.QtCore import Qt as QtCore

        # ESC to exit agent view
        if event.key() == QtCore.Key.Key_Escape and self.current_mode == "agent_internal":
            self.exit_agent_view()
            event.accept()
        else:
            super().keyPressEvent(event)
