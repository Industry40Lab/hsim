#!/usr/bin/env python3
"""
Demo script - Creates a sample simulation model
"""

import json
import uuid
from hsim.gui.models.model import (
    SimulationModel, Block, Connection, Position, Size, FSM, State, Transition
)
from hsim.gui.models.block_definitions import BlockType
from hsim.gui.utils.code_generator import CodeGenerator


def create_demo_model():
    """Create a demo manufacturing line model"""
    model = SimulationModel(name="Manufacturing Line Demo")

    # Create Generator (raw material arrivals)
    gen = Block(
        id=str(uuid.uuid4()),
        type=BlockType.GENERATOR.value,
        name="Raw Material Arrivals",
        position=Position(100, 200),
        size=Size(120, 100),
        properties={
            "serviceTime": 5.0,
            "serviceTimeFunction": "exponential"
        }
    )
    model.add_block(gen)

    # Create Buffer (input queue)
    buffer1 = Block(
        id=str(uuid.uuid4()),
        type=BlockType.BUFFER.value,
        name="Input Queue",
        position=Position(300, 200),
        size=Size(120, 100),
        properties={
            "capacity": "10",
            "queueType": "standard"
        }
    )
    model.add_block(buffer1)

    # Create Server (processing machine)
    server1 = Block(
        id=str(uuid.uuid4()),
        type=BlockType.SERVER.value,
        name="Processing Machine",
        position=Position(500, 200),
        size=Size(120, 100),
        properties={
            "serviceTime": 8.0,
            "serviceTimeFunction": "normal"
        }
    )

    # Create FSM for server
    fsm = FSM(
        id=str(uuid.uuid4()),
        name="Processing Machine FSM",
        owner_block_id=server1.id
    )

    # Add states
    starving = State(
        id=str(uuid.uuid4()),
        name="Starving",
        position=Position(100, 100),
        is_initial=True,
        color="#EF4444"
    )
    fsm.add_state(starving)

    working = State(
        id=str(uuid.uuid4()),
        name="Working",
        position=Position(300, 100),
        color="#10B981"
    )
    fsm.add_state(working)

    blocking = State(
        id=str(uuid.uuid4()),
        name="Blocking",
        position=Position(500, 100),
        color="#F59E0B"
    )
    fsm.add_state(blocking)

    # Add transitions
    t1 = Transition(
        id=str(uuid.uuid4()),
        from_state=starving.id,
        to_state=working.id,
        label="part_arrives",
        transition_type="message"
    )
    fsm.add_transition(t1)

    t2 = Transition(
        id=str(uuid.uuid4()),
        from_state=working.id,
        to_state=blocking.id,
        label="processing_done",
        transition_type="timeout"
    )
    fsm.add_transition(t2)

    t3 = Transition(
        id=str(uuid.uuid4()),
        from_state=blocking.id,
        to_state=starving.id,
        label="part_forwarded",
        transition_type="event"
    )
    fsm.add_transition(t3)

    server1.fsm_id = fsm.id
    model.add_fsm(fsm)
    model.add_block(server1)

    # Create Quality Inspection
    quality = Block(
        id=str(uuid.uuid4()),
        type=BlockType.QUALITY_MACHINE.value,
        name="Quality Inspection",
        position=Position(700, 200),
        size=Size(120, 100),
        properties={
            "serviceTime": 2.0,
            "serviceTimeFunction": "constant",
            "quality_threshold": 0.95
        }
    )
    model.add_block(quality)

    # Create Buffer (output queue)
    buffer2 = Block(
        id=str(uuid.uuid4()),
        type=BlockType.BUFFER.value,
        name="Output Queue",
        position=Position(900, 200),
        size=Size(120, 100),
        properties={
            "capacity": "inf",
            "queueType": "standard"
        }
    )
    model.add_block(buffer2)

    # Create Terminator (finished goods)
    term = Block(
        id=str(uuid.uuid4()),
        type=BlockType.TERMINATOR.value,
        name="Finished Goods",
        position=Position(1100, 200),
        size=Size(120, 100),
        properties={}
    )
    model.add_block(term)

    # Create connections
    connections = [
        (gen.id, buffer1.id, ""),
        (buffer1.id, server1.id, ""),
        (server1.id, quality.id, ""),
        (quality.id, buffer2.id, "pass"),
        (buffer2.id, term.id, ""),
    ]

    for from_id, to_id, label in connections:
        conn = Connection(
            id=str(uuid.uuid4()),
            from_block=from_id,
            to_block=to_id,
            label=label
        )
        model.add_connection(conn)

    return model


def main():
    """Create and save demo model"""
    print("Creating demo manufacturing line model...")

    model = create_demo_model()

    # Save as .hsim file
    output_file = "demo_manufacturing_line.hsim"
    with open(output_file, 'w') as f:
        json.dump(model.to_dict(), f, indent=2)
    print(f"✓ Saved model to {output_file}")

    # Generate Python code
    generator = CodeGenerator(model)
    code = generator.generate()

    code_file = "demo_manufacturing_line.py"
    with open(code_file, 'w') as f:
        f.write(code)
    print(f"✓ Generated Python code to {code_file}")

    print("\nModel Summary:")
    print(f"  - Name: {model.name}")
    print(f"  - Blocks: {len(model.blocks)}")
    print(f"  - Connections: {len(model.connections)}")
    print(f"  - FSMs: {len(model.fsms)}")

    print("\nBlocks:")
    for block in model.blocks.values():
        print(f"  - {block.name} ({block.type})")

    print("\nTo open in GUI:")
    print(f"  python -m hsim.gui.main")
    print(f"  Then: File → Open → {output_file}")

    print("\nTo run simulation:")
    print(f"  python {code_file}")


if __name__ == "__main__":
    main()
