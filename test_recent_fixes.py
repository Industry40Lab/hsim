#!/usr/bin/env python
"""
Test script to verify recent GUI fixes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hsim.gui.models.block_definitions import BlockType, get_block_definition
from hsim.gui.models.model import SimulationModel, FSM, State, Position, Size, Transition
import uuid

def test_block_definitions():
    """Test that SUMachine and ManualStation are defined"""
    print("Testing Block Definitions...")

    # Test SUMachine
    try:
        su_def = get_block_definition(BlockType.SU_MACHINE)
        print(f"  ✓ SUMachine defined: {su_def.name}")
        assert su_def.has_fsm == True, "SUMachine should have FSM"
        print(f"  ✓ SUMachine has FSM enabled")
    except Exception as e:
        print(f"  ✗ SUMachine test failed: {e}")
        return False

    # Test ManualStation
    try:
        manual_def = get_block_definition(BlockType.MANUAL_STATION)
        print(f"  ✓ ManualStation defined: {manual_def.name}")
        assert manual_def.has_fsm == True, "ManualStation should have FSM"
        print(f"  ✓ ManualStation has FSM enabled")
    except Exception as e:
        print(f"  ✗ ManualStation test failed: {e}")
        return False

    print("  ✅ Block definitions test passed\n")
    return True

def test_fsm_operations():
    """Test FSM state and transition operations"""
    print("Testing FSM Operations...")

    # Create FSM
    fsm = FSM(id=str(uuid.uuid4()), name="TestFSM")

    # Add states
    state1 = State(
        id=str(uuid.uuid4()),
        name="State1",
        position=Position(x=100, y=100),
        size=Size(width=100, height=50),
        color="#6366F1",
        is_initial=True
    )

    state2 = State(
        id=str(uuid.uuid4()),
        name="State2",
        position=Position(x=300, y=100),
        size=Size(width=100, height=50),
        color="#6366F1",
        is_initial=False
    )

    fsm.add_state(state1)
    fsm.add_state(state2)
    print(f"  ✓ Added 2 states to FSM")

    # Add transition
    transition = Transition(
        id=str(uuid.uuid4()),
        from_state=state1.id,
        to_state=state2.id,
        condition="true",
        label=""
    )

    fsm.add_transition(transition)
    print(f"  ✓ Added transition from {state1.name} to {state2.name}")

    # Test state removal
    fsm.remove_state(state2.id)
    print(f"  ✓ Removed {state2.name}")

    if len(fsm.states) == 1:
        print(f"  ✓ FSM now has {len(fsm.states)} state")
    else:
        print(f"  ✗ FSM should have 1 state, has {len(fsm.states)}")
        return False

    # Transition should also be removed
    if len(fsm.transitions) == 0:
        print(f"  ✓ Transition auto-removed with state")
    else:
        print(f"  ✗ Transition should be removed, but {len(fsm.transitions)} remain")
        return False

    print("  ✅ FSM operations test passed\n")
    return True

def test_model_operations():
    """Test model operations"""
    print("Testing Model Operations...")

    model = SimulationModel(name="TestModel")

    # Test get_fsm_by_id exists
    if hasattr(model, 'get_fsm_by_id'):
        print("  ✓ get_fsm_by_id method exists")
    else:
        print("  ✗ get_fsm_by_id method NOT found")
        return False

    # Test connections structure
    if isinstance(model.connections, dict):
        print("  ✓ Connections is a dict")
    else:
        print(f"  ✗ Connections should be dict, is {type(model.connections)}")
        return False

    # Test get_fsm_by_id functionality
    fsm = FSM(id="test-fsm-123", name="TestFSM")
    model.add_fsm(fsm)

    retrieved_fsm = model.get_fsm_by_id("test-fsm-123")
    if retrieved_fsm and retrieved_fsm.id == "test-fsm-123":
        print("  ✓ get_fsm_by_id() retrieves FSM correctly")
    else:
        print("  ✗ get_fsm_by_id() failed to retrieve FSM")
        return False

    print("  ✅ Model operations test passed\n")
    return True

def test_defensive_block_creation():
    """Test defensive programming for block creation"""
    print("Testing Defensive Block Creation...")

    # Test BlockType enum validation
    try:
        valid_type = BlockType("generator")
        print("  ✓ Valid BlockType 'generator' works")
    except ValueError:
        print("  ✗ Valid BlockType 'generator' failed")
        return False

    # Test invalid block type handling
    try:
        invalid_type = BlockType("InvalidBlock")
        print("  ✗ Should have raised ValueError for invalid block type")
        return False
    except ValueError:
        print("  ✓ Invalid block type raises ValueError as expected")

    # Test get_block_definition with valid type
    try:
        definition = get_block_definition(BlockType.GENERATOR)
        if definition:
            print("  ✓ get_block_definition returns valid definition")
        else:
            print("  ✗ get_block_definition returned None")
            return False
    except:
        print("  ✗ get_block_definition failed for valid type")
        return False

    print("  ✅ Defensive block creation test passed\n")
    return True

def main():
    print("=" * 60)
    print("RECENT GUI FIXES VERIFICATION TEST")
    print("=" * 60)
    print()

    tests = [
        ("Block Definitions (SUMachine/ManualStation)", test_block_definitions),
        ("FSM Operations (state/transition add/remove)", test_fsm_operations),
        ("Model Operations (get_fsm_by_id, connections)", test_model_operations),
        ("Defensive Block Creation", test_defensive_block_creation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(r[1] for r in results)
    print()
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print()
        print("Recent fixes verified:")
        print("  1. SUMachine and ManualStation block definitions ✓")
        print("  2. FSM state and transition operations ✓")
        print("  3. Model.get_fsm_by_id() method ✓")
        print("  4. Connections dict structure ✓")
        print("  5. Defensive error handling ✓")
        print()
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
