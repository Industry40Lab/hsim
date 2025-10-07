# hsim GUI - Test Plan and Feedback Form

## Overview
This document provides a structured test plan for the recently implemented GUI fixes. Please test each section and provide feedback using the questions provided.

---

## Test Section 1: Block Creation

### What to Test
1. Open the GUI: `python -m hsim.gui.main`
2. Try creating blocks from the left panel palette:
   - Generator
   - Buffer
   - Server
   - SUMachine (previously crashed)
   - ManualStation (previously crashed)
   - UnreliableMachine
   - QualityMachine
   - Terminator

### Questions for Feedback
**Q1.1**: Did SUMachine and ManualStation create without crashing?
- [ ] Yes, both work perfectly
- [ ] SUMachine works, ManualStation crashes
- [ ] ManualStation works, SUMachine crashes
- [ ] Both still crash

**Q1.2**: Are all block types creating successfully?
- [ ] Yes, all blocks create fine
- [ ] Some blocks fail (please specify which): _______________

**Q1.3**: Any error messages or unexpected behavior during block creation?
- [ ] No issues
- [ ] Yes (please describe): _______________

---

## Test Section 2: FSM Editor Access

### What to Test
1. Place a Server block on the canvas
2. Try opening the FSM editor in multiple ways:
   - **Method A**: Double-click the block
   - **Method B**: Right-click the block in the left panel "Main" section → "Open Internal View"

### Questions for Feedback
**Q2.1**: Does double-clicking a block open the FSM editor?
- [ ] Yes, opens smoothly
- [ ] No, nothing happens
- [ ] Yes, but with issues (describe): _______________

**Q2.2**: Does the FSM toolbar appear when you enter FSM mode?
- [ ] Yes, I see: ➕ State, ➡️ Transition, ⬅️ Back buttons
- [ ] No, toolbar doesn't appear
- [ ] Toolbar appears but missing buttons

**Q2.3**: Does the components palette (left panel) hide when in FSM mode?
- [ ] Yes, it hides automatically
- [ ] No, it stays visible
- [ ] Partially hides

**Q2.4**: When you press ESC or click "⬅️ Back", do you return to main view?
- [ ] Yes, returns smoothly
- [ ] No, stays in FSM mode
- [ ] Returns but with visual issues (describe): _______________

---

## Test Section 3: FSM State Creation and Editing

### What to Test
1. Enter FSM editor for a block
2. Click "➕ State" button multiple times (create 3-4 states)
3. Drag states around the canvas
4. Click on a state to select it
5. Check the properties panel on the right

### Questions for Feedback
**Q3.1**: Does clicking "➕ State" create new states?
- [ ] Yes, creates states at viewport center
- [ ] No, nothing happens
- [ ] Creates states but wrong position

**Q3.2**: Can you drag states around freely?
- [ ] Yes, smooth dragging
- [ ] No, states won't move
- [ ] Dragging is glitchy (describe): _______________

**Q3.3**: When you click a state, does the properties panel update?
- [ ] Yes, shows state properties (Name, Initial State, On Enter/Exit)
- [ ] No, properties panel doesn't update
- [ ] Shows wrong properties

**Q3.4**: Can you edit the state name in the properties panel?
- [ ] Yes, changes save immediately
- [ ] Yes, but have to click save button
- [ ] No, can't edit

**Q3.5**: Right-click a state - does a context menu appear with "Delete State"?
- [ ] Yes, and delete works
- [ ] Menu appears but delete doesn't work
- [ ] No context menu

---

## Test Section 4: FSM Transitions

### What to Test
1. In FSM editor, create 2 states
2. Select both states (click first, then Ctrl+click second)
3. Click "➡️ Transition" button
4. Try dragging one of the states
5. Click the transition arrow

### Questions for Feedback
**Q4.1**: Does clicking "➡️ Transition" with 2 states selected create a transition?
- [ ] Yes, arrow appears connecting the states
- [ ] No, nothing happens
- [ ] Shows error message (what message?): _______________

**Q4.2**: What happens if you click "➡️ Transition" with 0 or 1 states selected?
- [ ] Shows helpful error message
- [ ] Creates transition anyway (wrong)
- [ ] Crashes

