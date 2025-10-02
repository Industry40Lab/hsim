# hsim Model Designer - GUI Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ hsim - Model Designer                                                    [_][□][X]  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ File  Edit  View  Simulation  Help                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ [New] [Open] [Save] │ [Run] │ [Zoom+] [Zoom-]                                      │
├────────────┬──────────────────────────────────────────────────────────┬─────────────┤
│            │                                                            │             │
│ Component  │                    Model Canvas                          │ Properties  │
│  Palette   │                                                            │    Panel    │
│            │                                                            │             │
│ ┌────────┐ │  ┌──────────────────────────────────────────────────┐   │ ┌─────────┐ │
│ │DES Blocks│ │  │                                                 │   │ │ Block   │ │
│ ├────────┤ │  │     ⚡                                            │   │ │ Info    │ │
│ │⚡Gen   │ │  │  Generator 1                                      │   │ ├─────────┤ │
│ │📦Buffer│ │  │         │                                         │   │ │Name:    │ │
│ │⚙️Server│ │  │         │                                         │   │ │Server 1 │ │
│ │📫Store │ │  │         ▼                                         │   │ │         │ │
│ │🛑Term  │ │  │     ⚙️                                            │   │ │Type:    │ │
│ └────────┘ │  │  Server 1                                         │   │ │server   │ │
│            │  │         │                                         │   │ └─────────┘ │
│ ┌────────┐ │  │         │                                         │   │             │
│ │Resources│ │  │         ▼                                         │   │ ┌─────────┐ │
│ ├────────┤ │  │     🛑                                            │   │ │Properties│
│ │🔧Unreli│ │  │  Terminator 1                                     │   │ ├─────────┤ │
│ │✓Quality│ │  │                                                 │   │ │Service  │ │
│ └────────┘ │  │                                                 │   │ │Time: 2.0│ │
│            │  │                                                 │   │ │         │ │
│ ┌────────┐ │  │                                                 │   │ │Distrib: │ │
│ │Advanced│ │  │                                                 │   │ │[Const▼]│ │
│ ├────────┤ │  │                                                 │   │ │         │ │
│ │🔗Assemb│ │  │                                                 │   │ │         │ │
│ └────────┘ │  │                                                 │   │ └─────────┘ │
│            │  │                                                 │   │             │
│ ┌────────┐ │  │                                                 │   │             │
│ │ Agents │ │  │                                                 │   │             │
│ ├────────┤ │  │                                                 │   │             │
│ │🤖Custom│ │  └──────────────────────────────────────────────────┘   │             │
│ └────────┘ │                                                            │             │
│            │  [Model Canvas]  [FSM Editor]                             │             │
│            │                                                            │             │
│  Drag      │                                                            │             │
│  blocks    │                                                            │             │
│  onto      │                                                            │             │
│  canvas    │                                                            │             │
├────────────┴──────────────────────────────────────────────────────────┴─────────────┤
│ Ready                                                  3 blocks, 2 connections       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Key UI Elements

### Left Panel - Component Palette (200-300px)
- **Title bar**: "Component Palette"
- **Collapsible sections**:
  - DES Blocks (Generator, Buffer, Server, Store, Terminator)
  - Resources (Unreliable Machine, Quality Machine)
  - Advanced (Assembly)
  - Agents (Custom Agent)
- **Each item**:
  - Color-coded button
  - Icon + name
  - Draggable to canvas
- **Info text**: "Drag blocks onto canvas"

### Center Panel - Tabbed View (Expandable)
#### Tab 1: Model Canvas
- **Grid background** (toggleable)
- **Zoom controls** (mouse wheel, buttons)
- **Pan support** (middle-mouse drag)
- **Visual blocks**:
  - Shapes: circles (Gen/Term), rectangles (others)
  - Colors: per block type
  - Icons + names
  - Selection highlighting
- **Connections**:
  - Arrows with arrowheads
  - Labels (optional)
  - Selectable
- **Context menus**:
  - Canvas: Add block, Select all
  - Block: Rename, Properties, Create connection, Delete
  - Connection: Edit label, Delete

#### Tab 2: FSM Editor (for blocks with FSM)
- Similar canvas for states/transitions
- Hierarchical state support
- Breadcrumb navigation
- "Back to Model" button

### Right Panel - Properties Panel (250-400px)
- **Title bar**: "Properties"
- **Dynamic content** based on selection:

**When block selected:**
```
┌─────────────────┐
│ Block Information │
├─────────────────┤
│ Name: [Server 1]│
│ Type: server    │
└─────────────────┘

┌─────────────────┐
│ Properties      │
├─────────────────┤
│ Service Time:   │
│ [2.0      ]     │
│                 │
│ Distribution:   │
│ [Constant   ▼]  │
└─────────────────┘
```

