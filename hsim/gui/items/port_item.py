"""
Port graphics items for connection points on blocks
"""

from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter


class PortItemSignals(QObject):
    """Signals for PortItem"""
    connection_drag_started = pyqtSignal(str, str)  # block_id, port_name
    connection_drag_ended = pyqtSignal(str, str, object)  # block_id, port_name, target_port


class PortItem(QGraphicsEllipseItem):
    """Visual port on a block for connections"""

    def __init__(self, block_id: str, port_name: str, port_type: str, parent=None):
        """
        Args:
            block_id: ID of the parent block
            port_name: Name of this port (e.g., 'input', 'output', 'next')
            port_type: 'input' or 'output'
            parent: Parent graphics item
        """
        # Increased from 10x10 to 14x14 for better visibility
        super().__init__(-7, -7, 14, 14, parent)  # 14x14 circle centered at (0,0)

        self.block_id = block_id
        self.port_name = port_name
        self.port_type = port_type  # 'input' or 'output'
        self.signals = PortItemSignals()

        # Visual settings - brighter colors for better visibility
        self.normal_color = QColor("#3B82F6") if port_type == "input" else QColor("#10B981")
        self.hover_color = QColor("#60A5FA") if port_type == "input" else QColor("#34D399")
        self.active_color = QColor("#2563EB") if port_type == "input" else QColor("#059669")

        self.setBrush(QBrush(self.normal_color))
        self.setPen(QPen(QColor("white"), 2.5))  # Thicker border for visibility

        # Interaction
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setZValue(10)  # Always on top

        # State
        self.is_hovering = False
        self.is_dragging = False

    def hoverEnterEvent(self, event):
        """Mouse entered port"""
        self.is_hovering = True
        self.setBrush(QBrush(self.hover_color))
        self.setPen(QPen(QColor("white"), 3.5))  # Thicker on hover
        self.setScale(1.4)  # Larger scale on hover
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Mouse left port"""
        if not self.is_dragging:
            self.is_hovering = False
            self.setBrush(QBrush(self.normal_color))
            self.setPen(QPen(QColor("white"), 2.5))
            self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Start dragging connection from this port"""
        if event.button() == Qt.MouseButton.LeftButton and self.port_type == "output":
            self.is_dragging = True
            self.setBrush(QBrush(self.active_color))
            self.signals.connection_drag_started.emit(self.block_id, self.port_name)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """End dragging connection"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False

            # Check if released over another port
            scene_pos = event.scenePos()
            items = self.scene().items(scene_pos)

            target_port = None
            for item in items:
                if isinstance(item, PortItem) and item != self and item.port_type == "input":
                    target_port = item
                    break

            self.signals.connection_drag_ended.emit(self.block_id, self.port_name, target_port)

            # Reset visual state
            if self.is_hovering:
                self.setBrush(QBrush(self.hover_color))
            else:
                self.setBrush(QBrush(self.normal_color))
                self.setPen(QPen(QColor("white"), 2.5))
                self.setScale(1.0)

        super().mouseReleaseEvent(event)

    def get_scene_center(self) -> QPointF:
        """Get the center position of this port in scene coordinates"""
        return self.scenePos() + QPointF(0, 0)  # Already centered due to (-5,-5,10,10)

    def paint(self, painter, option, widget=None):
        """Custom paint to add glow effect when hovering"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.is_hovering or self.is_dragging:
            # Draw multi-layer glow for better visibility
            glow_color = QColor(self.hover_color)

            # Outer glow (faint)
            glow_color.setAlpha(60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QRectF(-12, -12, 24, 24))

            # Middle glow (medium)
            glow_color.setAlpha(100)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QRectF(-10, -10, 20, 20))

            # Inner glow (bright)
            glow_color.setAlpha(150)
            painter.setBrush(QBrush(glow_color))
            painter.drawEllipse(QRectF(-8, -8, 16, 16))

        # Draw main port
        super().paint(painter, option, widget)
