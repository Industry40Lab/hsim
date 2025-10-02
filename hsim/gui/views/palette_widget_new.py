"""
Component Palette - Professional toolbox with visual block representations
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize, QRectF, QPointF
from PyQt6.QtGui import (
    QDrag, QPainter, QColor, QFont, QPen, QBrush, QPainterPath,
    QLinearGradient
)

from hsim.gui.models.block_definitions import (
    BlockType, get_blocks_by_category, get_block_definition
)


class BlockPreviewItem(QGraphicsItem):
    """Visual preview of a block in the palette"""

    def __init__(self, block_def, parent=None):
        super().__init__(parent)
        self.block_def = block_def
        self.hover = False
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(0, 0, 80, 70)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw shape based on block type
        color = QColor(self.block_def.color)
        if self.hover:
            color = color.lighter(110)

        # Create gradient
        gradient = QLinearGradient(0, 0, 0, 60)
        gradient.setColorAt(0, color.lighter(120))
        gradient.setColorAt(1, color)

        pen = QPen(color.darker(130), 2)
        brush = QBrush(gradient)

        painter.setPen(pen)
        painter.setBrush(brush)

        if self.block_def.shape == "circle":
            painter.drawEllipse(QRectF(10, 5, 60, 60))
        elif self.block_def.shape == "rounded":
            painter.drawRoundedRect(QRectF(10, 5, 60, 60), 10, 10)
        else:  # rectangle
            painter.drawRect(QRectF(10, 5, 60, 60))

        # Draw icon
        painter.setPen(QPen(QColor("white")))
        font = QFont()
        font.setPointSize(20)
        painter.setFont(font)
        painter.drawText(QRectF(10, 5, 60, 60), Qt.AlignmentFlag.AlignCenter, self.block_def.icon)

    def hoverEnterEvent(self, event):
        self.hover = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hover = False
        self.update()


class PaletteBlockWidget(QWidget):
    """Widget representing a single block type in the palette"""

    clicked = pyqtSignal(str)  # Emits block type

    def __init__(self, block_def, parent=None):
        super().__init__(parent)
        self.block_def = block_def
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Create mini preview
        scene = QGraphicsScene()
        preview_item = BlockPreviewItem(self.block_def)
        scene.addItem(preview_item)
        scene.setSceneRect(0, 0, 80, 70)

        preview = QGraphicsView(scene)
        preview.setFixedSize(90, 80)
        preview.setFrameShape(QFrame.Shape.NoFrame)
        preview.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        preview.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        preview.setStyleSheet("background: transparent;")
        preview.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name label
        name_label = QLabel(self.block_def.name)
        name_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        # Description tooltip
        self.setToolTip(self.block_def.description)

        # Enable drag
        self.setAcceptDrops(False)

        # Style
        self.setStyleSheet("""
            PaletteBlockWidget {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 5px;
            }
            PaletteBlockWidget:hover {
                background: #F9FAFB;
                border: 2px solid #3B82F6;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
            self.clicked.emit(self.block_def.type.value)

    def mouseMoveEvent(self, event):
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


class CategoryWidget(QWidget):
    """Professional category widget with grid layout"""

    def __init__(self, category_name, blocks, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.blocks = blocks
        self.expanded = True
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4B5563, stop:1 #374151);
                border-radius: 3px;
            }
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(8, 5, 8, 5)

        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_expanded)
        header_layout.addWidget(self.toggle_btn)

        title_label = QLabel(self.category_name)
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Count badge
        count_label = QLabel(str(len(self.blocks)))
        count_label.setFixedSize(25, 20)
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setStyleSheet("""
            QLabel {
                background: #3B82F6;
                color: white;
                font-size: 10px;
                font-weight: bold;
                border-radius: 10px;
            }
        """)
        header_layout.addWidget(count_label)

        layout.addWidget(header_widget)

        # Content container
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(8)

        # Add blocks in grid (2 columns)
        row_widget = None
        row_layout = None

        for i, block_def in enumerate(self.blocks):
            if i % 2 == 0:
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                content_layout.addWidget(row_widget)

            block_widget = PaletteBlockWidget(block_def)
            block_widget.setFixedSize(100, 110)
            row_layout.addWidget(block_widget)

        # Add stretch to last row if needed
        if row_layout and len(self.blocks) % 2 == 1:
            row_layout.addStretch()

        content_layout.addStretch()
        layout.addWidget(self.content_widget)

    def toggle_expanded(self):
        self.expanded = not self.expanded
        self.content_widget.setVisible(self.expanded)
        self.toggle_btn.setText("▼" if self.expanded else "▶")


class PaletteWidget(QWidget):
    """Professional component palette"""

    block_selected = pyqtSignal(str)  # Emits block type when selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1F2937, stop:1 #111827);
            }
        """)
        title_layout = QVBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("📦 Components")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title)

        subtitle = QLabel("Drag onto canvas")
        subtitle.setStyleSheet("""
            QLabel {
                color: #9CA3AF;
                font-size: 10px;
            }
        """)
        title_layout.addWidget(subtitle)

        layout.addWidget(title_bar)

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
        container_layout.setSpacing(10)

        # Get blocks by category
        categories = get_blocks_by_category()

        # Define category order
        category_order = ["DES Blocks", "Resources", "Advanced", "Agents"]

        # Add category sections
        for category_name in category_order:
            if category_name in categories:
                section = CategoryWidget(category_name, categories[category_name])
                container_layout.addWidget(section)

        # Add any remaining categories
        for category_name, blocks in categories.items():
            if category_name not in category_order:
                section = CategoryWidget(category_name, blocks)
                container_layout.addWidget(section)

        # Add stretch to push everything to the top
        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)
