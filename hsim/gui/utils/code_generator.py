"""
Code generator - Generate Python code from simulation model
"""

from hsim.gui.models.model import SimulationModel
from hsim.gui.models.block_definitions import get_block_definition, BlockType


class CodeGenerator:
    """Generate Python code from a simulation model"""

    def __init__(self, model: SimulationModel):
        self.model = model

    def generate(self) -> str:
        """Generate complete Python code"""
        lines = []

        # Header
        lines.append("# Auto-generated simulation code from hsim Model Designer")
        lines.append(f"# Model: {self.model.name}")
        lines.append(f"# Version: {self.model.version}")
        lines.append("")

        # Imports
        lines.extend(self._generate_imports())
        lines.append("")

        # Main function
        lines.append("def main():")
        lines.append("    # Create environment")
        lines.append("    env = Environment()")
        lines.append("")

        # Create blocks
        lines.append("    # Create blocks")
        for block in self.model.blocks.values():
            lines.append(f"    {self._generate_block_code(block)}")
        lines.append("")

        # Create connections
        lines.append("    # Create connections")
        for connection in self.model.connections.values():
            from_block = self.model.get_block_by_id(connection.from_block)
            to_block = self.model.get_block_by_id(connection.to_block)
            if from_block and to_block:
                from_var = self._sanitize_name(from_block.name)
                to_var = self._sanitize_name(to_block.name)
                lines.append(f"    {from_var}.connections['next'] = {to_var}")
        lines.append("")

        # Activate FSMs
        lines.append("    # Activate FSMs")
        for block in self.model.blocks.values():
            block_def = get_block_definition(BlockType(block.type))
            if block_def and block_def.has_fsm:
                var_name = self._sanitize_name(block.name)
                lines.append(f"    {var_name}.activate_fsm()")
        lines.append("")

        # Run simulation
        lines.append("    # Run simulation")
        lines.append("    env.run(100)  # Adjust simulation time as needed")
        lines.append("")

        # Entry point
        lines.append("")
        lines.append("if __name__ == '__main__':")
        lines.append("    main()")

        return "\n".join(lines)

    def _generate_imports(self) -> list[str]:
        """Generate import statements"""
        imports = set()
        imports.add("from hsim.core.core.env import Environment")
        imports.add("import numpy as np")

        # Collect all unique modules needed
        for block in self.model.blocks.values():
            block_def = get_block_definition(BlockType(block.type))
            if block_def and block_def.python_module:
                imports.add(
                    f"from {block_def.python_module} import {block_def.python_class}"
                )

        return sorted(list(imports))

    def _generate_block_code(self, block) -> str:
        """Generate code for a single block"""
        block_def = get_block_definition(BlockType(block.type))
        if not block_def:
            return f"# Unknown block type: {block.type}"

        var_name = self._sanitize_name(block.name)
        class_name = block_def.python_class

        # Build arguments
        args = [f"env", f"'{block.name}'"]

        # Add properties
        for prop_def in block_def.properties:
            value = block.properties.get(prop_def.name, prop_def.default)

            # Handle special cases
            if prop_def.name == "serviceTimeFunction":
                if value == "exponential":
                    args.append("serviceTimeFunction=np.random.exponential")
                elif value == "normal":
                    args.append("serviceTimeFunction=np.random.normal")
                elif value == "uniform":
                    args.append("serviceTimeFunction=np.random.uniform")
                else:
                    args.append("serviceTimeFunction=None")
            elif prop_def.name == "capacity" and value == "inf":
                args.append("capacity=np.inf")
            else:
                # Standard property
                if isinstance(value, str):
                    args.append(f"{prop_def.name}='{value}'")
                else:
                    args.append(f"{prop_def.name}={value}")

        args_str = ", ".join(args)
        return f"{var_name} = {class_name}({args_str})"

    def _sanitize_name(self, name: str) -> str:
        """Convert block name to valid Python variable name"""
        # Replace spaces and special chars with underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        # Ensure it starts with a letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized.lower()
