"""
Redesigned block graphics item - Icon-based with visible ports
"""

from PyQt6.QtWidgets import QGraphicsItem, QGraphicsItemGroup, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath

from hsim.gui.models.block_definitions import get_block_definition, BlockType
from hsim.gui.models.model import Block
from hsim.gui.items.port_item import PortItem


class BlockItemSignals(QObject):
    """Signals for BlockItemV2"""
    position_changed = pyqtSignal(str, float, float)  # block_id, x, y
    double_clicked = pyqtSignal(str)  # block_id
    properties_requested = pyqtSignal(object)  # block data
    deleted = pyqtSignal(str)  # block_id


class BlockItem(QGraphicsItemGroup):
    """Simplified icon-based block with visible ports"""

    def __init__(self, block: Block, parent=None):
        super().__init__(parent)
        self.block = block
        self.block_def = get_block_definition(BlockType(block.type))
        self.signals = BlockItemSignals()

        # Graphics elements
        self.background_item = None
        self.icon_item = None
        self.name_item = None
        self.ports = {}  # port_name -> PortItem

        # State
        self.is_selected = False
        self.is_hovering = False

        # Setup
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self.create_graphics()
        self.update_appearance()
        self.setPos(self.block.position.x, self.block.position.y)

    def create_graphics(self):
        """Create the graphical elements - simple icon + ports"""
        # Size: compact 60x60 icon
        size = 60
        self.block.size.width = size
        self.block.size.height = size

        # Background circle/square
        self.background_item = QGraphicsRectItem(0, 0, size, size)
        if self.block_def.shape == "circle":
            # Make it circular with painter path
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            # We'll use rounded rectangle for simplicity
            self.background_item.setRect(0, 0, size, size)
        else:
            self.background_item.setRect(0, 0, size, size)

        self.addToGroup(self.background_item)

        # Large emoji icon
        self.icon_item = QGraphicsTextItem(self.block_def.icon)
        font = QFont()
        font.setPointSize(32)  # Large icon
        self.icon_item.setFont(font)

        # Center icon
        icon_rect = self.icon_item.boundingRect()
        self.icon_item.setPos(
            (size - icon_rect.width()) / 2,
            (size - icon_rect.height()) / 2 - 5
        )
        self.addToGroup(self.icon_item)

        # Name below (smaller)
        self.name_item = QGraphicsTextItem(self.block.name)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        self.name_item.setFont(font)

        # Center name below block
        name_rect = self.name_item.boundingRect()
        self.name_item.setPos(
            (size - name_rect.width()) / 2,
            size + 2
        )
        self.addToGroup(self.name_item)

        # Create ports
        self.create_ports(size)

    def create_ports(self, size):
        """Create input and output ports"""
        # Input port on left
        # Don't use addToGroup() - it blocks mouse events!
        # Instead, use setParentItem() for positioning only
        input_port = PortItem(self.block.id, "input", "input")
        input_port.setParentItem(self)
        input_port.setPos(-5, size / 2)  # Left center
        self.ports["input"] = input_port

        # Output port on right
        output_port = PortItem(self.block.id, "next", "output")
        output_port.setParentItem(self)
        output_port.setPos(size + 5, size / 2)  # Right center
        self.ports["next"] = output_port

        # Ports will emit signals that canvas connects to
        # No need to connect here

    def on_port_drag_started(self, block_id, port_name):
        """Port drag started - notify canvas"""
        # This will be handled by canvas
        pass

    def on_port_drag_ended(self, block_id, port_name, target_port):
        """Port drag ended - create connection if valid target"""
        # This will be handled by canvas
        pass

    def update_appearance(self):
        """Update visual appearance based on state"""
        # Color from block definition
        color = QColor(self.block_def.color)

        if self.isSelected():
            # Selected: bright with thick border
            self.background_item.setBrush(QBrush(color))
            self.background_item.setPen(QPen(QColor("#2563EB"), 4))
        elif self.is_hovering:
            # Hovering: slightly brighter
            lighter = color.lighter(120)
            self.background_item.setBrush(QBrush(lighter))
            self.background_item.setPen(QPen(QColor("#60A5FA"), 2))
        else:
            # Normal: semi-transparent
            color.setAlpha(200)
            self.background_item.setBrush(QBrush(color))
            self.background_item.setPen(QPen(QColor("white"), 2))

        # Icon color
        self.icon_item.setDefaultTextColor(QColor("white"))

        # Name color
        if self.isSelected():
            self.name_item.setDefaultTextColor(QColor("#2563EB"))
        else:
            self.name_item.setDefaultTextColor(QColor("#374151"))

    def paint(self, painter, option, widget=None):
        """Custom paint for drop shadow"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw subtle drop shadow
        if not self.isSelected():
            shadow_color = QColor(0, 0, 0, 30)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(shadow_color))
            painter.drawRoundedRect(QRectF(2, 2, 60, 60), 8, 8)

        super().paint(painter, option, widget)

    def boundingRect(self):
        """Return bounding rectangle"""
        return QRectF(-10, -10, 80, 90)  # Include ports and name

    def shape(self):
        """Return shape for collision detection"""
        path = QPainterPath()
        path.addRect(0, 0, 60, 60)
        return path

    def hoverEnterEvent(self, event):
        """Mouse entered block"""
        self.is_hovering = True
        self.update_appearance()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Mouse left block"""
        self.is_hovering = False
        self.update_appearance()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.signals.double_clicked.emit(self.block.id)
            event.accept()

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_appearance()

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Snap to grid (20px grid)
            GRID_SIZE = 20
            new_pos = value
            snapped_x = round(new_pos.x() / GRID_SIZE) * GRID_SIZE
            snapped_y = round(new_pos.y() / GRID_SIZE) * GRID_SIZE
            return QPointF(snapped_x, snapped_y)

        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update block model
            pos = self.pos()
            self.block.position.x = pos.x()
            self.block.position.y = pos.y()
            self.signals.position_changed.emit(self.block.id, pos.x(), pos.y())

        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        """Handle right-click - Show properties"""
        from PyQt6.QtWidgets import QMenu

        menu = QMenu()

        # Properties
        props_action = menu.addAction("✏️ Edit Properties")
        props_action.triggered.connect(lambda: self.signals.properties_requested.emit(self.block))

        # Separator
        menu.addSeparator()

        # Delete
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.signals.deleted.emit(self.block.id))

        menu.exec(event.screenPos())
        event.accept()

    def get_port_scene_pos(self, port_name: str) -> QPointF:
        """Get the scene position of a port"""
        if port_name in self.ports:
            return self.ports[port_name].get_scene_center()
        return self.scenePos()

    def get_center_pos(self) -> QPointF:
        """Get the center position of the block in scene coordinates"""
        rect = self.boundingRect()
        center = QPointF(rect.center().x(), rect.center().y())
        return self.mapToScene(center)

    def add_port(self, port_name: str, port_type: str):
        """Add a new port to the block dynamically"""
        if port_name in self.ports:
            return  # Port already exists

        size = 60  # Block size

        # Create new port
        new_port = PortItem(self.block.id, port_name, port_type)
        new_port.setParentItem(self)

        # Position based on port type and existing ports of that type
        if port_type == "input":
            # Count existing input ports
            input_count = sum(1 for p in self.ports.values() if p.port_type == "input")
            # Stack vertically on left side
            y_offset = 15 + (input_count * 15)
            new_port.setPos(-5, y_offset)
        else:  # output
            # Count existing output ports
            output_count = sum(1 for p in self.ports.values() if p.port_type == "output")
            # Stack vertically on right side
            y_offset = 15 + (output_count * 15)
            new_port.setPos(size + 5, y_offset)

        self.ports[port_name] = new_port
