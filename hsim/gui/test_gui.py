#!/usr/bin/env python3
"""
Test script for hsim GUI - validates model without requiring display
"""

import sys
import uuid
from hsim.gui.models.model import (
    SimulationModel, Block, Connection, Position, Size, FSM, State, Transition
)
from hsim.gui.models.block_definitions import (
    BlockType, get_block_definition, get_blocks_by_category
)
from hsim.gui.utils.code_generator import CodeGenerator


def test_block_definitions():
    """Test block definitions"""
    print("Testing block definitions...")

    # Test getting block definition
    server_def = get_block_definition(BlockType.SERVER)
    assert server_def is not None
    assert server_def.name == "Server"
    assert server_def.color == "#F59E0B"
    print(f"✓ Server definition: {server_def.name} ({server_def.icon})")

    # Test getting blocks by category
    categories = get_blocks_by_category()
    assert "DES Blocks" in categories
    assert len(categories["DES Blocks"]) >= 5
    print(f"✓ Found {len(categories)} categories")

    for category, blocks in categories.items():
        print(f"  - {category}: {len(blocks)} blocks")

    print()


def test_model_creation():
    """Test creating a simulation model"""
    print("Testing model creation...")

    # Create model
    model = SimulationModel(name="Test Model")

    # Create a Generator
    gen_block = Block(
        id=str(uuid.uuid4()),
        type=BlockType.GENERATOR.value,
        name="Generator 1",
        position=Position(100, 100),
        size=Size(100, 80),
        properties={"serviceTime": 1.0, "serviceTimeFunction": "exponential"}
    )
    model.add_block(gen_block)
    print(f"✓ Created Generator: {gen_block.name}")

    # Create a Server
    server_block = Block(
        id=str(uuid.uuid4()),
        type=BlockType.SERVER.value,
        name="Server 1",
        position=Position(300, 100),
        size=Size(100, 80),
        properties={"serviceTime": 2.0, "serviceTimeFunction": "constant"}
    )
    model.add_block(server_block)
    print(f"✓ Created Server: {server_block.name}")

    # Create a Terminator
    term_block = Block(
        id=str(uuid.uuid4()),
        type=BlockType.TERMINATOR.value,
        name="Terminator 1",
        position=Position(500, 100),
        size=Size(100, 80),
        properties={}
    )
    model.add_block(term_block)
    print(f"✓ Created Terminator: {term_block.name}")

    # Create connections
    conn1 = Connection(
        id=str(uuid.uuid4()),
        from_block=gen_block.id,
        to_block=server_block.id,
        label=""
    )
    model.add_connection(conn1)
    print(f"✓ Connected {gen_block.name} → {server_block.name}")

    conn2 = Connection(
        id=str(uuid.uuid4()),
        from_block=server_block.id,
        to_block=term_block.id,
        label=""
    )
    model.add_connection(conn2)
    print(f"✓ Connected {server_block.name} → {term_block.name}")

    print(f"✓ Model has {len(model.blocks)} blocks and {len(model.connections)} connections")
    print()

    return model


def test_serialization(model):
    """Test model serialization"""
    print("Testing serialization...")

    # Serialize to dict
    data = model.to_dict()
    assert data["name"] == "Test Model"
    assert len(data["blocks"]) == 3
    assert len(data["connections"]) == 2
    print(f"✓ Serialized to dict: {len(data['blocks'])} blocks")

    # Deserialize from dict
    model2 = SimulationModel.from_dict(data)
    assert model2.name == model.name
    assert len(model2.blocks) == len(model.blocks)
    assert len(model2.connections) == len(model.connections)
    print(f"✓ Deserialized from dict: {len(model2.blocks)} blocks")

    print()


def test_code_generation(model):
    """Test Python code generation"""
    print("Testing code generation...")

    generator = CodeGenerator(model)
    code = generator.generate()

    # Check code contains expected elements
    assert "from hsim.core.core.env import Environment" in code
    assert "def main():" in code
    assert "env = Environment()" in code
    assert "generator_1 = Generator" in code
    assert "server_1 = Server" in code
    assert "terminator_1 = Terminator" in code
    assert "generator_1.connections['next'] = server_1" in code

    print("✓ Generated Python code:")
    print("-" * 60)
    print(code)
    print("-" * 60)
    print()


def test_fsm():
    """Test FSM creation"""
    print("Testing FSM...")

    # Create FSM
    fsm = FSM(id=str(uuid.uuid4()), name="Test FSM")

    # Add states
    state1 = State(
        id=str(uuid.uuid4()),
        name="Idle",
        position=Position(100, 100),
        is_initial=True
    )
    fsm.add_state(state1)
    print(f"✓ Added state: {state1.name}")

    state2 = State(
        id=str(uuid.uuid4()),
        name="Working",
        position=Position(300, 100)
    )
    fsm.add_state(state2)
    print(f"✓ Added state: {state2.name}")

    # Add transition
    trans = Transition(
        id=str(uuid.uuid4()),
        from_state=state1.id,
        to_state=state2.id,
        label="start",
        transition_type="message"
    )
    fsm.add_transition(trans)
    print(f"✓ Added transition: {state1.name} → {state2.name}")

    # Serialize
    fsm_data = fsm.to_dict()
    assert len(fsm_data["states"]) == 2
    assert len(fsm_data["transitions"]) == 1
    print(f"✓ FSM serialized: {len(fsm_data['states'])} states, {len(fsm_data['transitions'])} transitions")

    # Deserialize
    fsm2 = FSM.from_dict(fsm_data)
    assert len(fsm2.states) == 2
    assert len(fsm2.transitions) == 1
    print(f"✓ FSM deserialized successfully")

    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("hsim GUI Model Tests")
    print("=" * 60)
    print()

    try:
        test_block_definitions()
        model = test_model_creation()
        test_serialization(model)
        test_code_generation(model)
        test_fsm()

        print("=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
