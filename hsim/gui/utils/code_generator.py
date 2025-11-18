"""
Code generator - Generate Python code from simulation model
"""

from hsim.gui.models.model import SimulationModel
from hsim.gui.models.block_definitions import get_block_definition, BlockType


class CodeGenerator:
    """Generate Python code from a simulation model"""

    def __init__(self, model: SimulationModel):
        self.model = model

    def validate_model(self) -> list[str]:
        """Validate model before code generation. Returns list of errors."""
        errors = []

        # Check for orphaned connections
        for connection in self.model.connections.values():
            from_block = self.model.get_block_by_id(connection.from_block)
            to_block = self.model.get_block_by_id(connection.to_block)
            if not from_block:
                errors.append(f"Connection {connection.id}: from_block '{connection.from_block}' not found")
            if not to_block:
                errors.append(f"Connection {connection.id}: to_block '{connection.to_block}' not found")

        # Check for FSMs with no initial state
        for fsm in self.model.fsms.values():
            if fsm.states:
                has_initial = any(state.is_initial for state in fsm.states.values())
                if not has_initial:
                    errors.append(f"FSM '{fsm.name}': No initial state defined")

        # Check for transitions with invalid states
        for fsm in self.model.fsms.values():
            for transition in fsm.transitions:
                if transition.from_state not in fsm.states:
                    errors.append(f"FSM '{fsm.name}': Transition from unknown state '{transition.from_state}'")
                if transition.to_state not in fsm.states:
                    errors.append(f"FSM '{fsm.name}': Transition to unknown state '{transition.to_state}'")

        # Check for circular parent-child relationships
        for block in self.model.blocks.values():
            if self._has_circular_hierarchy(block.id):
                errors.append(f"Block '{block.name}': Circular hierarchy detected")

        return errors

    def _has_circular_hierarchy(self, block_id: str, visited: set = None) -> bool:
        """Check if a block has circular parent-child relationship"""
        if visited is None:
            visited = set()

        if block_id in visited:
            return True

        visited.add(block_id)
        block = self.model.get_block_by_id(block_id)
        if block and block.parent_id:
            return self._has_circular_hierarchy(block.parent_id, visited)

        return False

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

        # Generate FSM classes if any custom FSMs exist
        fsm_code = self._generate_fsm_classes()
        if fsm_code:
            lines.extend(fsm_code)
            lines.append("")

        # Main function
        lines.append("def main():")
        lines.append("    # Create environment")
        lines.append("    env = Environment()")
        lines.append("")

        # Create blocks (only top-level, no parent)
        lines.append("    # Create blocks")
        for block in self.model.blocks.values():
            if not block.parent_id:  # Only top-level blocks
                lines.extend(self._generate_block_code(block, indent=1))
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

    def _generate_fsm_classes(self) -> list[str]:
        """Generate FSM class definitions for blocks with custom FSMs"""
        lines = []

        # Check if any blocks have custom FSMs with states
        has_custom_fsms = any(
            fsm.states for fsm in self.model.fsms.values()
        )

        if not has_custom_fsms:
            return lines

        lines.append("# FSM Classes")
        lines.append("from hsim.core.fsm.fsm import FSM, State, Transition")
        lines.append("")

        # Generate FSM class for each block that has states
        for fsm in self.model.fsms.values():
            if not fsm.states:
                continue

            fsm_class_name = self._sanitize_name(fsm.name).title().replace('_', '')
            lines.append(f"class {fsm_class_name}(FSM):")
            lines.append("    \"\"\"Auto-generated FSM class\"\"\"")
            lines.append("")
            lines.append("    def __init__(self, owner):")
            lines.append("        super().__init__(owner)")
            lines.append("")

            # Add states
            for state in fsm.states.values():
                state_var = self._sanitize_name(state.name)
                lines.append(f"        # State: {state.name}")
                lines.append(f"        {state_var} = State()")
                lines.append(f"        {state_var}.name = '{state.name}'")

                if state.on_enter:
                    lines.append(f"        # On Enter:")
                    for enter_line in state.on_enter.split('\n'):
                        if enter_line.strip():
                            lines.append(f"        #   {enter_line}")

                if state.on_exit:
                    lines.append(f"        # On Exit:")
                    for exit_line in state.on_exit.split('\n'):
                        if exit_line.strip():
                            lines.append(f"        #   {exit_line}")

                lines.append(f"        self.add_state({state_var})")

                if state.is_initial:
                    lines.append(f"        self.initial_state = {state_var}")

                lines.append("")

            # Add transitions
            if fsm.transitions:
                lines.append("        # Transitions")
                for transition in fsm.transitions:
                    from_state = fsm.states.get(transition.from_state)
                    to_state = fsm.states.get(transition.to_state)
                    if from_state and to_state:
                        from_var = self._sanitize_name(from_state.name)
                        to_var = self._sanitize_name(to_state.name)
                        cond = f"'{transition.condition}'" if transition.condition else "None"
                        lines.append(f"        # {from_state.name} → {to_state.name}")
                        if transition.condition:
                            lines.append(f"        #   Condition: {transition.condition}")
                        lines.append(f"        self.add_transition(Transition({from_var}, {to_var}, condition={cond}))")

            lines.append("")

        return lines

    def _generate_block_code(self, block, indent: int = 1) -> list[str]:
        """Generate code for a single block and its children (returns list of lines)"""
        lines = []
        indent_str = "    " * indent

        block_def = get_block_definition(BlockType(block.type))
        if not block_def:
            lines.append(f"{indent_str}# Unknown block type: {block.type}")
            return lines

        var_name = self._sanitize_name(block.name)
        class_name = block_def.python_class

        # Build arguments
        args = ["env", f"'{block.name}'"]

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
        lines.append(f"{indent_str}{var_name} = {class_name}({args_str})")

        # Generate child blocks (hierarchical agents)
        if block.children:
            lines.append(f"{indent_str}# Sub-agents of {block.name}")
            for child_id in block.children:
                child_block = self.model.get_block_by_id(child_id)
                if child_block:
                    child_lines = self._generate_block_code(child_block, indent=indent)
                    lines.extend(child_lines)

        return lines

    def _sanitize_name(self, name: str) -> str:
        """Convert block name to valid Python variable name"""
        # Replace spaces and special chars with underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        # Ensure it starts with a letter or underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized.lower()
