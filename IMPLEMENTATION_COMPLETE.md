# FSM Container Implementation - Complete

## Summary

Successfully implemented FSM as visual containers in the hsim GUI. This allows agents to have multiple FSMs, each acting as a visual container for states and transitions.

## Changes Made

### 1. Data Model Updates (`model.py`)

**Block class**:
- Changed `fsm_id` (single FSM) to `fsm_ids` (list of FSMs)
- Added backward compatibility property `fsm_id` that returns first FSM
- Updated serialization to handle both old and new formats

**FSM class**:
- Added `position` and `size` fields for visual representation
- FSMs are now visual containers that can be placed on canvas
- Updated serialization with backward compatibility

### 2. New Visual Component (`fsm_item.py`)

Created `FSMItem` class:
- Visual container displayed as dashed rectangle
- Semi-transparent blue background
- Movable and selectable
- Title label showing FSM name
- Context menu for rename/delete
- Signals for selection, properties, and deletion

### 3. Library Updates (`main_window.py`)

Added FSM Container to Library:
- New item: "📊 FSM Container" in FSM Elements category
- Mapped to "fsm_container" create mode
- Status message guides user to create FSM first, then add states

### 4. Canvas Widget Updates (`canvas_widget.py`)

**New instance variables**:
- `selected_fsm_id`: Tracks which FSM will receive new states
- `fsm_items`: Dictionary of FSM visual items

**New methods**:
- `_create_fsm_container_at()`: Creates FSM container at click position
- `_on_fsm_selected()`: Handles FSM selection (auto-targets for states)
- `_on_fsm_properties_requested()`: Opens FSM properties
- `_on_fsm_deleted()`: Removes FSM and updates model
- `_load_agent_fsms()`: Loads all FSM containers when entering agent view
- `_load_fsm_states_and_transitions()`: Loads states/transitions for a specific FSM

**Updated methods**:
- `mousePressEvent()`: Added handler for "fsm_container" mode
- `_create_state_at()`: Now checks for selected FSM instead of requiring single FSM
- `enter_agent_view()`: Loads all FSMs (agents can have 0 or more FSMs)
- `exit_agent_view()`: Properly saves/restores selected_fsm_id

### 5. Updated Imports

- Added `FSMItem` to canvas_widget imports
- Added `State`, `Transition` to model imports

## Workflow

### Creating an FSM Container

1. Double-click an agent block to enter internal view
2. Click "📊 FSM Container" in Library
3. Click canvas to place FSM container
4. FSM appears as dashed blue rectangle
5. FSM is auto-selected (ready to receive states)

### Adding States to FSM

1. Ensure an FSM container is selected (click to select if needed)
2. Click "⭕ State" in Library
3. Click inside FSM container to place state
4. State is added to the selected FSM
5. Status bar confirms: "Created state: State1"

### Multiple FSMs per Agent

- Click "FSM Container" multiple times to create multiple FSMs
- Each FSM can have its own states and transitions
- Select an FSM before adding states (click FSM container)
- Visual feedback: selected FSM has thicker blue border

### Backward Compatibility

**Old models** (single `fsm_id`):
- Automatically converted to `fsm_ids` list on load
- First FSM is auto-selected
- States/transitions loaded correctly

**New models** (multiple `fsm_ids`):
- All FSMs saved and loaded
- FSM containers appear in agent view
- States grouped by FSM container

## Design Decisions Implemented

### Q1: Any block can be opened to expose sub-agents
✅ **Implemented**: All blocks can be opened (even if no FSMs exist)

### Q2: Anything is an agent, so it COULD have an FSM
✅ **Implemented**: FSM as container for states and transitions
- Agents start with 0 FSMs
- Create FSM containers as needed
- Multiple FSMs per agent supported

### Q3: Connectors connect port to port
✅ **Already implemented**: Port-to-port drag-drop connections

### Q4: Code generation
⏸️ **Postponed**: As requested by user

## File Structure

```
hsim/gui/
├── models/
│   └── model.py ✅ Updated (fsm_ids, FSM visual properties)
├── items/
│   └── fsm_item.py ✅ New (FSM container visual)
└── views/
    ├── main_window.py ✅ Updated (Library + FSM mapping)
    └── canvas_widget.py ✅ Updated (FSM creation + loading)
```

## Testing Checklist

- [ ] Install PyQt6: `pip install PyQt6`
- [ ] Run GUI: `python -m hsim.gui.main`
- [ ] Create a block (e.g., Server)
- [ ] Double-click Server to enter internal view
- [ ] Click "FSM Container" in Library
- [ ] Click canvas to place FSM (blue dashed rectangle appears)
- [ ] Click "State" in Library
- [ ] Click inside FSM container (state appears)
- [ ] Click "State" again to add another state
- [ ] Click "Transition" in Library
- [ ] Click first state, then second state (arrow appears)
- [ ] Select FSM container (click it)
- [ ] Status bar shows: "Selected FSM: FSM_1"
- [ ] Create another FSM container
- [ ] Add states to the second FSM
- [ ] Verify states are grouped by their FSM container
- [ ] Press ESC to return to main view
- [ ] Reopen agent - FSMs and states should persist
- [ ] Save model (Ctrl+S)
- [ ] Close and reopen - verify FSMs load correctly

## Known Limitations

1. **Properties Panel**: FSM properties editing not yet implemented
   - Placeholder method `show_fsm_properties()` added
   - Currently shows "TODO" when double-clicking FSM

2. **FSM Toolbar**: Still creates states/transitions in backward-compat mode
   - Toolbar should be updated to use selected FSM
   - Currently works but doesn't leverage multiple FSMs

3. **Visual Containment**: States can be placed outside FSM boundaries
   - No enforcement of states staying inside FSM rectangle
   - Future: Add boundary checking and auto-resize

4. **FSM Resizing**: FSM containers are fixed size
   - No resize handles implemented
   - Future: Add corner handles for resizing

## Future Enhancements

1. **Auto-layout**: Automatically arrange FSM containers
2. **FSM Collapse**: Minimize FSM to show only title bar
3. **Drag States Between FSMs**: Move states from one FSM to another
4. **FSM Templates**: Save/load FSM patterns
5. **Visual Indicators**: Show which FSM is active/selected more prominently
6. **Constraint Checking**: Prevent overlapping FSM containers

## Migration Guide

**For existing models**:
- No action needed
- Old `fsm_id` automatically converted to `fsm_ids`
- FSM containers appear automatically in agent view

**For code using the model**:
- Use `block.fsm_ids` for list of FSMs
- Use `block.fsm_id` for backward compat (returns first FSM)
- Iterate `block.fsm_ids` to access all FSMs

## Validation

All Python files have valid syntax:
- ✅ model.py
- ✅ fsm_item.py
- ✅ canvas_widget.py
- ✅ main_window.py

Implementation complete and ready for testing!
