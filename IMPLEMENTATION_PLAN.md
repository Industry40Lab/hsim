# hsim GUI - Complete Implementation Plan

## Current Status Assessment

### ✅ Completed (Part 1)
1. **Data Model Updates**
   - Block.fsm_ids supports multiple FSMs per agent
   - FSM.position and FSM.size for visual containers
   - Backward compatibility for old fsm_id
   - Serialization/deserialization working

2. **Component Library**
   - All DES blocks from hsim.core added
   - FSM Container item in library
   - Proper categorization
   - Block definitions match hsim.core modules

3. **Visual Components**
   - FSMItem class created (fsm_item.py)
   - Signals for selection, deletion, properties
   - Semi-transparent visual container
   - Title label and context menu

4. **Bug Fixes**
   - Block.to_dict() serialization bug fixed
   - CodeGenerator connection iteration fixed
   - Library links match hsim.core modules

### ❌ Not Completed (Critical Gaps)

#### 1. FSM Container Integration (Part 2)
**Current Problem**: Canvas methods for FSM containers don't exist
- `canvas_widget.py:896` still checks `block.fsm_id` (single FSM)
- No `_create_fsm_container_at()` method
- No `_load_agent_fsms()` method
- No FSM selection handling
- State creation doesn't target selected FSM

**Impact**: Users cannot create or use FSM containers in GUI

#### 2. Code Generation
**Current Problem**: Basic structure exists but incomplete
- FSM code generation not implemented
- Hierarchical agent code generation unclear
- Connection port names not handled properly
- No validation before code generation

**Impact**: Cannot export models to executable Python code

#### 3. Simulation Execution
**Current Problem**: No integration with simulation engine
- "Run" button (F5) is placeholder
- No way to execute generated code from GUI
- No results visualization
- No progress monitoring

**Impact**: GUI is a design tool only, cannot run simulations

#### 4. Model Validation
**Current Problem**: No consistency checking
- Can create orphaned connections
- Can delete blocks with existing connections
- No cycle detection in connections
- No FSM completeness checking

**Impact**: Can create invalid models that fail at runtime

---

## Implementation Roadmap

### Phase 1: Complete FSM Container Integration (HIGH PRIORITY)
**Goal**: Make FSM containers fully functional in GUI
**Estimated Effort**: 4-6 hours

#### Tasks:
1. **Update `enter_agent_view()` in canvas_widget.py**
   - Remove requirement for `block.fsm_id` (single FSM)
   - Accept agents with 0 or more FSMs
   - Call `_load_agent_fsms()` instead of `_load_fsm_graphics()`

2. **Implement `_create_fsm_container_at(x, y)`**
   ```python
   def _create_fsm_container_at(self, x, y):
       """Create FSM container at position in agent view"""
       if self.current_agent_id is None:
           # Error: must be in agent view
           return

       # Create FSM in data model
       fsm = FSM(
           id=str(uuid.uuid4()),
           name=f"FSM_{len(self.model.fsms) + 1}",
           owner_block_id=self.current_agent_id,
           position=Position(x, y),
           size=Size(400, 300)
       )
       self.model.add_fsm(fsm)

       # Add to owner block's fsm_ids list
       owner_block = self.model.get_block_by_id(self.current_agent_id)
       if owner_block:
           owner_block.fsm_ids.append(fsm.id)

       # Create visual item
       fsm_item = FSMItem(fsm)
       fsm_item.signals.selected.connect(self._on_fsm_selected)
       fsm_item.signals.deleted.connect(self._on_fsm_deleted)
       fsm_item.signals.properties_requested.connect(self._on_fsm_properties_requested)
       self.scene.addItem(fsm_item)
       self.fsm_items[fsm.id] = fsm_item

       # Auto-select new FSM for state addition
       self.selected_fsm_id = fsm.id
       self.model_changed.emit()
   ```

