# Code-GUI Synchronization Plan

**Goal**: Bidirectional synchronization between Python code and visual GUI models

**Status**: Planning → Implementation

---

## Overview

Enable seamless integration between code and visual design:

1. **Show Object Methods in GUI** - Introspect and display class methods/properties
2. **Modify Methods from GUI** - Edit code directly in properties panel
3. **Import Code to GUI** - Parse Python files and create visual models
4. **Export GUI to Code** - Generate complete, runnable Python code

---

## Architecture Design

### Data Model Extensions

**Current State**:
- Block has: `id, type, name, position, size, properties, fsm_ids, parent_id, children`
- Properties stored as `Dict[str, Any]`

**New Requirements**:
```python
@dataclass
class Block:
    # ... existing fields ...
    custom_methods: Dict[str, str] = field(default_factory=dict)  # method_name -> code
    custom_attributes: Dict[str, Any] = field(default_factory=dict)  # attr_name -> value
    method_overrides: Dict[str, str] = field(default_factory=dict)  # override base methods
```

**State Extensions**:
```python
@dataclass
class State:
    # ... existing fields ...
    on_enter_code: str = ""  # Executable Python code
    on_exit_code: str = ""   # Executable Python code
    on_state_code: str = ""  # Continuous behavior
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GUI Layer                            │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Properties   │  │ Code Editor  │  │ Method       │ │
│  │ Panel        │  │ Widget       │  │ Inspector    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│                  Sync Layer                             │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Code         │  │ Code         │  │ Method       │ │
│  │ Parser       │  │ Generator    │  │ Introspector │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
├─────────────────────────────────────────────────────────┤
│                  Data Layer                             │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Model        │  │ Block        │  │ FSM          │ │
│  │ (enhanced)   │  │ (enhanced)   │  │ (enhanced)   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Feature 1: Show Object Methods in GUI

**Goal**: Display class methods and properties when block is selected

### Implementation Steps

#### 1.1 Method Introspector
**File**: `hsim/gui/utils/method_introspector.py` (NEW)

```python
import inspect
from typing import Dict, List, Tuple
from hsim.gui.models.block_definitions import get_block_definition, BlockType

class MethodIntrospector:
    """Introspect Python classes to extract methods and attributes"""

    @staticmethod
    def get_class_methods(block_type: str) -> Dict[str, dict]:
        """Get all methods for a block type

        Returns:
            {
                'method_name': {
                    'signature': 'def method_name(self, arg1, arg2)',
                    'docstring': 'Method description',
                    'source': 'def method_name(self, arg1, arg2):\n    ...',
                    'is_public': True,
                    'parameters': [('arg1', 'type'), ('arg2', 'type')],
                    'return_type': 'str'
                }
            }
        """
        block_def = get_block_definition(BlockType(block_type))
        if not block_def or not block_def.python_module:
            return {}

        # Import the class
        module_path = block_def.python_module
        class_name = block_def.python_class

        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)

            methods = {}
            for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
                if name.startswith('_') and not name.startswith('__'):
                    continue  # Skip private methods

                signature = str(inspect.signature(method))
                docstring = inspect.getdoc(method) or ""
                source = inspect.getsource(method) if hasattr(method, '__code__') else ""

                methods[name] = {
                    'signature': f"def {name}{signature}",
                    'docstring': docstring,
                    'source': source,
                    'is_public': not name.startswith('_'),
                    'parameters': list(inspect.signature(method).parameters.keys()),
                    'return_type': inspect.signature(method).return_annotation
                }

            return methods
        except Exception as e:
            print(f"Error introspecting {block_type}: {e}")
            return {}

    @staticmethod
    def get_class_attributes(block_type: str) -> Dict[str, dict]:
        """Get class attributes and their types"""
        # Similar to get_class_methods but for attributes
        pass
```

#### 1.2 Methods Panel Widget
**File**: `hsim/gui/views/methods_panel.py` (NEW)

```python
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QSplitter,
                             QPushButton, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal

