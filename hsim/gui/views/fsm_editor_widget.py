"""
FSM Editor - Visual editor for Agent state machines
Agents can have multiple disconnected states/FSMs
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene,
    QToolBar, QPushButton, QLabel, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush

from hsim.gui.models.model import FSM, State as FSMState, Transition, Position, Size
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

        # Main splitter: canvas (left) + properties (right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

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

        splitter.addWidget(self.view)
        splitter.addWidget(right_panel)
        splitter.setSizes([1200, 300])

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
            return

        # Draw states
        # TODO: Create StateItem graphics
        for state_id, state in self.current_fsm.states.items():
            # For now, just show placeholder
            pass

        # Draw transitions
        # TODO: Create TransitionItem graphics
        for transition in self.current_fsm.transitions:
            # For now, just show placeholder
            pass

    def add_state(self):
        """Add a new state to the agent's FSM"""
        if not self.current_agent or not self.current_fsm:
            return

        # Create new state
        state = FSMState(
            id=str(uuid.uuid4()),
            name=f"State_{len(self.current_fsm.states) + 1}",
            position=Position(100, 100),
            size=Size(120, 60),
            is_initial=len(self.current_fsm.states) == 0,  # First state is initial
            on_enter="",
            on_exit=""
        )

        self.current_fsm.add_state(state)
        self.load_fsm()

    def add_transition(self):
        """Add transition between selected states"""
        # TODO: Implement transition creation
        pass

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
