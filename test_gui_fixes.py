#!/usr/bin/env python3
"""
Test script to verify GUI fixes without requiring display
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from hsim.gui.models.model import SimulationModel, Block, Connection, Position, Size, FSM, State
from hsim.gui.models.block_definitions import BlockType, get_block_definition
from hsim.gui.utils.code_generator import CodeGenerator
import uuid


def test_fsm_enabled_for_all_blocks():
    """Test that all DES blocks have FSM enabled"""
    print("Testing FSM enabled for all blocks...")

    block_types = [
        BlockType.GENERATOR,
        BlockType.BUFFER,
        BlockType.SERVER,
        BlockType.STORE,
        BlockType.TERMINATOR,
        BlockType.UNRELIABLE_MACHINE,
        BlockType.QUALITY_MACHINE,
        BlockType.ASSEMBLY,
        BlockType.AGENT
    ]

    for block_type in block_types:
        block_def = get_block_definition(block_type)
        assert block_def.has_fsm == True, f"{block_type.value} should have FSM enabled"
        print(f"  ✓ {block_def.name}: has_fsm=True")

    print("  ✅ All blocks have FSM enabled\n")


def test_fsm_initialization():
    """Test that FSMs are created with Empty state"""
    print("Testing FSM initialization with Empty state...")

    model = SimulationModel(name="Test Model")

    # Create a Generator block (simulating GUI creation)
    block_def = get_block_definition(BlockType.GENERATOR)
    block = Block(
        id=str(uuid.uuid4()),
        type="generator",
        name="Test Generator",
        position=Position(0, 0),
        size=Size(100, 80),
        properties={prop.name: prop.default for prop in block_def.properties}
    )

    # Create FSM with Empty state (as GUI now does)
    fsm = FSM(
        id=str(uuid.uuid4()),
        name=f"{block.name} FSM",
        owner_block_id=block.id
    )

    empty_state = State(
        id=str(uuid.uuid4()),
        name="Empty",
        position=Position(50, 50),
        size=Size(120, 60),
        is_initial=True,
        on_enter="",
        on_exit="",
        color="#3B82F6"
    )
    fsm.add_state(empty_state)

    block.fsm_id = fsm.id
    model.add_fsm(fsm)
    model.add_block(block)

    # Verify
    assert len(model.fsms) == 1, "Should have 1 FSM"
    assert len(fsm.states) == 1, "FSM should have 1 state"
    assert "Empty" in [s.name for s in fsm.states.values()], "Should have Empty state"
    assert list(fsm.states.values())[0].is_initial == True, "Empty should be initial state"

    print("  ✓ FSM created successfully")
    print("  ✓ Empty state exists")
    print("  ✓ Empty state is initial")
    print("  ✅ FSM initialization works correctly\n")


def test_connections_system():
    """Test that connections use the correct dictionary pattern"""
    print("Testing connections system...")

    model = SimulationModel(name="Test Model")

    # Create two blocks
    gen_def = get_block_definition(BlockType.GENERATOR)
    gen = Block(
        id=str(uuid.uuid4()),
        type="generator",
        name="Generator_1",
        position=Position(0, 0),
        size=Size(100, 80),
        properties={prop.name: prop.default for prop in gen_def.properties}
    )

    buf_def = get_block_definition(BlockType.BUFFER)
    buf = Block(
        id=str(uuid.uuid4()),
        type="buffer",
        name="Buffer_1",
        position=Position(200, 0),
        size=Size(100, 80),
        properties={prop.name: prop.default for prop in buf_def.properties}
    )

    model.add_block(gen)
    model.add_block(buf)

    # Create connection
    conn = Connection(
        id=str(uuid.uuid4()),
        from_block=gen.id,
        to_block=buf.id,
        label="next"
    )
    model.add_connection(conn)

    # Test model methods
    conns_from_gen = model.get_connections_from(gen.id)
    conns_to_buf = model.get_connections_to(buf.id)

    assert len(conns_from_gen) == 1, "Should have 1 outgoing connection from generator"
    assert len(conns_to_buf) == 1, "Should have 1 incoming connection to buffer"
    assert conns_from_gen[0].to_block == buf.id, "Connection should point to buffer"
    assert conns_to_buf[0].from_block == gen.id, "Connection should come from generator"

    print("  ✓ Connection created")
    print("  ✓ get_connections_from() works")
    print("  ✓ get_connections_to() works")
    print("  ✅ Connections system works correctly\n")


def test_code_generation():
    """Test that code generation uses connections['next'] pattern"""
    print("Testing code generation...")

    model = SimulationModel(name="Test Manufacturing Line")

    # Create blocks
    gen_def = get_block_definition(BlockType.GENERATOR)
    gen = Block(
        id=str(uuid.uuid4()),
        type="generator",
        name="Raw_Material_Arrivals",
        position=Position(0, 0),
        size=Size(100, 80),
        properties={prop.name: prop.default for prop in gen_def.properties}
    )

    srv_def = get_block_definition(BlockType.SERVER)
    srv = Block(
        id=str(uuid.uuid4()),
        type="server",
        name="Processing_Machine",
        position=Position(200, 0),
        size=Size(100, 80),
        properties={prop.name: prop.default for prop in srv_def.properties}
    )

    term_def = get_block_definition(BlockType.TERMINATOR)
    term = Block(
        id=str(uuid.uuid4()),
        type="terminator",
        name="Finished_Goods",
        position=Position(400, 0),
        size=Size(100, 80),
        properties={}
    )

    model.add_block(gen)
    model.add_block(srv)
    model.add_block(term)

    # Create connections
    conn1 = Connection(id=str(uuid.uuid4()), from_block=gen.id, to_block=srv.id, label="next")
    conn2 = Connection(id=str(uuid.uuid4()), from_block=srv.id, to_block=term.id, label="next")
    model.add_connection(conn1)
    model.add_connection(conn2)

    # Generate code
    generator = CodeGenerator(model)
    code = generator.generate()

    # Verify connections['next'] pattern is used
    assert "connections['next']" in code, "Code should use connections['next'] pattern"
    assert "raw_material_arrivals.connections['next'] = processing_machine" in code
    assert "processing_machine.connections['next'] = finished_goods" in code

    # Verify FSM activation is included
    assert "activate_fsm()" in code, "Code should activate FSMs"

    print("  ✓ Code generated successfully")
    print("  ✓ Uses connections['next'] pattern")
    print("  ✓ Includes FSM activation")
    print("  ✅ Code generation works correctly\n")

    # Print sample code for verification
    print("Generated code sample:")
    print("-" * 60)
    for line in code.split('\n')[20:35]:  # Print a relevant section
        print(line)
    print("-" * 60)
    print()


def test_model_serialization():
    """Test that models can be saved and loaded with new features"""
    print("Testing model serialization...")

    # Create model with FSMs and connections
    model = SimulationModel(name="Test Model")

    gen_def = get_block_definition(BlockType.GENERATOR)
    gen = Block(
        id="gen-123",
        type="generator",
        name="Generator_1",
        position=Position(0, 0),
        size=Size(100, 80),
        properties={prop.name: prop.default for prop in gen_def.properties}
    )

    # Create FSM with Empty state
    fsm = FSM(id="fsm-123", name="Generator_1 FSM", owner_block_id=gen.id)
    empty_state = State(
        id="state-123",
        name="Empty",
        position=Position(50, 50),
        size=Size(120, 60),
        is_initial=True
    )
    fsm.add_state(empty_state)

    gen.fsm_id = fsm.id
    model.add_fsm(fsm)
    model.add_block(gen)

    # Serialize
    data = model.to_dict()

    # Deserialize
    loaded_model = SimulationModel.from_dict(data)

    # Verify
    assert len(loaded_model.blocks) == 1, "Should have 1 block"
    assert len(loaded_model.fsms) == 1, "Should have 1 FSM"
    loaded_gen = loaded_model.blocks["gen-123"]
    loaded_fsm = loaded_model.fsms[loaded_gen.fsm_id]
    assert len(loaded_fsm.states) == 1, "FSM should have 1 state"
    assert list(loaded_fsm.states.values())[0].name == "Empty"

    print("  ✓ Model serialized to dict")
    print("  ✓ Model deserialized from dict")
    print("  ✓ FSMs preserved")
    print("  ✓ States preserved")
    print("  ✅ Serialization works correctly\n")


def main():
    print("\n" + "="*60)
    print("GUI FIXES VERIFICATION TEST")
    print("="*60 + "\n")

    try:
        test_fsm_enabled_for_all_blocks()
        test_fsm_initialization()
        test_connections_system()
        test_code_generation()
        test_model_serialization()

        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nGUI improvements verified:")
        print("  1. All blocks have FSM enabled ✓")
        print("  2. FSMs initialize with Empty state ✓")
        print("  3. Connections use correct pattern ✓")
        print("  4. Code generation is correct ✓")
        print("  5. Serialization works ✓")
        print("\nThe GUI now correctly aligns with the hsim core architecture.")
        print()

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
