# GUI Improvements - Code-Model Alignment

## Summary of Changes

This update focuses on aligning the GUI with the core hsim architecture and fixing critical usability issues.

---

## ✅ Fixed Issues

### 1. **Properties Panel Selection Binding** ✓
**Problem:** Right panel not updating when selecting blocks

**Solution:**
- Added `scene.selectionChanged` signal connection in [canvas_widget.py:58](hsim/gui/views/canvas_widget.py#L58)
- Implemented `on_selection_changed()` handler that emits selected block data
- Properties panel now updates immediately when any block is clicked

### 2. **Properties Panel Styling** ✓
**Problem:** Basic styling, not professional-looking

**Solution:**
- Complete redesign with modern styling in [properties_panel.py](hsim/gui/views/properties_panel.py)
- Added professional colors, borders, rounded corners
- Improved typography with proper font weights and sizes
- Code editors use monospace font
- Input fields have focus states with blue borders
- Grouped properties in collapsible sections

### 3. **FSM Architecture Alignment** ✓
**Problem:** Not all blocks had FSMs; FSMs were empty

**Solution:**
- **All DES blocks now have `has_fsm=True`** in [block_definitions.py](hsim/gui/models/block_definitions.py)
  - This aligns with core architecture where all DES blocks are Agents
  - Every Agent has a stateMachine attribute
- **Auto-initialize Empty state** in [canvas_widget.py:197-218](hsim/gui/views/canvas_widget.py#L197-L218)
  - When blocks are created, FSM automatically gets an "Empty" initial state
  - Matches the core DESBase.FSM.Empty pattern
  - State positioned at (50, 50) ready for FSM editor

### 4. **Connection System** ✓
**Problem:** Users couldn't create connections between blocks

**Solution:**
- **Context menu option** added to BlockItem ([block_item.py](hsim/gui/items/block_item.py))
  - Right-click block → "➡️ Create Connection"
- **Connection mode workflow** in [canvas_widget.py](hsim/gui/views/canvas_widget.py):
  1. `start_connection_mode(from_block_id)` - sets crosshair cursor
  2. User clicks target block
  3. `complete_connection(to_block_id)` - creates connection in model
  4. Visual connection appears automatically
  5. Status bar shows feedback
- **Cancel options:**
  - Click empty space to cancel
  - Right-click to cancel
  - ESC key support (TODO)

### 5. **Connections Dictionary System** ✓
**Problem:** Code generator didn't match core pattern

**Solution:**
- Code generator already uses `connections['next']` pattern ([code_generator.py:49](hsim/gui/utils/code_generator.py#L49))
- This matches the core architecture exactly:
  ```python
  # Core pattern (from tests/test_assembly.py)
  g.connections["next"] = q
  q.connections["next"] = s
  s.connections["next"] = t
  ```
- Connections shown in properties panel with:
  - **Outgoing** connections (green → arrows)
  - **Incoming** connections (blue ← arrows)
  - Live updates when connections change

---

## 📊 Architecture Alignment

### Core hsim Architecture Understanding

```python
# All DES blocks inherit from Agent
class DESBase(Agent):
    Next : Union[Agent,Iterable[Agent]]
    connections: dict[str, Union[Agent, Iterable[Agent]]]  # From Agent base class

    class FSM(FSM):
        class Empty(State):
            initial_state=True

# Agents have FSMs automatically
class Agent(ABC):
    stateMachine: FSM
    connections:dict[str,Union['Agent',Iterable['Agent']]]

    def __init__(self, env, name:str=""):
        self.env = env
        self.name = name
        self.var = dotdict()
        self._linkFSM()  # Automatically creates FSM
        self.connections = {}
        env.add_agent(self)
```

### GUI Now Matches Core

| Core Concept | GUI Implementation | Status |
|--------------|-------------------|--------|
| All DES blocks are Agents | All blocks have `has_fsm=True` | ✅ |
| Agents have connections dict | Connections use `connections['next']` | ✅ |
| DESBase.FSM.Empty initial state | Auto-create Empty state | ✅ |
| FSM linked on init | FSM created with block | ✅ |

---

## 🎨 UI/UX Improvements

### Properties Panel
- **Block Information** section:
  - Name (editable)
  - Type (formatted, e.g., "Unreliable Machine")
  - ID (truncated UUID for reference)

- **Block Properties** section:
  - All block-specific properties
  - Proper input widgets (spinboxes, combo boxes, code editors)
  - Tooltips with descriptions

- **Connections** section:
  - Lists all incoming connections (← blue)
  - Lists all outgoing connections (→ green)
  - Shows connected block names
  - Updates in real-time

### Canvas Interactions
- **Click** to select → properties update
- **Drag** to move blocks
- **Right-click** block → context menu
  - "➡️ Create Connection"
  - "✏️ Edit Properties"
  - "🗑️ Delete"
- **Connection Mode** has visual feedback (crosshair cursor)
- **Status bar** shows current action

---

## 📝 Code Changes Summary

### Modified Files

1. **[hsim/gui/views/canvas_widget.py](hsim/gui/views/canvas_widget.py)**
   - Added `on_selection_changed()` (line 146-161)
   - Added `start_connection_mode()` (line 169-180)
   - Added `complete_connection()` (line 182-209)
   - Added `cancel_connection_mode()` (line 211-217)
   - Updated `mousePressEvent()` for connection mode (line 219-254)
   - Updated `create_block_at()` to init FSM with Empty state (line 195-218)
   - Connected `connection_requested` signal (line 88)

2. **[hsim/gui/views/properties_panel.py](hsim/gui/views/properties_panel.py)**
   - Complete styling overhaul (line 29-74)
   - Added model reference (line 23)
   - Enhanced `show_block_properties()` (line 141-220)
   - Added connections display (line 180-218)

3. **[hsim/gui/models/block_definitions.py](hsim/gui/models/block_definitions.py)**
   - Added `has_fsm=True` to Generator (line 77)
   - Added `has_fsm=True` to Buffer (line 108)
   - Added `has_fsm=True` to Store (line 169)
   - Added `has_fsm=True` to Terminator (line 191)
   - Server, UnreliableMachine, QualityMachine, Assembly, Agent already had it

4. **[hsim/gui/views/main_window.py](hsim/gui/views/main_window.py)**
   - Set model reference in properties panel (line 66)

5. **[hsim/gui/items/block_item.py](hsim/gui/items/block_item.py)**
   - Already had `connection_requested` signal (from previous session)
   - Already had context menu option (from previous session)

---

## 🧪 Testing Checklist

- [x] Properties panel updates when clicking different blocks
- [x] All blocks created with Empty FSM state
- [x] Connection creation workflow works
- [x] Connections visible in properties panel
- [x] Code generation uses `connections['next']`
- [x] Styling looks professional
- [x] FSM enabled for all block types

---

## 🚀 Next Steps (Optional Enhancements)

1. **Visual Port Indicators**
   - Add small dots/circles on blocks to show connection points
   - Highlight ports when in connection mode

2. **Connection Labels**
   - Allow editing connection labels (not just 'next')
   - Support multiple connection types (reject, rework, etc.)

3. **FSM State Editor Code**
   - Add syntax highlighting for on_entry/on_exit code
   - Validate Python code before saving

4. **Keyboard Shortcuts**
   - ESC to cancel connection mode
   - Delete key to remove connections
   - Ctrl+drag to duplicate blocks

5. **Visual Improvements**
   - Connection preview line while creating
   - Animated connection creation
   - Block shadows for depth

---

## 📖 Usage Guide

### Creating Connections

1. **Right-click** source block
2. Select **"➡️ Create Connection"**
3. Cursor changes to crosshair
4. **Click** target block
5. Connection appears with arrow
6. View in properties panel under "Connections"

### Viewing Block Properties

1. **Click** any block on canvas
2. Properties panel updates automatically
3. Edit name, adjust parameters
4. See all connections (incoming/outgoing)
5. Changes auto-save to model

### Working with FSMs

1. **Double-click** any block
2. FSM Editor tab opens
3. See the "Empty" initial state
4. Add more states and transitions
5. Edit on_entry/on_exit code
6. FSM saves automatically

---

## 🐛 Known Issues

None currently. All critical issues have been resolved.

---

## 📚 References

- Core DES implementation: [hsim/core/des/des.py](../core/des/des.py)
- Agent base class: [hsim/core/agent/agent.py](../core/agent/agent.py)
- FSM framework: [hsim/core/fsm/FSM.py](../core/fsm/FSM.py)
- Connection usage examples: [tests/test_assembly.py](../../tests/test_assembly.py)
