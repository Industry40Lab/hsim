"""
Component Palette - Toolbox with all available DES blocks and agents
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize
from PyQt6.QtGui import QDrag, QPainter, QColor, QFont

from hsim.gui.models.block_definitions import (
    BlockType, get_blocks_by_category, get_block_definition
)


class BlockPaletteItem(QPushButton):
    """A draggable block item in the palette"""

    def __init__(self, block_def, parent=None):
        super().__init__(parent)
        self.block_def = block_def

        # Set up appearance
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {block_def.color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
                text-align: left;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(block_def.color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(block_def.color, 0.3)};
            }}
        """)

        # Set text
        self.setText(f"{block_def.icon}  {block_def.name}")

        # Enable drag
        self.setAcceptDrops(False)

    def _darken_color(self, hex_color, factor=0.2):
        """Darken a hex color"""
        color = QColor(hex_color)
        h, s, v, a = color.getHsv()
        v = int(v * (1 - factor))
        color.setHsv(h, s, v, a)
        return color.name()

    def mousePressEvent(self, event):
        """Handle mouse press to initiate drag"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move to start drag operation"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.block_def.type.value)
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        # Execute drag
        drag.exec(Qt.DropAction.CopyAction)


class CategorySection(QWidget):
    """A collapsible category section in the palette"""

    def __init__(self, category_name, blocks, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.blocks = blocks
        self.expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 5)
        layout.setSpacing(2)

        # Category header
        self.header = QPushButton(f"▼ {category_name}")
        self.header.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: white;
                border: none;
                padding: 8px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)
        self.header.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.header)

        # Container for block items
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(5)

        # Add block items
        for block_def in blocks:
            item = BlockPaletteItem(block_def)
            self.content_layout.addWidget(item)

        layout.addWidget(self.content)

    def toggle_expanded(self):
        """Toggle section expansion"""
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)
        arrow = "▼" if self.expanded else "▶"
        self.header.setText(f"{arrow} {self.category_name}")


class PaletteWidget(QWidget):
    """Component palette with all available blocks"""

    block_selected = pyqtSignal(str)  # Emits block type when selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("Component Palette")
        title.setStyleSheet("""
            QLabel {
                background-color: #1F2937;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Scroll area for categories
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #F3F4F6;
                border: none;
            }
        """)

        # Container for categories
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)

        # Get blocks by category
        categories = get_blocks_by_category()

        # Define category order
        category_order = ["DES Blocks", "Resources", "Advanced", "Agents"]

        # Add category sections
        for category_name in category_order:
            if category_name in categories:
                section = CategorySection(category_name, categories[category_name])
                container_layout.addWidget(section)

        # Add any remaining categories
        for category_name, blocks in categories.items():
            if category_name not in category_order:
                section = CategorySection(category_name, blocks)
                container_layout.addWidget(section)

        # Add stretch to push everything to the top
        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Info label at bottom
        info_label = QLabel("Drag blocks onto canvas")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #E5E7EB;
                color: #6B7280;
                padding: 8px;
                font-size: 11px;
            }
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
