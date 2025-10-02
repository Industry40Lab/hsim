"""
Graphics items for connections between blocks
"""

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QColor, QPainter, QPainterPath, QPolygonF
import math

from hsim.gui.models.model import Connection


class ConnectionItemSignals(QObject):
    """Signals for ConnectionItem"""
    deleted = pyqtSignal(str)  # connection_id


class ConnectionItem(QGraphicsPathItem):
    """Visual representation of a connection between blocks"""

    def __init__(self, connection: Connection, from_item, to_item, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.from_item = from_item
        self.to_item = to_item
        self.signals = ConnectionItemSignals()

        # Setup
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)  # Draw connections behind blocks

        # Connect to block movements
        self.from_item.signals.position_changed.connect(self.update_path)
        self.to_item.signals.position_changed.connect(self.update_path)

        self.update_path()

    def update_path(self, *args):
        """Update the connection path"""
        path = QPainterPath()

        # Get start and end points
        start = self.from_item.get_center_pos()
        end = self.to_item.get_center_pos()

        if self.connection.control_points:
            # Curved connection
            path.moveTo(start)
            for cp in self.connection.control_points:
                path.quadTo(QPointF(cp.x, cp.y), end)
        else:
            # Straight connection
            path.moveTo(start)
            path.lineTo(end)

            # Add arrowhead at the end
            self.add_arrowhead(path, start, end)

        self.setPath(path)
        self.update_appearance()

    def add_arrowhead(self, path, start, end):
        """Add an arrowhead at the end of the line"""
        # Calculate arrow angle
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())

        # Arrow size
        arrow_size = 10

        # Calculate arrow points
        p1 = end
        p2 = QPointF(
            end.x() - arrow_size * math.cos(angle - math.pi / 6),
            end.y() - arrow_size * math.sin(angle - math.pi / 6)
        )
        p3 = QPointF(
            end.x() - arrow_size * math.cos(angle + math.pi / 6),
            end.y() - arrow_size * math.sin(angle + math.pi / 6)
        )

        # Add arrow polygon
        arrow = QPolygonF([p1, p2, p3, p1])
        path.addPolygon(arrow)

    def update_appearance(self):
        """Update visual appearance"""
        color = QColor("#374151")
        if self.isSelected():
            pen = QPen(QColor("#3B82F6"), 3)
        else:
            pen = QPen(color, 2)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        brush = QColor("#374151") if not self.isSelected() else QColor("#3B82F6")
        self.setBrush(brush)

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_appearance()
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        """Handle right-click context menu"""
        menu = QMenu()

        # Edit label action
        edit_label_action = menu.addAction("Edit Label")
        edit_label_action.triggered.connect(self.edit_label)

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_connection)

        menu.exec(event.screenPos())

    def edit_label(self):
        """Edit connection label"""
        from PyQt6.QtWidgets import QInputDialog
        label, ok = QInputDialog.getText(
            None, "Edit Connection Label",
            "Enter label:",
            text=self.connection.label
        )
        if ok:
            self.connection.label = label
            # TODO: Display label on connection

    def delete_connection(self):
        """Delete this connection"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None, "Delete Connection",
            "Delete this connection?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.signals.deleted.emit(self.connection.id)
