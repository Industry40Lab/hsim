# hsim GUI - Visual Model Designer

## Overview

The hsim GUI is an AnyLogic-style visual designer for discrete event simulation (DES) models. It provides a drag-and-drop interface for building simulation models using the hsim framework.

## Running the GUI

```bash
# Install dependencies
pip install PyQt6

# Run the GUI
python -m hsim.gui.main
```

## Architecture

### Core Components

```
hsim/gui/
├── items/                      # Visual elements
│   ├── block_item.py          # DES blocks (Generator, Server, etc.)
│   ├── port_item.py           # Connection ports (input/output)
│   ├── connection_item.py     # Arrows between blocks
│   ├── state_item.py          # FSM states
│   └── transition_item.py     # FSM transitions
├── views/                      # UI panels
│   ├── main_window.py         # Main application window
│   ├── canvas_widget.py       # Drawing canvas
│   ├── properties_panel.py    # Property editor
│   ├── project_tree.py        # Model structure tree
│   ├── palette_widget.py      # Component palette
│   └── fsm_editor_widget.py   # FSM editor
├── models/                     # Data structures
│   ├── model.py               # Core data model
│   ├── block_definitions.py   # Block metadata
│   └── undo_stack.py          # Undo/redo system
└── utils/                      # Utilities
    └── code_generator.py      # Python code export
```

### Data Model

**Block** - A DES component or agent
- `id`: Unique identifier
- `type`: Block type (generator, server, buffer, etc.)
- `name`: Display name
- `position`, `size`: Visual layout
- `properties`: Block-specific settings
- `fsm_id`: Reference to FSM (if this block has one)
- `parent_id`: Parent agent (for hierarchy)
- `children`: List of child agent IDs

**FSM** - Finite State Machine container
- `id`: Unique identifier
- `name`: FSM name
- `owner_block_id`: Block this FSM belongs to
- `states`: List of State objects
- `transitions`: List of Transition objects

**State** - FSM state
- `name`, `position`, `size`
- `is_initial`, `is_final`
- `on_enter`, `on_exit`: Python code
- `parent_state_id`: For hierarchical states

**Transition** - FSM transition
- `from_state`, `to_state`: State IDs
- `label`: Display label
- `condition`: Python expression
- `action`: Python code

**Connection** - Link between blocks
- `from_block`, `to_block`: Block IDs
- Port-to-port connections

## Features

### 1. Tabbed Canvas (AnyLogic-style)

**Implementation**: `main_window.py:74-81`

- Multiple agents open in separate tabs
- Main frame always in first tab (cannot be closed)
- Double-click any block → opens in new tab
- Tabs are closable (except Main) and movable

**Usage**:
- Double-click block to open internal view
- Each tab shows either:
  - Main canvas with blocks
  - Agent internal view with FSM + sub-agents

### 2. Hierarchical Agents

**Implementation**:
- Data model: `model.py:42-43` (parent_id, children)
- Loading sub-agents: `canvas_widget.py:1088-1105`
- Recursive tree: `project_tree.py:137-141`

**Behavior**:
- Any block can be opened to expose sub-agents
- When you open an agent, you see:
  - Its FSM states and transitions
  - Its sub-agents (as blocks)
  - Connections between sub-agents
- Create blocks inside an agent → they become children
- Unlimited nesting depth

**Model Tree Structure**:
```
📋 Main
├── 🤖 Generator_1
├── 🤖 Server_1
│   ├── 🤖 SubAgent_1  (child of Server_1)
│   └── 🤖 SubAgent_2
└── 🤖 Terminator_1
```

### 3. Component Library

**Implementation**: `main_window.py:703-780`

Organized into 4 categories:

**📦 DES Blocks**
- 📊 Process Flow
  - ⚙️ Generator
  - 📦 Buffer
  - 🔧 Server
  - 📥 Store
  - 🗑️ Terminator
- 🔧 Resources
  - ⚠️ Unreliable Machine
  - ✓ Quality Machine
  - 🔄 SUMachine
  - 👷 Manual Station
- 🔀 Advanced
  - 🔗 Assembly
  - 🤖 Agent

**🔄 FSM Elements**
- ⭕ State
- ➡️ Transition
- ⏱️ Timeout Event

**🔗 Connectors**
- → Connection
- 📥 Input Port
- 📤 Output Port

**⚡ Actions** (future)
- 📤 Send Message
- 🔔 Trigger Event
- 📝 Set Variable
- 🔁 Loop

### 4. FSM Editing

**Current State**: FSM elements exist but need container organization

