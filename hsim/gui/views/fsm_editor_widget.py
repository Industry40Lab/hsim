"""
FSM Editor Widget - Editor for finite state machines
"""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush

from hsim.gui.models.model import FSM


class FSMEditorWidget(QGraphicsView):
    """Editor for finite state machines"""

    selection_changed = pyqtSignal(str, object)  # item_type, item_data

    def __init__(self, fsm: FSM = None, parent=None):
        super().__init__(parent)
        self.fsm = fsm
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.state_items = {}
        self.transition_items = {}

        self.setup_scene()
        self.setup_view()

        if fsm:
            self.load_fsm()

    def setup_scene(self):
        """Setup the graphics scene"""
        self.scene.setSceneRect(0, 0, 2000, 2000)
        self.scene.setBackgroundBrush(QBrush(QColor("#F9FAFB")))

    def setup_view(self):
        """Setup the view"""
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)

    def set_fsm(self, fsm: FSM):
        """Set the FSM to edit"""
        self.fsm = fsm
        self.load_fsm()

    def load_fsm(self):
        """Load FSM into editor"""
        self.scene.clear()
        self.state_items.clear()
        self.transition_items.clear()

        if not self.fsm:
            # Show placeholder
            label = QLabel("Select a block with FSM to edit")
            label.setStyleSheet("color: #9CA3AF; font-size: 14px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            proxy = self.scene.addWidget(label)
            proxy.setPos(500, 500)
            return

        # TODO: Load states and transitions
        # For now, show placeholder
        label = QLabel(f"FSM Editor for {self.fsm.name}\\n(Implementation in progress)")
        label.setStyleSheet("color: #6B7280; font-size: 14px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        proxy = self.scene.addWidget(label)
        proxy.setPos(500, 500)

    def delete_selected(self):
        """Delete selected items"""
        # TODO: Implement deletion
        pass

    def zoom_in(self):
        """Zoom in"""
        self.scale(1.2, 1.2)

    def zoom_out(self):
        """Zoom out"""
        self.scale(1/1.2, 1/1.2)

    def zoom_reset(self):
        """Reset zoom"""
        self.resetTransform()

    def set_grid_visible(self, visible):
        """Set grid visibility"""
        # TODO: Implement grid
        pass
