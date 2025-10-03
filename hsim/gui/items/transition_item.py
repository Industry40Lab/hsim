"""
Transition graphics item for FSM/Agent editor
"""

from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsTextItem, QGraphicsItem
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QObject
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPainterPath, QPolygonF

from hsim.gui.models.model import Transition
import math


class TransitionItemSignals(QObject):
    """Signals for TransitionItem"""
    selected = pyqtSignal(str)  # transition_id
    deleted = pyqtSignal(str)  # transition_id


class TransitionItem(QGraphicsPathItem):
    """Visual representation of an FSM transition"""

    def __init__(self, transition: Transition, from_state_item, to_state_item, parent=None):
        super().__init__(parent)
        self.transition = transition
        self.from_state = from_state_item
        self.to_state = to_state_item
        self.signals = TransitionItemSignals()

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Appearance
        self.setPen(QPen(QColor("#6B7280"), 2))
        self.setZValue(-1)  # Behind states

        # Label
        self.label = None
        if transition.label:
            self.label = QGraphicsTextItem(transition.label, self)
            font = QFont()
            font.setPointSize(10)
            self.label.setFont(font)
            self.label.setDefaultTextColor(QColor("#374151"))

        self.update_path()

    def update_path(self):
        """Update the arrow path between states"""
        # Get centers of states
        from_rect = self.from_state.sceneBoundingRect()
        to_rect = self.to_state.sceneBoundingRect()

        from_center = from_rect.center()
        to_center = to_rect.center()

        # Calculate intersection points with state borders
        from_point = self.get_border_point(from_rect, from_center, to_center)
        to_point = self.get_border_point(to_rect, to_center, from_center)

        # Create curved path
        path = QPainterPath()
        path.moveTo(from_point)

        # Control points for curve
        dx = to_point.x() - from_point.x()
        dy = to_point.y() - from_point.y()

        ctrl1 = QPointF(from_point.x() + dx * 0.3, from_point.y())
        ctrl2 = QPointF(from_point.x() + dx * 0.7, to_point.y())

        path.cubicTo(ctrl1, ctrl2, to_point)

        # Add arrowhead
        arrow_size = 12
        angle = math.atan2(to_point.y() - ctrl2.y(), to_point.x() - ctrl2.x())

        arrow_p1 = QPointF(
            to_point.x() - arrow_size * math.cos(angle - math.pi / 6),
            to_point.y() - arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = QPointF(
            to_point.x() - arrow_size * math.cos(angle + math.pi / 6),
            to_point.y() - arrow_size * math.sin(angle + math.pi / 6)
        )

        arrow_head = QPolygonF([to_point, arrow_p1, arrow_p2])
        path.addPolygon(arrow_head)

        self.setPath(path)

        # Position label at midpoint
        if self.label:
            mid_x = (from_point.x() + to_point.x()) / 2
            mid_y = (from_point.y() + to_point.y()) / 2
            label_rect = self.label.boundingRect()
            self.label.setPos(mid_x - label_rect.width() / 2, mid_y - label_rect.height() / 2)

    def get_border_point(self, rect, from_center, to_center):
        """Get point on rectangle border along line from from_center to to_center"""
        # Simple approach: use rect center for now
        # TODO: Calculate actual intersection with rounded rect border
        return rect.center()

    def itemChange(self, change, value):
        """Handle item changes"""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if self.isSelected():
                self.setPen(QPen(QColor("#2563EB"), 3))
                self.signals.selected.emit(self.transition.id)
            else:
                self.setPen(QPen(QColor("#6B7280"), 2))

        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        """Handle right-click"""
        from PyQt6.QtWidgets import QMenu

        menu = QMenu()

        delete_action = menu.addAction("🗑️ Delete Transition")
        delete_action.triggered.connect(lambda: self.signals.deleted.emit(self.transition.id))

        menu.exec(event.screenPos())
        event.accept()
