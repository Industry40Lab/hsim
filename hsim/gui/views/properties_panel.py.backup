"""
Code-focused Properties Panel - Simple code editor approach
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QScrollArea, QFrame, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class PropertiesPanel(QWidget):
    """Code-focused properties panel for editing agents"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self.model = None

        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Modern dark styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QLabel {
                color: #D4D4D4;
                font-size: 12px;
            }
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                padding: 6px;
                color: #D4D4D4;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #007ACC;
            }
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                padding: 8px;
                color: #D4D4D4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 1px solid #007ACC;
            }
            QTabWidget::pane {
                border: 1px solid #3E3E3E;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #D4D4D4;
                padding: 8px 16px;
                border: 1px solid #3E3E3E;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border-bottom: 2px solid #007ACC;
            }
            QTabBar::tab:hover {
                background-color: #3E3E3E;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)

        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: #2D2D2D; border-bottom: 1px solid #3E3E3E;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 8, 12, 8)

        title_label = QLabel("Properties")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFFFFF;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addWidget(title_bar)

        # Content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)

        # Empty state
        self.empty_label = QLabel("Select a block to edit properties")
        self.empty_label.setStyleSheet("color: #808080; padding: 40px 20px; font-size: 12px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.empty_label)

        layout.addWidget(self.content_widget)

    def clear_properties(self):
        """Clear all property widgets"""
        # Clear layout
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_block_properties(self, block):
        """Show properties for a block - code-focused approach"""
        self.current_item = block
        self.clear_properties()

        if block is None:
            self.empty_label = QLabel("Select a block to edit properties")
            self.empty_label.setStyleSheet("color: #808080; padding: 40px 20px; font-size: 12px;")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(self.empty_label)
            return

        # Name field
        name_label = QLabel("Name:")
        name_edit = QLineEdit(block.name)
        name_edit.textChanged.connect(lambda text: setattr(block, 'name', text))
        self.content_layout.addWidget(name_label)
        self.content_layout.addWidget(name_edit)

        # Type info
        type_label = QLabel(f"Type: {block.type.replace('_', ' ').title()}")
        type_label.setStyleSheet("color: #808080; font-size: 11px; padding: 4px 0;")
        self.content_layout.addWidget(type_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #3E3E3E; margin: 8px 0;")
        self.content_layout.addWidget(sep)

        # Tabs for different code sections
        tabs = QTabWidget()

        # Properties code tab
        props_tab = QTextEdit()
        props_tab.setPlaceholderText("# Block properties as Python code\n# Example:\nserviceTime = 2.0\ncapacity = 10")

        # Convert current properties to code
        props_code = self._properties_to_code(block.properties)
        props_tab.setPlainText(props_code)
        props_tab.textChanged.connect(lambda: self._update_properties_from_code(block, props_tab.toPlainText()))

        tabs.addTab(props_tab, "Properties")

        # Connections tab
        if self.model:
            conn_tab = QTextEdit()
            conn_tab.setReadOnly(True)
            conn_code = self._connections_to_code(block)
            conn_tab.setPlainText(conn_code)

            tabs.addTab(conn_tab, "Connections")

        self.content_layout.addWidget(tabs)
        self.content_layout.addStretch()

    def _properties_to_code(self, properties: dict) -> str:
        """Convert properties dict to Python code"""
        lines = []
        lines.append("# Block properties")
        lines.append("# Edit these values as Python expressions")
        lines.append("")

        if not properties:
            lines.append("# No properties defined")
            return "\n".join(lines)

        for key, value in properties.items():
            if isinstance(value, str):
                lines.append(f"{key} = '{value}'")
            else:
                lines.append(f"{key} = {value}")

        return "\n".join(lines)

    def _update_properties_from_code(self, block, code: str):
        """Parse code back into properties dict"""
        # Simple parser - execute code in safe namespace
        try:
            namespace = {}
            # Filter out comments and empty lines
            exec_lines = [line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
            if exec_lines:
                exec('\n'.join(exec_lines), {}, namespace)
                # Update block properties
                block.properties.update(namespace)
        except:
            pass  # Ignore syntax errors during typing

    def _connections_to_code(self, block) -> str:
        """Show connections as code"""
        lines = []
        lines.append(f"# Connections for {block.name}")
        lines.append("")

        conns_from = self.model.get_connections_from(block.id)
        conns_to = self.model.get_connections_to(block.id)

        if conns_from:
            lines.append("# Outgoing:")
            for conn in conns_from:
                to_block = self.model.get_block_by_id(conn.to_block)
                if to_block:
                    safe_name = block.name.replace(' ', '_').lower()
                    safe_to = to_block.name.replace(' ', '_').lower()
                    lines.append(f"{safe_name}.connections['{conn.label}'] = {safe_to}")

        if conns_to:
            lines.append("")
            lines.append("# Incoming:")
            for conn in conns_to:
                from_block = self.model.get_block_by_id(conn.from_block)
                if from_block:
                    safe_from = from_block.name.replace(' ', '_').lower()
                    safe_name = block.name.replace(' ', '_').lower()
                    lines.append(f"{safe_from}.connections['{conn.label}'] = {safe_name}")

        if not conns_from and not conns_to:
            lines.append("# No connections")

        return "\n".join(lines)

    def show_state_properties(self, state):
        """Show properties for an FSM state"""
        # TODO: Implement
        pass

    def show_transition_properties(self, transition):
        """Show properties for an FSM transition"""
        # TODO: Implement
        pass
