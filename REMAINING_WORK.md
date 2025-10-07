# Remaining Work - Major Features

## ✅ Completed Quick Fixes

1. **Model tab cleanup** - Removed agent types (now only in Library)
2. **Library reorganization** - Moved Ports to Connectors, removed Message Link
3. **Port Event removed** - Not an FSM element

## 🔧 Remaining Major Features

### Issue #2: Hierarchical Agent Structure (Tree Structure)

**Current**: Agents are flat - can't contain sub-agents
**Needed**: Agents can contain sub-agents (composition/hierarchy)

#### Requirements
- When you open an agent, you can add:
  - Sub-agents (nested agents)
  - FSM states
  - Connections between sub-agents
  - Ports

#### Implementation Plan

**1. Model Changes** - Support parent-child relationships
```python
# model.py
class Block:
    def __init__(self, ...):
        ...
        self.parent_id = None  # ID of parent agent
        self.children = []  # List of child agent IDs
```

**2. Canvas View Stack** - Track agent hierarchy
```python
# canvas_widget.py
self.agent_stack = [("main", main_scene)]  # Stack of (agent_id, scene)

def enter_agent_view(self, agent_id):
    # Push current view onto stack
    self.agent_stack.append((agent_id, new_scene))
    # Show agent's internal view with:
    # - Sub-agents (as blocks)
    # - FSM states
    # - Connections
```

**3. Model Tree Updates** - Show hierarchy
```python
# Recursive tree building
Main (Frame)
├── Generator_1
├── Server_1
│   ├── SubAgent_1  # Child of Server_1
│   └── SubAgent_2
└── Terminator_1
```

**4. Breadcrumb Navigation**
```
Main > Server_1 > SubAgent_2 > FSM
```

---

### Issue #3: Tabbed Central Canvas

**Current**: Single canvas view, stack-based navigation
**Needed**: Multiple tabs, each showing different agent

#### Requirements
- Open multiple agents simultaneously in tabs
- Tab for each open agent
- Switch between agent views
- Close tabs independently

#### Implementation Plan

**1. Replace Single Canvas with QTabWidget**
```python
# main_window.py
def setup_ui(self):
    ...
    # Center panel - Tabbed canvas
    self.canvas_tabs = QTabWidget()
    self.canvas_tabs.setTabsClosable(True)
    self.canvas_tabs.tabCloseRequested.connect(self._close_agent_tab)

    # Main canvas always in first tab
    self.main_canvas = CanvasWidget(self.model, self)
    self.canvas_tabs.addTab(self.main_canvas, "📋 Main")
```

**2. Open Agent in New Tab**
```python
def open_agent_in_tab(self, agent_id):
    # Check if already open
    for i in range(self.canvas_tabs.count()):
        if self.canvas_tabs.widget(i).current_agent_id == agent_id:
            self.canvas_tabs.setCurrentIndex(i)
            return

    # Create new canvas for this agent
    agent_canvas = CanvasWidget(self.model, self)
    agent_canvas.enter_agent_view(agent_id)

    block = self.model.get_block_by_id(agent_id)
    self.canvas_tabs.addTab(agent_canvas, f"🤖 {block.name}")
    self.canvas_tabs.setCurrentWidget(agent_canvas)
```

**3. Tab Management**
```python
def _close_agent_tab(self, index):
    if index == 0:  # Can't close Main tab
        return
    self.canvas_tabs.removeTab(index)
```

**4. Context Menu "Open in New Tab"**
```python
# project_tree.py - context menu
open_tab_action = menu.addAction("📑 Open in New Tab")
open_tab_action.triggered.connect(
    lambda: self._open_in_tab(agent_id)
)
```

---

### Issue #6: Add FSM Elements and Connectors to Frames

**Current**: Can only add DES blocks to frames
**Needed**: Can add States, Transitions, Ports, Connections

#### Requirements
- Click "⭕ State" in Library → create mode
- Click in frame → place state
- Same for Transitions, Ports, Connections

#### Implementation Plan

