# hsim Model Designer

AnyLogic-style visual designer for discrete event simulation models using PyQt6.

## Features

### Model Canvas
- **Drag-and-drop interface** for creating simulation models
- **Component Palette** with all DES blocks organized by category:
  - DES Blocks: Generator, Buffer, Server, Store, Terminator
  - Resources: UnreliableMachine, QualityMachine, SUMachine
  - Advanced: Assembly
  - Agents: Custom Agent with FSM
- **Visual connections** between blocks with automatic routing
- **Properties panel** for editing block parameters in real-time
- **Grid display** with snap-to-grid support
- **Zoom and pan** controls

### FSM Editor
- Visual editor for finite state machines (embedded in agents)
- Hierarchical states support
- Multiple transition types (timeout, message, condition, event)
- State entry/exit actions
- Transition guards and actions

### Code Generation
- Export models as Python code
- Generates complete runnable simulations using hsim framework
- Handles all block types and connections
- Includes FSM definitions

### File Management
- Save/load models as `.hsim` files (JSON format)
- Import existing models
- Export to Python code

## Installation

```bash
# Install PyQt6
pip install PyQt6

# Or use the requirements file
pip install -r requirements.txt
```

## Running the Application

### On Linux/Mac with Display:
```bash
python -m hsim.gui.main
```

### On WSL2 with X Server:
1. Install an X server on Windows (e.g., VcXsrv, Xming)
2. Set the DISPLAY environment variable:
```bash
export DISPLAY=:0
python -m hsim.gui.main
```

### On Windows:
```bash
python -m hsim.gui.main
```

## Quick Start Guide

### Creating a Simple Model

1. **Add Blocks**: Drag blocks from the Component Palette onto the canvas
   - Start with a Generator (⚡)
   - Add a Server (⚙️)
   - End with a Terminator (🛑)

2. **Connect Blocks**: Right-click on a block → Create Connection → Click target block

3. **Edit Properties**: Select a block to see its properties in the right panel
   - Set service times, distributions, capacities, etc.

4. **Edit FSM** (for agents/servers): Double-click a block with FSM to open the FSM editor

5. **Export**: File → Export Python Code to generate runnable simulation

### Example Workflow

```
1. Drag Generator onto canvas
2. Set interarrival time to 2.0, distribution to "exponential"
3. Drag Server onto canvas
4. Set service time to 3.0, distribution to "constant"
5. Drag Terminator onto canvas
6. Connect: Generator → Server → Terminator
7. Export Python code
8. Run generated code: python exported_model.py
```

## Keyboard Shortcuts

- **Ctrl+N**: New model
- **Ctrl+O**: Open model
- **Ctrl+S**: Save model
- **Ctrl+Shift+S**: Save as
- **Delete**: Delete selected items
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+0**: Reset zoom
- **F5**: Run simulation (TODO)

## File Format

Models are saved as JSON files with `.hsim` extension:

```json
{
  "name": "My Model",
  "version": "1.0",
  "blocks": {
    "block-id": {
      "id": "block-id",
      "type": "generator",
      "name": "Generator 1",
      "position": {"x": 100, "y": 100},
      "size": {"width": 100, "height": 80},
      "properties": {
        "serviceTime": 1.0,
        "serviceTimeFunction": "exponential"
      }
    }
  },
  "connections": [
    {
      "id": "conn-id",
      "from": "block-id-1",
      "to": "block-id-2",
      "label": ""
    }
  ],
  "fsms": {}
}
```

## Architecture

### Components

- **models/**: Data structures for simulation models
  - `model.py`: Core model classes (Block, Connection, FSM, State, Transition)
  - `block_definitions.py`: Metadata for all DES block types

- **views/**: UI components
  - `main_window.py`: Main application window with menus
  - `canvas_widget.py`: Model canvas with drag-drop
  - `palette_widget.py`: Component toolbox
  - `properties_panel.py`: Dynamic property editor
  - `fsm_editor_widget.py`: FSM editor

- **items/**: Qt Graphics Items
  - `block_item.py`: Visual representation of blocks
  - `connection_item.py`: Visual connections between blocks

- **utils/**: Utilities
  - `code_generator.py`: Python code generation

## Supported Block Types

### DES Blocks
- **Generator**: Creates entities at specified intervals
- **Buffer**: Stores entities in a queue (with capacity)
- **Server**: Processes entities for a service time
- **Store**: Immediately forwards entities
- **Terminator**: Destroys entities (exit point)

### Resources
- **Unreliable Machine**: Server with random failures (MTTF/MTTR)
- **Quality Machine**: Server with quality inspection and rejection
- **SU Machine**: Server with setup/operation sequences

### Advanced
- **Assembly**: Joins multiple entities into one

### Agents
- **Custom Agent**: Agent with custom FSM behavior

## TODO / Future Enhancements

- [ ] Complete FSM editor implementation
- [ ] State/Transition graphics items
- [ ] Undo/Redo functionality
- [ ] Clipboard support (copy/paste blocks)
- [ ] Auto-layout algorithms
- [ ] Connection routing improvements
- [ ] Simulation runner with animation
- [ ] Real-time statistics display
- [ ] Gantt chart integration
- [ ] Multi-page models
- [ ] Component grouping
- [ ] Custom block types
- [ ] Plugin system

## Troubleshooting

### Qt Platform Plugin Error (WSL/Linux)

If you get "Could not load the Qt platform plugin" error:

```bash
# Try using offscreen platform
export QT_QPA_PLATFORM=offscreen
python -m hsim.gui.main

# Or install X server dependencies
sudo apt-get install libxcb-cursor0
```

### Import Errors

Make sure hsim is installed:
```bash
pip install -e .
```

## Contributing

This is a work in progress. Main areas needing development:
1. FSM editor completion (state/transition items)
2. Simulation runner integration
3. Enhanced code generation (FSM class definitions)
4. More block types (Frame, Switch, etc.)

## License

Same as hsim framework.
