"""
Main application window with three-panel layout
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QTabWidget, QLabel,
    QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from hsim.gui.models.model import SimulationModel
from hsim.gui.models.undo_stack import UndoStack
from hsim.gui.views.palette_widget import PaletteWidget
from hsim.gui.views.canvas_widget import CanvasWidget
from hsim.gui.views.fsm_editor_widget import FSMEditorWidget
from hsim.gui.views.properties_panel import PropertiesPanel
from hsim.gui.views.project_tree import ProjectTree
import json


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.model = SimulationModel(name="New Model")
        self.current_file = None
        self.undo_stack = UndoStack()
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.connect_signals()
        self.update_undo_redo_actions()

    def setup_ui(self):
        """Setup the UI layout"""
        self.setWindowTitle("hsim - Model Designer")
        self.setGeometry(100, 100, 1600, 900)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Tabbed interface
        left_panel = QTabWidget()
        left_panel.setTabPosition(QTabWidget.TabPosition.North)
        left_panel.setMinimumWidth(200)
        left_panel.setMaximumWidth(300)

        # Tab 1: Model Structure (what's in the model)
        self.model_structure_tree = self._create_model_structure_tree()
        left_panel.addTab(self.model_structure_tree, "📋 Model")

        # Tab 2: Component Library (what can be added)
        self.component_library = self._create_component_library()
        left_panel.addTab(self.component_library, "📚 Library")

        # Keep references for compatibility
        self.project_tree = self.model_structure_tree  # Old name
        self.palette = self.component_library  # Old name

        # Center panel - Tabbed canvas (AnyLogic style)
        self.canvas_tabs = QTabWidget()
        self.canvas_tabs.setTabsClosable(True)
        self.canvas_tabs.setMovable(True)
        self.canvas_tabs.tabCloseRequested.connect(self._close_agent_tab)

        # Main frame always in first tab (cannot be closed)
        self.main_canvas = CanvasWidget(self.model, self)
        self.canvas_tabs.addTab(self.main_canvas, "📋 Main")

        # Keep reference for compatibility
        self.canvas = self.main_canvas
        self.fsm_editor = FSMEditorWidget(self)  # Keep for compatibility

        # Right panel - Properties Panel (code-focused)
        self.properties_panel = PropertiesPanel(self)
        self.properties_panel.model = self.model
        self.properties_panel.setMinimumWidth(300)
        self.properties_panel.setMaximumWidth(400)

        # Add widgets to splitter
        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(self.canvas_tabs)
        self.main_splitter.addWidget(self.properties_panel)

        # Set splitter sizes (left: 250, center: 1000, right: 300)
        self.main_splitter.setSizes([250, 1000, 300])

        main_layout.addWidget(self.main_splitter)

    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("📄 &New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_model)
        file_menu.addAction(new_action)

        open_action = QAction("📁 &Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_model)
        file_menu.addAction(open_action)

        save_action = QAction("💾 &Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_model)
        file_menu.addAction(save_action)

        save_as_action = QAction("💾 Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_model_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_python_action = QAction("🐍 Export &Python Code...", self)
        export_python_action.triggered.connect(self.export_python)
        file_menu.addAction(export_python_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        self.undo_action = QAction("↶ &Undo", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("↷ &Redo", self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        copy_action = QAction("📋 &Copy", self)
        copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        copy_action.triggered.connect(self.copy_selected)
        edit_menu.addAction(copy_action)

        paste_action = QAction("📄 &Paste", self)
        paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        paste_action.triggered.connect(self.paste_from_clipboard)
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        delete_action = QAction("🗑️ &Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("🔍+ Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("🔍- Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("🔍 &Reset Zoom", self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(self.zoom_reset)
        view_menu.addAction(zoom_reset_action)

        view_menu.addSeparator()

        toggle_grid_action = QAction("⊞ Show &Grid", self)
        toggle_grid_action.setCheckable(True)
        toggle_grid_action.setChecked(True)
        toggle_grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(toggle_grid_action)

        # Arrange menu
        arrange_menu = menubar.addMenu("&Arrange")

        align_left_action = QAction("⬅️ Align &Left", self)
        align_left_action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        align_left_action.setToolTip("Align selected blocks to the left")
        align_left_action.triggered.connect(self.align_left)
        arrange_menu.addAction(align_left_action)

        align_right_action = QAction("➡️ Align &Right", self)
        align_right_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        align_right_action.setToolTip("Align selected blocks to the right")
        align_right_action.triggered.connect(self.align_right)
        arrange_menu.addAction(align_right_action)

        align_top_action = QAction("⬆️ Align &Top", self)
        align_top_action.setShortcut(QKeySequence("Ctrl+Shift+T"))
        align_top_action.setToolTip("Align selected blocks to the top")
        align_top_action.triggered.connect(self.align_top)
        arrange_menu.addAction(align_top_action)

        align_bottom_action = QAction("⬇️ Align &Bottom", self)
        align_bottom_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        align_bottom_action.setToolTip("Align selected blocks to the bottom")
        align_bottom_action.triggered.connect(self.align_bottom)
        arrange_menu.addAction(align_bottom_action)

        arrange_menu.addSeparator()

        align_h_center_action = QAction("↔️ Align &Horizontal Center", self)
        align_h_center_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        align_h_center_action.setToolTip("Align selected blocks to horizontal center")
        align_h_center_action.triggered.connect(self.align_horizontal_center)
        arrange_menu.addAction(align_h_center_action)

        align_v_center_action = QAction("↕️ Align &Vertical Center", self)
        align_v_center_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        align_v_center_action.setToolTip("Align selected blocks to vertical center")
        align_v_center_action.triggered.connect(self.align_vertical_center)
        arrange_menu.addAction(align_v_center_action)

        arrange_menu.addSeparator()

        distribute_h_action = QAction("⬌ Distribute Horizontally", self)
        distribute_h_action.setToolTip("Distribute selected blocks evenly horizontally")
        distribute_h_action.triggered.connect(self.distribute_horizontally)
        arrange_menu.addAction(distribute_h_action)

        distribute_v_action = QAction("⬍ Distribute Vertically", self)
        distribute_v_action.setToolTip("Distribute selected blocks evenly vertically")
        distribute_v_action.triggered.connect(self.distribute_vertically)
        arrange_menu.addAction(distribute_v_action)

        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")

        run_action = QAction("▶️ &Run", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self.run_simulation)
        sim_menu.addAction(run_action)

        validate_action = QAction("✓ &Validate Model", self)
        validate_action.triggered.connect(self.validate_model)
        sim_menu.addAction(validate_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("ℹ️ &About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # New
        new_action = QAction("📄 New", self)
        new_action.setToolTip("Create a new model (Ctrl+N)")
        new_action.triggered.connect(self.new_model)
        toolbar.addAction(new_action)

        # Open
        open_action = QAction("📁 Open", self)
        open_action.setToolTip("Open an existing model (Ctrl+O)")
        open_action.triggered.connect(self.open_model)
        toolbar.addAction(open_action)

        # Save
        save_action = QAction("💾 Save", self)
        save_action.setToolTip("Save the current model (Ctrl+S)")
        save_action.triggered.connect(self.save_model)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Undo
        self.undo_toolbar_action = QAction("↶ Undo", self)
        self.undo_toolbar_action.setToolTip("Undo the last action (Ctrl+Z)")
        self.undo_toolbar_action.triggered.connect(self.undo)
        toolbar.addAction(self.undo_toolbar_action)

        # Redo
        self.redo_toolbar_action = QAction("↷ Redo", self)
        self.redo_toolbar_action.setToolTip("Redo the last undone action (Ctrl+Shift+Z)")
        self.redo_toolbar_action.triggered.connect(self.redo)
        toolbar.addAction(self.redo_toolbar_action)

        toolbar.addSeparator()

        # Run
        run_action = QAction("▶️ Run", self)
        run_action.setToolTip("Run simulation (F5)")
        run_action.triggered.connect(self.run_simulation)
        toolbar.addAction(run_action)

        toolbar.addSeparator()

        # Zoom controls
        zoom_in_action = QAction("🔍+ Zoom In", self)
        zoom_in_action.setToolTip("Zoom in (Ctrl++)")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("🔍- Zoom Out", self)
        zoom_out_action.setToolTip("Zoom out (Ctrl+-)")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("🔍 Reset", self)
        zoom_reset_action.setToolTip("Reset zoom to 100% (Ctrl+0)")
        zoom_reset_action.triggered.connect(self.zoom_reset)
        toolbar.addAction(zoom_reset_action)
        
        toolbar.addSeparator()
        
        # Grid toggle
        self.grid_toggle_action = QAction("⊞ Grid", self)
        self.grid_toggle_action.setCheckable(True)
        self.grid_toggle_action.setChecked(True)
        self.grid_toggle_action.setToolTip("Toggle grid visibility")
        self.grid_toggle_action.triggered.connect(self.toggle_grid)
        toolbar.addAction(self.grid_toggle_action)
        
        # Snap to grid toggle
        self.snap_toggle_action = QAction("🧲 Snap", self)
        self.snap_toggle_action.setCheckable(True)
        self.snap_toggle_action.setChecked(True)
        self.snap_toggle_action.setToolTip("Toggle snap to grid")
        self.snap_toggle_action.triggered.connect(self.toggle_snap)
        toolbar.addAction(self.snap_toggle_action)

        # FSM Toolbar (hidden by default, shown when in agent_internal mode)
        self.fsm_toolbar = QToolBar("FSM Editor Toolbar")
        self.fsm_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.fsm_toolbar)
        self.fsm_toolbar.hide()  # Hidden by default

        # Add State button
        add_state_action = QAction("➕ State", self)
        add_state_action.setToolTip("Add a new state to the FSM")
        add_state_action.triggered.connect(self.add_fsm_state)
        self.fsm_toolbar.addAction(add_state_action)

        # Add Transition button
        add_transition_action = QAction("➡️ Transition", self)
        add_transition_action.setToolTip("Add a transition between two states")
        add_transition_action.triggered.connect(self.add_fsm_transition)
        self.fsm_toolbar.addAction(add_transition_action)

        self.fsm_toolbar.addSeparator()

        # Back to main view button
        back_action = QAction("⬅️ Back", self)
        back_action.setToolTip("Return to main canvas view (ESC)")
        back_action.triggered.connect(self.exit_fsm_view)
        self.fsm_toolbar.addAction(back_action)

    def setup_statusbar(self):
        """Setup status bar"""
        self.statusBar().showMessage("Ready - Press F1 for help, Ctrl+N for new model")
        
        # Add permanent widgets to status bar
        from PyQt6.QtWidgets import QLabel
        
        # Selection info label
        self.selection_label = QLabel("No selection")
        self.selection_label.setStyleSheet("padding: 0 10px;")
        self.statusBar().addPermanentWidget(self.selection_label)
        
        # Zoom level label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("padding: 0 10px;")
        self.statusBar().addPermanentWidget(self.zoom_label)
        
        # Grid/snap status
        self.grid_status_label = QLabel("Grid: ON | Snap: ON")
        self.grid_status_label.setStyleSheet("padding: 0 10px;")
        self.statusBar().addPermanentWidget(self.grid_status_label)

    def connect_signals(self):
        """Connect signals between widgets"""
        # Canvas signals
        self.canvas.selection_changed.connect(self.properties_panel.show_block_properties)
        self.canvas.selection_changed.connect(self.on_selection_changed)
        self.canvas.block_double_clicked.connect(self.open_agent_internal_view)
        self.canvas.model_changed.connect(self.on_model_changed)
        self.canvas.mode_changed.connect(self.on_canvas_mode_changed)

        # Component Library signals
        # (Library uses itemClicked, handled in _on_library_item_clicked)

        # Model Structure tree signals
        self.model_structure_tree.agent_instance_selected.connect(self.on_agent_instance_selected)
        self.model_structure_tree.agent_type_selected.connect(self.on_agent_type_selected)
        self.model_structure_tree.create_custom_agent.connect(self.create_custom_agent)

    def open_agent_internal_view(self, block_id):
        """Open agent's internal view in NEW TAB (AnyLogic style)"""
        block = self.model.get_block_by_id(block_id)
        if not block:
            return

        # Check if already open in a tab
        for i in range(self.canvas_tabs.count()):
            widget = self.canvas_tabs.widget(i)
            if hasattr(widget, 'current_agent_id') and widget.current_agent_id == block_id:
                # Already open, just switch to that tab
                self.canvas_tabs.setCurrentIndex(i)
                return

        # Create new canvas for this agent
        agent_canvas = CanvasWidget(self.model, self)
        agent_canvas.enter_agent_view(block_id)

        # Connect signals for this canvas
        agent_canvas.selection_changed.connect(self.properties_panel.show_block_properties)
        agent_canvas.block_double_clicked.connect(self.open_agent_internal_view)
        agent_canvas.model_changed.connect(self.on_model_changed)
        agent_canvas.mode_changed.connect(self.on_canvas_mode_changed)

        # Add tab
        tab_index = self.canvas_tabs.addTab(agent_canvas, f"🤖 {block.name}")
        self.canvas_tabs.setCurrentIndex(tab_index)

        self.statusBar().showMessage(f"Opened {block.name} in new tab")

    def on_agent_instance_selected(self, instance_id):
        """Handle agent instance selection/double-click from project tree"""
        block = self.model.get_block_by_id(instance_id)
        if block:
            # Open agent internal view (FSM editor)
            self.open_agent_internal_view(instance_id)

    def on_agent_type_selected(self, type_name):
        """Handle agent type selection from project tree"""
        # Set canvas to create mode for this type
        self.canvas.set_create_mode(type_name)
        self.statusBar().showMessage(f"Click to place: {type_name}")

    def create_custom_agent(self):
        """Create a new custom agent type"""
        # TODO: Open custom agent designer
        self.statusBar().showMessage("Custom agent creation not yet implemented")

    def on_model_changed(self):
        """Handle model changes - refresh project tree"""
        self.project_tree.refresh_instances()

    def on_selection_changed(self, block):
        """Handle selection changes - update status bar"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'scene'):
            selected_items = current_canvas.scene.selectedItems()
            if len(selected_items) == 0:
                self.selection_label.setText("No selection")
            elif len(selected_items) == 1:
                if block:
                    self.selection_label.setText(f"Selected: {block.name}")
                else:
                    self.selection_label.setText("1 item selected")
            else:
                self.selection_label.setText(f"{len(selected_items)} items selected")

    def on_canvas_mode_changed(self, mode: str):
        """Handle canvas mode changes - show/hide FSM toolbar"""
        if mode == "agent_internal":
            self.fsm_toolbar.show()
            # Component library stays visible (contains FSM elements too)
        else:
            self.fsm_toolbar.hide()

    # File operations
    def new_model(self):
        """Create a new model"""
        reply = QMessageBox.question(
            self, "New Model",
            "Create a new model? Unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.model = SimulationModel(name="New Model")
            self.canvas.set_model(self.model)
            self.fsm_editor.set_fsm(None)
            self.current_file = None
            self.statusBar().showMessage("New model created")

    def open_model(self):
        """Open a model from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Model", "", "hsim Models (*.hsim);;All Files (*)"
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.model = SimulationModel.from_dict(data)
                self.canvas.set_model(self.model)
                self.fsm_editor.set_fsm(None)
                self.current_file = filename
                self.statusBar().showMessage(f"Opened {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def save_model(self):
        """Save the current model"""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_model_as()

    def save_model_as(self):
        """Save the current model with a new filename"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Model", "", "hsim Models (*.hsim);;All Files (*)"
        )
        if filename:
            if not filename.endswith('.hsim'):
                filename += '.hsim'
            self._save_to_file(filename)

    def _save_to_file(self, filename):
        """Save model to a file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.model.to_dict(), f, indent=2)
            self.current_file = filename
            self.statusBar().showMessage(f"Saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def export_python(self):
        """Export model as Python code"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Python Code", "", "Python Files (*.py);;All Files (*)"
        )
        if filename:
            try:
                from hsim.gui.utils.code_generator import CodeGenerator
                generator = CodeGenerator(self.model)
                code = generator.generate()

                with open(filename, 'w') as f:
                    f.write(code)
                self.statusBar().showMessage(f"Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export:\n{e}")

    # Edit operations
    def delete_selected(self):
        """Delete selected items"""
        current_widget = self.canvas_tabs.currentWidget()
        if hasattr(current_widget, 'delete_selected'):
            current_widget.delete_selected()

    # View operations
    def zoom_in(self):
        """Zoom in the current view"""
        current_widget = self.canvas_tabs.currentWidget()
        if hasattr(current_widget, 'zoom_in'):
            current_widget.zoom_in()
            self._update_zoom_label(current_widget)

    def zoom_out(self):
        """Zoom out the current view"""
        current_widget = self.canvas_tabs.currentWidget()
        if hasattr(current_widget, 'zoom_out'):
            current_widget.zoom_out()
            self._update_zoom_label(current_widget)

    def zoom_reset(self):
        """Reset zoom to 100%"""
        current_widget = self.canvas_tabs.currentWidget()
        if hasattr(current_widget, 'zoom_reset'):
            current_widget.zoom_reset()
            self._update_zoom_label(current_widget)
    
    def _update_zoom_label(self, canvas):
        """Update zoom label in status bar"""
        if hasattr(canvas, 'zoom_level'):
            zoom_percent = int(canvas.zoom_level * 100)
            self.zoom_label.setText(f"{zoom_percent}%")

    def toggle_grid(self, checked):
        """Toggle grid display"""
        current_widget = self.canvas_tabs.currentWidget()
        if hasattr(current_widget, 'set_grid_visible'):
            current_widget.set_grid_visible(checked)
            self.statusBar().showMessage(f"Grid {'visible' if checked else 'hidden'}", 1000)
            self._update_grid_status_label()
    
    def toggle_snap(self, checked):
        """Toggle snap to grid"""
        current_widget = self.canvas_tabs.currentWidget()
        if hasattr(current_widget, 'grid_snap'):
            current_widget.grid_snap = checked
            self.statusBar().showMessage(f"Snap to grid {'enabled' if checked else 'disabled'}", 1000)
            self._update_grid_status_label()
    
    def _update_grid_status_label(self):
        """Update grid/snap status in status bar"""
        grid_on = self.grid_toggle_action.isChecked()
        snap_on = self.snap_toggle_action.isChecked()
        self.grid_status_label.setText(
            f"Grid: {'ON' if grid_on else 'OFF'} | Snap: {'ON' if snap_on else 'OFF'}"
        )

    # Simulation operations
    def run_simulation(self):
        """Run the simulation"""
        # TODO: Implement simulation runner
        QMessageBox.information(
            self, "Run Simulation",
            "Simulation runner not yet implemented.\nUse 'Export Python Code' to run manually."
        )

    def validate_model(self):
        """Validate the model"""
        # TODO: Implement model validation
        errors = []

        # Check for generators
        generators = [b for b in self.model.blocks.values() if b.type == "generator"]
        if not generators:
            errors.append("Model has no Generator blocks")

        # Check for terminators
        terminators = [b for b in self.model.blocks.values() if b.type == "terminator"]
        if not terminators:
            errors.append("Model has no Terminator blocks")

        # Check for disconnected blocks
        for block_id, block in self.model.blocks.items():
            if block.type != "generator" and not self.model.get_connections_to(block_id):
                errors.append(f"Block '{block.name}' has no incoming connections")
            if block.type != "terminator" and not self.model.get_connections_from(block_id):
                errors.append(f"Block '{block.name}' has no outgoing connections")

        if errors:
            QMessageBox.warning(
                self, "Validation Errors",
                "Model validation found issues:\n\n" + "\n".join(f"• {e}" for e in errors)
            )
        else:
            QMessageBox.information(
                self, "Validation",
                "Model is valid!"
            )

    # FSM Toolbar Actions
    def add_fsm_state(self):
        """Add a new state to the current FSM"""
        if self.canvas.current_mode == "agent_internal" and self.canvas.current_fsm:
            # Delegate to canvas widget
            self.canvas.create_fsm_state()
        else:
            self.statusBar().showMessage("Cannot add state: Not in FSM editing mode", 3000)

    def add_fsm_transition(self):
        """Add a transition between selected states"""
        if self.canvas.current_mode == "agent_internal" and self.canvas.current_fsm:
            # Delegate to canvas widget
            self.canvas.create_fsm_transition()
        else:
            self.statusBar().showMessage("Cannot add transition: Not in FSM editing mode", 3000)

    def exit_fsm_view(self):
        """Exit FSM editing view and return to main canvas"""
        if self.canvas.current_mode == "agent_internal":
            # Exit agent view (this will emit mode_changed signal)
            self.canvas.exit_agent_view()
        else:
            self.statusBar().showMessage("Already in main view", 2000)

    def _create_model_structure_tree(self):
        """Create Model Structure tree (shows what's in the model)"""
        tree = ProjectTree(self)
        tree.set_model(self.model)
        return tree

    def _create_component_library(self):
        """Create Component Library (shows what can be added)"""
        from PyQt6.QtGui import QFont

        library = QTreeWidget()
        library.setHeaderLabel("Components")
        library.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #CCCCCC;
                border: none;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 6px;
            }
            QTreeWidget::item:hover {
                background-color: #2A2D2E;
            }
        """)

        font = QFont()
        font.setBold(True)

        # DES Blocks category
        des_blocks = QTreeWidgetItem(library, ["📦 DES Blocks"])
        des_blocks.setFont(0, font)
        des_blocks.setExpanded(True)

        # Process Flow
        process = QTreeWidgetItem(des_blocks, ["📊 Process Flow"])
        QTreeWidgetItem(process, ["⚙️ Generator"])
        QTreeWidgetItem(process, ["📦 Buffer"])
        QTreeWidgetItem(process, ["🔧 Server"])
        QTreeWidgetItem(process, ["📥 Store"])
        QTreeWidgetItem(process, ["🗑️ Terminator"])

        # Resources
        resources = QTreeWidgetItem(des_blocks, ["🔧 Resources"])
        QTreeWidgetItem(resources, ["⚠️ Unreliable Machine"])
        QTreeWidgetItem(resources, ["✓ Quality Machine"])
        QTreeWidgetItem(resources, ["🔄 SUMachine"])
        QTreeWidgetItem(resources, ["👷 Manual Station"])

        # Advanced
        advanced = QTreeWidgetItem(des_blocks, ["🔀 Advanced"])
        QTreeWidgetItem(advanced, ["🔗 Assembly"])
        QTreeWidgetItem(advanced, ["🤖 Agent"])

        # FSM Elements category
        fsm_elements = QTreeWidgetItem(library, ["🔄 FSM Elements"])
        fsm_elements.setFont(0, font)
        fsm_elements.setExpanded(True)
        QTreeWidgetItem(fsm_elements, ["⭕ State"])
        QTreeWidgetItem(fsm_elements, ["➡️ Transition"])
        QTreeWidgetItem(fsm_elements, ["⏱️ Timeout Event"])

        # Connectors category (includes ports)
        connectors = QTreeWidgetItem(library, ["🔗 Connectors"])
        connectors.setFont(0, font)
        connectors.setExpanded(True)
        QTreeWidgetItem(connectors, ["→ Connection"])
        QTreeWidgetItem(connectors, ["📥 Input Port"])
        QTreeWidgetItem(connectors, ["📤 Output Port"])

        # Actions category
        actions = QTreeWidgetItem(library, ["⚡ Actions"])
        actions.setFont(0, font)
        actions.setExpanded(False)
        QTreeWidgetItem(actions, ["📤 Send Message"])
        QTreeWidgetItem(actions, ["🔔 Trigger Event"])
        QTreeWidgetItem(actions, ["📝 Set Variable"])
        QTreeWidgetItem(actions, ["🔁 Loop"])

        # Connect drag-drop for DES blocks
        library.itemClicked.connect(self._on_library_item_clicked)

        return library

    def _on_library_item_clicked(self, item, column):
        """Handle library item click"""
        item_text = item.text(0)

        # Map library items to block types
        block_mapping = {
            # DES Blocks
            "⚙️ Generator": "generator",
            "📦 Buffer": "buffer",
            "🔧 Server": "server",
            "📥 Store": "store",
            "🗑️ Terminator": "terminator",
            "⚠️ Unreliable Machine": "unreliable_machine",
            "✓ Quality Machine": "quality_machine",
            "🔄 SUMachine": "su_machine",
            "👷 Manual Station": "manual_station",
            "🔗 Assembly": "assembly",
            "🤖 Agent": "agent"
        }

        # FSM Elements and Connectors
        fsm_element_mapping = {
            "⭕ State": "state",
            "➡️ Transition": "transition",
            "⏱️ Timeout Event": "timeout_event",
            "→ Connection": "connection",
            "📥 Input Port": "input_port",
            "📤 Output Port": "output_port"
        }

        current_canvas = self.canvas_tabs.currentWidget()

        if item_text in block_mapping:
            block_type = block_mapping[item_text]
            current_canvas.set_create_mode(block_type)
            self.statusBar().showMessage(f"Click canvas to place: {item_text}", 3000)
        elif item_text in fsm_element_mapping:
            element_type = fsm_element_mapping[item_text]
            current_canvas.set_create_mode(element_type)

            # Different messages for different element types
            if element_type == "state":
                self.statusBar().showMessage("Click canvas to place State", 3000)
            elif element_type == "transition":
                self.statusBar().showMessage("Click source state, then target state to create Transition", 5000)
            elif element_type == "timeout_event":
                self.statusBar().showMessage("Click state to add Timeout Event", 3000)
            elif element_type == "connection":
                self.statusBar().showMessage("Drag from output port to input port to create Connection", 5000)
            elif element_type in ["input_port", "output_port"]:
                port_type = "Input" if element_type == "input_port" else "Output"
                self.statusBar().showMessage(f"Click agent block to add {port_type} Port", 3000)

    def _close_agent_tab(self, index):
        """Close an agent tab"""
        if index == 0:
            # Cannot close Main tab
            self.statusBar().showMessage("Cannot close Main tab", 2000)
            return

        # Get widget before removing
        widget = self.canvas_tabs.widget(index)

        # Remove tab
        self.canvas_tabs.removeTab(index)

        # Delete widget to free memory
        if widget:
            widget.deleteLater()

        self.statusBar().showMessage("Tab closed", 1000)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About hsim Model Designer",
            "<h2>hsim Model Designer</h2>"
            "<p><b>Visual designer for discrete event simulation models</b></p>"
            "<p>Version 1.0.0</p>"
            "<hr>"
            "<p>Features:</p>"
            "<ul>"
            "<li>🎨 AnyLogic-style interface with dark theme</li>"
            "<li>🔧 Visual block-based modeling</li>"
            "<li>🔄 FSM editor for agent behaviors</li>"
            "<li>⚡ Hierarchical agent composition</li>"
            "<li>↶ Undo/Redo support</li>"
            "<li>📋 Copy/Paste functionality</li>"
            "<li>⬌ Alignment and distribution tools</li>"
            "<li>🧲 Grid snapping</li>"
            "<li>🐍 Python code export</li>"
            "</ul>"
            "<hr>"
            "<p>Built with PyQt6 and the hsim framework</p>"
            "<p>© 2025 hsim Project</p>"
        )
    
    def undo(self):
        """Undo the last action"""
        description = self.undo_stack.undo()
        if description:
            self.statusBar().showMessage(f"Undone: {description}", 2000)
            self.update_undo_redo_actions()
            self.on_model_changed()
    
    def redo(self):
        """Redo the last undone action"""
        description = self.undo_stack.redo()
        if description:
            self.statusBar().showMessage(f"Redone: {description}", 2000)
            self.update_undo_redo_actions()
            self.on_model_changed()
    
    def update_undo_redo_actions(self):
        """Update undo/redo action states and tooltips"""
        can_undo = self.undo_stack.can_undo()
        can_redo = self.undo_stack.can_redo()
        
        self.undo_action.setEnabled(can_undo)
        self.redo_action.setEnabled(can_redo)
        self.undo_toolbar_action.setEnabled(can_undo)
        self.redo_toolbar_action.setEnabled(can_redo)
        
        if can_undo:
            undo_text = self.undo_stack.get_undo_text()
            self.undo_action.setToolTip(f"Undo: {undo_text}")
            self.undo_toolbar_action.setToolTip(f"Undo: {undo_text}")
        else:
            self.undo_action.setToolTip("Nothing to undo")
            self.undo_toolbar_action.setToolTip("Nothing to undo")
        
        if can_redo:
            redo_text = self.undo_stack.get_redo_text()
            self.redo_action.setToolTip(f"Redo: {redo_text}")
            self.redo_toolbar_action.setToolTip(f"Redo: {redo_text}")
        else:
            self.redo_action.setToolTip("Nothing to redo")
            self.redo_toolbar_action.setToolTip("Nothing to redo")
    
    def copy_selected(self):
        """Copy selected blocks"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'copy_selected'):
            count = current_canvas.copy_selected()
            if count > 0:
                self.statusBar().showMessage(f"Copied {count} block(s)", 2000)
            else:
                self.statusBar().showMessage("No blocks selected to copy", 2000)
    
    def paste_from_clipboard(self):
        """Paste blocks from clipboard"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'paste_from_clipboard'):
            count = current_canvas.paste_from_clipboard()
            if count > 0:
                self.statusBar().showMessage(f"Pasted {count} block(s)", 2000)
            else:
                self.statusBar().showMessage("Nothing to paste", 2000)
    
    def align_left(self):
        """Align selected blocks to the left"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'align_left'):
            current_canvas.align_left()
            self.statusBar().showMessage("Aligned to left", 1000)
    
    def align_right(self):
        """Align selected blocks to the right"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'align_right'):
            current_canvas.align_right()
            self.statusBar().showMessage("Aligned to right", 1000)
    
    def align_top(self):
        """Align selected blocks to the top"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'align_top'):
            current_canvas.align_top()
            self.statusBar().showMessage("Aligned to top", 1000)
    
    def align_bottom(self):
        """Align selected blocks to the bottom"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'align_bottom'):
            current_canvas.align_bottom()
            self.statusBar().showMessage("Aligned to bottom", 1000)
    
    def align_horizontal_center(self):
        """Align selected blocks to horizontal center"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'align_horizontal_center'):
            current_canvas.align_horizontal_center()
            self.statusBar().showMessage("Aligned to horizontal center", 1000)
    
    def align_vertical_center(self):
        """Align selected blocks to vertical center"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'align_vertical_center'):
            current_canvas.align_vertical_center()
            self.statusBar().showMessage("Aligned to vertical center", 1000)
    
    def distribute_horizontally(self):
        """Distribute selected blocks horizontally"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'distribute_horizontally'):
            current_canvas.distribute_horizontally()
            self.statusBar().showMessage("Distributed horizontally", 1000)
    
    def distribute_vertically(self):
        """Distribute selected blocks vertically"""
        current_canvas = self.canvas_tabs.currentWidget()
        if hasattr(current_canvas, 'distribute_vertically'):
            current_canvas.distribute_vertically()
            self.statusBar().showMessage("Distributed vertically", 1000)