3. **Implement `_load_agent_fsms(owner_block)`**
   ```python
   def _load_agent_fsms(self, owner_block):
       """Load all FSM containers for an agent"""
       for fsm_id in owner_block.fsm_ids:
           fsm = self.model.get_fsm_by_id(fsm_id)
           if not fsm:
               continue

           # Create FSM container visual
           fsm_item = FSMItem(fsm)
           fsm_item.signals.selected.connect(self._on_fsm_selected)
           fsm_item.signals.deleted.connect(self._on_fsm_deleted)
           fsm_item.signals.properties_requested.connect(self._on_fsm_properties_requested)
           self.scene.addItem(fsm_item)
           self.fsm_items[fsm.id] = fsm_item

           # Load states and transitions for this FSM
           self._load_fsm_states_and_transitions(fsm)
   ```

4. **Implement FSM event handlers**
   - `_on_fsm_selected(fsm_id)`: Set `self.selected_fsm_id = fsm_id`
   - `_on_fsm_deleted(fsm_id)`: Remove FSM from model and scene
   - `_on_fsm_properties_requested(fsm)`: Show properties panel

5. **Update `_create_state_at(x, y)`**
   - Check `self.selected_fsm_id` instead of `self.current_fsm`
   - Show error if no FSM selected
   - Add state to selected FSM

6. **Update `mousePressEvent()`**
   - Handle `create_mode == "fsm_container"`
   - Call `_create_fsm_container_at()` with snapped coordinates

7. **Test Complete Workflow**
   - Create agent
   - Enter agent view
   - Create FSM container
   - Select FSM
   - Add states to FSM
   - Add transitions
   - Create second FSM
   - Verify state isolation between FSMs

**Acceptance Criteria**:
- ✅ Can create FSM containers in agent view
- ✅ Can create multiple FSMs per agent
- ✅ States are added to selected FSM only
- ✅ Transitions work within FSM
- ✅ FSM containers can be moved and deleted
- ✅ Properties panel shows FSM properties when selected

---

### Phase 2: Code Generation & Validation (HIGH PRIORITY)
**Goal**: Export working Python code from models
**Estimated Effort**: 6-8 hours

#### Tasks:

1. **FSM Code Generation**
   - Generate FSM class definitions from states/transitions
   - Generate state on_enter/on_exit methods
   - Generate transition conditions and actions
   - Handle hierarchical states
   - Multiple FSMs per agent

2. **Hierarchical Agent Code Generation**
   - Generate nested class structure for sub-agents
   - Handle parent-child relationships
   - Generate proper initialization order
   - Pass environment down hierarchy

3. **Connection Code Generation**
   - Map connection visual IDs to port names
   - Handle multiple outputs (reject, rework, etc.)
   - Generate proper port assignments
   - Validate connection compatibility

4. **Validation System**
   - Check for orphaned connections (deleted blocks)
   - Verify all connections have valid from/to blocks
   - Check FSM completeness (at least one initial state)
   - Detect cycles in agent hierarchy
   - Verify all states have valid parent FSM

5. **Code Generator Improvements**
   ```python
   class CodeGenerator:
       def generate_fsm_code(self, fsm: FSM, indent: int = 1) -> str:
           """Generate FSM class with states and transitions"""

       def generate_agent_code(self, block: Block, indent: int = 1) -> str:
           """Generate agent with sub-agents and FSMs"""

       def validate_model(self) -> List[str]:
           """Return list of validation errors"""
   ```

6. **Testing**
   - Test with simple model (Generator → Server → Terminator)
   - Test with FSMs (states, transitions, conditions)
   - Test with hierarchical agents
   - Test with multiple FSMs per agent
   - Verify generated code runs without errors
   - Verify simulation produces expected results

**Acceptance Criteria**:
- ✅ Generated code runs without errors
- ✅ FSM behavior matches visual design
- ✅ Hierarchical agents work correctly
- ✅ Connections map to correct ports
- ✅ Validation catches common errors before generation

---

### Phase 3: Simulation Execution (MEDIUM PRIORITY)
**Goal**: Run simulations from GUI and visualize results
**Estimated Effort**: 8-10 hours

#### Tasks:

1. **Run Button Implementation**
   - Generate code from model
   - Execute in subprocess to avoid blocking GUI
   - Capture stdout/stderr
   - Show progress dialog
   - Handle errors gracefully

2. **Simulation Configuration**
   - Dialog for simulation time
   - Random seed option
   - Output options (console, file, results panel)
   - Performance metrics to collect

