# New Issues - Implementation Plan

## Issues Identified

1. **Port connections not obvious** - User didn't realize ports can be dragged
2. **Ports not shown in agent internal view** - Should see ports inside agents
3. **"Main" should be an agent** - Everything is agent-based
4. **Left panel needs reorganization** - Split into Model Structure vs Component Library

---

## Issue #1: Port Connection Clarity ✅ (Already Works!)

**Status**: **Feature exists but not discoverable**

### Current Implementation
- Port-to-port dragging IS implemented
- Drag from green output port → blue input port
- Connection automatically creates

### What's Missing
- **Visual feedback during drag**
- **Instructions/hints for users**
- **Hover tooltips on ports**

### Quick Fix
Add visual feedback and instructions:

```python
# port_item.py - Add tooltip
def __init__(self, ...):
    ...
    if port_type == "input":
        self.setToolTip("Input port - Drop connections here")
    else:
        self.setToolTip("Output port - Drag to create connection")
```

### User Instructions
**How to connect blocks:**
1. Hover over the **green output port** (right side of block)
2. Click and **drag** to the **blue input port** (left side of target block)
3. Release to create connection

---

## Issue #2: Ports in Agent Internal View

**Problem**: When viewing agent FSM, ports should be visible as part of agent interface

### Design Decision Needed
**Question**: What should ports look like inside an agent?

**Option A**: Show ports as special states
- Port becomes a state in the FSM
- "Input Port" state, "Output Port" state
- FSM transitions connect to/from port states

**Option B**: Show ports as separate interface layer
- Ports displayed at agent boundaries (top/sides)
- FSM states are internal behavior
- Ports connect to specific states

**Option C**: Hybrid approach
- Ports visible at agent boundary
- Visual indicators showing which states handle port events
- Can connect FSM transitions to port events

### Recommended: Option C

**Implementation**:
1. Show port items at agent view boundaries
2. Add "port event" transition type
3. Connect: `PortInput → State → PortOutput`

```python
# In enter_agent_view(), add ports to FSM scene
def enter_agent_view(self, block_id):
    ...
    # Load FSM
    self._load_fsm_graphics()

    # Add port interface layer
    self._load_agent_ports()

def _load_agent_ports(self):
    """Show ports in agent internal view"""
    if not self.current_agent_id:
        return

    block = self.model.get_block_by_id(self.current_agent_id)
    block_item = self.block_items.get(self.current_agent_id)

    if block_item:
        # Create port visualizations at boundaries
        for port_name, port in block_item.ports.items():
            port_vis = AgentPortVisualization(port_name, port.port_type)
            # Position at scene boundary
            if port.port_type == "input":
                port_vis.setPos(50, scene_height / 2)
            else:
                port_vis.setPos(scene_width - 50, scene_height / 2)

            self.scene.addItem(port_vis)
```

---

## Issue #3: "Main" as an Agent

**Concept**: The top-level canvas ("Main") should itself be modeled as an agent

###  Architecture Change

**Current**:
```
Model
├── Blocks (agents)
└── Connections
```

**Proposed**:
```
Model
└── Main Agent
    ├── Internal FSM
    ├── Sub-agents (what we call "blocks")
    └── Internal connections
```

### Benefits
- **Consistency**: Everything is an agent
- **Composition**: Main can have its own FSM
- **Hierarchy**: Natural parent-child relationships
- **Recursion**: Agents contain agents (fractal structure)

### Implementation

```python
# model.py
class SimulationModel:
    def __init__(self, name="New Model"):
        self.name = name

        # Main is the root agent
        self.main_agent = Block(
            id="main",
            type="agent",
            name="Main",
            position=Position(0, 0),
            size=Size(2000, 2000),
            properties={}
        )

        # Main has its own FSM
        self.main_fsm = FSM(
            id="main-fsm",
            name="Main FSM",
            owner_block_id="main"
        )

        # Blocks are sub-agents of Main
        self.blocks = {}  # These are Main's children
        self.connections = {}  # These are Main's internal connections
```

### Canvas Updates

```python
# canvas_widget.py
def __init__(self):
    ...
    # Start at Main agent level
    self.current_agent_stack = ["main"]  # Stack of agent IDs
    self.enter_agent_view("main")  # Start inside Main

def enter_agent_view(self, block_id):
    """Enter an agent's internal view"""
    if block_id == "main":
        # Show main canvas with all blocks
        self._show_main_view()
    else:
        # Show agent's FSM
        self._show_fsm_view(block_id)
```

