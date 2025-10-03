# hsim GUI - Clean & Ready

## What Changed

### Files Cleaned Up
- ❌ Removed all `_v2`, `_new`, `_backup` files
- ✅ Kept only final versions (no version numbers in names)
- ✅ Updated all imports to reference clean names

### FSM Tab Removed
- ❌ Removed FSM tab from properties panel (was on right side)
- ✅ FSM editing now in dedicated Agent Editor tab

### Agent Editor Created
- ✅ New `fsm_editor_widget.py` for editing agents
- ✅ Supports multiple disconnected states/FSMs
- ✅ Exposes agent ports
- ✅ Edit on_enter/on_exit code
- ✅ Called "Agent Editor" not "FSM Editor" (correct terminology)

## Current Structure

```
hsim/gui/
├── items/
│   ├── block_item.py          # Icon-based blocks with ports
│   ├── port_item.py           # Connection ports (blue/green)
│   └── connection_item.py     # Arrows
├── views/
│   ├── canvas_widget.py       # Main canvas
│   ├── palette_widget.py      # Simple palette
│   ├── properties_panel.py    # Code editor (2 tabs: Properties, Connections)
│   ├── fsm_editor_widget.py   # Agent editor
│   └── main_window.py         # Main window
└── models/
    ├── model.py               # Data structures
    └── block_definitions.py   # Block metadata
```

## How It Works

1. **Canvas**: Drag-drop blocks, connect ports
2. **Properties**: Edit block properties as code
3. **Agent Editor**: Double-click block → edit states/transitions
4. **Generate**: Export to Python code

All clean, no version numbers!