class MethodsPanel(QWidget):
    """Panel to display and edit object methods"""

    method_edited = pyqtSignal(str, str)  # method_name, new_code

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_block = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Splitter for methods list and code view
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Methods tree
        self.methods_tree = QTreeWidget()
        self.methods_tree.setHeaderLabels(["Method", "Signature"])
        self.methods_tree.itemClicked.connect(self.on_method_selected)
        splitter.addWidget(self.methods_tree)

        # Code editor
        code_container = QWidget()
        code_layout = QVBoxLayout(code_container)

        self.method_label = QLabel("Select a method to view/edit")
        code_layout.addWidget(self.method_label)

        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Method code will appear here...")
        code_layout.addWidget(self.code_editor)

        # Buttons
        button_layout = QVBoxLayout()
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.clicked.connect(self.save_method)
        button_layout.addWidget(self.save_btn)

        self.revert_btn = QPushButton("↶ Revert to Original")
        self.revert_btn.clicked.connect(self.revert_method)
        button_layout.addWidget(self.revert_btn)

        code_layout.addLayout(button_layout)
        splitter.addWidget(code_container)

        layout.addWidget(splitter)
        self.setLayout(layout)

    def show_block_methods(self, block):
        """Display methods for a block"""
        from hsim.gui.utils.method_introspector import MethodIntrospector

        self.current_block = block
        self.methods_tree.clear()

        # Get methods via introspection
        methods = MethodIntrospector.get_class_methods(block.type)

        for method_name, method_info in methods.items():
            item = QTreeWidgetItem([method_name, method_info['signature']])
            item.setData(0, Qt.ItemDataRole.UserRole, method_info)
            self.methods_tree.addTopLevelItem(item)

        # Add custom methods from block
        if hasattr(block, 'custom_methods'):
            custom_folder = QTreeWidgetItem(["📝 Custom Methods"])
            self.methods_tree.addTopLevelItem(custom_folder)

            for method_name, code in block.custom_methods.items():
                item = QTreeWidgetItem([method_name, "custom"])
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'source': code,
                    'is_custom': True
                })
                custom_folder.addChild(item)

    def on_method_selected(self, item, column):
        """Show method code when selected"""
        method_info = item.data(0, Qt.ItemDataRole.UserRole)
        if method_info:
            self.method_label.setText(f"Method: {item.text(0)}")
            self.code_editor.setPlainText(method_info.get('source', ''))

    def save_method(self):
        """Save edited method code"""
        # Get current method
        selected = self.methods_tree.selectedItems()
        if not selected:
            return

        method_name = selected[0].text(0)
        new_code = self.code_editor.toPlainText()

        # Emit signal
        self.method_edited.emit(method_name, new_code)

    def revert_method(self):
        """Revert to original method code"""
        # Reload from class definition
        pass
```

#### 1.3 Integration with Properties Panel
**File**: `hsim/gui/views/properties_panel.py` (MODIFY)

Add tab for methods:
```python
def setup_ui(self):
    # ... existing code ...

    # Add Methods tab
    self.methods_panel = MethodsPanel()
    self.methods_panel.method_edited.connect(self.on_method_edited)
    self.tabs.addTab(self.methods_panel, "⚙️ Methods")

def show_block_properties(self, block):
    # ... existing code ...

    # Show methods
    self.methods_panel.show_block_methods(block)
```

---

## Feature 2: Modify Methods from GUI

**Goal**: Edit method code directly in properties panel

### Implementation Steps

#### 2.1 Code Editor Widget
**File**: `hsim/gui/widgets/code_editor.py` (NEW)

```python
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QRegularExpression
import re

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_highlighting_rules()

    def setup_highlighting_rules(self):
        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#C678DD"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            'def', 'class', 'if', 'else', 'elif', 'for', 'while',
            'return', 'import', 'from', 'as', 'try', 'except',
            'finally', 'with', 'pass', 'break', 'continue', 'yield',
            'lambda', 'self', 'True', 'False', 'None'
        ]

        for keyword in keywords:
            pattern = QRegularExpression(f"\\b{keyword}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5C6370"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((
            QRegularExpression("#[^\n]*"),
            comment_format
        ))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98C379"))
        self.highlighting_rules.append((
            QRegularExpression("\".*?\"|'.*?'"),
            string_format
        ))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#61AFEF"))
        self.highlighting_rules.append((
            QRegularExpression("\\b[A-Za-z_][A-Za-z0-9_]*(?=\\()"),
            function_format
        ))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(),
                             match.capturedLength(), format)

