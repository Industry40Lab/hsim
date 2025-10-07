"""
Enhanced Properties Panel - Live form-based property editor
Displays properties as form fields with live updates
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QScrollArea, QFrame, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from hsim.gui.models.block_definitions import get_block_definition, BlockType, PropertyType


class PropertiesPanel(QWidget):
    """Form-based properties panel for editing agents"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_block = None
        self.model = None
        self.property_widgets = {}  # property_name -> widget

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
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #2D2D2D;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                padding: 6px;
                color: #D4D4D4;
                font-size: 12px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #007ACC;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 4px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #D4D4D4;
                margin-right: 5px;
            }
            QGroupBox {
                border: 1px solid #3E3E3E;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                background-color: #2D2D2D;
            }
            QCheckBox::indicator:checked {
                background-color: #007ACC;
                border-color: #007ACC;
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

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #1E1E1E; }")

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(12, 12, 12, 12)
        self.content_layout.setSpacing(12)

        # Empty state
        self.empty_label = QLabel("Select a block to edit properties")
        self.empty_label.setStyleSheet("color: #808080; padding: 40px 20px; font-size: 12px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.empty_label)

        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)

    def clear_properties(self):
        """Clear all property widgets"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.property_widgets.clear()

    def show_block_properties(self, block):
        """Show properties for a block with live form fields"""
        # Handle both Block objects and block IDs
        if isinstance(block, str):
            # It's a block ID, get the block from model
            if self.model:
                block = self.model.get_block_by_id(block)
            else:
                return

        self.current_block = block
        self.clear_properties()

        if block is None:
            self.empty_label = QLabel("Select a block to edit properties")
            self.empty_label.setStyleSheet("color: #808080; padding: 40px 20px; font-size: 12px;")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(self.empty_label)
            return

        # Block header
        header = QLabel(f"{block.type.replace('_', ' ').title()}")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF; padding-bottom: 4px;")
        self.content_layout.addWidget(header)

        # Name field
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self.content_layout.addWidget(name_label)

        name_edit = QLineEdit(block.name)
        name_edit.textChanged.connect(lambda text: setattr(block, 'name', text))
        self.content_layout.addWidget(name_edit)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #3E3E3E; margin: 8px 0;")
        self.content_layout.addWidget(sep)

        # Get block definition
        try:
            block_def = get_block_definition(BlockType(block.type))
        except (ValueError, KeyError):
            # Unknown block type
            error_label = QLabel(f"Unknown block type: {block.type}")
            error_label.setStyleSheet("color: #FF6B6B;")
            self.content_layout.addWidget(error_label)
            self.content_layout.addStretch()
            return

        # Parameters group
        if block_def.properties:
            params_group = QGroupBox("⚙️ Parameters")
            params_layout = QVBoxLayout(params_group)
            params_layout.setSpacing(10)

            for prop_def in block_def.properties:
                # Property label
                prop_label = QLabel(f"{prop_def.label}:")
                params_layout.addWidget(prop_label)

                # Property input widget (based on type)
                widget = self._create_property_widget(block, prop_def)
                if widget:
                    params_layout.addWidget(widget)
                    self.property_widgets[prop_def.name] = widget

            self.content_layout.addWidget(params_group)

        # Statechart group (if block has FSM)
        if block_def.has_fsm:
            fsm_group = QGroupBox("🔄 Statechart")
            fsm_layout = QVBoxLayout(fsm_group)

            # Get FSM info
            fsm = None
            if self.model and block.fsm_id:
                fsm = self.model.get_fsm_by_id(block.fsm_id)

            if fsm:
                state_count = len(fsm.states)
                initial_count = sum(1 for s in fsm.states.values() if s.is_initial)
                fsm_info = QLabel(f"States: {state_count} ({initial_count} initial)")
                fsm_info.setStyleSheet("color: #A0A0A0; font-size: 11px;")
                fsm_layout.addWidget(fsm_info)
            else:
                fsm_info = QLabel("No FSM defined")
                fsm_info.setStyleSheet("color: #808080; font-size: 11px;")
                fsm_layout.addWidget(fsm_info)

            # Instruction hint
            hint = QLabel("Double-click block to edit FSM")
            hint.setStyleSheet("color: #606060; font-size: 10px; font-style: italic; padding-top: 4px;")
            fsm_layout.addWidget(hint)

            self.content_layout.addWidget(fsm_group)

        # Connections group
        if self.model:
            connections = [c for c in self.model.connections.values() if c.from_block == block.id]
            if connections:
                conn_group = QGroupBox("🔗 Connections")
                conn_layout = QVBoxLayout(conn_group)

                for conn in connections:
                    to_block = self.model.get_block_by_id(conn.to_block)
                    if to_block:
                        conn_label = QLabel(f"→ {to_block.name} ({conn.from_port} → {conn.to_port})")
                        conn_label.setStyleSheet("color: #A0A0A0; font-size: 11px; padding: 2px 0;")
                        conn_layout.addWidget(conn_label)

                self.content_layout.addWidget(conn_group)

        self.content_layout.addStretch()

    def _create_property_widget(self, block, prop_def):
        """Create appropriate widget for property type"""
        current_value = block.properties.get(prop_def.name, prop_def.default)

        if prop_def.type == PropertyType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setRange(
                prop_def.min_value if prop_def.min_value is not None else -99999.0,
                prop_def.max_value if prop_def.max_value is not None else 99999.0
            )
            widget.setValue(float(current_value) if current_value else prop_def.default)
            widget.setSingleStep(0.1)
            widget.setDecimals(2)
            widget.valueChanged.connect(
                lambda val, name=prop_def.name: self._update_property(block, name, val)
            )
            widget.setToolTip(prop_def.description)
            return widget

        elif prop_def.type == PropertyType.INT:
            widget = QSpinBox()
            widget.setRange(
                int(prop_def.min_value) if prop_def.min_value is not None else -99999,
                int(prop_def.max_value) if prop_def.max_value is not None else 99999
            )
            widget.setValue(int(current_value) if current_value else prop_def.default)
            widget.valueChanged.connect(
                lambda val, name=prop_def.name: self._update_property(block, name, val)
            )
            widget.setToolTip(prop_def.description)
            return widget

        elif prop_def.type == PropertyType.STRING:
            widget = QLineEdit(str(current_value) if current_value else prop_def.default)
            widget.textChanged.connect(
                lambda text, name=prop_def.name: self._update_property(block, name, text)
            )
            widget.setToolTip(prop_def.description)
            return widget

        elif prop_def.type == PropertyType.CHOICE:
            widget = QComboBox()
            if prop_def.choices:
                widget.addItems(prop_def.choices)
                # Set current value
                current_str = str(current_value) if current_value else prop_def.default
                index = widget.findText(current_str)
                if index >= 0:
                    widget.setCurrentIndex(index)
            widget.currentTextChanged.connect(
                lambda text, name=prop_def.name: self._update_property(block, name, text)
            )
            widget.setToolTip(prop_def.description)
            return widget

        elif prop_def.type == PropertyType.BOOL:
            widget = QCheckBox()
            widget.setChecked(bool(current_value) if current_value is not None else prop_def.default)
            widget.stateChanged.connect(
                lambda state, name=prop_def.name: self._update_property(block, name, state == Qt.CheckState.Checked.value)
            )
            widget.setToolTip(prop_def.description)
            return widget

        elif prop_def.type == PropertyType.CODE:
            widget = QTextEdit()
            widget.setPlainText(str(current_value) if current_value else prop_def.default)
            widget.setMaximumHeight(100)
            widget.textChanged.connect(
                lambda name=prop_def.name, w=widget: self._update_property(block, name, w.toPlainText())
            )
            widget.setToolTip(prop_def.description)
            widget.setStyleSheet("""
                QTextEdit {
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                }
            """)
            return widget

        return None

    def _update_property(self, block, property_name, value):
        """Update block property"""
        if block:
            block.properties[property_name] = value

    def show_state_properties(self, state):
        """Show properties for an FSM state"""
        self.clear_properties()

        if state is None:
            self.empty_label = QLabel("Select a state to edit properties")
            self.empty_label.setStyleSheet("color: #808080; padding: 40px 20px; font-size: 12px;")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(self.empty_label)
            return

        # State header
        header = QLabel("FSM State")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF; padding-bottom: 4px;")
        self.content_layout.addWidget(header)

        # Name field
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self.content_layout.addWidget(name_label)

        name_edit = QLineEdit(state.name)
        name_edit.textChanged.connect(lambda text: setattr(state, 'name', text))
        self.content_layout.addWidget(name_edit)

        # Initial state checkbox
        initial_check = QCheckBox("Initial State")
        initial_check.setChecked(state.is_initial)
        initial_check.stateChanged.connect(lambda: setattr(state, 'is_initial', initial_check.isChecked()))
        self.content_layout.addWidget(initial_check)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #3E3E3E; margin: 8px 0;")
        self.content_layout.addWidget(sep)

        # Actions group
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QVBoxLayout(actions_group)

        # On Enter
        enter_label = QLabel("On Enter:")
        actions_layout.addWidget(enter_label)

        enter_edit = QTextEdit()
        enter_edit.setMaximumHeight(80)
        enter_edit.setPlainText(state.on_enter if state.on_enter else "")
        enter_edit.textChanged.connect(lambda: setattr(state, 'on_enter', enter_edit.toPlainText()))
        actions_layout.addWidget(enter_edit)

        # On Exit
        exit_label = QLabel("On Exit:")
        actions_layout.addWidget(exit_label)

        exit_edit = QTextEdit()
        exit_edit.setMaximumHeight(80)
        exit_edit.setPlainText(state.on_exit if state.on_exit else "")
        exit_edit.textChanged.connect(lambda: setattr(state, 'on_exit', exit_edit.toPlainText()))
        actions_layout.addWidget(exit_edit)

        self.content_layout.addWidget(actions_group)

        # Spacer
        self.content_layout.addStretch()

    def show_transition_properties(self, transition):
        """Show properties for an FSM transition"""
        self.clear_properties()

        if transition is None:
            self.empty_label = QLabel("Select a transition to edit properties")
            self.empty_label.setStyleSheet("color: #808080; padding: 40px 20px; font-size: 12px;")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(self.empty_label)
            return

        # Transition header
        header = QLabel("FSM Transition")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF; padding-bottom: 4px;")
        self.content_layout.addWidget(header)

        # Label field
        label_label = QLabel("Label:")
        label_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        self.content_layout.addWidget(label_label)

        label_edit = QLineEdit(transition.label if transition.label else "")
        label_edit.textChanged.connect(lambda text: setattr(transition, 'label', text))
        self.content_layout.addWidget(label_edit)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #3E3E3E; margin: 8px 0;")
        self.content_layout.addWidget(sep)

        # Condition group
        condition_group = QGroupBox("🔀 Condition")
        condition_layout = QVBoxLayout(condition_group)

        condition_label = QLabel("Condition Expression:")
        condition_layout.addWidget(condition_label)

        condition_edit = QTextEdit()
        condition_edit.setMaximumHeight(60)
        condition_edit.setPlainText(transition.condition if transition.condition else "true")
        condition_edit.textChanged.connect(lambda: setattr(transition, 'condition', condition_edit.toPlainText()))
        condition_layout.addWidget(condition_edit)

        hint_label = QLabel("Example: self.queue.length() > 0")
        hint_label.setStyleSheet("color: #808080; font-size: 11px; font-style: italic;")
        condition_layout.addWidget(hint_label)

        self.content_layout.addWidget(condition_group)

        # Action group
        action_group = QGroupBox("⚡ Action")
        action_layout = QVBoxLayout(action_group)

        action_label = QLabel("On Transition:")
        action_layout.addWidget(action_label)

        action_edit = QTextEdit()
        action_edit.setMaximumHeight(80)
        action_edit.setPlainText(transition.action if hasattr(transition, 'action') and transition.action else "")
        action_edit.textChanged.connect(lambda: setattr(transition, 'action', action_edit.toPlainText()))
        action_layout.addWidget(action_edit)

        self.content_layout.addWidget(action_group)

        # Spacer
        self.content_layout.addStretch()
