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
        """Initialize the default tree structure"""
        self.tree.clear()

        # Main simulation node
        self.main_node = QTreeWidgetItem(self.tree, ["📋 Main"])
        self.main_node.setExpanded(True)
        font = QFont()
        font.setBold(True)
        self.main_node.setFont(0, font)

        # Agents category
        self.agents_node = QTreeWidgetItem(self.tree, ["🤖 Agent Types"])
        self.agents_node.setExpanded(True)
        self.agents_node.setFont(0, font)

        # Add built-in agent types (DES blocks are agents)
        builtin_agents = QTreeWidgetItem(self.agents_node, ["📦 Built-in"])

        # Process Flow Agents
        process_category = QTreeWidgetItem(builtin_agents, ["📊 Process Flow"])
        self._add_agent_type(process_category, "Generator", "⚙️", "Generates entities")
        self._add_agent_type(process_category, "Buffer", "📦", "Stores entities")
        self._add_agent_type(process_category, "Server", "🔧", "Processes entities")
        self._add_agent_type(process_category, "Terminator", "🗑️", "Destroys entities")

        # Resource Agents
        resource_category = QTreeWidgetItem(builtin_agents, ["🔧 Resources"])
        self._add_agent_type(resource_category, "UnreliableMachine", "⚠️", "Machine with failures")
        self._add_agent_type(resource_category, "QualityMachine", "✓", "Quality control")
        self._add_agent_type(resource_category, "SUMachine", "🔄", "Setup/operation")

        # Custom agents category
        self.custom_agents_node = QTreeWidgetItem(self.agents_node, ["⭐ Custom"])
        self.custom_agents_node.setExpanded(True)

        # Resources category (instances)
        self.resources_node = QTreeWidgetItem(self.tree, ["🏭 Resources"])
        self.resources_node.setFont(0, font)

        # Expand all
        self.tree.expandAll()

    def _add_agent_type(self, parent, name, icon, description):
        """Add an agent type to the tree"""
        item = QTreeWidgetItem(parent, [f"{icon} {name}"])
        item.setData(0, Qt.ItemDataRole.UserRole, {
            'type': 'agent_type',
            'name': name,
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

        elif data and data['type'] == 'custom_agent_type':
            # Context menu for custom agent type
            menu.addAction("✏️ Edit Agent Type")
            menu.addAction("🗑️ Delete Agent Type")

        elif data and data['type'] == 'agent_instance':
            # Context menu for agent instance
            menu.addAction("🔍 Open Internal View")
            menu.addAction("📝 Edit Properties")
            menu.addSeparator()
            menu.addAction("🗑️ Delete Instance")

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