class CodeEditorWidget(QTextEdit):
    """Enhanced text editor for Python code"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()

        # Add syntax highlighting
        self.highlighter = PythonSyntaxHighlighter(self.document())

    def setup_editor(self):
        # Monospace font
        font = QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.setFont(font)

        # Tab settings
        self.setTabStopDistance(40)

        # Line numbers (future enhancement)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
```

#### 2.2 Method Validation
**File**: `hsim/gui/utils/code_validator.py` (NEW)

```python
import ast
from typing import List, Tuple

class CodeValidator:
    """Validate Python code for syntax and basic errors"""

    @staticmethod
    def validate_python(code: str) -> Tuple[bool, List[str]]:
        """Validate Python code syntax

        Returns:
            (is_valid, errors)
        """
        errors = []

        try:
            ast.parse(code)
            return (True, [])
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
            return (False, errors)
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return (False, errors)

    @staticmethod
    def validate_method_signature(code: str, expected_name: str) -> Tuple[bool, List[str]]:
        """Validate that code defines the expected method"""
        errors = []

        try:
            tree = ast.parse(code)

            # Find function definition
            func_defs = [node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)]

            if not func_defs:
                errors.append("No function definition found")
                return (False, errors)

            if func_defs[0].name != expected_name:
                errors.append(f"Function name '{func_defs[0].name}' doesn't match expected '{expected_name}'")
                return (False, errors)

            return (True, [])
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return (False, errors)
```

---

## Feature 3: Import Code to GUI (REVERSE ENGINEERING)

**Goal**: Parse existing Python simulation code and create visual model

### Implementation Steps

#### 3.1 Code Parser
**File**: `hsim/gui/utils/code_parser.py` (NEW)

```python
import ast
from typing import Dict, List, Optional
from hsim.gui.models.model import SimulationModel, Block, Connection, Position

class CodeParser:
    """Parse Python simulation code and create GUI model"""

    def __init__(self):
        self.model = SimulationModel()
        self.block_vars = {}  # var_name -> Block
        self.current_x = 100
        self.current_y = 100

    def parse_file(self, filepath: str) -> SimulationModel:
        """Parse Python file and create model"""
        with open(filepath, 'r') as f:
            code = f.read()
        return self.parse_code(code)

    def parse_code(self, code: str) -> SimulationModel:
        """Parse Python code and create model"""
        try:
            tree = ast.parse(code)

            # Find main() function
            main_func = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'main':
                    main_func = node
                    break

            if not main_func:
                print("No main() function found")
                return self.model

            # Parse main function body
            for stmt in main_func.body:
                self._parse_statement(stmt)

            return self.model
        except Exception as e:
            print(f"Error parsing code: {e}")
            return self.model

    def _parse_statement(self, stmt):
        """Parse a single statement"""
        if isinstance(stmt, ast.Assign):
            # Block creation: generator_1 = Generator(env, 'Generator 1', ...)
            self._parse_assignment(stmt)
        elif isinstance(stmt, ast.Expr):
            # Method call or connection
            if isinstance(stmt.value, ast.Call):
                self._parse_call(stmt.value)

    def _parse_assignment(self, stmt):
        """Parse block assignment"""
        if not stmt.targets or len(stmt.targets) != 1:
            return

        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            return

        var_name = target.id

        # Check if it's a block creation
        if isinstance(stmt.value, ast.Call):
            if isinstance(stmt.value.func, ast.Name):
                class_name = stmt.value.func.id

                # Create block
                block = self._create_block_from_call(var_name, class_name, stmt.value)
                if block:
                    self.block_vars[var_name] = block
                    self.model.add_block(block)

    def _create_block_from_call(self, var_name: str, class_name: str, call_node) -> Optional[Block]:
        """Create Block from constructor call"""
        # Map class name to block type
        class_to_type = {
            'Generator': 'generator',
            'Server': 'server',
            'Buffer': 'buffer',
            'Terminator': 'terminator',
            'Store': 'store',
            'Assembly': 'assembly',
            # ... add all block types
        }

        block_type = class_to_type.get(class_name)
        if not block_type:
            return None

        # Extract name from arguments
        block_name = var_name
        if len(call_node.args) >= 2:
            if isinstance(call_node.args[1], ast.Constant):
                block_name = call_node.args[1].value

        # Extract properties from keyword arguments
        properties = {}
        for keyword in call_node.keywords:
            if isinstance(keyword.value, ast.Constant):
                properties[keyword.arg] = keyword.value.value

        # Create block with auto-layout
        block = Block(
            type=block_type,
            name=block_name,
            position=Position(self.current_x, self.current_y),
            properties=properties
        )

        # Update position for next block
        self.current_x += 150
        if self.current_x > 800:
            self.current_x = 100
            self.current_y += 120

        return block

    def _parse_call(self, call_node):
        """Parse method calls (connections, etc.)"""
        # Handle connections: generator_1.connections['next'] = server_1
        # This is actually in the parent Assign node, not a Call
        pass
```

#### 3.2 Import Dialog
**File**: `hsim/gui/dialogs/import_dialog.py` (NEW)

```python
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit,
                             QPushButton, QLabel, QFileDialog,
                             QMessageBox)
from PyQt6.QtCore import pyqtSignal

class ImportCodeDialog(QDialog):
    """Dialog for importing Python code"""

    code_imported = pyqtSignal(object)  # SimulationModel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Python Code")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Instructions
        label = QLabel("Paste or load Python simulation code:")
        layout.addWidget(label)

        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText(
            "def main():\n"
            "    env = Environment()\n"
            "    generator = Generator(env, 'Gen1')\n"
            "    ..."
        )
        layout.addWidget(self.code_editor)

        # Buttons
        load_btn = QPushButton("📁 Load from File...")
        load_btn.clicked.connect(self.load_file)
        layout.addWidget(load_btn)

        import_btn = QPushButton("✅ Import")
        import_btn.clicked.connect(self.import_code)
        layout.addWidget(import_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)

    def load_file(self):
        """Load Python file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Python File", "", "Python Files (*.py)"
        )
        if filename:
            with open(filename, 'r') as f:
                self.code_editor.setPlainText(f.read())

    def import_code(self):
        """Import code and create model"""
        from hsim.gui.utils.code_parser import CodeParser

        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "Empty Code", "Please enter Python code to import")
            return

        parser = CodeParser()
        model = parser.parse_code(code)

        if len(model.blocks) == 0:
            QMessageBox.warning(self, "No Blocks Found",
                              "Could not find any simulation blocks in the code")
            return

        self.code_imported.emit(model)
        self.accept()
