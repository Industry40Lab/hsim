"""
Simple, clean component palette
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDrag

from hsim.gui.models.block_definitions import BLOCK_DEFINITIONS, BlockType


class SimplePaletteWidget(QWidget):
    """Simple component palette with icon buttons"""

    block_selected = pyqtSignal(str)  # Emits block type

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                border-right: 1px solid #E0E0E0;
            }
            QPushButton {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 10px;
                text-align: left;
                font-size: 12px;
                margin: 2px 4px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
                border: 1px solid #BDBDBD;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
            QLabel {
                font-size: 11px;
                color: #757575;
                font-weight: bold;
                padding: 12px 8px 4px 8px;
            }
        """)

        # Title
        title = QLabel("Components")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #212121;
                font-weight: bold;
                padding: 12px 8px;
                background-color: #FAFAFA;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        # Content
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(2)

        # Group blocks by category
        categories = {}
        for block_type, block_def in BLOCK_DEFINITIONS.items():
            if block_def.category not in categories:
                categories[block_def.category] = []
            categories[block_def.category].append((block_type, block_def))

        # Add category sections
        for category, items in categories.items():
            # Category header
            cat_label = QLabel(category)
            content_layout.addWidget(cat_label)

            # Block buttons
            for block_type, block_def in items:
                btn = QPushButton(f"{block_def.icon}  {block_def.name}")
                btn.clicked.connect(lambda checked, bt=block_type.value: self.block_selected.emit(bt))
                btn.setToolTip(block_def.description)
                content_layout.addWidget(btn)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)
