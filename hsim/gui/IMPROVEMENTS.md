# GUI Improvements Implementation Guide

## Issues to Address

### 1. Professional Component Palette ✓
- **Status**: New palette created in `palette_widget_new.py`
- **Features**:
  - Grid layout with visual block previews
  - Professional styling with gradients
  - 2-column layout
  - Count badges on categories
  - Hover effects

### 2. Connection Creation
**Current Issue**: Cannot create connections between blocks

**Solution**: Add connection mode to canvas
```python
# In canvas_widget.py, add:
def start_connection_mode(self, from_block_id):
    """Start connection creation mode"""
    self.connection_mode = True
    self.connection_from = from_block_id
    self.setCursor(Qt.CursorShape.CrossCursor)
    # Show visual feedback

def complete_connection(self, to_block_id):
    """Complete connection creation"""
    if self.connection_mode and self.connection_from:
        conn = Connection(
            id=str(uuid.uuid4()),
            from_block=self.connection_from,
            to_block=to_block_id
        )
        self.model.add_connection(conn)
        self.add_connection_item(conn)
    self.connection_mode = False
    self.connection_from = None
    self.setCursor(Qt.CursorShape.ArrowCursor)
```

**Add to block_item.py context menu**:
```python
create_connection_action = menu.addAction("Create Connection")
create_connection_action.triggered.connect(
    lambda: self.signals.connection_requested.emit(self.block.id)
)
```

### 3. Properties Panel Selection
**Current Issue**: Properties panel doesn't show selected block

**Solution**: Connect scene selection to properties panel
```python
# In canvas_widget.py:
def mousePressEvent(self, event):
    super().mousePressEvent(event)

    # Update selected block
    selected_items = self.scene.selectedItems()
    if selected_items:
        item = selected_items[0]
        if isinstance(item, BlockItem):
            self.selection_changed.emit(item.block)
    else:
        self.selection_changed.emit(None)
```

### 4. FSM Editor Components
**Needed**: State and Transition graphics items

**Files to create**:
- `hsim/gui/items/state_item.py`
- `hsim/gui/items/transition_item.py`

**State Item Features**:
- Resizable rectangles
- Hierarchical (can contain other states)
- Color coding
- Double-click to edit
- Entry/exit actions

**Transition Item Features**:
- Arrow from state to state
- Labels (event/condition)
- Curved paths
- Control points

### 5. Code Properties
**Needed**: Code editor widgets for:
- `on_enter` (state entry code)
- `on_exit` (state exit code)
- `on_transition` (transition action code)
- Custom code blocks

**Solution**: Use QTextEdit with syntax highlighting
```python
from PyQt6.Qsci import QsciScintilla, QsciLexerPython

class CodeEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set Python lexer for syntax highlighting
        lexer = QsciLexerPython(self)
        self.setLexer(lexer)

        # Set font
        font = QFont("Consolas", 10)
        self.setFont(font)

        # Line numbers
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")

        # Auto-indent
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
```

### 6. Agent-Based Architecture
**Current**: Blocks and Agents treated separately
**Needed**: All blocks ARE agents

**Conceptual Changes**:
1. Rename "DES Blocks" → "Pre-configured Agents"
2. All blocks inherit from Agent base class
3. Generator, Server, etc. are specialized agents with FSMs
4. User can create custom agents by defining FSM

**Model Changes**:
```python
# In block_definitions.py:
class AgentType(Enum):
    GENERATOR_AGENT = "generator"  # Pre-configured agent
    SERVER_AGENT = "server"
    BUFFER_AGENT = "buffer"
    CUSTOM_AGENT = "agent"  # User-defined FSM
```

## Implementation Priority

### Phase 1: Connection Creation (High Priority) ✓
1. Update BlockItem to emit connection_requested signal
2. Add connection mode to CanvasWidget
3. Add visual feedback during connection creation
4. Test drag-to-connect workflow

### Phase 2: Properties Panel Fix (High Priority)
1. Connect scene selection to properties panel
2. Update properties panel when selection changes
3. Add code editor widgets for FSM states/transitions

###Phase 3: Professional Palette (Medium Priority) ✓
1. Replace old palette with new professional version
2. Test drag-drop with new palette
3. Update styling

### Phase 4: FSM Editor Completion (Medium Priority)
1. Create StateItem graphics class
2. Create TransitionItem graphics class
3. Update FSM editor to use new items
4. Add state/transition editing

### Phase 5: Agent Architecture (Low Priority)
1. Refactor conceptual model (all blocks are agents)
2. Update documentation
3. Update UI labels and categories

## Quick Fixes for Immediate Use

### Fix 1: Enable Connection Creation
Add this to `block_item.py` context menu (line ~145):
```python
# After "Edit Properties"
menu.addSeparator()
create_conn_action = menu.addAction("➡️ Create Connection")
create_conn_action.triggered.connect(
    lambda: self.signals.connection_requested.emit(self.block.id)
)
```

Add signal to BlockItemSignals:
```python
connection_requested = pyqtSignal(str)  # block_id
```

### Fix 2: Show Properties on Selection
In `canvas_widget.py`, update `mousePressEvent`:
```python
def mousePressEvent(self, event):
    if event.button() == Qt.MouseButton.LeftButton and self.create_mode:
        # ... existing code ...
    else:
        super().mousePressEvent(event)
        # Emit selection after click
        QTimer.singleShot(0, self.emit_selection)

def emit_selection(self):
    selected_items = self.scene.selectedItems()
    if selected_items and isinstance(selected_items[0], BlockItem):
        self.selection_changed.emit(selected_items[0].block)
    else:
        self.selection_changed.emit(None)
```

### Fix 3: Use New Palette
In `main_window.py`, replace import:
```python
from hsim.gui.views.palette_widget_new import PaletteWidget
```

## Testing Checklist

After implementing fixes:
- [ ] Can drag blocks from palette to canvas
- [ ] Can right-click block and select "Create Connection"
- [ ] Can click target block to complete connection
- [ ] Connection arrow appears between blocks
- [ ] Selecting block shows properties in right panel
- [ ] Properties panel updates when changing selection
- [ ] Can edit block properties (service time, etc.)
- [ ] Can double-click Server to open FSM editor
- [ ] Can save and load models with connections

## Files to Modify

1. `hsim/gui/views/canvas_widget.py` - Add connection mode
2. `hsim/gui/items/block_item.py` - Add connection signal
3. `hsim/gui/views/main_window.py` - Use new palette
4. `hsim/gui/views/properties_panel.py` - Add code editors

## Files to Create

1. `hsim/gui/items/state_item.py` - FSM state graphics
2. `hsim/gui/items/transition_item.py` - FSM transition graphics
3. `hsim/gui/widgets/code_editor.py` - Syntax-highlighted code editor