```

---

## Feature 4: Export GUI to Code (ENHANCED)

**Goal**: Generate complete, runnable Python code with custom methods

### Enhancements to CodeGenerator

#### 4.1 Export Custom Methods
```python
def _generate_block_code(self, block, indent: int = 1) -> list[str]:
    lines = []
    indent_str = "    " * indent

    # ... existing block creation code ...

    # Add custom methods if any
    if hasattr(block, 'custom_methods') and block.custom_methods:
        var_name = self._sanitize_name(block.name)
        for method_name, method_code in block.custom_methods.items():
            lines.append(f"{indent_str}# Custom method: {method_name}")
            lines.append(f"{indent_str}def {var_name}_{method_name}(self):")
            for code_line in method_code.split('\n'):
                lines.append(f"{indent_str}    {code_line}")
            lines.append(f"{indent_str}{var_name}.{method_name} = {var_name}_{method_name}.__get__({var_name})")

    return lines
```

#### 4.2 Export FSM Actions (Not Comments)
```python
def _generate_fsm_classes(self) -> list[str]:
    # ... existing code ...

    # Instead of comments for on_enter/on_exit, generate actual methods
    if state.on_enter:
        lines.append(f"        def on_enter_{state_var}(agent):")
        for enter_line in state.on_enter.split('\n'):
            if enter_line.strip():
                lines.append(f"            {enter_line}")
        lines.append(f"        {state_var}.on_enter = on_enter_{state_var}")
