"""
Project Tree - Hierarchical view of simulation model structure
Shows agents, resources, custom types, and model hierarchy
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QMenu, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont


class ProjectTree(QWidget):
    """Hierarchical project structure tree"""

    # Signals
    agent_type_selected = pyqtSignal(str)  # Agent type name
    agent_instance_selected = pyqtSignal(str)  # Instance ID
    create_custom_agent = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.setup_ui()

    def setup_ui(self):
        """Setup project tree UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Project Structure")
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #CCCCCC;
                border: none;
                outline: none;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
                color: #FFFFFF;
            }
            QTreeWidget::item:hover {
                background-color: #2A2D2E;
            }
            QTreeWidget::branch {
                background-color: #252526;
            }
        """)

        # Context menu
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Selection handling
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)

        layout.addWidget(self.tree)

        # Initialize tree structure
        self.init_tree_structure()

    def init_tree_structure(self):
        """Initialize the default tree structure - ONLY instances, no types"""
        self.tree.clear()

        # Main frame (root container)
        self.main_node = QTreeWidgetItem(self.tree, ["📋 Main (Frame)"])
        self.main_node.setExpanded(True)
        font = QFont()
        font.setBold(True)
        self.main_node.setFont(0, font)

        # Note: Agent types are now in Library tab, not here
        # This tree only shows actual instances in the model

        # Expand all
        self.tree.expandAll()

    def _add_agent_type(self, parent, name, icon, description, display_name=None):
        """Add an agent type to the tree"""
        # Use display_name for UI, name for enum value
        label = display_name if display_name else name
        item = QTreeWidgetItem(parent, [f"{icon} {label}"])
        item.setData(0, Qt.ItemDataRole.UserRole, {
            'type': 'agent_type',
            'name': name,  # This is the enum value (e.g., "generator")
            'description': description
        })
        item.setToolTip(0, description)
        return item

    def set_model(self, model):
        """Set the simulation model"""
        self.model = model
        self.refresh_instances()

    def refresh_instances(self):
        """Refresh agent instances from model"""
        if not self.model:
            return

        # Clear main node
        self.main_node.takeChildren()

        # Add all blocks as agent instances
        for block in self.model.blocks.values():
            item = QTreeWidgetItem(self.main_node, [f"  {block.name} ({block.type})"])
            item.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'agent_instance',
                'id': block.id,
                'block': block
            })

            # If block has FSM, show statechart indicator
            if block.fsm_id:
                item.setText(0, f"  {block.name} ({block.type}) 🔄")

    def add_custom_agent_type(self, name, base_type=None):
        """Add a custom agent type to the tree"""
        icon = "🎯"
        if base_type:
            item = QTreeWidgetItem(self.custom_agents_node, [f"{icon} {name} (extends {base_type})"])
        else:
            item = QTreeWidgetItem(self.custom_agents_node, [f"{icon} {name}"])

        item.setData(0, Qt.ItemDataRole.UserRole, {
            'type': 'custom_agent_type',
            'name': name,
            'base_type': base_type
        })

        self.custom_agents_node.setExpanded(True)
        return item

    def on_item_clicked(self, item, column):
        """Handle item click"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        if data['type'] == 'agent_type' or data['type'] == 'custom_agent_type':
            self.agent_type_selected.emit(data['name'])
        elif data['type'] == 'agent_instance':
            self.agent_instance_selected.emit(data['id'])

    def on_item_double_clicked(self, item, column):
        """Handle item double-click - open agent editor"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        if data['type'] == 'agent_instance':
            # Signal to open agent internal view
            self.agent_instance_selected.emit(data['id'])

    def show_context_menu(self, position):
        """Show context menu for tree items"""
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if item == self.agents_node or item == self.custom_agents_node:
            # Context menu for agents category
            action = menu.addAction("➕ Create Custom Agent")
            action.triggered.connect(self.create_custom_agent_dialog)

        elif data and data['type'] == 'agent_type':
            # Context menu for agent type
            action = menu.addAction(f"📖 View {data['name']} Documentation")
            action.triggered.connect(lambda: self.view_documentation(data['name']))

        elif data and data['type'] == 'custom_agent_type':
            # Context menu for custom agent type
            edit_action = menu.addAction("✏️ Edit Agent Type")
            edit_action.triggered.connect(lambda: self.edit_custom_agent(data['name']))

            delete_action = menu.addAction("🗑️ Delete Agent Type")
            delete_action.triggered.connect(lambda: self.delete_custom_agent(item))

        elif data and data['type'] == 'agent_instance':
            # Context menu for agent instance
            open_action = menu.addAction("🔍 Open Internal View")
            open_action.triggered.connect(lambda: self.agent_instance_selected.emit(data['id']))

            edit_action = menu.addAction("📝 Edit Properties")
            edit_action.triggered.connect(lambda: self.edit_instance_properties(data['id']))

            menu.addSeparator()

            delete_action = menu.addAction("🗑️ Delete Instance")
            delete_action.triggered.connect(lambda: self.delete_instance(data['id']))

        if menu.actions():
            menu.exec(self.tree.viewport().mapToGlobal(position))

    def create_custom_agent_dialog(self):
        """Show dialog to create custom agent"""
        name, ok = QInputDialog.getText(
            self,
            "Create Custom Agent",
            "Agent type name:",
            text="MyAgent"
        )

        if ok and name:
            # Check for duplicates
            if self._agent_type_exists(name):
                QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    f"Agent type '{name}' already exists."
                )
                return

            # Add to tree
            self.add_custom_agent_type(name)

            # Signal to create agent designer
            self.create_custom_agent.emit()

    def _agent_type_exists(self, name):
        """Check if agent type name already exists"""
        # Check custom agents
        for i in range(self.custom_agents_node.childCount()):
            child = self.custom_agents_node.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get('name') == name:
                return True
        return False

    def get_selected_agent_type(self):
        """Get currently selected agent type"""
        item = self.tree.currentItem()
        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data and (data['type'] == 'agent_type' or data['type'] == 'custom_agent_type'):
                return data['name']
        return None

    # Context menu action handlers
    def view_documentation(self, agent_name):
        """View documentation for agent type"""
        QMessageBox.information(
            self,
            f"{agent_name} Documentation",
            f"Documentation for {agent_name} agent type.\n\n"
            "This would open the online documentation or show help text."
        )

    def edit_custom_agent(self, agent_name):
        """Edit custom agent type"""
        QMessageBox.information(
            self,
            "Edit Custom Agent",
            f"Opening editor for custom agent: {agent_name}\n\n"
            "This feature will be implemented in a future update."
        )

    def delete_custom_agent(self, item):
        """Delete custom agent type"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        reply = QMessageBox.question(
            self,
            "Delete Custom Agent",
            f"Are you sure you want to delete '{data['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove from tree
            parent = item.parent()
            if parent:
                parent.removeChild(item)

            # TODO: Remove from model if custom agent types are stored there
            QMessageBox.information(
                self,
                "Deleted",
                f"Custom agent '{data['name']}' has been deleted."
            )

    def edit_instance_properties(self, instance_id):
        """Edit properties of agent instance"""
        if not self.model:
            return

        block = self.model.get_block_by_id(instance_id)
        if not block:
            return

        # Get main window to show properties
        main_window = self.window()
        if main_window and hasattr(main_window, 'properties_panel'):
            main_window.properties_panel.show_block_properties(block)
            QMessageBox.information(
                self,
                "Edit Properties",
                f"Properties for '{block.name}' are now shown in the Properties panel."
            )

    def delete_instance(self, instance_id):
        """Delete agent instance from model"""
        if not self.model:
            return

        block = self.model.get_block_by_id(instance_id)
        if not block:
            return

        reply = QMessageBox.question(
            self,
            "Delete Instance",
            f"Are you sure you want to delete '{block.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove block from model
            self.model.remove_block(instance_id)

            # Refresh tree
            self.refresh_instances()

            # Get main window to refresh canvas
            main_window = self.window()
            if main_window and hasattr(main_window, 'canvas'):
                main_window.canvas.refresh_from_model()

            QMessageBox.information(
                self,
                "Deleted",
                f"Agent instance '{block.name}' has been deleted."
            )