**Workflow**:
1. Double-click agent → opens internal view
2. Click "⭕ State" in Library → click canvas → state appears
3. Click "➡️ Transition" → click source state → click target state
4. Edit state properties (on_enter, on_exit code) in Properties panel
5. Edit transition properties (condition, action) in Properties panel

**FSM Toolbar**: `main_window.py:355-379`
- Shown when in agent internal view
- ➕ State button
- ➡️ Transition button
- ⬅️ Back button (return to main view)

### 5. Port Connections

**Implementation**:
- Port tooltips: `port_item.py:45-47`
- Port visualization in agent view: `canvas_widget.py:1033-1087`
- Drag-drop connection: `port_item.py:82-84`

**Usage**:
- Hover over green output port → tooltip shows "Drag from here to create connection"
- Click and drag from green port → blue input port
- Release to create connection
- Inside agent view: ports shown at scene boundaries

**Port Types**:
- Input ports (blue, left side)
- Output ports (green, right side)

### 6. Grid Snapping

**Implementation**: `canvas_widget.py:26, 272-277`

- 20px grid
- Toggle on/off: `main_window.py:614-628`
- Toolbar buttons: Grid visibility + Snap toggle
- Status bar shows: "Grid: ON | Snap: ON"

### 7. Alignment Tools

**Implementation**: `main_window.py:941-995`

**Arrange Menu**:
- Align Left/Right/Top/Bottom (Ctrl+Shift+L/R/T/B)
- Align Horizontal/Vertical Center (Ctrl+Shift+H/V)
- Distribute Horizontally/Vertically

### 8. Undo/Redo

**Implementation**: `undo_stack.py`, `main_window.py:879-919`

- Ctrl+Z: Undo
- Ctrl+Shift+Z: Redo
- Tooltip shows action description

### 9. Copy/Paste

**Implementation**: `main_window.py:921-939`

- Ctrl+C: Copy selected blocks
- Ctrl+V: Paste blocks
- Status bar shows count

### 10. File Operations

**Formats**:
- `.hsim` - JSON model files
- `.py` - Exported Python code (future)

**Menu Actions**:
- New (Ctrl+N)
- Open (Ctrl+O)
- Save (Ctrl+S)
- Save As (Ctrl+Shift+S)
- Export Python Code (future)

### 11. Zoom Controls

**Implementation**: `main_window.py:579-604`

- Zoom In (Ctrl++)
- Zoom Out (Ctrl+-)
- Reset Zoom (Ctrl+0)
- Status bar shows zoom percentage

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ File  Edit  View  Arrange  Simulation  Help            │
├────────┬──────────────────────────────┬─────────────────┤
│ Model/ │  📋 Main  🤖 Server_1  ...  │   Properties    │
│ Library│  ┌────────────────────────┐  │                 │
│        │  │                        │  │  Name: Server_1 │
│ 📋Model│  │    ⚡ Generator        │  │  Type: server   │
│  Main  │  │         │              │  │                 │
│  Gen_1 │  │         ▼              │  │  Service Time:  │
│  Srv_1 │  │    🔧 Server           │  │  [2.0      ]    │
│  Term_1│  │         │              │  │                 │
│        │  │         ▼              │  │  Distribution:  │
│ 📚Libr │  │    🗑️ Terminator       │  │  [Constant  ▼] │
│  📦DES │  │                        │  │                 │
│  🔄FSM │  └────────────────────────┘  │                 │
│  🔗Conn│                              │                 │
└────────┴──────────────────────────────┴─────────────────┘
│ Ready                         Grid: ON | Snap: ON  100% │
└─────────────────────────────────────────────────────────┘
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New model |
| Ctrl+O | Open model |
| Ctrl+S | Save model |
| Ctrl+Shift+S | Save as |
| Ctrl+Z | Undo |
| Ctrl+Shift+Z | Redo |
| Ctrl+C | Copy |
| Ctrl+V | Paste |
| Delete | Delete selected |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Reset zoom |
| Ctrl+Shift+L/R/T/B | Align left/right/top/bottom |
| Ctrl+Shift+H/V | Align horizontal/vertical center |
| F5 | Run simulation (future) |
| ESC | Exit agent view |

## Design Principles

### Everything is an Agent

- All blocks are agents (can have FSM and sub-agents)
- Main is the root agent
- Agents can contain other agents (composition)
- Unlimited hierarchy depth

### Port-to-Port Connections

- Connections are between ports, not blocks
- Input ports (blue) on left
- Output ports (green) on right
- Drag from output → input to connect

