# Bug Fix: ValueError on Block Creation

## Problem
When clicking agent types in the project tree, the application crashed with:
```
ValueError: 'SUMachine' is not a valid BlockType
```

## Root Cause
The project tree was emitting display names (e.g., "SUMachine", "Generator") instead of the BlockType enum values (e.g., "su_machine", "generator").

The canvas widget's `create_block_at()` method expects enum values:
```python
block_def = get_block_definition(BlockType(block_type))
                                 ^^^^^^^^^^^^^^^^^^^^^
                                 # Needs "su_machine", not "SUMachine"
```

## Solution

### File: `hsim/gui/views/project_tree.py`

1. **Updated `_add_agent_type()` method** to accept `display_name` parameter:
```python
def _add_agent_type(self, parent, name, icon, description, display_name=None):
    """Add an agent type to the tree"""
    # Use display_name for UI, name for enum value
    label = display_name if display_name else name
    item = QTreeWidgetItem(parent, [f"{icon} {label}"])
    item.setData(0, Qt.ItemDataRole.UserRole, {
        'type': 'agent_type',
        'name': name,  # ← This is the enum value (e.g., "generator")
        'description': description
    })
```

2. **Updated all agent type registrations** to use enum values:
```python
# BEFORE (WRONG):
self._add_agent_type(process_category, "Generator", "⚙️", "Generates entities")

# AFTER (CORRECT):
self._add_agent_type(process_category, "generator", "⚙️", "Generates entities", display_name="Generator")
```

3. **Added missing block types**:
   - Store
   - ManualStation
   - Assembly
   - Agent

4. **Organized into categories**:
   - 📊 Process Flow: Generator, Buffer, Server, Store, Terminator
   - 🔧 Resources: UnreliableMachine, QualityMachine, SUMachine, ManualStation
   - 🔀 Advanced: Assembly, Agent

## Result
✅ Project tree displays friendly names: "Generator", "SUMachine"
✅ Internal data uses enum values: "generator", "su_machine"
✅ Canvas receives correct BlockType enum values
✅ All blocks can be created without errors

## Testing
- [x] Click "Generator" in project tree → creates generator block
- [x] Click "SUMachine" in project tree → creates su_machine block
- [x] Click "Buffer" in palette → creates buffer block
- [x] All block types work from both tree and palette
