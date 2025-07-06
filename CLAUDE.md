# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Running the Flask Application
```bash
cd hsim/GSOM/flask
python app.py
```
The web application will be available at `http://localhost:5000`

### Running Tests
```bash
python -m pytest tests/
```

### Running the Core Simulation
```bash
python hsim/GSOM/GSOMGame.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Building the Package
```bash
python setup.py build
python setup.py sdist
```

## Architecture Overview

**hsim** is a discrete event simulation (DES) framework designed for manufacturing system modeling, with a specific focus on the GSOM (Global Supply Operations Management) simulation game.

### Core Components

#### 1. Simulation Engine (`hsim/core/`)
- **Environment**: Time management and agent registry with support for both virtual and real-time simulation
- **Events**: Priority-based event scheduling system with conditional triggers
- **Agents**: Base entities with FSM (Finite State Machine) integration
- **FSM**: State machine framework for complex entity behaviors
- **DES**: Discrete event simulation building blocks (servers, buffers, generators, terminators)

#### 2. Manufacturing Simulation (`hsim/GSOM/`)
- **GSOMGame.py**: Main manufacturing simulation with Excel-based configuration
- **Flask Web Interface**: Multi-user game platform with authentication and results tracking
- **Routes**: Modular Flask blueprint organization (auth, main, account, admin)

#### 3. Analysis Tools (`hsim/core/utils/`)
- **Gantt Chart Generation**: Visual timeline analysis for simulation runs
- **Performance Metrics**: Throughput calculation and statistical analysis
- **State Logging**: Comprehensive utilization tracking

### Key Design Patterns

#### Event-Driven Architecture
All simulation progress is driven by scheduled events with priority-based execution ensuring deterministic behavior.

#### State Machine Pattern
Every simulation entity has associated FSM behavior with hierarchical state management and transition guards.

#### Message Passing
Entities communicate via structured message objects with asynchronous delivery and receipt tracking.

#### Composition Over Inheritance
Complex entities are built from simpler components using frame systems and port-based connections.

### File Structure Notes

- **hsim/core/**: Core simulation framework (reusable)
- **hsim/GSOM/**: Manufacturing game implementation
- **hsim/a/**, **hsim/b/**, **hsim/c/**: Analysis modules for different scenarios
- **hsim/tests/**: Test suite
- **old/**: Legacy code (not actively maintained)

### Configuration Files

- **requirements.txt**: Python dependencies
- **setup.py**: Package configuration
- **launch.json**: VS Code debug configuration
- **hsim/GSOM/flask/config.py**: Flask application configuration

### Database

The Flask application uses SQLite for user management:
- **Location**: `hsim/GSOM/flask/static/db/users.db`
- **Schema**: Users table with username, email, password

### Security Notes

- The Flask application includes a hardcoded secret key that should be changed in production
- Azure Communication Services connection string is exposed in config.py
- Database connections should be reviewed for SQL injection vulnerabilities

### Development Notes

- The codebase uses path manipulation to handle imports across different operating systems
- Simulation results are exported to Excel files with multiple sheets (utilization, throughput, operators)
- The web interface supports real-time simulation monitoring and results visualization
- Gantt charts are generated as HTML files for simulation analysis

## Deep Architecture Understanding

### Core Simulation Engine

**hsim** is a sophisticated discrete event simulation (DES) framework built around several key architectural patterns:

#### 1. Event-Driven Simulation Core
- **Environment**: Virtual time management with precise event scheduling
- **Scheduler**: Priority-based event queue using sorted containers for O(log n) insertion
- **Events**: Multiple event types with lazy evaluation and cancellation support
  - `TimedEvent`: Scheduled for specific simulation times
  - `DelayEvent`: Relative timing from current simulation time
  - `ConditionEvent`: Triggered when logical conditions become true
  - `VerifiableEvent`: Conditional events with verification and disabling logic

#### 2. Finite State Machine Framework
- **FSM Class**: Comprehensive state machine with introspection-based element discovery
- **State Management**: Hierarchical states with entry/exit behaviors and lifecycle tracking
- **Transition System**: Multiple transition types (timeout, message, condition, event-based)
- **History Tracking**: Complete state and transition logs with timestamps for analysis

#### 3. Agent-Based Architecture
- **Agent Base Class**: Abstract foundation with automatic FSM integration
- **Variable Storage**: MATLAB-style dot notation via `dotdict` for flexible attribute access
- **Connection System**: Dictionary-based entity relationships for complex topologies
- **Lifecycle Management**: Automatic activation/deactivation with environment coordination

#### 4. Message Passing System
- **Asynchronous Communication**: Structured message objects with sender/receiver tracking
- **Priority Queues**: Custom priority handling with heap-based message sorting
- **Receipt System**: Message delivery tracking and acknowledgment mechanisms
- **Queue Integration**: Tight integration with DES blocks for workflow control

#### 5. DES Building Blocks
**Core Components:**
- `DESBase`: Abstract foundation with store management and forwarding logic
- `DESBlock`: Single-store entity with configurable queue types (standard, priority, locked)
- `DESMulti`: Multi-store entity for complex assembly and joining operations
- `TimedBlock`: Service time calculation mixin with flexible time specification

**Pre-built Components:**
- `Server`: Processing stations with FSM-based behavior and service time distributions
- `Buffer`: Capacity-managed storage with automatic forwarding
- `Generator`: Entity creation with configurable arrival patterns
- `Terminator`: Entity destruction and system exit points
- `Assembly`: Multi-input joining operations with synchronization logic

**Advanced Resources:**
- `UnreliableMachine`: Failure-prone servers with MTTF/MTTR modeling
- `QualityMachine`: Quality control with rejection paths and rework loops
- `SUMachine`: Setup/operation sequences with operator requirements

#### 6. Performance Optimizations

**Event Scheduling:**
- Lazy deletion for cancelled events (O(1) cancellation)
- Sequence numbers for deterministic ordering of simultaneous events
- Sorted containers for efficient priority queue operations

**Memory Management:**
- Weak references in callback systems to prevent memory leaks
- Efficient event queue management with periodic cleanup
- Modular design for selective loading of components

**Condition Monitoring (NEW - Performance Enhancement):**
- **Problem**: Original system checked all condition events at every time step (O(n) per step)
- **Solution**: Implemented reactive observable system with callback-based monitoring

### New Observable System

#### Observable Variables with Operator Overloading
```python
# Traditional assignment (prevented):
# obj.value = 5  # Raises AttributeError