**Q4.3**: When you drag a state, does the transition arrow follow it?
- [ ] Yes, arrow updates dynamically (FIXED ISSUE #1)
- [ ] No, arrow stays in original position (BUG)

**Q4.4**: Can you click on the transition arrow to select it?
- [ ] Yes, and properties panel shows transition properties
- [ ] Yes, but properties don't update
- [ ] Can't select transition

**Q4.5**: Can you edit transition properties (Label, Condition)?
- [ ] Yes, edits save immediately
- [ ] Yes, but laggy
- [ ] No, can't edit

---

## Test Section 5: Multiple Agent Views (Scene Isolation)

### What to Test
1. Create 3 different blocks (e.g., Server, Buffer, Generator)
2. Open FSM editor for first block, add 2 states
3. Press ESC to return to main view
4. Open FSM editor for second block, add 3 different states
5. Press ESC to return
6. Open FSM editor for third block

### Questions for Feedback
**Q5.1**: When you open the second block's FSM, do you see states from the first block?
- [ ] No, only new block's states visible (CORRECT - FIXED ISSUE #2)
- [ ] Yes, old states are still visible (BUG)

**Q5.2**: When you go back and forth between blocks, are the views clean?
- [ ] Yes, each block has its own isolated FSM view
- [ ] No, states accumulate and make a mess

**Q5.3**: Can you open nested views (block → FSM → sub-block → FSM)?
- [ ] Yes, scene stack handles multiple levels
- [ ] No, crashes or gets confused
- [ ] Haven't tried yet

---

## Test Section 6: Port Visibility

### What to Test
1. Place several blocks on canvas
2. Look at the connection points (ports) on the blocks
3. Hover your mouse over the ports

### Questions for Feedback
**Q6.1**: Are the ports visible enough?
- [ ] Yes, much better than before (FIXED ISSUE #10)
- [ ] Still too small
- [ ] Too large now

**Q6.2**: When you hover over a port, does it glow?
- [ ] Yes, nice multi-layer glow effect
- [ ] Yes, but glow is too subtle
- [ ] No glow effect

**Q6.3**: Can you distinguish input ports (blue) from output ports (green)?
- [ ] Yes, colors are clear
- [ ] Colors too similar
- [ ] Can't tell the difference

**Q6.4**: On a scale of 1-10, how visible are the ports now?
- Rating: _____ / 10
- Before fix they were: _____ / 10

---

## Test Section 7: Project Tree Context Menus

### What to Test
1. In the left panel, find the "📋 Main" section (shows your placed blocks)
2. Right-click on a block instance
3. Try each menu option:
   - "🔍 Open Internal View"
   - "📝 Edit Properties"
   - "🗑️ Delete Instance"

### Questions for Feedback
**Q7.1**: Do all context menu actions work?
- [ ] Yes, all 3 options work (FIXED ISSUE #8)
- [ ] Some work (which ones?): _______________
- [ ] None work

**Q7.2**: "Open Internal View" - does it open the FSM editor?
- [ ] Yes
- [ ] No

**Q7.3**: "Edit Properties" - does it show properties in the right panel?
- [ ] Yes, shows properties immediately
- [ ] Yes, but shows wrong properties
- [ ] No effect

**Q7.4**: "Delete Instance" - does it ask for confirmation before deleting?
- [ ] Yes, shows confirmation dialog
- [ ] No, deletes immediately (not ideal)
- [ ] Doesn't delete at all

**Q7.5**: After deleting, does the block disappear from both tree and canvas?
- [ ] Yes, removed from both
- [ ] Only from tree
- [ ] Only from canvas
- [ ] Still visible in both

---

## Test Section 8: Properties Panel Live Editing

### What to Test
1. Select a block on canvas
2. Edit its properties in the right panel (change name, parameters)
3. Click a state in FSM editor
4. Edit state properties (name, actions)
5. Click a transition
6. Edit transition properties (condition)

### Questions for Feedback
**Q8.1**: Do block property changes save immediately as you type?
- [ ] Yes, live updates
- [ ] No, have to click save button
- [ ] No, changes don't save at all

**Q8.2**: Do state property changes (name, on_enter, on_exit) save immediately?
- [ ] Yes, live updates (FIXED ISSUE #11)
- [ ] No, have to save manually
- [ ] Can't edit state properties

**Q8.3**: Can you edit transition conditions?
- [ ] Yes, with helpful hint text
- [ ] Yes, but no hints
- [ ] Can't edit transitions

**Q8.4**: Is the properties panel responsive?
- [ ] Yes, instant updates
- [ ] Laggy (how much delay?): _______________
- [ ] Freezes when editing

---

## Test Section 9: Overall Workflow

### What to Test
Complete this end-to-end workflow:
1. Create a Generator block
2. Create a Server block
3. Create a Terminator block
4. Open Server's FSM editor
5. Add 2 states: "Idle" and "Processing"
6. Create transition from Idle → Processing
7. Edit transition condition to: "self.queue.length() > 0"
8. Add On Enter action to Processing state: "print('Started processing')"
9. Exit FSM editor (ESC)
10. Save the model

### Questions for Feedback
**Q9.1**: Were you able to complete the entire workflow without errors?
- [ ] Yes, smooth experience
- [ ] Yes, but hit some issues (describe): _______________
- [ ] No, got stuck at step #_____ because: _______________

**Q9.2**: On a scale of 1-10, how intuitive was the FSM editing workflow?
- Rating: _____ / 10
- What was confusing (if any): _______________

**Q9.3**: Did you encounter any crashes during this workflow?
- [ ] No crashes
- [ ] Yes, crashed when: _______________

---

## Test Section 10: Edge Cases and Error Handling

### What to Test
1. Try to create a transition with 0 states selected
2. Try to create a transition with 1 state selected
3. Try to create a transition with 3 states selected
4. Try to create a duplicate transition (same from/to states)
5. Delete a state that has transitions connected to it

### Questions for Feedback
**Q10.1**: What happens with wrong number of states selected for transition?
- [ ] Shows helpful error message in status bar
- [ ] Does nothing (confusing)
- [ ] Crashes

**Q10.2**: What happens when creating duplicate transition?
- [ ] Shows error message: "Transition already exists"
- [ ] Creates duplicate (wrong)
- [ ] Crashes

**Q10.3**: When you delete a state with transitions, do the transitions also delete?
- [ ] Yes, transitions auto-delete
- [ ] No, transitions remain (orphaned)
- [ ] Crashes

---

## General Feedback

### Open-Ended Questions

**Q11.1**: What is the BEST improvement from all the fixes?
Answer: _______________

**Q11.2**: What still needs work or feels clunky?
Answer: _______________

**Q11.3**: Any visual issues? (colors, sizes, alignments, etc.)
Answer: _______________

**Q11.4**: Any performance issues? (lag, freezing, slow responses)
Answer: _______________

**Q11.5**: Features you'd like to see next?
Answer: _______________

**Q11.6**: Overall satisfaction rating (1-10):
- Before fixes: _____ / 10
- After fixes: _____ / 10

---

## Bug Report Template

If you encounter any bugs, please fill out:

**Bug #___**
- **What were you doing?**: _______________
- **What did you expect?**: _______________
- **What actually happened?**: _______________
- **Error message (if any)**: _______________
- **Can you reproduce it?**: [ ] Yes [ ] No
- **Steps to reproduce**:
  1. _______________
  2. _______________
  3. _______________

---

## Checklist: All 11 Original Issues

Based on your testing, verify each fix:

- [ ] ✅ **Issue #1**: Transitions follow states when dragged
- [ ] ✅ **Issue #2**: States don't persist between different agent views
- [ ] ✅ **Issue #3**: Delete state works (right-click menu)
- [ ] ✅ **Issue #4**: Can add states (➕ button) and transitions (➡️ button)
- [ ] ✅ **Issue #5**: Components palette hides in FSM mode
- [ ] ✅ **Issue #6**: SUMachine and ManualStation don't crash
- [ ] ✅ **Issue #7**: Can create links between blocks (no AttributeError)
- [ ] ✅ **Issue #8**: Right-click commands in project tree work
- [ ] ✅ **Issue #9**: [Future] Distinguish agent classes vs instances (not critical)
- [ ] ✅ **Issue #10**: Ports are visible (larger, glow effect)
- [ ] ✅ **Issue #11**: Can edit state/transition properties

---

## Priority Issues (If Any Found)

If you find critical bugs during testing, list them here in priority order:

1. **[P0 - Critical]**: _______________
2. **[P1 - High]**: _______________
3. **[P2 - Medium]**: _______________
4. **[P3 - Low]**: _______________

---

## Notes Section

Use this space for any additional observations, screenshots references, or comments:

_______________
_______________
_______________

---

## Submission

Once you've completed testing, please provide:
1. Answers to all questions above
2. Any bug reports
3. Overall satisfaction rating
4. Top 3 priorities for next iteration (if any)

Thank you for testing! 🚀
