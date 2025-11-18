# Code Import/Export and Visualization

**Simplified Focus**: Import existing code, visualize code structure, export to code

---

## Core Features (Simplified)

### 1. Code Visualization (Read-Only) ✅
**Purpose**: Show users what methods/attributes are available in each block type

**Implementation**:
- Display methods in properties panel (read-only)
- Show method signatures and docstrings
- No editing - just for reference

**Already have**: MethodIntrospector ✅

---

### 2. Import Code → GUI (PRIORITY) 🎯
**Purpose**: Load existing Python simulation files and create visual models

**Use Cases**:
- User has existing simulation.py file
- Import → See visual representation
- Modify in GUI
- Export enhanced version

**Implementation**: CodeParser using Python AST

---

### 3. Export GUI → Code ✅
**Purpose**: Generate runnable Python code from visual model

**Already working!**
- Block creation
- Connections
- FSM classes
- Validation

---

## Implementation Plan (Focused)

### Phase 1: Code Visualization (2 hours)
- Simple read-only panel showing methods
- Integration with properties panel
- Test with various block types

### Phase 2: Code Import (8-10 hours) - PRIORITY
- AST-based parser
- Detect blocks, connections
- Create visual layout
- Handle common patterns
- Import dialog

### Phase 3: Testing (3-4 hours)
- Test import with GSOM simulation
- Test export (already works)
- Round-trip: import → modify → export
- Create examples

---

## Code Import Strategy

### What to Parse:

```python
def main():
    env = Environment()

    # Parse these: Block creation
    gen = Generator(env, 'Generator 1', serviceTime=1.0)
    srv = Server(env, 'Server 1', serviceTime=2.0)
    term = Terminator(env, 'Terminator 1')

    # Parse these: Connections
    gen.connections['next'] = srv
    srv.connections['next'] = term

    # Parse these: FSM activation
    gen.activate_fsm()
    srv.activate_fsm()

    # Parse this: Run command
    env.run(100)
```

### What to Create:
- Block objects with position (auto-layout)
- Connection objects between blocks
- Store properties (serviceTime, etc.)
- Layout blocks in grid pattern

### What to Ignore (for now):
- Custom methods
- Complex logic (loops, conditionals)
- Custom FSMs (focus on standard blocks first)

---

## UI Design (Simplified)

### Code Visualization Panel

```
┌─────────────────────────────────────────┐
│ Properties | Code Info | Connections   │
├─────────────────────────────────────────┤
│  [Code Info Tab - Read Only]            │
│                                         │
│  Block Type: Server                     │
│  Python Class: hsim.core.des.Server     │
│                                         │
│  Available Methods:                     │
│  ┌───────────────────────────────────┐ │
│  │ ⚡ Lifecycle                       │ │
│  │   • __init__(env, name, ...)      │ │
│  │   • activate()                     │ │
│  │                                    │ │
│  │ 🔄 Processing                      │ │
│  │   • process(entity)                │ │
│  │   • handle_event()                 │ │
│  │                                    │ │
│  │ 🎯 FSM                             │ │
│  │   • activate_fsm()                 │ │
│  │   • deactivate_fsm()               │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Click method to see docstring]       │
└─────────────────────────────────────────┘
```

### Import Dialog

```
┌─────────────────────────────────────────┐
│  Import Python Simulation               │
├─────────────────────────────────────────┤
│  Select Python file to import:         │
│                                         │
│  [📁 Browse...]  simulation.py          │
│                                         │
│  Preview:                               │
│  ┌───────────────────────────────────┐ │
│  │ Found:                             │ │
│  │  • 3 blocks (Generator, Server,    │ │
│  │    Terminator)                     │ │
│  │  • 2 connections                   │ │
│  │  • env.run(100)                    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  Layout:                                │
│  ◉ Auto (grid layout)                   │
│  ○ Horizontal                           │
│  ○ Vertical                             │
│                                         │
│  [✅ Import]  [❌ Cancel]               │
└─────────────────────────────────────────┘
```

---

## Timeline (Focused)

### This Session (2-3 hours)
1. Code visualization panel (simple, read-only)
2. Start code parser implementation

### Next Session (6-8 hours)
1. Complete code parser
2. Import dialog
3. Test with GSOM simulation
4. Handle edge cases

### Following Session (3-4 hours)
1. Testing and examples
2. Documentation
3. Polish

**Total: 11-15 hours** (much less than full sync!)

---

## Success Criteria

- ✅ Can display methods for any block type
- ✅ Can import simple Python simulation files
- ✅ Can export visual models to Python code (already works)
- ✅ Round-trip works: import → modify → export → run
- ✅ Works with GSOM simulation

---

## Next Steps

1. Create simple code visualization panel (2 hours)
2. Implement code parser (6-8 hours)
3. Test import workflow (2-3 hours)
