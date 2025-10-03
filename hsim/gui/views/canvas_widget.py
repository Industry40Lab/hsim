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
        block_def = get_block_definition(BlockType(block_type))

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
            from hsim.gui.models.model import State as FSMState
            fsm = FSM(
                id=str(uuid.uuid4()),
                name=f"{block.name} FSM",
                owner_block_id=block.id
            )

            # Create default Empty initial state (matching core implementation)
            empty_state = FSMState(
                id=str(uuid.uuid4()),
                name="Empty",
                position=Position(50, 50),
                size=Size(120, 60),
                is_initial=True,
                on_enter="",
                on_exit="",
                color="#3B82F6"
            )
            fsm.add_state(empty_state)

            block.fsm_id = fsm.id
            self.model.add_fsm(fsm)

        # Add to model
        self.model.add_block(block)

        # Add to canvas
        self.add_block_item(block)

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