3. **Results Visualization**
   - Add results panel (bottom dock)
   - Show simulation log (stdout/stderr)
   - Show performance metrics (throughput, utilization)
   - Gantt chart integration (use existing hsim Gantt code)
   - Export results to Excel

4. **Monitoring & Control**
   - Progress bar for long simulations
   - Stop button to terminate simulation
   - Real-time log updates
   - Error highlighting in log

**Acceptance Criteria**:
- ✅ Can run simulation from GUI (F5)
- ✅ Simulation output shown in results panel
- ✅ Can stop running simulation
- ✅ Errors shown with helpful messages
- ✅ Results can be exported

---

### Phase 4: Enhanced User Experience (MEDIUM PRIORITY)
**Goal**: Polish GUI for production use
**Estimated Effort**: 6-8 hours

#### Tasks:

1. **Visual Feedback Improvements**
   - Rubber band line while creating connections
   - Port highlight on hover (already implemented)
   - Connection preview before creation
   - Snap indicators (grid lines highlight)

2. **FSM Container Enhancements**
   - Resizing handles (corner/edge)
   - Auto-resize to fit states
   - Collapse/expand FSM containers
   - FSM outline color customization

3. **Property Panel Improvements**
   - Syntax highlighting for Python code (on_enter, on_exit, conditions)
   - Autocomplete for common patterns
   - Validation indicators (red/green)
   - Help text for each property

4. **Model Validation UI**
   - Validation panel showing errors/warnings
   - Click error to jump to problem location
   - Auto-validation on model changes
   - Warning icons on invalid blocks/connections

5. **Examples & Templates**
   - Create 5 example models:
     - Simple production line (Generator → Server → Terminator)
     - Quality control with rework (QualityMachine)
     - Maintenance with failures (UnreliableMachine)
     - Manual operations (ManualStation, Operator)
     - Complex hierarchical factory
   - Template dialog on File → New
   - Example models in Help menu

6. **Documentation**
   - Update GUI_DOCUMENTATION.md with accurate implementation status
   - Add screenshots to documentation
   - Create quick start guide
   - Video tutorial (or screenshot walkthrough)

**Acceptance Criteria**:
- ✅ Visual feedback is clear and helpful
- ✅ FSM containers can be resized
- ✅ Property panel has syntax highlighting
- ✅ Validation panel shows errors clearly
- ✅ 5 working example models available
- ✅ Documentation is accurate and helpful

---

### Phase 5: Advanced Features (LOW PRIORITY)
**Goal**: Add power-user features
**Estimated Effort**: 10-12 hours

#### Tasks:

1. **Actions Category Implementation**
   - Send Message action (visual + code generation)
   - Trigger Event action
   - Set Variable action
   - Loop action (repeat N times)
   - Conditional action (if-then-else)

2. **Connection Routing**
   - Smart auto-routing to avoid overlaps
   - Orthogonal (right-angle) connections
   - Curved connection option
   - Manual control point editing

3. **Search & Navigation**
   - Quick search for blocks/states (Ctrl+F)
   - Find usages (where is this block connected?)
   - Navigate to definition (for sub-agents)
   - Breadcrumb navigation in agent hierarchy

4. **Multi-Agent Collaboration**
   - Model versioning (git integration)
   - Diff view for model changes
   - Merge conflict resolution
   - Change history panel

5. **Performance Optimization**
   - Lazy loading for large models (1000+ blocks)
   - Virtual scrolling in project tree
   - Cached rendering for complex scenes
   - Background auto-save (every 60s)

**Acceptance Criteria**:
- ✅ Actions can be added and generate correct code
- ✅ Connections route intelligently
- ✅ Search finds blocks/states quickly
- ✅ Can handle models with 500+ blocks without lag

---

## Testing Strategy

### Unit Tests
- Model serialization/deserialization
- Code generation for each block type
- FSM state machine logic
- Connection validation

### Integration Tests
- Complete workflow tests (create, save, load, run)
- FSM container integration
- Hierarchical agent editing
- Code generation → execution

### Manual Testing Checklist
See GUI_TEST_PLAN.md for comprehensive manual testing guide

### Performance Tests
- Large model loading (500+ blocks)
- Complex FSM editing (50+ states)
- Rapid operations (undo/redo 100 times)
- Memory leaks (run for 1 hour of editing)

---