**1. Extend Create Mode**
```python
# canvas_widget.py
def set_create_mode(self, element_type: str):
    self.create_mode = element_type
    # element_type can be:
    # - "generator", "server", etc. (blocks)
    # - "state" (FSM state)
    # - "transition" (FSM transition)
    # - "input_port", "output_port" (ports)
    # - "connection" (connection line)
```

**2. Handle Different Element Types**
```python
def mousePressEvent(self, event):
    if self.create_mode == "state":
        self._create_state_at(x, y)
    elif self.create_mode == "transition":
        self._enter_transition_create_mode()
    elif self.create_mode == "input_port":
        self._create_port_at(x, y, "input")
    elif self.create_mode == "output_port":
        self._create_port_at(x, y, "output")
    elif self.create_mode == "connection":
        self._enter_connection_mode()
    else:
        # Existing block creation
        self.create_block_at(self.create_mode, x, y)
```

**3. Update Library Click Handler**
```python
# main_window.py
def _on_library_item_clicked(self, item, column):
    item_text = item.text(0)

    element_mapping = {
        # Blocks
        "⚙️ Generator": "generator",
        ...
        # FSM Elements
        "⭕ State": "state",
        "➡️ Transition": "transition",
        "⏱️ Timeout Event": "timeout",
        # Connectors
        "→ Connection": "connection",
        "📥 Input Port": "input_port",
        "📤 Output Port": "output_port",
    }

    if item_text in element_mapping:
        element_type = element_mapping[item_text]
        self.canvas_tabs.currentWidget().set_create_mode(element_type)
```

**4. Visual Feedback**
```python
# Different cursors for different modes
if create_mode == "state":
    self.setCursor(Qt.CursorShape.PointingHandCursor)
elif create_mode == "transition":
    self.setCursor(Qt.CursorShape.CrossCursor)
elif create_mode == "connection":
    self.setCursor(Qt.CursorShape.CrossCursor)
```

---

## Implementation Priority

### Phase 1: Enable Element Creation (Issue #6) - 2 hours
This is most urgent for usability

1. Extend `set_create_mode()` to handle all element types
2. Add handlers for each element type in `mousePressEvent()`
3. Update Library click handler mapping
4. Test creating states, transitions, ports in frames

### Phase 2: Hierarchical Agents (Issue #2) - 4 hours
Core architectural change

1. Add parent/child relationships to Block model
2. Update canvas to show sub-agents
3. Recursive tree building in Model tab
4. Breadcrumb navigation

### Phase 3: Tabbed Canvas (Issue #3) - 3 hours
UI improvement

1. Replace single canvas with QTabWidget
2. Open agent in new tab functionality
3. Tab management (close, switch)
4. Update all references from `self.canvas` to `self.canvas_tabs.currentWidget()`

---

## Questions Before Implementation

**Q1**: For hierarchical agents - should sub-agents:
- [ ] Have their own separate canvas view (like frames)?
- [ ] Appear as blocks inside parent agent's canvas?
- [ ] Both (blocks in parent, can open to see their internals)?

**Q2**: For tabs - should:
- [ ] Double-click always open in current tab (replace view)?
- [ ] Double-click always open in new tab?
- [ ] Context menu decide ("Open" vs "Open in New Tab")?

**Q3**: For FSM elements in frames - should:
- [ ] States placed in frame become part of frame's FSM?
- [ ] Or are they separate from agent FSMs?
- [ ] Or frames can't have FSMs (just contain agents)?

**Q4**: For connections in frames - should:
- [ ] Connection tool create links between agents?
- [ ] Or between ports specifically?
- [ ] Or both depending on context?

---

## Current Status

✅ **Done**:
- Model tab shows only instances
- Library has correct categories
- Ports moved to Connectors
- Message Link removed

⏳ **In Progress**:
- None currently

🔜 **Next**:
- Waiting for answers to questions above
- Then implement Phase 1 (element creation)

---

## Summary

The main architectural work needed:
1. **Hierarchical agents** - Parent/child relationships
2. **Tabbed canvas** - Multiple open agents
3. **Universal create mode** - Add any element to any frame

Each requires careful design decisions before implementation. Please answer the questions above so I can proceed correctly.
