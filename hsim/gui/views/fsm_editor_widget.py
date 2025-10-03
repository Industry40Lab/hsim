"""
FSM Editor - Visual editor for Agent state machines
Agents can have multiple disconnected states/FSMs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QToolBar, QPushButton, QLabel, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont

from hsim.gui.models.model import FSM, State as FSMState, Transition, Position, Size
from hsim.gui.items.state_item import StateItem
from hsim.gui.items.transition_item import TransitionItem
import uuid


class FSMEditorWidget(QWidget):
    """FSM Editor for agents - supports multiple disconnected FSMs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_fsm = None  # Current FSM being edited
        self.current_agent = None  # Agent (block) being edited
        self.model = None  # Reference to simulation model

        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2D2D2D;
                border-bottom: 1px solid #3E3E3E;
                spacing: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #3E3E3E;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4E4E4E;
            }
            QPushButton:pressed {
                background-color: #2E2E2E;
            }
            QLabel {
                color: #D4D4D4;
                padding: 0 8px;
            }
        """)

        # Add state button
        add_state_btn = QPushButton("+ State")
        add_state_btn.clicked.connect(self.add_state)
        toolbar.addWidget(add_state_btn)

        # Add transition button
        add_trans_btn = QPushButton("+ Transition")
        add_trans_btn.clicked.connect(self.add_transition)
        toolbar.addWidget(add_trans_btn)

        toolbar.addSeparator()

        # Expose port button
        expose_port_btn = QPushButton("⚡ Expose Port")
        expose_port_btn.clicked.connect(self.expose_agent_port)
        toolbar.addWidget(expose_port_btn)

        toolbar.addSeparator()

        # Agent info label
        self.agent_label = QLabel("No agent selected")
        self.agent_label.setStyleSheet("color: #9CA3AF; font-style: italic;")
        toolbar.addWidget(self.agent_label)

        layout.addWidget(toolbar)

        # Main splitter: code (left) + canvas (center) + properties (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - FSM code view
        left_panel = QWidget()
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border-right: 1px solid #3E3E3E;
            }
            QLabel {
                color: #D4D4D4;
                font-size: 12px;
                padding: 4px;
            }
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                color: #D4D4D4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(12, 12, 12, 12)

        code_label = QLabel("FSM Code View")
        code_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        left_layout.addWidget(code_label)

        self.fsm_code_view = QTextEdit()
        self.fsm_code_view.setReadOnly(True)
        self.fsm_code_view.setPlaceholderText("# FSM code will be displayed here\n# States, transitions, and behavior")
        left_layout.addWidget(self.fsm_code_view)

        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(400)

        # Canvas for states/transitions
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 1500)
        self.scene.setBackgroundBrush(QBrush(QColor("#1E1E1E")))

        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("QGraphicsView { border: none; }")

        # Right panel - selected item properties
        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border-left: 1px solid #3E3E3E;
            }
            QLabel {
                color: #D4D4D4;
                font-size: 12px;
                padding: 4px;
            }
            QTextEdit {
                background-color: #1E1E1E;
                border: 1px solid #3E3E3E;
                border-radius: 3px;
                color: #D4D4D4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)

        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 12, 12, 12)

        # State properties section
        state_label = QLabel("State Properties")
        state_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        right_layout.addWidget(state_label)

        self.state_name_edit = QTextEdit()
        self.state_name_edit.setPlaceholderText("State name")
        self.state_name_edit.setMaximumHeight(30)
        right_layout.addWidget(self.state_name_edit)

        on_enter_label = QLabel("on_enter code:")
        right_layout.addWidget(on_enter_label)

        self.on_enter_edit = QTextEdit()
        self.on_enter_edit.setPlaceholderText("# Python code executed when entering state\nprint('entering')")
        right_layout.addWidget(self.on_enter_edit)

        on_exit_label = QLabel("on_exit code:")
        right_layout.addWidget(on_exit_label)

        self.on_exit_edit = QTextEdit()
        self.on_exit_edit.setPlaceholderText("# Python code executed when exiting state\nprint('exiting')")
        right_layout.addWidget(self.on_exit_edit)

        right_layout.addStretch()

        right_panel.setMinimumWidth(300)
        right_panel.setMaximumWidth(400)

        splitter.addWidget(left_panel)
        splitter.addWidget(self.view)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900, 300])

        layout.addWidget(splitter)

    def set_agent(self, block, model):
        """Set the agent (block) to edit"""
        self.current_agent = block
        self.model = model

        if block:
            self.agent_label.setText(f"Editing: {block.name}")

            # Load agent's FSM
            if block.fsm_id and model and block.fsm_id in model.fsms:
                self.current_fsm = model.fsms[block.fsm_id]
                self.load_fsm()
            else:
                self.scene.clear()
        else:
            self.agent_label.setText("No agent selected")
            self.current_fsm = None
            self.scene.clear()

    def load_fsm(self):
        """Load FSM states and transitions into canvas"""
        self.scene.clear()

        if not self.current_fsm:
            self.fsm_code_view.setPlainText("# No FSM loaded")
            return

        # Store state items for transition drawing
        state_items = {}

        # Draw states
        for state_id, state in self.current_fsm.states.items():
            state_item = StateItem(state)
            state_item.setPos(state.position.x, state.position.y)

            # Connect signals
            state_item.signals.position_changed.connect(
                lambda sid=state_id, pos=state.position: self._on_state_moved(sid, pos)
            )
            state_item.signals.selected.connect(self._on_state_selected)
            state_item.signals.deleted.connect(self._on_state_deleted)

            self.scene.addItem(state_item)
            state_items[state_id] = state_item

        # Draw transitions
        for transition in self.current_fsm.transitions:
            if transition.from_state in state_items and transition.to_state in state_items:
                from_item = state_items[transition.from_state]
                to_item = state_items[transition.to_state]

                trans_item = TransitionItem(transition, from_item, to_item)
                trans_item.signals.selected.connect(self._on_transition_selected)
                trans_item.signals.deleted.connect(self._on_transition_deleted)

                self.scene.addItem(trans_item)

        # Update code view
        self.fsm_code_view.setPlainText(self._generate_fsm_code())

    def add_state(self):
        """Add a new state to the agent's FSM"""
        if not self.current_agent or not self.current_fsm:
            return

        # Generate unique state name
        state_count = len(self.current_fsm.states)
        state_name = f"State_{state_count + 1}"

        # Ensure uniqueness
        while any(s.name == state_name for s in self.current_fsm.states.values()):
            state_count += 1
            state_name = f"State_{state_count + 1}"

        # Create new state at center of view
        view_center = self.view.mapToScene(self.view.viewport().rect().center())

        state = FSMState(
            id=str(uuid.uuid4()),
            name=state_name,
            position=Position(x=view_center.x() - 60, y=view_center.y() - 30),
            size=Size(width=120, height=60),
            is_initial=len(self.current_fsm.states) == 0,  # First state is initial
            is_final=False,
            on_enter="",
            on_exit=""
        )

        self.current_fsm.add_state(state)
        self.load_fsm()
        self.show_state_properties(state)

    def add_transition(self):
        """Add transition between selected states"""
        if not self.current_agent or not self.current_fsm:
            return

        # Get selected states from scene
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, StateItem)]

        if len(selected_items) != 2:
            # Show message in status bar
            main_window = self._get_main_window()
            if main_window:
                main_window.statusBar().showMessage("Select exactly 2 states to create a transition", 3000)
            return

        from_state = selected_items[0].state
        to_state = selected_items[1].state

        # Create new transition
        from hsim.gui.model.fsm_model import FSMTransition
        transition = FSMTransition(
            id=str(uuid.uuid4()),
            from_state=from_state.id,
            to_state=to_state.id,
            label="",
            transition_type="message",
            timeout=None,
            condition="",
            on_transition=""
        )

        self.current_fsm.add_transition(transition)
        self.load_fsm()
        self.show_transition_properties(transition)

    def _get_main_window(self):
        """Get main window through parent hierarchy"""
        widget = self.parent()
        while widget and not hasattr(widget, 'statusBar'):
            widget = widget.parent()
        return widget

    def expose_agent_port(self):
        """Expose an agent port for external connections"""
        # TODO: Implement port exposure
        # This allows connecting to the agent's internal states from outside
        pass

    def show_state_properties(self, state):
        """Show properties for selected state"""
        if state:
            self.state_name_edit.setPlainText(state.name)
            self.on_enter_edit.setPlainText(state.on_enter)
            self.on_exit_edit.setPlainText(state.on_exit)

    def show_transition_properties(self, transition):
        """Show properties for selected transition"""
        # TODO: Implement
        pass

    def _on_state_moved(self, state_id, position):
        """Handle state being moved"""
        if self.current_fsm and state_id in self.current_fsm.states:
            state = self.current_fsm.states[state_id]
            state.position.x = position.x
            state.position.y = position.y

    def _on_state_selected(self, state_id):
        """Handle state selection"""
        if self.current_fsm and state_id in self.current_fsm.states:
            state = self.current_fsm.states[state_id]
            self.show_state_properties(state)

    def _on_state_deleted(self, state_id):
        """Handle state deletion"""
        if self.current_fsm:
            self.current_fsm.remove_state(state_id)
            self.load_fsm()

    def _on_transition_selected(self, transition_id):
        """Handle transition selection"""
        if self.current_fsm:
            for transition in self.current_fsm.transitions:
                if transition.id == transition_id:
                    self.show_transition_properties(transition)
                    break

    def _on_transition_deleted(self, transition_id):
        """Handle transition deletion"""
        if self.current_fsm:
            self.current_fsm.remove_transition(transition_id)
            self.load_fsm()

    def _generate_fsm_code(self) -> str:
        """Generate Python code representation of the FSM"""
        if not self.current_fsm:
            return "# No FSM loaded"

        lines = []
        lines.append(f"# FSM: {self.current_fsm.name}")
        if self.current_agent:
            lines.append(f"# Agent: {self.current_agent.name}")
        lines.append("")

        # States
        lines.append("# States:")
        if not self.current_fsm.states:
            lines.append("#   (no states defined)")
        else:
            for state_id, state in self.current_fsm.states.items():
                initial = " [INITIAL]" if state.is_initial else ""
                final = " [FINAL]" if state.is_final else ""
                lines.append(f"#   - {state.name}{initial}{final}")

                if state.on_enter:
                    lines.append(f"#       on_enter:")
                    for code_line in state.on_enter.split('\n'):
                        lines.append(f"#         {code_line}")

                if state.on_exit:
                    lines.append(f"#       on_exit:")
                    for code_line in state.on_exit.split('\n'):
                        lines.append(f"#         {code_line}")

        lines.append("")

        # Transitions
        lines.append("# Transitions:")
        if not self.current_fsm.transitions:
            lines.append("#   (no transitions defined)")
        else:
            for transition in self.current_fsm.transitions:
                from_state = self.current_fsm.states.get(transition.from_state)
                to_state = self.current_fsm.states.get(transition.to_state)

                if from_state and to_state:
                    label = f" [{transition.label}]" if transition.label else ""
                    lines.append(f"#   {from_state.name} -> {to_state.name}{label}")

                    if transition.transition_type != "message":
                        lines.append(f"#       type: {transition.transition_type}")

                    if transition.timeout:
                        lines.append(f"#       timeout: {transition.timeout}")

                    if transition.condition:
                        lines.append(f"#       condition: {transition.condition}")

                    if transition.on_transition:
                        lines.append(f"#       on_transition:")
                        for code_line in transition.on_transition.split('\n'):
                            lines.append(f"#         {code_line}")

        lines.append("")
        lines.append("# Double-click states to edit properties")
        lines.append("# Use '+ State' and '+ Transition' buttons to add elements")

        return '\n'.join(lines)