# Observable assignment (required):
wrapped_obj = make_observable(obj)
wrapped_obj.value << 5  # Triggers callbacks
wrapped_obj.value >> 10  # Alternative syntax

# Callbacks automatically notified:
observe_attribute(wrapped_obj, 'value', lambda old, new: print(f"{old} -> {new}"))
```

#### Reactive Condition Events
- **Callback-based Triggers**: Condition events only check when dependencies change
- **Observable Dependencies**: Explicit declaration of what variables a condition depends on
- **Automatic Optimization**: System automatically optimizes condition checking
- **Backward Compatibility**: Legacy condition events still supported

#### Benefits
- **Performance**: Eliminates O(n) condition checking per time step
- **Clarity**: Explicit dependency declaration makes code more readable
- **Flexibility**: Support for complex dependency graphs
- **Integration**: Seamless integration with existing simulation components

### Service Time Calculation System

**Flexible Time Specification:**
- Fixed values: `serviceTime=3.0`
- Functions: `serviceTime=lambda: random.exponential(2)`
- Parameters: `serviceTime=[mean, std], serviceTimeFunction=normal_dist`
- Entity-specific: `serviceTime=None` (uses entity.serviceTime attribute)

**Function Integration:**
- Support for both parameterized and parameterless functions
- Automatic parameter unpacking for complex distributions
- Entity attribute access for context-dependent timing
- Error handling for invalid time specifications

### Key Design Patterns

#### 1. Composition Over Inheritance
- **Frame System**: Build complex entities from simpler components
- **Port-Based Connections**: Standardized input/output interfaces
- **Agent Aggregation**: Complex behaviors through composition

#### 2. Factory Pattern
- **Queue Factory**: Creates different queue types based on specifications
- **Component Builders**: Automated creation of simulation entities
- **Resource Templates**: Reusable patterns for manufacturing elements

#### 3. Observer Pattern
- **Observable Variables**: Change notification system
- **Event Callbacks**: Reactive programming support
- **State Monitoring**: Automatic tracking of system changes

#### 4. Strategy Pattern
- **Service Time Functions**: Pluggable time calculation strategies
- **Queue Types**: Different queuing disciplines (FIFO, priority, locked)
- **Transition Guards**: Configurable state transition conditions

### Testing and Validation

**Comprehensive Test Suite:**
- Unit tests for core components
- Integration tests for complex scenarios
- Performance benchmarks and optimization validation
- Regression tests to ensure backward compatibility

**Performance Characteristics:**
- Event creation: ~0.5M events/second
- Event execution: ~1M events/second
- Memory efficient: Weak references and lazy cleanup
- Scalable: O(log n) insertion, O(1) cancellation

### Advanced Features

#### Gantt Chart Generation
- Visual timeline analysis for simulation runs
- Agent state tracking over time
- Resource utilization visualization
- Export to HTML for interactive analysis

#### Statistical Analysis
- Automatic utilization calculation
- Throughput metrics with confidence intervals
- State duration analysis
- Performance bottleneck identification

#### Network Topology
- Automatic graph generation from connections
- Visual representation of simulation structure
- Dependency analysis and cycle detection
- Export capabilities for external analysis

### Manufacturing Simulation Capabilities

**GSOM Game Integration:**
- Complex production line modeling
- Technology investment decision support
- Performance optimization scenarios
- Multi-user competitive environment

**Industry 4.0 Features:**
- IoT sensor simulation
- AI-augmented quality control
- Smart maintenance scheduling
- Automated material handling (AGV simulation)

This architecture provides a robust foundation for discrete event simulation with particular strength in manufacturing systems, offering both high performance and extensive customization capabilities.