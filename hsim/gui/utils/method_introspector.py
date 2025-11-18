"""
Method Introspector - Extract methods and attributes from Python classes
"""

import inspect
from typing import Dict, List, Optional, Any
from hsim.gui.models.block_definitions import get_block_definition, BlockType


class MethodIntrospector:
    """Introspect Python classes to extract methods and attributes"""

    @staticmethod
    def get_class_methods(block_type: str) -> Dict[str, dict]:
        """Get all methods for a block type

        Args:
            block_type: Block type string (e.g., 'generator', 'server')

        Returns:
            Dictionary of methods:
            {
                'method_name': {
                    'signature': 'def method_name(self, arg1, arg2)',
                    'docstring': 'Method description',
                    'source': 'def method_name(self, arg1, arg2):\\n    ...',
                    'is_public': True,
                    'parameters': ['self', 'arg1', 'arg2'],
                    'return_annotation': <type>
                }
            }
        """
        try:
            block_def = get_block_definition(BlockType(block_type))
            if not block_def or not block_def.python_module:
                return {}

            # Import the class
            module_path = block_def.python_module
            class_name = block_def.python_class

            try:
                # Import module dynamically
                parts = module_path.split('.')
                module = __import__(module_path, fromlist=[parts[-1]])
                cls = getattr(module, class_name)

                methods = {}

                # Get all methods including inherited ones
                for name, method in inspect.getmembers(cls):
                    # Skip non-methods
                    if not (inspect.ismethod(method) or inspect.isfunction(method)):
                        continue

                    # Skip special methods except important ones
                    if name.startswith('__'):
                        if name not in ['__init__', '__str__', '__repr__']:
                            continue

                    # Get method details
                    try:
                        signature = inspect.signature(method)
                        signature_str = f"def {name}{signature}"

                        docstring = inspect.getdoc(method) or ""

                        # Try to get source code
                        try:
                            source = inspect.getsource(method)
                        except (OSError, TypeError):
                            source = "# Source not available"

                        # Get parameters
                        parameters = list(signature.parameters.keys())

                        # Determine if public method
                        is_public = not name.startswith('_') or name.startswith('__')

                        methods[name] = {
                            'signature': signature_str,
                            'docstring': docstring,
                            'source': source,
                            'is_public': is_public,
                            'parameters': parameters,
                            'return_annotation': signature.return_annotation
                        }
                    except Exception as e:
                        # Some methods might not have signature available
                        methods[name] = {
                            'signature': f"def {name}(...)",
                            'docstring': "",
                            'source': "# Source not available",
                            'is_public': not name.startswith('_'),
                            'parameters': [],
                            'return_annotation': None
                        }

                return methods

            except (ImportError, AttributeError) as e:
                print(f"Error importing {module_path}.{class_name}: {e}")
                return {}

        except Exception as e:
            print(f"Error introspecting {block_type}: {e}")
            return {}

    @staticmethod
    def get_class_attributes(block_type: str) -> Dict[str, dict]:
        """Get class attributes and their types

        Args:
            block_type: Block type string

        Returns:
            Dictionary of attributes:
            {
                'attr_name': {
                    'type': <type>,
                    'value': <default_value>,
                    'docstring': 'Attribute description'
                }
            }
        """
        try:
            block_def = get_block_definition(BlockType(block_type))
            if not block_def or not block_def.python_module:
                return {}

            module_path = block_def.python_module
            class_name = block_def.python_class

            try:
                parts = module_path.split('.')
                module = __import__(module_path, fromlist=[parts[-1]])
                cls = getattr(module, class_name)

                attributes = {}

                # Get class attributes
                for name, value in inspect.getmembers(cls):
                    # Skip methods, private attrs, and special attrs
                    if inspect.ismethod(value) or inspect.isfunction(value):
                        continue
                    if name.startswith('_'):
                        continue

                    attributes[name] = {
                        'type': type(value).__name__,
                        'value': value,
                        'docstring': ""
                    }

                # Try to get type hints if available
                if hasattr(cls, '__annotations__'):
                    for attr_name, attr_type in cls.__annotations__.items():
                        if attr_name in attributes:
                            attributes[attr_name]['type'] = str(attr_type)
                        else:
                            attributes[attr_name] = {
                                'type': str(attr_type),
                                'value': None,
                                'docstring': ""
                            }

                return attributes

            except (ImportError, AttributeError) as e:
                print(f"Error importing {module_path}.{class_name}: {e}")
                return {}

        except Exception as e:
            print(f"Error introspecting attributes for {block_type}: {e}")
            return {}

    @staticmethod
    def get_method_categories(methods: Dict[str, dict]) -> Dict[str, List[str]]:
        """Categorize methods by type

        Args:
            methods: Dictionary from get_class_methods()

        Returns:
            {
                'Lifecycle': ['__init__', 'activate', ...],
                'Processing': ['process', 'handle_event', ...],
                'State': ['get_state', 'set_state', ...],
                'Utility': ['__str__', '__repr__', ...],
                'FSM': ['activate_fsm', 'deactivate_fsm', ...],
                'Other': [...]
            }
        """
        categories = {
            'Lifecycle': [],
            'Processing': [],
            'State': [],
            'Utility': [],
            'FSM': [],
            'Connection': [],
            'Other': []
        }

        # Keywords for categorization
        lifecycle_keywords = ['__init__', 'activate', 'deactivate', 'start', 'stop', 'reset']
        processing_keywords = ['process', 'handle', 'execute', 'run', 'update']
        state_keywords = ['get_state', 'set_state', 'state', 'status']
        utility_keywords = ['__str__', '__repr__', 'to_dict', 'from_dict']
        fsm_keywords = ['fsm', 'transition', 'state_machine']
        connection_keywords = ['connect', 'disconnect', 'connection', 'port']

        for method_name in methods.keys():
            name_lower = method_name.lower()

            categorized = False

            # Check lifecycle
            if any(kw in name_lower for kw in lifecycle_keywords):
                categories['Lifecycle'].append(method_name)
                categorized = True

            # Check FSM
            elif any(kw in name_lower for kw in fsm_keywords):
                categories['FSM'].append(method_name)
                categorized = True

            # Check processing
            elif any(kw in name_lower for kw in processing_keywords):
                categories['Processing'].append(method_name)
                categorized = True

            # Check state
            elif any(kw in name_lower for kw in state_keywords):
                categories['State'].append(method_name)
                categorized = True

            # Check utility
            elif any(kw in name_lower for kw in utility_keywords):
                categories['Utility'].append(method_name)
                categorized = True

            # Check connection
            elif any(kw in name_lower for kw in connection_keywords):
                categories['Connection'].append(method_name)
                categorized = True

            # Default to Other
            if not categorized:
                categories['Other'].append(method_name)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