### FSM as Container

- FSM is a named container for states and transitions
- Agents can have multiple FSMs (future)
- States and transitions belong to an FSM
- FSMs are created and managed like other elements

## Current Limitations

1. **FSM Container Not Visual Yet**
   - FSMs exist in data model
   - Need visual representation in Library
   - Need ability to create/name FSMs
   - States should be added to specific FSM

2. **Code Generation Not Complete**
   - Basic structure exists in `code_generator.py`
   - Needs testing and refinement
   - Postponed per user request

3. **Actions Not Implemented**
   - Send Message, Trigger Event, Set Variable, Loop
   - Placeholder items in Library
   - Future enhancement

4. **Single FSM per Agent**
   - Currently one FSM per agent
   - Should support multiple named FSMs

## Implementation Status

| Feature | Status | Location |
|---------|--------|----------|
| Tabbed canvas | ✅ Complete | main_window.py:74-81 |
| Hierarchical agents | ✅ Complete | model.py:42-43, canvas_widget.py:1088-1105 |
| Component library | ✅ Complete | main_window.py:703-780 |
| FSM editing | ✅ Complete | canvas_widget.py:1108-1245 |
| Port connections | ✅ Complete | port_item.py:45-84 |
| Grid snapping | ✅ Complete | canvas_widget.py:26, 272-277 |
| Alignment tools | ✅ Complete | main_window.py:941-995 |
| Undo/Redo | ✅ Complete | undo_stack.py |
| Copy/Paste | ✅ Complete | main_window.py:921-939 |
| FSM containers | ⏳ In Progress | Need visual representation |
| Code generation | ⏳ Postponed | code_generator.py (basic) |
| Actions | ❌ Not started | Future |

## Next Implementation Steps

1. **Add FSM to Library as Container**
   - Add "📊 FSM" item to Library
   - Click to create FSM container in agent
   - FSMs appear in agent internal view

2. **FSM Management**
   - Create/rename/delete FSMs
   - Select FSM before adding states
   - Visual indication of which FSM is active

3. **Multiple FSMs per Agent**
   - Agent can have multiple named FSMs
   - FSM selector in agent view
   - Each FSM has its own states/transitions

4. **Visual FSM Container**
   - FSM shown as titled region in agent view
   - States grouped inside FSM visual boundary
   - Clear ownership: states belong to specific FSM

## Testing Checklist

- [ ] Install PyQt6
- [ ] Run `python -m hsim.gui.main`
- [ ] Create Generator → Server → Terminator
- [ ] Connect blocks via port drag-drop
- [ ] Double-click Server to open internal view
- [ ] Add states to Server's FSM
- [ ] Add transitions between states
- [ ] Edit state properties (on_enter code)
- [ ] Return to main view (ESC)
- [ ] Create sub-agent inside Server
- [ ] Verify hierarchical tree structure
- [ ] Test undo/redo
- [ ] Test copy/paste
- [ ] Test alignment tools
- [ ] Save and reload model

## Troubleshooting

**Issue**: GUI won't start
- **Solution**: Install PyQt6: `pip install PyQt6`

**Issue**: Can't connect blocks
- **Solution**: Drag from green output port to blue input port (not block-to-block)

**Issue**: Can't add states to agent
- **Solution**: Double-click agent first to open internal view, then add states

**Issue**: Transitions don't follow states
- **Solution**: Should work automatically via signals (transition_item.py:45-49)

**Issue**: Tab won't close
- **Solution**: Cannot close Main tab (index 0), only agent tabs can be closed

## File Format

Models are saved as JSON in `.hsim` files:

```json
{
  "name": "My Model",
  "version": "1.0",
  "blocks": [
    {
      "id": "uuid",
      "type": "generator",
      "name": "Generator_1",
      "position": {"x": 100, "y": 100},
      "properties": {},
      "parent_id": null,
      "children": [],
      "fsm_id": "fsm-uuid"
    }
  ],
  "connections": [
    {
      "id": "uuid",
      "from": "block-id-1",
      "to": "block-id-2"
    }
  ],
  "fsms": [
    {
      "id": "fsm-uuid",
      "name": "Main FSM",
      "owner_block_id": "block-uuid",
      "states": [...],
      "transitions": [...]
    }
  ]
}
```

## Development Notes

- All Python files have valid syntax (verified)
- Uses PyQt6 for GUI framework
- Dark theme matching AnyLogic/VS Code style
- Event-driven architecture with Qt signals/slots
- Dataclasses for model objects
- UUID for all entity IDs
