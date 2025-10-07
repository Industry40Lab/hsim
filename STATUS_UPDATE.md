# Status Update - AnyLogic-Style Implementation

## ✅ Completed Features

### 1. Tabbed Canvas (Q2: Always New Tab)
**Status**: ✅ COMPLETE

**Implementation**:
- Replaced single canvas with `QTabWidget`
- Main frame always in first tab (cannot be closed)
- Double-clicking agent opens in new tab
- If agent already open, switches to existing tab
- Closable tabs (except Main)
- Movable tabs

**Files Modified**:
- [main_window.py](hsim/gui/views/main_window.py#L69-L77) - Tab widget setup
- [main_window.py](hsim/gui/views/main_window.py#L289-L317) - Open in new tab logic
- [main_window.py](hsim/gui/views/main_window.py#L637-L654) - Close tab handler

**Usage**:
- Double-click any agent → opens in new tab
- Click tab to switch views
- X button to close (Main cannot be closed)
- Library applies to currently active tab

---

### 2. Model Tab Cleanup
**Status**: ✅ COMPLETE

**Changes**:
- Removed all agent types (now only in Library)
- Shows only instances in model
- Main frame as root node
- Clean tree structure

**Files Modified**:
- [project_tree.py](hsim/gui/views/project_tree.py#L72-L87) - Simplified structure

---

### 3. Library Reorganization
**Status**: ✅ COMPLETE

**Changes**:
- Moved Ports from FSM Elements to Connectors
- Removed Message Link (doesn't exist)
- Removed Port Event from FSM Elements
- Added Input Port and Output Port under Connectors

**Files Modified**:
- [main_window.py](hsim/gui/views/main_window.py#L549-L563) - Updated categories

**Current Library Structure**:
```
📦 DES Blocks
  📊 Process Flow (Generator, Buffer, Server, Store, Terminator)
  🔧 Resources (Unreliable, Quality, SU, Manual)
  🔀 Advanced (Assembly, Agent)

🔄 FSM Elements
  ⭕ State
  ➡️ Transition
  ⏱️ Timeout Event

🔗 Connectors
  → Connection
  📥 Input Port
  📤 Output Port

⚡ Actions
  📤 Send Message
  🔔 Trigger Event
  📝 Set Variable
  🔁 Loop
```

---

### 4. Hierarchical Agent Model (Partial)
**Status**: 🔄 IN PROGRESS

**Completed**:
- Added `parent_id` and `children` fields to Block model
- Updated serialization (to_dict/from_dict)
- Model supports hierarchy

**Files Modified**:
- [model.py](hsim/gui/models/model.py#L42-L43) - Added hierarchy fields
- [model.py](hsim/gui/models/model.py#L55-L56) - Serialization
- [model.py](hsim/gui/models/model.py#L70-L71) - Deserialization

**Remaining Work**:
- Canvas must show sub-agents as blocks when inside parent
- When you open an agent tab, show its children
- Update Model tree to show hierarchy recursively
- Add "Add Sub-Agent" functionality

---

## 🔧 Remaining Work

### Priority 1: Complete Hierarchical Agents (2-3 hours)

#### A. Show Sub-Agents in Agent View
When opening an agent tab, should show:
- Agent's FSM states (already works)
- Agent's sub-agents as blocks (NEW)
- Connections between sub-agents (NEW)
- Ports at boundaries (already works)

**Implementation Needed**:
```python
# canvas_widget.py
def enter_agent_view(self, block_id):
    ...
    # Load FSM
    self._load_fsm_graphics()

    # Load sub-agents as blocks (NEW)
    self._load_sub_agents(block)

    # Load ports
    self._load_agent_ports(block)

def _load_sub_agents(self, parent_block):
    """Show sub-agents as blocks inside parent"""
    for child_id in parent_block.children:
        child_block = self.model.get_block_by_id(child_id)
        if child_block:
            # Create block item in this scene
            self.add_block_item(child_block)
```

#### B. Create Sub-Agents
When inside an agent, clicking Library items should create sub-agents

**Implementation Needed**:
```python
# canvas_widget.py
def create_block_at(self, block_type, x, y):
    ...
    # Determine parent
    if self.current_mode == "agent_internal":
        parent_id = self.current_agent_id
    else:
        parent_id = "main"  # Top level

    block.parent_id = parent_id

    # Add to parent's children list
    if parent_id != "main":
        parent = self.model.get_block_by_id(parent_id)
        if parent:
            parent.children.append(block.id)
```

#### C. Hierarchical Model Tree
Show tree structure recursively

**Implementation Needed**:
```python
# project_tree.py
def refresh_instances(self):
    self.main_node.takeChildren()

    # Show only top-level agents (parent_id == None)
    for block in self.model.blocks.values():
        if block.parent_id is None:
            self._add_block_tree_item(self.main_node, block)

def _add_block_tree_item(self, parent_node, block):
    """Recursively add block and its children"""
    item = QTreeWidgetItem(parent_node, [f"  {block.name} ({block.type})"])
    item.setData(0, Qt.ItemDataRole.UserRole, {
        'type': 'agent_instance',
        'id': block.id,
        'block': block
    })

    # Add children recursively
    for child_id in block.children:
        child = self.model.get_block_by_id(child_id)
        if child:
            self._add_block_tree_item(item, child)
```

---

### Priority 2: Enable FSM/Connector Creation (1-2 hours)

**Goal**: Click State/Transition/Port in Library → place in frame

**Current Status**: Only DES blocks can be placed

**Implementation Needed**:
```python
# main_window.py _on_library_item_clicked()
element_mapping = {
    # DES Blocks (already works)
    "⚙️ Generator": "generator",
    ...
    # FSM Elements (NEW)
    "⭕ State": "state",
    "➡️ Transition": "transition",
    # Connectors (NEW)
    "📥 Input Port": "input_port",
    "📤 Output Port": "output_port",
}

# canvas_widget.py mousePressEvent()
if self.create_mode == "state":
    self._create_state_at(x, y)
elif self.create_mode == "transition":
    # Enter transition mode - select 2 states
    self._start_transition_creation()
elif self.create_mode == "input_port":
    self._create_port_at(x, y, "input")
```

---

## Testing Checklist

### ✅ Already Testable
- [ ] Open agent in new tab (double-click)
- [ ] Switch between tabs
- [ ] Close tab (not Main)
- [ ] Library applies to active tab
- [ ] Model tab shows only instances
- [ ] Library has correct categories

### 🔄 Will Be Testable After Hierarchical Agents
- [ ] Open agent → see sub-agents as blocks
- [ ] Create sub-agent inside agent
- [ ] Model tree shows hierarchy
- [ ] Navigate nested agents

### 🔜 Will Be Testable After FSM Creation
- [ ] Click State → place in frame
- [ ] Click Transition → connect states
- [ ] Click Port → add to agent boundary

---

## Summary

**Working Now**:
1. ✅ Tabbed canvas (AnyLogic style)
2. ✅ Model tab (only instances)
3. ✅ Library reorganized
4. ✅ Port tooltips and visibility

**Almost Done** (model ready, needs UI):
5. 🔄 Hierarchical agents (model supports it, need canvas/tree updates)

**TODO**:
6. 🔜 FSM element creation from Library
7. 🔜 Connector creation from Library

**Estimated Time**:
- Complete hierarchical agents: 2-3 hours
- Enable FSM/connector creation: 1-2 hours
- **Total**: 3-5 hours remaining

---

## Next Steps

Please confirm priority:
1. Should I complete hierarchical agents first (show sub-agents, tree structure)?
2. Or enable FSM element creation first (state/transition placement)?
3. Or both in parallel?

Once confirmed, I'll proceed with implementation.