**When state selected (FSM editor):**
```
┌─────────────────┐
│ State Information│
├─────────────────┤
│ Name: [Working] │
│ Initial: [✓]    │
│ Final:   [ ]    │
├─────────────────┤
│ On Enter:       │
│ [code editor]   │
│                 │
│ On Exit:        │
│ [code editor]   │
└─────────────────┘
```

**When nothing selected:**
```
┌─────────────────┐
│                 │
│  Select an item │
│  to view        │
│  properties     │
│                 │
└─────────────────┘
```

### Top Menu Bar

**File**
- New (Ctrl+N)
- Open... (Ctrl+O)
- Save (Ctrl+S)
- Save As... (Ctrl+Shift+S)
- ---
- Export Python Code...
- ---
- Exit (Ctrl+Q)

**Edit**
- Undo (Ctrl+Z) [TODO]
- Redo (Ctrl+Y) [TODO]
- ---
- Delete (Del)

**View**
- Zoom In (Ctrl++)
- Zoom Out (Ctrl+-)
- Reset Zoom (Ctrl+0)
- ---
- Show Grid [✓]

**Simulation**
- Run (F5) [TODO]
- Validate Model

**Help**
- About

### Toolbar
```
[New] [Open] [Save] │ [Run] │ [Zoom+] [Zoom-]
```

### Status Bar
```
Ready                                  3 blocks, 2 connections
```

## Interaction Flows

### Creating a Simple Model
1. **Drag Generator** from palette → canvas
2. **Drag Server** from palette → canvas
3. **Drag Terminator** from palette → canvas
4. **Right-click Generator** → "Create Connection" → Click Server
5. **Right-click Server** → "Create Connection" → Click Terminator
6. **Click Generator** → Edit properties in right panel
7. **File** → "Export Python Code"

### Editing Block Properties
1. **Click block** on canvas
2. Properties panel updates automatically
3. **Edit values** in property widgets
4. Changes apply immediately to model

### Opening FSM Editor
1. **Double-click** a Server or Agent with FSM
2. Canvas switches to FSM Editor tab
3. See states and transitions
4. Edit state/transition properties

### Saving/Loading
1. **File** → "Save As..."
2. Choose location, enter filename
3. Saves as `.hsim` file (JSON)
4. **File** → "Open..."
5. Select `.hsim` file
6. Model loads into canvas

## Color Scheme

- **Background**: Light gray (#F9FAFB)
- **Grid**: Light gray (#E5E7EB)
- **Selection**: Blue (#3B82F6)
- **Generator**: Green (#10B981)
- **Buffer**: Blue (#3B82F6)
- **Server**: Amber (#F59E0B)
- **Terminator**: Red (#EF4444)
- **Panel headers**: Dark gray (#1F2937)
- **Connection arrows**: Dark gray (#374151)

## Typography

- **Headers**: Bold, 14px
- **Block names**: Bold, 10px
- **Properties**: Regular, 11px
- **Icons**: 24px (blocks), 16px (palette items)

## Responsive Behavior

- **Panel widths**: Resizable via splitters
- **Canvas**: Expandable, scrollable
- **Zoom**: 50% - 200%
- **Grid**: Fixed 20px spacing
- **Block sizes**: Default 100x80, resizable (TODO)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New model |
| Ctrl+O | Open model |
| Ctrl+S | Save model |
| Ctrl+Shift+S | Save as |
| Delete | Delete selected |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Reset zoom |
| F5 | Run simulation |
| Ctrl+Q | Quit |

## Mouse Actions

| Action | Result |
|--------|--------|
| Left-click | Select item |
| Left-drag | Move block |
| Ctrl+Left-click | Multi-select |
| Right-click | Context menu |
| Double-click | Open FSM / Rename |
| Middle-drag | Pan canvas |
| Wheel | Zoom |
| Drag from palette | Add block |

## Context Menus

### Canvas Context Menu
- Paste (Ctrl+V) [TODO]
- ---
- Select All (Ctrl+A)

### Block Context Menu
- Rename
- Properties
- ---
- Create Connection
- ---
- Delete

### Connection Context Menu
- Edit Label
- ---
- Make Curved [TODO]
- Make Straight [TODO]
- ---
- Delete

## Window States

### Initial State (Empty Model)
- Canvas is empty with grid
- Palette shows all blocks
- Properties panel shows "Select an item..."
- Status bar: "Ready"

### With Model Loaded
- Canvas shows all blocks and connections
- Properties panel reflects selection
- Status bar shows block/connection count
- Tab shows model name

### FSM Editor Open
- Center switches to FSM Editor tab
- Shows states and transitions for selected block
- Breadcrumb: "Model → Server 1 → FSM"
- Properties panel shows state/transition properties
