"""
Model Canvas - Main workspace for drag-drop block design
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

from hsim.gui.models.model import SimulationModel, Block, Connection, Position, Size, FSM
from hsim.gui.models.block_definitions import BlockType, get_block_definition
from hsim.gui.items.block_item import BlockItem  # Use new version
from hsim.gui.items.connection_item import ConnectionItem
from hsim.gui.items.port_item import PortItem
import uuid


class CanvasWidget(QGraphicsView):
    """Canvas for designing simulation models"""

    selection_changed = pyqtSignal(object)  # Emits selected block
    block_double_clicked = pyqtSignal(str)  # Emits block ID
    model_changed = pyqtSignal()  # Emits when model changes
    mode_changed = pyqtSignal(str)  # Emits "main" or "agent_internal"

    def __init__(self, model: SimulationModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # State
        self.block_items = {}  # block_id -> BlockItem
        self.connection_items = {}  # connection_id -> ConnectionItem
        self.create_mode = None  # Block type to create on click
        self.connection_mode = False
        self.connection_from = None
        self.grid_visible = True
        self.zoom_level = 1.0

        # Canvas mode (main process flow or agent internal FSM view)
        self.current_mode = "main"  # "main" or "agent_internal"
        self.current_agent_id = None  # ID of agent being edited in internal view
        self.current_fsm = None  # FSM being displayed in internal view
        self.state_items = {}  # state_id -> StateItem (in FSM view)
        self.transition_items = {}  # transition_id -> TransitionItem (in FSM view)

        # Scene stack for nested agent editing
        self.scene_stack = []  # Stack of (scene, mode, agent_id, fsm) tuples
        self.main_scene = self.scene  # Save reference to main scene

        self.setup_scene()
        self.setup_view()
        self.load_model()

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
        for connection in self.model.connections:
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

    def start_connection_mode(self, from_block_id: str):
        """Start connection creation mode"""
        self.connection_mode = True
        self.connection_from = from_block_id
        self.setCursor(Qt.CursorShape.CrossCursor)

        # Show status message
        from_block = self.model.get_block_by_id(from_block_id)
        if from_block:
            window = self._get_main_window()
            if window:
                window.statusBar().showMessage(
                    f"Creating connection from '{from_block.name}' - Click target block"
                )

    def complete_connection(self, to_block_id: str):
        """Complete connection creation"""
        if not self.connection_from or to_block_id == self.connection_from:
            self.cancel_connection_mode()
            return

        # Create connection in model
        conn = Connection(
            id=str(uuid.uuid4()),
            from_block=self.connection_from,
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
                # Create new block at click position
                scene_pos = self.mapToScene(event.pos())
                self.create_block_at(self.create_mode, scene_pos.x(), scene_pos.y())

                # Exit create mode
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

        # Create block data
        block = Block(
            id=str(uuid.uuid4()),
            type=block_type,
            name=f"{block_def.name} {len(self.model.blocks) + 1}",
            position=Position(x - 50, y - 40),  # Center on click
            size=Size(100, 80),
            properties={prop.name: prop.default for prop in block_def.properties}
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

    def delete_selected(self):
        """Delete selected items"""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, BlockItem):
                self.on_block_deleted(item.block.id)
            elif isinstance(item, ConnectionItem):
                self.on_connection_deleted(item.connection.id)

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
        """Enter agent internal view - show FSM statechart"""
        block = self.model.get_block_by_id(block_id)
        if not block or not block.fsm_id:
            return

        fsm = self.model.get_fsm_by_id(block.fsm_id)
        if not fsm:
            return

        # Push current scene state onto stack
        self.scene_stack.append((
            self.scene,
            self.current_mode,
            self.current_agent_id,
            self.current_fsm
        ))

        # Create NEW scene for this agent's FSM
        fsm_scene = QGraphicsScene()
        fsm_scene.setSceneRect(0, 0, 2000, 2000)
        fsm_scene.setBackgroundBrush(QBrush(QColor("#F5F3FF")))  # Slight purple tint

        # Switch to new scene
        self.setScene(fsm_scene)
        self.scene = fsm_scene

        # Update mode
        self.current_mode = "agent_internal"
        self.current_agent_id = block_id
        self.current_fsm = fsm

        # Clear state/transition items from previous view
        self.state_items.clear()
        self.transition_items.clear()

        # Load FSM into NEW scene
        self._load_fsm_graphics()

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
        previous_scene, previous_mode, previous_agent_id, previous_fsm = self.scene_stack.pop()

        # Current scene will be garbage collected, no need to manually clear
        # This prevents the rendering issues from leftover items

        # Switch back to previous scene
        self.setScene(previous_scene)
        self.scene = previous_scene

        # Restore mode
        self.current_mode = previous_mode
        self.current_agent_id = previous_agent_id
        self.current_fsm = previous_fsm

        # Clear state/transition items (they belong to the discarded scene)
        self.state_items.clear()
        self.transition_items.clear()

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
