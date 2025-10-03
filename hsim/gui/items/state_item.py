"""
State graphics item for FSM/Agent editor
"""

from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath

from hsim.gui.models.model import State as FSMState


class StateItemSignals(QObject):
    """Signals for StateItem"""
    position_changed = pyqtSignal(str, float, float)  # state_id, x, y
    selected = pyqtSignal(str)  # state_id
    double_clicked = pyqtSignal(str)  # state_id
    deleted = pyqtSignal(str)  # state_id


class StateItem(QGraphicsRectItem):
    """Visual representation of an FSM state"""

    def __init__(self, state: FSMState, parent=None):
        super().__init__(0, 0, state.size.width, state.size.height, parent)
        self.state = state
        self.signals = StateItemSignals()

        # Rounded corners
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        # Appearance
        self.update_appearance()

        # Text label
        self.label = QGraphicsTextItem(state.name, self)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setDefaultTextColor(QColor("white"))

        # Center text
        label_rect = self.label.boundingRect()
        self.label.setPos(
            (state.size.width - label_rect.width()) / 2,
            (state.size.height - label_rect.height()) / 2
        )

        # Position on canvas
        self.setPos(state.position.x, state.position.y)

    def update_appearance(self):
        """Update visual appearance"""
        # Color
        color = QColor(self.state.color)

        # Initial state = green border
        if self.state.is_initial:
            self.setPen(QPen(QColor("#10B981"), 4))
            self.setBrush(QBrush(QColor("#10B981").lighter(140)))
        else:
            self.setPen(QPen(QColor(self.state.color), 2))
            self.setBrush(QBrush(color.lighter(150)))

        # Selected state = blue glow
        if self.isSelected():
            self.setPen(QPen(QColor("#2563EB"), 4))

    def paint(self, painter, option, widget=None):
        """Custom paint for rounded corners"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw rounded rectangle
        rect = self.rect()
        path = QPainterPath()
        path.addRoundedRect(rect, 8, 8)

        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawPath(path)

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos = self.pos()
            self.state.position.x = pos.x()
            self.state.position.y = pos.y()
            self.signals.position_changed.emit(self.state.id, pos.x(), pos.y())

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self.update_appearance()
            if self.isSelected():
                self.signals.selected.emit(self.state.id)

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.signals.double_clicked.emit(self.state.id)
            event.accept()

    def contextMenuEvent(self, event):
        """Handle right-click"""
        from PyQt6.QtWidgets import QMenu

        menu = QMenu()

        delete_action = menu.addAction("🗑️ Delete State")
        delete_action.triggered.connect(lambda: self.signals.deleted.emit(self.state.id))

        menu.exec(event.screenPos())
        event.accept()