---

## Issue #4: Left Panel Reorganization

**Current**: Single tree with mixed agent types and instances

**Proposed**: **Tabs** separating concerns

### New Structure

```
┌─────────────────────────┐
│ [Model] [Library]       │  ← Tabs
├─────────────────────────┤
│ Model Tab:              │
│  📋 Main (root agent)   │
│    ├── Generator_1      │
│    ├── Server_1         │
│    └── Terminator_1     │
│                         │
├─────────────────────────┤
│ Library Tab:            │
│  📦 DES Blocks          │
│    ├── Generator        │
│    ├── Buffer           │
│    └── ...              │
│  🔄 FSM Elements        │
│    ├── State            │
│    ├── Transition       │
│    └── Port Event       │
│  🔗 Connectors          │
│    ├── Connection       │
│    └── Message Link     │
│  ⚡ Actions             │
│    ├── Send Message     │
│    └── Timeout          │
└─────────────────────────┘
```

### Implementation

```python
# main_window.py
def setup_ui(self):
    ...
    # Left panel with tabs
    self.left_tabs = QTabWidget()

    # Tab 1: Model Structure
    self.model_tree = ModelStructureTree(self)
    self.left_tabs.addTab(self.model_tree, "📋 Model")

    # Tab 2: Component Library
    self.component_library = ComponentLibrary(self)
    self.left_tabs.addTab(self.component_library, "📚 Library")

    left_splitter.addWidget(self.left_tabs)
```

### Model Structure Tree

Shows **what exists** in the model:
- Main agent (root)
  - Child agents (blocks)
  - Connections between them
- Each agent expandable to show:
  - FSM states
  - FSM transitions
  - Ports
  - Properties

### Component Library

Shows **what can be added**:
- **DES Blocks**: Generator, Buffer, Server, etc.
- **FSM Elements**: State, Transition, Port Event
- **Connectors**: Connection line, Message link
- **Actions**: Send Message, Set Variable, Timeout

Drag-and-drop from library to canvas.

---

## Implementation Priority

### Phase 1: Quick Wins ✅
1. **Add port tooltips** - 5 minutes
2. **Add instructions to status bar** - 5 minutes
3. **Test existing port drag** - Verify it works

### Phase 2: Port Visibility
4. **Show ports in agent view** - 1 hour
   - Create AgentPortVisualization class
   - Add _load_agent_ports() method
   - Position at scene boundaries

### Phase 3: Left Panel Tabs
5. **Split into Model/Library tabs** - 2 hours
   - Create QTabWidget
   - Separate ModelStructureTree
   - Create ComponentLibrary widget
   - Update all signal connections

### Phase 4: Main as Agent
6. **Refactor Main to be root agent** - 3 hours
   - Update SimulationModel structure
   - Handle "main" specially in canvas
   - Update serialization
   - Migrate existing models

---

## Questions for User

Before implementing, please confirm:

**Q1**: For ports in agent view, do you prefer:
- [ ] Option A: Ports as FSM states
- [ ] Option B: Ports as boundary interface
- [ ] Option C: Hybrid (ports at boundary + state connections)

**Q2**: For "Main as Agent", should:
- [ ] Main have its own FSM (can define main-level behavior)?
- [ ] Main be just a container (no FSM)?

**Q3**: For Component Library, what elements are most important:
- [ ] Just DES blocks
- [ ] DES blocks + FSM elements (states, transitions)
- [ ] Full library (blocks, FSM, connectors, actions)

**Q4**: Should existing models auto-migrate to new structure?
- [ ] Yes, preserve compatibility
- [ ] No, clean break (users re-create models)

**Q5**: Priority order:
1. _____ (most urgent)
2. _____
3. _____
4. _____ (can wait)

---

## Next Steps

Once you provide answers to the questions above, I'll implement in the priority order you specify.

**Current Status**:
- ✅ Port connections work (just need discoverability)
- ⏳ Waiting for design decisions on ports in agent view
- ⏳ Waiting for confirmation on Main-as-Agent approach
- ⏳ Waiting for Component Library requirements