## Risk Assessment

### High Risk Items
1. **Code generation correctness** - Generated code may not match visual design
   - Mitigation: Extensive testing, validation before generation

2. **Performance with large models** - GUI may lag with 500+ blocks
   - Mitigation: Profiling, lazy loading, virtual scrolling

3. **Data loss on crashes** - User work may be lost
   - Mitigation: Auto-save every 60s, backup files

### Medium Risk Items
1. **FSM container complexity** - Multiple FSMs may confuse users
   - Mitigation: Clear visual hierarchy, good documentation

2. **Connection routing** - Auto-routing may create messy diagrams
   - Mitigation: Manual control points, smart algorithms

### Low Risk Items
1. **Platform compatibility** - May have issues on Mac/Windows
   - Mitigation: Cross-platform testing with PyQt6

---

## Success Metrics

### Minimum Viable Product (MVP)
- ✅ All Phase 1 tasks complete (FSM containers work)
- ✅ All Phase 2 tasks complete (code generation works)
- ✅ Can create, save, load, and run a simple simulation
- ✅ No critical bugs in core workflow

### Full Release v1.0
- ✅ All Phase 1-3 tasks complete
- ✅ 50% of Phase 4 tasks complete
- ✅ All manual tests passing
- ✅ 5 example models working
- ✅ Documentation complete

### Future Enhancements (v2.0)
- ✅ All Phase 4-5 tasks complete
- ✅ Performance optimizations
- ✅ Advanced features (Actions, smart routing, search)

---

## Current Priorities (Next Steps)

### Immediate (This Session)
1. ✅ Complete FSM Container Implementation (Phase 1)
   - All canvas methods for FSM containers
   - Full integration with state creation
   - Test workflow end-to-end

2. ✅ Update enter_agent_view() for multiple FSMs

3. ✅ Test and fix any bugs found

### This Week
1. Complete code generation (Phase 2)
2. Add validation system
3. Create 2-3 example models
4. Test generated code execution

### This Month
1. Implement simulation runner (Phase 3)
2. Add results visualization
3. Polish UI (Phase 4)
4. Complete documentation

---

## Dependencies & Requirements

### Python Packages
- PyQt6 (GUI framework) - REQUIRED
- numpy (random distributions) - existing
- pandas (results export) - optional
- matplotlib (charts) - optional

### hsim Core
- All modules in hsim.core must be importable
- FSM framework must support code generation
- DES blocks must have consistent interfaces

### Development Tools
- pytest (testing) - recommended
- black (code formatting) - recommended
- pylint (code quality) - recommended

---

## Questions for User

1. **Priorities**: Which phase should we focus on first?
   - Phase 1 (FSM containers) - Critical for design workflow
   - Phase 2 (Code generation) - Critical for running simulations
   - Phase 3 (Simulation runner) - Nice to have for integrated workflow

2. **Code Generation Strategy**:
   - Generate standalone Python files users can run separately?
   - Or execute directly from GUI with embedded runner?
   - Both?

3. **FSM Behavior**:
   - Should FSM containers be auto-created on agent creation?
   - Or require explicit FSM container creation (current design)?

4. **Validation**:
   - Strict validation (prevent invalid operations)?
   - Or warning-based (allow but warn)?

---

## Timeline Estimate

### Aggressive (1 week, 40 hours)
- Day 1-2: Phase 1 (FSM containers) - 12 hours
- Day 3-4: Phase 2 (Code generation) - 14 hours
- Day 5: Phase 3 (Basic runner) - 8 hours
- Day 6-7: Testing & bug fixes - 6 hours

### Realistic (2 weeks, 60 hours)
- Week 1: Phase 1 + Phase 2 + Testing - 30 hours
- Week 2: Phase 3 + Phase 4 (partial) + Examples - 30 hours

### Conservative (3 weeks, 80 hours)
- Week 1: Phase 1 + Testing - 20 hours
- Week 2: Phase 2 + Validation - 30 hours
- Week 3: Phase 3 + Phase 4 + Documentation - 30 hours

---

## Notes

- This plan assumes single developer working part-time
- Priorities may shift based on user feedback
- Testing is critical - don't skip it
- Documentation should be updated continuously, not at end
- Consider user feedback early and often