```

---

## UI/UX Design

### Menu Integration

**File → Import Python Code...**
- Opens ImportCodeDialog
- Parses code and creates blocks
- Shows success message with block count

**File → Export Python Code**
- Enhanced to include custom methods
- Validation before export
- Save to .py file

### Properties Panel Tabs

```
┌─────────────────────────────────────────┐
│ Properties | Methods | FSM | Connections│
├─────────────────────────────────────────┤
│                                         │
│  [Methods Tab Selected]                 │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ Base Methods                       │ │
│  │  ├─ activate_fsm()                │ │
│  │  ├─ process(entity)               │ │
│  │  └─ update_state()                │ │
│  │ Custom Methods                     │ │
│  │  ├─ custom_logic()                │ │
│  │  └─ + Add Method                  │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Method: process(entity)                │
│  ┌───────────────────────────────────┐ │
│  │ def process(self, entity):        │ │
│  │     self.queue.put(entity)        │ │
│  │     self.trigger_event()          │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [💾 Save] [↶ Revert] [+ Add Method]  │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase A: Show Methods (3-4 hours)
1. Create MethodIntrospector class ✅
2. Create MethodsPanel widget ✅
3. Integrate with PropertiesPanel ✅
4. Test with existing blocks ✅

### Phase B: Edit Methods (4-5 hours)
1. Create CodeEditorWidget with syntax highlighting ✅
2. Add CodeValidator for Python syntax ✅
3. Wire up save/revert functionality ✅
4. Store custom methods in Block model ✅
5. Test method editing workflow ✅

### Phase C: Import Code (6-8 hours)
1. Create CodeParser with AST parsing ✅
2. Handle block creation from code ✅
3. Handle connection parsing ✅
4. Create ImportCodeDialog ✅
5. Test with various Python files ✅
6. Handle edge cases (errors, incomplete code) ✅

### Phase D: Enhanced Export (3-4 hours)
1. Modify CodeGenerator for custom methods ✅
2. Export FSM actions as code (not comments) ✅
3. Add validation before export ✅
4. Test round-trip (import → export) ✅

### Phase E: Testing & Polish (4-5 hours)
1. End-to-end testing of all features ✅
2. Bug fixes ✅
3. Documentation updates ✅
4. Example workflows ✅

---

## Total Estimated Effort

**20-26 hours** for complete bidirectional code-GUI sync

---

## Testing Strategy

### Unit Tests
- MethodIntrospector with various block types
- CodeValidator with valid/invalid Python
- CodeParser with sample simulation code
- CodeGenerator with custom methods

### Integration Tests
- Import code → Edit in GUI → Export → Compare
- Create model → Export → Import → Verify equivalence
- Edit methods → Save → Export → Run Python code

### Manual Tests
1. Import existing GSOM simulation
2. Modify methods in GUI
3. Export and run simulation
4. Verify results match original

---

## Success Criteria

- ✅ Can introspect and display all block methods
- ✅ Can edit method code with syntax highlighting
- ✅ Can import Python simulation files
- ✅ Can export complete runnable Python code
- ✅ Round-trip works: Import → Edit → Export → Run
- ✅ Custom methods persist in .hsim files
- ✅ Validation catches errors before save/export

---

## Future Enhancements

1. **Visual Debugging**
   - Breakpoints in visual model
   - Step through FSM states
   - Watch variables

2. **Code Completion**
   - Autocomplete for hsim classes
   - Method suggestions
   - Parameter hints

3. **Git Integration**
   - Version control for models
   - Diff view for changes
   - Collaborative editing

4. **Live Reload**
   - Auto-reload when .py file changes
   - Sync model with code edits in external editor

---

## Next Steps

**Immediate**: Start with Phase A (Show Methods)
1. Create MethodIntrospector
2. Create MethodsPanel
3. Test with simple blocks

**This Session**: Complete Phase A + B
**Next Session**: Phase C + D
**Following Session**: Phase E (Testing & Polish)
