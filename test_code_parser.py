"""
Test script for CodeParser
"""

from hsim.gui.utils.code_parser import CodeParser

# Test code to parse
test_code = """
from hsim.core.core.env import Environment
from hsim.core.des.pymulate import Generator, Server, Terminator
import numpy as np

def main():
    # Create environment
    env = Environment()

    # Create blocks
    generator_1 = Generator(env, 'Generator 1', serviceTime=1.0, serviceTimeFunction=np.random.exponential)
    server_1 = Server(env, 'Server 1', serviceTime=2.0, serviceTimeFunction=None)
    terminator_1 = Terminator(env, 'Terminator 1')

    # Create connections
    generator_1.connections['next'] = server_1
    server_1.connections['next'] = terminator_1

    # Activate FSMs
    generator_1.activate_fsm()
    server_1.activate_fsm()
    terminator_1.activate_fsm()

    # Run simulation
    env.run(100)

if __name__ == '__main__':
    main()
"""

print("=" * 60)
print("Testing CodeParser")
print("=" * 60)

parser = CodeParser()
model, report = parser.parse_and_report(test_code)

print(f"\n📊 Parse Report:")
print(f"  Blocks found: {report['blocks_found']}")
print(f"  Connections found: {report['connections_found']}")
print(f"  FSMs found: {report['fsms_found']}")

if report['warnings']:
    print(f"\n⚠️  Warnings:")
    for warning in report['warnings']:
        print(f"  - {warning}")

print(f"\n📦 Blocks:")
for block_id, block in model.blocks.items():
    print(f"  • {block.name} ({block.type})")
    print(f"    Position: ({block.position.x}, {block.position.y})")
    if block.properties:
        print(f"    Properties: {block.properties}")

print(f"\n🔗 Connections:")
for conn_id, conn in model.connections.items():
    from_block = model.get_block_by_id(conn.from_block)
    to_block = model.get_block_by_id(conn.to_block)
    if from_block and to_block:
        print(f"  • {from_block.name} → {to_block.name}")

print(f"\n✅ Test completed!")
print(f"   Supported classes: {', '.join(parser.get_supported_classes())}")
