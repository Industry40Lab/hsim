#!/usr/bin/env python3
"""
Demo of the improved visual editor with:
- Icon-based blocks with visible ports
- Drag-drop connections from ports
- Code-focused properties panel
- Simpler, cleaner interface
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set Qt platform to offscreen for headless environments
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

from hsim.gui.models.model import SimulationModel, Block, Position, Size
from hsim.gui.models.block_definitions import BlockType, get_block_definition
from hsim.gui.items.block_item import BlockItem
from hsim.gui.views.properties_panel import PropertiesPanel
import uuid


class SimpleVisualEditor(QMainWindow):
    """Simple demo of the improved visual editor"""

    def __init__(self):
        super().__init__()
        self.model = SimulationModel(name="Demo Model")
        self.setup_ui()
        self.create_demo_blocks()

    def setup_ui(self):
        """Setup UI"""
        self.setWindowTitle("hsim Visual Editor - Improved Design")
        self.setGeometry(100, 100, 1400, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Simple palette
        left_panel = self.create_palette()
        left_panel.setMinimumWidth(180)
        left_panel.setMaximumWidth(200)

        # Center: Canvas
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 2000)
        self.scene.setBackgroundBrush(QBrush(QColor("#F5F5F5")))

        self.view = QGraphicsView(self.scene)
        from PyQt6.QtGui import QPainter
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Right: Properties panel
        self.properties_panel = PropertiesPanel()
        self.properties_panel.model = self.model
        self.properties_panel.setMinimumWidth(300)
        self.properties_panel.setMaximumWidth(400)

        splitter.addWidget(left_panel)
        splitter.addWidget(self.view)
        splitter.addWidget(self.properties_panel)

        splitter.setSizes([200, 800, 300])

        layout.addWidget(splitter)

        # Connect selection
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def create_palette(self):
        """Create simple palette"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #FAFAFA;
                border-right: 1px solid #E0E0E0;
            }
            QPushButton {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                text-align: left;
                font-size: 12px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
                border: 1px solid #BDBDBD;
            }
            QLabel {
                font-size: 11px;
                color: #757575;
                font-weight: bold;
                padding: 8px 4px 4px 4px;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Title
        title = QLabel("Components")
        title.setStyleSheet("font-size: 13px; color: #212121; font-weight: bold; padding: 4px;")
        layout.addWidget(title)

        # Categories
        categories = {
            "DES Blocks": [
                ("⚡ Generator", BlockType.GENERATOR),
                ("📦 Buffer", BlockType.BUFFER),
                ("⚙️ Server", BlockType.SERVER),
                ("🛑 Terminator", BlockType.TERMINATOR),
            ],
            "Resources": [
                ("🔧 Unreliable", BlockType.UNRELIABLE_MACHINE),
                ("✓ Quality", BlockType.QUALITY_MACHINE),
            ]
        }

        for cat_name, items in categories.items():
            cat_label = QLabel(cat_name)
            layout.addWidget(cat_label)

            for label, block_type in items:
                btn = QPushButton(label)
                btn.clicked.connect(lambda checked, bt=block_type: self.add_block(bt))
                layout.addWidget(btn)

        layout.addStretch()

        return widget

    def add_block(self, block_type: BlockType):
        """Add a block to the canvas"""
        block_def = get_block_definition(block_type)

        # Create block
        block = Block(
            id=str(uuid.uuid4()),
            type=block_type.value,
            name=f"{block_def.name}_{len(self.model.blocks) + 1}",
            position=Position(100 + len(self.model.blocks) * 150, 100),
            size=Size(60, 60),
            properties={prop.name: prop.default for prop in block_def.properties}
        )

        self.model.add_block(block)

        # Create visual item
        item = BlockItem(block)
        item.signals.properties_requested.connect(self.on_properties_requested)
        item.signals.deleted.connect(self.on_block_deleted)

        self.scene.addItem(item)

        print(f"Added {block.name} at ({block.position.x}, {block.position.y})")

    def create_demo_blocks(self):
        """Create some demo blocks"""
        self.add_block(BlockType.GENERATOR)
        self.add_block(BlockType.BUFFER)
        self.add_block(BlockType.SERVER)
        self.add_block(BlockType.TERMINATOR)

    def on_selection_changed(self):
        """Handle selection change"""
        selected = self.scene.selectedItems()
        if selected:
            for item in selected:
                if isinstance(item, BlockItem):
                    self.properties_panel.show_block_properties(item.block)
                    return
        self.properties_panel.show_block_properties(None)

    def on_properties_requested(self, block):
        """Show properties"""
        self.properties_panel.show_block_properties(block)

    def on_block_deleted(self, block_id):
        """Delete block"""
        self.model.remove_block(block_id)
        # Remove from scene
        for item in self.scene.items():
            if isinstance(item, BlockItem) and item.block.id == block_id:
                self.scene.removeItem(item)
                break


def main():
    print("\n" + "="*60)
    print("HSIM VISUAL EDITOR - IMPROVED DESIGN DEMO")
    print("="*60)
    print("\nFeatures:")
    print("  • Icon-based blocks with visible ports")
    print("  • Input ports (blue) on left, output ports (green) on right")
    print("  • Code-focused properties panel")
    print("  • Cleaner, simpler interface")
    print("  • No forms - just code!")
    print("\nNote: Running in offscreen mode for demo")
    print("="*60 + "\n")

    app = QApplication(sys.argv)

    window = SimpleVisualEditor()

    print("Window created successfully!")
    print("Blocks added to canvas:")
    for block_id, block in window.model.blocks.items():
        print(f"  - {block.name} ({block.type})")

    print("\nProperties panel is code-focused:")
    print("  - Properties tab: Edit as Python code")
    print("  - FSM tab: View state machine")
    print("  - Connections tab: See connection code")

    print("\nDemo complete! ✓")
    print("To use with display, change QT_QPA_PLATFORM or run on desktop\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
