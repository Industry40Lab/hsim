# Testing the hsim GUI

## Prerequisites

Install PyQt6 (required for GUI):
```bash
pip install PyQt6
```

## Testing Options

### 1. Model Tests (No Display Required)

Test the data model, serialization, and code generation without GUI:

```bash
python hsim/gui/test_gui.py
```

**What it tests:**
- Block definitions
- Model creation (Generator → Server → Terminator)
- Serialization/deserialization
- Python code generation
- FSM creation and transitions

**Expected output:**
```
============================================================
hsim GUI Model Tests
============================================================

Testing block definitions...
✓ Server definition: Server (🔧)
✓ Found 4 categories
  - DES Blocks: 5 blocks
  - Resources: 4 blocks
  - Advanced: 2 blocks
  - Actions: 0 blocks

Testing model creation...
✓ Created Generator: Generator 1
✓ Created Server: Server 1
✓ Created Terminator: Terminator 1
✓ Connected Generator 1 → Server 1
✓ Connected Server 1 → Terminator 1
✓ Model has 3 blocks and 2 connections

Testing serialization...
✓ Serialized to dict: 3 blocks
✓ Deserialized from dict: 3 blocks

Testing code generation...
✓ Generated Python code:
[... generated code ...]

Testing FSM...
✓ Added state: Idle
✓ Added state: Working
✓ Added transition: Idle → Working
✓ FSM serialized: 2 states, 1 transitions
✓ FSM deserialized successfully

============================================================
✓ All tests passed!
============================================================
```

---

### 2. Full GUI Application (Display Required)

Launch the complete graphical interface:

```bash
python -m hsim.gui.main
```

**What to test:**

#### Basic Workflow
1. **Place DES blocks:**
   - Click "⚙️ Generator" in Library → click canvas
   - Click "🔧 Server" → click canvas
   - Click "🗑️ Terminator" → click canvas

2. **Connect blocks:**
   - Drag from green output port → blue input port

3. **Open agent internal view:**
   - Double-click Server block
   - New tab opens showing internal view

4. **Create FSM container:**
   - Click "📊 FSM Container" in Library
   - Click canvas inside agent view
   - Blue dashed rectangle appears

5. **Add states to FSM:**
   - Click FSM container to select it
   - Click "⭕ State" in Library → click inside FSM container
   - Repeat to add more states

6. **Add transitions:**
   - Click "➡️ Transition" in Library
   - Click first state → click second state
   - Arrow appears between states

7. **Edit properties:**
   - Select a state/block
   - Properties panel shows editable properties

8. **Test file operations:**
   - File → Save (Ctrl+S) - saves as `.hsim` file
   - File → Open (Ctrl+O) - loads model
   - File → Export Python Code - generates executable code

#### Advanced Features
- **Multiple FSMs:** Create multiple FSM containers in one agent
- **Hierarchical agents:** Create blocks inside agents (becomes sub-agents)
- **Alignment tools:** Arrange menu - align/distribute blocks
- **Undo/Redo:** Ctrl+Z / Ctrl+Shift+Z
- **Copy/Paste:** Ctrl+C / Ctrl+V
- **Zoom:** Ctrl++ / Ctrl+- / Ctrl+0
- **Grid snapping:** Toggle with toolbar button

---

## Current Implementation Status

### ✅ Fully Implemented
- Tabbed canvas (multiple agent tabs)
- Hierarchical agents (sub-agents)
- Component library with categories
- FSM visual containers (NEW!)
- Multiple FSMs per agent (NEW!)
- Port-to-port connections
- Properties panel
- Grid snapping
- Alignment tools
- Undo/Redo
- Copy/Paste
- Zoom controls
- File save/load

### ⚠️ Partially Implemented
- **FSM Container Integration:** Data model and library complete, canvas methods in progress
  - ✅ Block.fsm_ids (multiple FSMs)
  - ✅ FSM visual properties (position, size)
  - ✅ FSM Container in library
  - ⏳ Canvas FSM creation methods (in progress)
  - ⏳ Canvas FSM loading (in progress)

### ❌ Not Yet Implemented
- Code generation for FSMs (postponed)
- Actions category (Send Message, Trigger Event, etc.)
- FSM resizing handles
- Constraint checking (prevent overlapping FSMs)

---

## Troubleshooting

### GUI won't start
**Problem:** `ModuleNotFoundError: No module named 'PyQt6'`
**Solution:** `pip install PyQt6`

### Can't connect blocks
**Problem:** Dragging between blocks doesn't work
**Solution:** Drag from green output port to blue input port (not block-to-block)

### Can't add states
**Problem:** States won't appear in agent view
**Solution:**
1. Double-click agent to enter internal view
2. Create FSM container first
3. Click FSM container to select it
4. Then add states

### FSM Container not in library
**Problem:** Don't see "📊 FSM Container" option
**Solution:** Update to latest code from `GUI_v1` branch or `claude/review-gui-documentation-016WYkmuLFhRKkbc8jYV8vEt` branch

---

## Documentation

- **GUI_DOCUMENTATION.md** - Comprehensive user guide
- **GUI_TEST_PLAN.md** - Detailed testing checklist
- **IMPLEMENTATION_COMPLETE.md** - Technical implementation details
- **CLAUDE.md** - Developer guidance

---

## Bug Reports

If you find issues:
1. Note the steps to reproduce
2. Check console for error messages
3. Report with environment details (OS, Python version, PyQt6 version)

---

## Next Steps After Testing

Once testing is complete:
1. Report any bugs found
2. Confirm FSM container workflow works as expected
3. Provide feedback on usability
4. Identify priorities for next iteration
