"""
FSM Container graphics item - visual container for states and transitions
"""

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QFont

from hsim.gui.models.model import FSM


class FSMItemSignals(QObject):
    """Signals for FSMItem"""
    selected = pyqtSignal(str)  # fsm_id
    position_changed = pyqtSignal(str, float, float)  # fsm_id, x, y
    properties_requested = pyqtSignal(object)  # FSM object
    deleted = pyqtSignal(str)  # fsm_id


class FSMItem(QGraphicsRectItem):
    """Visual representation of an FSM container"""

    def __init__(self, fsm: FSM, parent=None):
        super().__init__(parent)
        self.fsm = fsm
        self.signals = FSMItemSignals()

        # Visual properties
        self.setRect(0, 0, fsm.size.width, fsm.size.height)
        self.setPos(fsm.position.x, fsm.position.y)

        # Appearance - semi-transparent container
        self.setPen(QPen(QColor("#3B82F6"), 2, Qt.PenStyle.DashLine))
        self.setBrush(QBrush(QColor(59, 130, 246, 30)))  # Light blue with transparency

        # Interaction
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(-10)  # Behind states and transitions but in front of canvas

        # Title label
        self.title_label = QGraphicsTextItem(fsm.name, self)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setDefaultTextColor(QColor("#3B82F6"))
        self.title_label.setPos(5, -20)  # Above the container

        # Resize handle (future enhancement)
        self.is_resizing = False

    def itemChange(self, change, value):
        """Handle item changes (movement, selection)"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = value
            self.fsm.position.x = pos.x()
            self.fsm.position.y = pos.y()
            self.signals.position_changed.emit(self.fsm.id, pos.x(), pos.y())
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:  # Selected
                self.setPen(QPen(QColor("#2563EB"), 3, Qt.PenStyle.DashLine))
                self.signals.selected.emit(self.fsm.id)
            else:  # Deselected
                self.setPen(QPen(QColor("#3B82F6"), 2, Qt.PenStyle.DashLine))
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click - request properties"""
        self.signals.properties_requested.emit(self.fsm)
        event.accept()

    def contextMenuEvent(self, event):
        """Show context menu"""
        menu = QMenu()

        rename_action = menu.addAction("✏️ Rename FSM")
        rename_action.triggered.connect(lambda: self.signals.properties_requested.emit(self.fsm))

        menu.addSeparator()

        delete_action = menu.addAction("🗑️ Delete FSM")
        delete_action.triggered.connect(lambda: self.signals.deleted.emit(self.fsm.id))

        menu.exec(event.screenPos())
        event.accept()

    def update_title(self, name: str):
        """Update the FSM title"""
        self.fsm.name = name
        self.title_label.setPlainText(name)

    def update_size(self, width: float, height: float):
        """Update the FSM container size"""
        self.fsm.size.width = width
        self.fsm.size.height = height
        self.setRect(0, 0, width, height)

    def contains_point(self, point):
        """Check if a point is inside this FSM container"""
        rect = QRectF(self.x(), self.y(), self.fsm.size.width, self.fsm.size.height)
        return rect.contains(point)
