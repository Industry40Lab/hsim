"""
Main application window with three-panel layout
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QTabWidget, QLabel,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from hsim.gui.models.model import SimulationModel
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
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.connect_signals()

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

        # Left panel - Project tree + Component Palette
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Project tree (top, 60% of left panel)
        self.project_tree = ProjectTree(self)
        self.project_tree.set_model(self.model)

        # Component palette (bottom, 40% of left panel)
        self.palette = PaletteWidget(self)

        # Vertical splitter for left panel
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.addWidget(self.project_tree)
        left_splitter.addWidget(self.palette)
        left_splitter.setSizes([400, 300])
        left_layout.addWidget(left_splitter)

        left_panel.setMinimumWidth(200)
        left_panel.setMaximumWidth(280)

        # Center panel - Main canvas (no tabs, embed agent editor in canvas)
        self.canvas = CanvasWidget(self.model, self)
        self.fsm_editor = FSMEditorWidget(self)  # Keep for compatibility

        # Right panel - Properties Panel (code-focused)
        self.properties_panel = PropertiesPanel(self)
        self.properties_panel.model = self.model
        self.properties_panel.setMinimumWidth(300)
        self.properties_panel.setMaximumWidth(400)

        # Add widgets to splitter
        self.main_splitter.addWidget(left_panel)
        self.main_splitter.addWidget(self.canvas)
        self.main_splitter.addWidget(self.properties_panel)

        # Set splitter sizes (left: 250, center: 1000, right: 300)
        self.main_splitter.setSizes([250, 1000, 300])

        main_layout.addWidget(self.main_splitter)

    def setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_model)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_model)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_model)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_model_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_python_action = QAction("Export &Python Code...", self)
        export_python_action.triggered.connect(self.export_python)
        file_menu.addAction(export_python_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setEnabled(False)  # TODO: Implement undo/redo
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setEnabled(False)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        delete_action = QAction("&Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset_action.triggered.connect(self.zoom_reset)
        view_menu.addAction(zoom_reset_action)

        view_menu.addSeparator()

        toggle_grid_action = QAction("Show &Grid", self)
        toggle_grid_action.setCheckable(True)
        toggle_grid_action.setChecked(True)
        toggle_grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(toggle_grid_action)

        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")

        run_action = QAction("&Run", self)
        run_action.setShortcut(QKeySequence("F5"))
        run_action.triggered.connect(self.run_simulation)
        sim_menu.addAction(run_action)

        validate_action = QAction("&Validate Model", self)
        validate_action.triggered.connect(self.validate_model)
        sim_menu.addAction(validate_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Setup toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # New
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_model)
        toolbar.addAction(new_action)

        # Open
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_model)
        toolbar.addAction(open_action)

        # Save
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_model)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # Run
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.run_simulation)
        toolbar.addAction(run_action)

        toolbar.addSeparator()

        # Zoom controls
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

    def setup_statusbar(self):
        """Setup status bar"""
        self.statusBar().showMessage("Ready")

    def connect_signals(self):
        """Connect signals between widgets"""
        # Canvas signals
        self.canvas.selection_changed.connect(self.properties_panel.show_block_properties)
        self.canvas.block_double_clicked.connect(self.open_agent_internal_view)
        self.canvas.model_changed.connect(self.on_model_changed)

        # Palette signals
        self.palette.block_selected.connect(self.canvas.set_create_mode)

        # Project tree signals
        self.project_tree.agent_instance_selected.connect(self.on_agent_instance_selected)
        self.project_tree.agent_type_selected.connect(self.on_agent_type_selected)
        self.project_tree.create_custom_agent.connect(self.create_custom_agent)

    def open_agent_internal_view(self, block_id):
        """Open agent's internal view (statechart embedded in canvas)"""
        block = self.model.get_block_by_id(block_id)
        if block:
            # TODO: Implement canvas mode switching to show agent internals
            # For now, use temporary FSM editor
            self.fsm_editor.set_agent(block, self.model)
            self.statusBar().showMessage(f"Opening internal view: {block.name}")

    def on_agent_instance_selected(self, instance_id):
        """Handle agent instance selection from project tree"""
        block = self.model.get_block_by_id(instance_id)
        if block:
            # Highlight on canvas
            self.canvas.select_block(instance_id)
            self.properties_panel.show_block_properties(instance_id)
            self.statusBar().showMessage(f"Selected: {block.name}")

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
        current_widget = self.center_tabs.currentWidget()
        if current_widget == self.canvas:
            self.canvas.delete_selected()
        elif current_widget == self.fsm_editor:
            self.fsm_editor.delete_selected()

    # View operations
    def zoom_in(self):
        """Zoom in the current view"""
        current_widget = self.center_tabs.currentWidget()
        if hasattr(current_widget, 'zoom_in'):
            current_widget.zoom_in()

    def zoom_out(self):
        """Zoom out the current view"""
        current_widget = self.center_tabs.currentWidget()
        if hasattr(current_widget, 'zoom_out'):
            current_widget.zoom_out()

    def zoom_reset(self):
        """Reset zoom to 100%"""
        current_widget = self.center_tabs.currentWidget()
        if hasattr(current_widget, 'zoom_reset'):
            current_widget.zoom_reset()

    def toggle_grid(self, checked):
        """Toggle grid display"""
        current_widget = self.center_tabs.currentWidget()
        if hasattr(current_widget, 'set_grid_visible'):
            current_widget.set_grid_visible(checked)

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

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About hsim Model Designer",
            "<h2>hsim Model Designer</h2>"
            "<p>Visual designer for discrete event simulation models</p>"
            "<p>Version 0.1.0</p>"
            "<p>Built with PyQt6 and hsim framework</p>"
        )
