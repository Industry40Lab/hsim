"""
Code Parser - Parse Python simulation code and create GUI model
"""

import ast
from typing import Dict, List, Optional, Set
from hsim.gui.models.model import SimulationModel, Block, Connection, Position
from hsim.gui.models.block_definitions import BlockType


class CodeParser:
    """Parse Python simulation code and create GUI model"""

    # Map Python class names to block types
    CLASS_TO_TYPE = {
        'Generator': 'generator',
        'Server': 'server',
        'Buffer': 'buffer',
        'EmptyBuffer': 'empty_buffer',
        'Store': 'store',
        'Terminator': 'terminator',
        'Assembly': 'assembly',
        'UnreliableMachine': 'unreliable_machine',
        'QualityMachine': 'quality_machine',
        'SUMachine': 'su_machine',
        'ManualStation': 'manual_station',
        'Operator': 'operator',
        'Switch': 'switch',
        'Agent': 'agent',
    }

    def __init__(self):
        self.model = SimulationModel()
        self.block_vars = {}  # var_name -> Block
        self.current_x = 100
        self.current_y = 100
        self.spacing_x = 180
        self.spacing_y = 150
        self.max_x = 900

    def parse_file(self, filepath: str) -> SimulationModel:
        """Parse Python file and create model"""
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        return self.parse_code(code)

    def parse_code(self, code: str) -> SimulationModel:
        """Parse Python code and create model

        Args:
            code: Python source code string

        Returns:
            SimulationModel with parsed blocks and connections
        """
        try:
            tree = ast.parse(code)

            # Find main() function
            main_func = self._find_main_function(tree)
            if not main_func:
                print("Warning: No main() function found")
                # Try to parse module-level statements
                self._parse_statements(tree.body)
            else:
                # Parse main function body
                self._parse_statements(main_func.body)

            return self.model

        except SyntaxError as e:
            print(f"Syntax error parsing code: {e}")
            return self.model
        except Exception as e:
            print(f"Error parsing code: {e}")
            import traceback
            traceback.print_exc()
            return self.model

    def _find_main_function(self, tree: ast.Module) -> Optional[ast.FunctionDef]:
        """Find main() function in AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'main':
                return node
        return None

    def _parse_statements(self, statements: List[ast.stmt]):
        """Parse list of statements"""
        for stmt in statements:
            if isinstance(stmt, ast.Assign):
                self._parse_assignment(stmt)
            elif isinstance(stmt, ast.Expr):
                self._parse_expression(stmt)

    def _parse_assignment(self, stmt: ast.Assign):
        """Parse assignment statement (block creation or connection)"""
        if not stmt.targets or len(stmt.targets) != 1:
            return

        target = stmt.targets[0]

        # Handle simple variable assignment: var = Constructor(...)
        if isinstance(target, ast.Name):
            var_name = target.id

            # Skip environment creation
            if var_name == 'env':
                return

            # Check if it's a block creation
            if isinstance(stmt.value, ast.Call):
                self._parse_block_creation(var_name, stmt.value)

        # Handle attribute assignment for connections: block.connections['next'] = other
        elif isinstance(target, ast.Subscript):
            self._parse_connection_assignment(target, stmt.value)

    def _parse_block_creation(self, var_name: str, call_node: ast.Call):
        """Parse block constructor call"""
        # Get class name
        class_name = None
        if isinstance(call_node.func, ast.Name):
            class_name = call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            class_name = call_node.func.attr

        if not class_name or class_name not in self.CLASS_TO_TYPE:
            return

        block_type = self.CLASS_TO_TYPE[class_name]

        # Extract block name from arguments
        # Typical: Block(env, 'Block Name', ...)
        block_name = var_name
        if len(call_node.args) >= 2:
            name_arg = call_node.args[1]
            if isinstance(name_arg, ast.Constant):
                block_name = str(name_arg.value)
            elif isinstance(name_arg, ast.Str):  # Python 3.7 compatibility
                block_name = name_arg.s

        # Extract properties from keyword arguments
        properties = {}
        for keyword in call_node.keywords:
            prop_name = keyword.arg
            value = self._extract_value(keyword.value)
            if value is not None:
                # Handle special cases
                if prop_name == 'serviceTimeFunction':
                    # Extract function name from attribute
                    if isinstance(keyword.value, ast.Attribute):
                        if isinstance(keyword.value.value, ast.Attribute):
                            # np.random.exponential
                            properties[prop_name] = keyword.value.attr
                    else:
                        properties[prop_name] = None
                else:
                    properties[prop_name] = value

        # Create block with auto-layout
        block = Block(
            type=block_type,
            name=block_name,
            position=Position(self.current_x, self.current_y),
            properties=properties
        )

        self.block_vars[var_name] = block
        self.model.add_block(block)

        # Update position for next block
        self.current_x += self.spacing_x
        if self.current_x > self.max_x:
            self.current_x = 100
            self.current_y += self.spacing_y

    def _parse_connection_assignment(self, target: ast.Subscript, value: ast.expr):
        """Parse connection assignment: block.connections['next'] = other_block"""
        # Get source block variable
        if not isinstance(target.value, ast.Attribute):
            return

        if not isinstance(target.value.value, ast.Name):
            return

        from_var = target.value.value.id

        # Get destination block variable
        to_var = None
        if isinstance(value, ast.Name):
            to_var = value.id

        if not from_var or not to_var:
            return

        # Create connection
        from_block = self.block_vars.get(from_var)
        to_block = self.block_vars.get(to_var)

        if from_block and to_block:
            connection = Connection(
                from_block=from_block.id,
                to_block=to_block.id
            )
            self.model.add_connection(connection)

    def _parse_expression(self, stmt: ast.Expr):
        """Parse expression statement (method calls)"""
        if isinstance(stmt.value, ast.Call):
            # Handle method calls like block.activate_fsm()
            # For now, we skip these as they're runtime behavior
            pass

    def _extract_value(self, node: ast.expr):
        """Extract Python value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7 compatibility
            return node.n
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            return node.s
        elif isinstance(node, ast.NameConstant):  # Python 3.7 compatibility
            return node.value
        elif isinstance(node, ast.Name):
            if node.id == 'None':
                return None
            elif node.id == 'True':
                return True
            elif node.id == 'False':
                return False
        elif isinstance(node, ast.Attribute):
            # Handle np.inf, etc.
            if isinstance(node.value, ast.Name):
                if node.value.id == 'np' and node.attr == 'inf':
                    return 'inf'
        return None

    def parse_and_report(self, code: str) -> tuple[SimulationModel, Dict[str, any]]:
        """Parse code and return model plus report

        Returns:
            (model, report_dict)
            report_dict contains: {
                'blocks_found': int,
                'connections_found': int,
                'fsms_found': int,
                'warnings': List[str]
            }
        """
        model = self.parse_code(code)

        report = {
            'blocks_found': len(model.blocks),
            'connections_found': len(model.connections),
            'fsms_found': len(model.fsms),
            'warnings': []
        }

        # Check for issues
        if report['blocks_found'] == 0:
            report['warnings'].append("No simulation blocks found in code")

        if report['blocks_found'] > 0 and report['connections_found'] == 0:
            report['warnings'].append("Blocks found but no connections detected")

        return model, report

    def get_supported_classes(self) -> List[str]:
        """Get list of supported Python classes for import"""
        return list(self.CLASS_TO_TYPE.keys())
