"""
Properties Panel - Dynamic property editor for selected items
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit,
    QPushButton, QScrollArea, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt

from hsim.gui.models.block_definitions import get_block_definition, BlockType, PropertyType


class PropertiesPanel(QWidget):
    """Properties panel for editing block/state/transition properties"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self.property_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Properties")
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

        # Scroll area for properties
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Container for property widgets
        self.properties_container = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_container)
        self.properties_layout.setContentsMargins(10, 10, 10, 10)

        # Empty state label
        self.empty_label = QLabel("Select an item to view properties")
        self.empty_label.setStyleSheet("color: #9CA3AF; padding: 20px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.properties_layout.addWidget(self.empty_label)

        scroll.setWidget(self.properties_container)
        layout.addWidget(scroll)

    def clear_properties(self):
        """Clear all property widgets"""
        for widget in self.property_widgets.values():
            widget.deleteLater()
        self.property_widgets.clear()

        # Clear layout
        while self.properties_layout.count():
            item = self.properties_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def show_block_properties(self, block):
        """Show properties for a block"""
        self.current_item = block
        self.clear_properties()

        if block is None:
            self.empty_label = QLabel("Select an item to view properties")
            self.empty_label.setStyleSheet("color: #9CA3AF; padding: 20px;")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.properties_layout.addWidget(self.empty_label)
            return

        # Block info group
        info_group = QGroupBox("Block Information")
        info_layout = QFormLayout(info_group)

        # Name
        name_edit = QLineEdit(block.name)
        name_edit.textChanged.connect(lambda text: setattr(block, 'name', text))
        info_layout.addRow("Name:", name_edit)
        self.property_widgets['name'] = name_edit

        # Type
        type_label = QLabel(block.type)
        info_layout.addRow("Type:", type_label)

        self.properties_layout.addWidget(info_group)

        # Block properties group
        block_def = get_block_definition(BlockType(block.type))
        if block_def and block_def.properties:
            props_group = QGroupBox("Properties")
            props_layout = QFormLayout(props_group)

            for prop_def in block_def.properties:
                widget = self.create_property_widget(prop_def, block)
                props_layout.addRow(f"{prop_def.label}:", widget)
                self.property_widgets[prop_def.name] = widget

            self.properties_layout.addWidget(props_group)

        self.properties_layout.addStretch()

    def create_property_widget(self, prop_def, block):
        """Create a widget for a property"""
        current_value = block.properties.get(prop_def.name, prop_def.default)

        if prop_def.type == PropertyType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(
                prop_def.min_value if prop_def.min_value is not None else 0,
                prop_def.max_value if prop_def.max_value is not None else 9999
            )
            widget.setValue(float(current_value))
            widget.valueChanged.connect(
                lambda val: block.properties.update({prop_def.name: val})
            )

        elif prop_def.type == PropertyType.INT:
            widget = QSpinBox()
            widget.setRange(
                int(prop_def.min_value) if prop_def.min_value is not None else 0,
                int(prop_def.max_value) if prop_def.max_value is not None else 9999
            )
            widget.setValue(int(current_value))
            widget.valueChanged.connect(
                lambda val: block.properties.update({prop_def.name: val})
            )

        elif prop_def.type == PropertyType.CHOICE:
            widget = QComboBox()
            widget.addItems(prop_def.choices)
            widget.setCurrentText(str(current_value))
            widget.currentTextChanged.connect(
                lambda val: block.properties.update({prop_def.name: val})
            )

        elif prop_def.type == PropertyType.BOOL:
            widget = QCheckBox()
            widget.setChecked(bool(current_value))
            widget.stateChanged.connect(
                lambda val: block.properties.update({prop_def.name: bool(val)})
            )

        elif prop_def.type == PropertyType.STRING:
            widget = QLineEdit()
            widget.setText(str(current_value))
            widget.textChanged.connect(
                lambda val: block.properties.update({prop_def.name: val})
            )

        else:  # CODE
            widget = QTextEdit()
            widget.setPlainText(str(current_value))
            widget.setMaximumHeight(100)
            widget.textChanged.connect(
                lambda: block.properties.update({prop_def.name: widget.toPlainText()})
            )

        widget.setToolTip(prop_def.description)
        return widget

    def show_state_properties(self, state):
        """Show properties for an FSM state"""
        # TODO: Implement state properties
        pass

    def show_transition_properties(self, transition):
        """Show properties for an FSM transition"""
        # TODO: Implement transition properties
        pass
