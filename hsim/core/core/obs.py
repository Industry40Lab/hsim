from abc import ABC, abstractmethod
from hmac import new
from typing import Any, Callable, Iterable, Optional, Type

from numpy import add

if __name__ == "__main__":
    import sys
    import os
    # Cross-platform path handling
    abs_path = os.path.abspath(__file__)
    parts = abs_path.split(os.sep)
    try:
        if "hsim" in parts:
            hsim_index = parts.index("hsim")
            hsim_path = os.sep.join(parts[:hsim_index + 1])
            if hsim_path not in sys.path:
                sys.path.append(hsim_path)
    except ValueError:
        pass


from hsim.core.core.event import BaseEvent
from hsim.core.core.env import Environment
import operator
import functools





# "change" wrapper that triggers notify after the execution of the method
def change(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.notify()
        return result
    return wrapper


class Observable(ABC):
    """Abstract base class for all observable types"""
    
    def __init__(self, env: Optional[Environment] = None):
        """Initialize shared observable infrastructure"""
        self._expressions = set()  # Track expressions that depend on this variable
        self._env = env
        self._event = BaseEvent(env).add() if env is not None else None

    def add_dependency(self, expr: 'Observable'):
        """Add an expression that depends on this observable"""
        if isinstance(expr, Observable):
            self._expressions.add(expr)
            expr._dependencies.add(self)
        else:
            raise TypeError("Only Observables can be added as dependencies")
        
    def add_environment(self, env: Environment):
        """Add an environment to this observable"""
        assert isinstance(env, Environment), "env must be an instance of Environment"
        if self._env is not None and self._env is not env:
            raise ValueError("Observable already has a different environment")
        self._env = env
        self._event = BaseEvent(env).add() if self._event is None else self._event
    
    @property
    def watchable(self) -> bool:
        return self._env is not None
    
    @property
    @abstractmethod
    def value(self) -> Any:
        """Get the current value - must be implemented by subclasses"""
        pass
    
    def notify(self,reset=False):
        """Notify observers of value change"""
        # Notify all expressions that depend on this observable
        for expr in self._expressions:
            expr.recalc()
        # Trigger the event if it exists
        if self.watchable:
            if reset == None or reset == True:
                self._event.trigger()
            if reset == None or reset == False:
                self._event.reset() if reset else None
    
    def __repr__(self):
        return f"{self.value} (O: {id(self)})"
    
    def __str__(self):
        return f"{self.value} (O)"
    
    def __hash__(self):
        return hash(id(self))
    
    # Mathematical operators that return ObservableExpression
    def __add__(self, other: Any):
        return ObservableExpression(operator.add, self, other)
    
    def __radd__(self, other: Any):
        return self + other
    
    def __sub__(self, other: Any):
        return ObservableExpression(operator.sub, self, other)
    
    def __rsub__(self, other: Any):
        return ObservableExpression(operator.sub, other, self)
    
    def __mul__(self, other: Any):
        return ObservableExpression(operator.mul, self, other)
    
    def __rmul__(self, other: Any):
        return self * other
    
    def __truediv__(self, other: Any):
        return ObservableExpression(operator.truediv, self, other)
    
    def __rtruediv__(self, other: Any):
        return ObservableExpression(operator.truediv, other, self)
    
    def __floordiv__(self, other: Any):
        return ObservableExpression(operator.floordiv, self, other)
    
    def __rfloordiv__(self, other: Any):
        return ObservableExpression(operator.floordiv, other, self)
    
    def __mod__(self, other: Any):
        return ObservableExpression(operator.mod, self, other)
    
    def __rmod__(self, other: Any):
        return ObservableExpression(operator.mod, other, self)
    
    def __pow__(self, other: Any):
        return ObservableExpression(operator.pow, self, other)
    
    def __rpow__(self, other: Any):
        return ObservableExpression(operator.pow, other, self)
    
    # Comparison operators
    def __eq__(self, other):
        return ObservableExpression(operator.eq, self, other)
        
    def __ne__(self, other: Any):
        return ObservableExpression(operator.ne, self, other)
    
    def __lt__(self, other: Any):
        return ObservableExpression(operator.lt, self, other)
    
    def __le__(self, other: Any):
        return ObservableExpression(operator.le, self, other)
    
    def __gt__(self, other: Any):
        return ObservableExpression(operator.gt, self, other)
    
    def __ge__(self, other: Any):
        return ObservableExpression(operator.ge, self, other)
    
    # Boolean operators
    def __and__(self, other: Any):
        return ObservableExpression(operator.and_, self, other)
    
    def __rand__(self, other: Any):
        return ObservableExpression(operator.and_, other, self)
    
    def __or__(self, other: Any):
        return ObservableExpression(operator.or_, self, other)
    
    def __ror__(self, other: Any):
        return ObservableExpression(operator.or_, other, self)
    
    # Unary operators
    def __neg__(self):
        return ObservableExpression(operator.neg, self)
    
    def __pos__(self):
        return ObservableExpression(operator.pos, self)
    
    def __abs__(self):
        return ObservableExpression(operator.abs, self)
    
    def __bool__(self):
        """Return True if the observable's value is truthy, False otherwise."""
        return bool(self.value)
    
    @staticmethod
    def any(*predicate: 'Observable') -> 'ObservableExpression':
        """
        Returns an ObservableExpression that is True if any element of the value is true (or satisfies the predicate).
        """
        return ObservableExpression(any,*predicate)
    
    @staticmethod    
    def all(*predicate: 'Observable') -> 'ObservableExpression':
        """
        Returns an ObservableExpression that is True if all elements of the value are true (or satisfy the predicate).
        """
        return ObservableExpression(all, *predicate)
    
    def proxy_item(self, key):
        """Create a reactive proxy for item access."""
        return ObservableProxy.item(self, key)
    
    def proxy_attr(self, name):
        """Create a reactive proxy for attribute access.""" 
        return ObservableProxy.attr(self, name)
    
    def item(self, key):
        """Create a reactive proxy for item access. More convenient than proxy_item()."""
        return ObservableProxy(self).item(key)
    
    def attr(self, name):
        """Create a reactive proxy for attribute access. More convenient than proxy_attr()."""
        return ObservableProxy(self).attr(name)


class ObservableVariable(Observable):
    def __init__(self, value: Any = None, env: Optional[Environment] = None):
        super().__init__(env)
        self._value = value
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, new_value: Any):
        if new_value != self._value:
            self._value = new_value
            self.notify()
            
    @change       
    def __iadd__(self, other: Any):
        self.value += other
        return self
    
    @change       
    def __isub__(self, other: Any):
        self.value -= other
        return self
    
    @change
    def __imul__(self, other: Any):
        self.value *= other
        return self
    
    @change
    def __itruediv__(self, other: Any):
        self.value /= other
        return self
    
    @change
    def __ifloordiv__(self, other: Any):
        self.value //= other
        return self
    
    @change
    def __imod__(self, other: Any):
        self.value %= other
        return self
    
    @change
    def __ipow__(self, other: Any):
        self.value **= other
        return self
    
    @change 
    def __ishift__(self, other: Any):
        """Shift operator."""
        self.value = other
        return self
    
    def __ilshift__(self, other: Any):
        return self.__ishift__(other)
    
    def __irshift__(self, other: Any):
        return self.__ishift__(other)
    
    def __getattribute__(self, name: str) -> Any:
        """Get attribute from the value if it supports attributes."""
        try:
            return object.__getattribute__(self, name)
        except AttributeError as e1:
            try:
                return object.__getattribute__(self._value, name)
            except AttributeError:
                raise AttributeError(f"'{type(self._value).__name__}' object has no attribute '{name}'") from e1
    
    def __getitem__(self, key: Any) -> Any:
        """Get item from the value if it supports indexing."""
        if hasattr(self._value, "__getitem__"):
            return self._value[key]
        else:
            raise TypeError(f"object of type '{type(self._value).__name__}' is not subscriptable")
    
    def __len__(self):
        if not hasattr(self._value, "__len__"):
            raise TypeError(f"object of type '{type(self._value).__name__}' has no len()")
        return len(self._value)
    
    def length(self):
        assert hasattr(self._value, "__len__"), TypeError(f"object of type '{type(self._value).__name__}' has no len()")
        return ObservableExpression(len, self)
    
    @change
    def __setitem__(self, index, value):
        self._value.__setitem__(index, value)  # Call the original __setitem__ method
     
    @change
    def append(self, item):
        self._value.append(item)
    
    @change
    def add(self, item):
        """Add an item to the observable variable."""
        if hasattr(self._value, "add"):
            self._value.add(item)
        else:
            raise TypeError(f"object of type '{type(self._value).__name__}' does not support 'add' method")
    
    @change
    def remove(self, item):
        self._value.remove(item)
    
    @change
    def pop(self, idx: Optional[int] = None):
        return self._value.pop() if idx is None else self._value.pop(idx)

    @change
    def update(self, key:str, value: Any):
        self._value[key] = value
        

class ObservableExpression(Observable):
    
    # Operator symbol mapping for mathematical notation
    _OP_SYMBOLS = {
        operator.add: '+',
        operator.sub: '-',
        operator.mul: '*',
        operator.truediv: '/',
        operator.floordiv: '//',
        operator.mod: '%',
        operator.pow: '**',
        operator.eq: '==',
        operator.ne: '!=',
        operator.lt: '<',
        operator.le: '<=',
        operator.gt: '>',
        operator.ge: '>=',
        operator.and_: 'and',
        operator.or_: 'or',
        operator.neg: '-',
        operator.pos: '+',
        operator.abs: 'abs',
        len: 'len',
        any: 'any',
        all: 'all',
    }
    
    def __init__(self, op: Callable, *operands: Observable):
        # Find environment from operands first
        env = None
        operands = list(operands)  # Convert to list to allow modifications
        for el in [idx for idx, operand in enumerate(operands) if isinstance(operand, Iterable) and not isinstance(operand, Observable) and not isinstance(operand, str)][::-1]:
            operands.extend(operands[el])
            operands.pop(el)
        operands = tuple(operands)  # Convert back to tuple after modifications
        
        for operand in operands:
            if isinstance(operand,Observable) and operand.watchable:
                if env is None:
                    env = operand._env
                else:
                    assert operand._env is env, f"All operands must share the same environment"
        
        super().__init__(env)
        
        self.op = op
        self.operands = operands
        self._dependencies = set()
        self._collect_dependencies()
        self._stored_value = self.value
        if self.value is True:
            self._stored_value = False
            self.recalc()
               
        for operand in operands:
            operand.add_dependency(self) if isinstance(operand, Observable) else None

    def _collect_dependencies(self):
        """Collect all observable dependencies recursively."""
        for operand in self.operands:
            if isinstance(operand, ObservableVariable):
                self._dependencies.add(operand)
            elif isinstance(operand, ObservableExpression) or isinstance(operand, ObservableProxy):
                self._dependencies.update(operand._dependencies)
    
    def recalc(self):
        old, new = self._stored_value, self.value
        self._stored_value = new
        if old != new:
            reset = new if type(old) == type(new) == bool else None
            self.notify(reset)
                    
    @property
    def value(self) -> Any:
        """Evaluate the expression using current values of operands."""
        # Special handling for ObservableCollection
        if hasattr(self, 'filter_func'):
            # Return filtered elements (not their values)
            result = []
            for element in self.elements:
                if isinstance(element, Observable):
                    element_value = element.value
                else:
                    element_value = element
                
                if self.filter_func(element_value):
                    result.append(element)  # Return the element itself, not its value
            return result
        
        # Regular expression evaluation
        values = []
        for operand in self.operands:
            if isinstance(operand, (Observable, ObservableExpression)):
                values.append(operand.value)
            elif isinstance(operand,Iterable) and len(self.operands) == 1:
                "If there's only one operand and it's iterable, use it directly"
                values = operand
                break
            else:
                values.append(operand)
        
        try:
            if self.op in [any, all]:
                return self.op(values)
            elif len(values) == 1:
                return self.op(values[0])
            elif len(values) == 2:
                return self.op(values[0], values[1])
            else:
                return self.op(*values)
        except TypeError as e:
            return None
            
            
    
    @property
    def dependencies(self) -> set:
        """Return all observable dependencies of this expression."""
        return self._dependencies.copy()
    
    def __repr__(self):
        return f"{self.value} = {self._format_expression()}"
    
    def __str__(self):
        return self._format_expression()
    
    def _format_expression(self) -> str:
        """Format the expression in mathematical notation."""
        op_symbol = self._OP_SYMBOLS.get(self.op, str(self.op))
        
        if self.op in [any, all] or len(self.operands) > 2:
            operands_str = ', '.join(self._format_operand(op) for op in self.operands)
            return f"{op_symbol}({operands_str})"
        elif len(self.operands) == 1:
            # Unary operators
            operand_str = self._format_operand(self.operands[0])
            if self.op in [operator.abs, len]:
                return f"{op_symbol}({operand_str})"
            else:
                return f"{op_symbol}{operand_str}"
        else:
            # Binary operators
            left_str = self._format_operand(self.operands[0])
            right_str = self._format_operand(self.operands[1])
            
            # Add parentheses for complex expressions to maintain precedence
            if isinstance(self.operands[0], ObservableExpression) and self._needs_parentheses(self.operands[0], True):
                left_str = f"({left_str})"
            if isinstance(self.operands[1], ObservableExpression) and self._needs_parentheses(self.operands[1], False):
                right_str = f"({right_str})"
            
            return f"{left_str} {op_symbol} {right_str}"
    
    def _format_operand(self, operand) -> str:
        """Format a single operand (Observable, ObservableExpression, or constant)."""
        if isinstance(operand, (Observable, ObservableExpression)):
            return str(operand)
        else:
            return str(operand)
    
    def _needs_parentheses(self, expr: 'ObservableExpression', is_left: bool) -> bool:
        """Determine if parentheses are needed for operator precedence."""
        # Only ObservableExpressions need parentheses
        if not isinstance(expr, ObservableExpression):
            return False
            
        # Operator precedence (higher number = higher precedence)
        precedence = {
            operator.pow: 6,
            operator.neg: 5, operator.pos: 5, operator.abs: 5,
            operator.mul: 4, operator.truediv: 4, operator.floordiv: 4, operator.mod: 4,
            operator.add: 3, operator.sub: 3,
            operator.eq: 2, operator.ne: 2, operator.lt: 2, operator.le: 2, operator.gt: 2, operator.ge: 2,
            operator.and_: 1,
            operator.or_: 0,
        }
        
        current_prec = precedence.get(self.op, 1)
        expr_prec = precedence.get(expr.op, 1)
        
        # Add parentheses if:
        # 1. Expression has lower precedence than current
        # 2. Same precedence and non-associative operation on the right
        if expr_prec < current_prec:
            return True
        elif expr_prec == current_prec and not is_left and self.op in [operator.sub, operator.truediv, operator.pow]:
            return True
        
        return False


class ObservableCollection(ObservableExpression):
    def __init__(self, *elements, filter_func: Callable = None):
        """
        Create an observable collection that filters elements based on a predicate.
        
        Args:
            *elements: Observable variables, expressions, or regular values
            filter_func: Function to filter elements (like f in [x for x in list if f(x)])
        """
        # Create a filter operation that will be evaluated by the parent class
        self.elements = list(elements)
        self.filter_func = filter_func if filter_func is not None else lambda val: True
        
        # Create a custom operation that filters the elements
        def filter_operation(*operands):
            result = []
            for i, operand in enumerate(operands):
                if self.filter_func(operand):
                    result.append(operand)
            return result
        
        # Initialize with the filter operation and all elements as operands
        super().__init__(filter_operation, *elements)
        
        self._stored_value = hash(tuple(self.value))
        for operand in self.operands:
            if not isinstance(operand, Observable):
                for value in operand.__dict__.values():
                    if isinstance(value, Observable):
                        self._register_observable(value)
                        break
            

    def _update_operands(self):
        """Update operands tuple and recalculate after list operations."""
        self.operands = tuple(self.elements)
        self.recalc()
        
    def recalc(self):
        old, new = self._stored_value, hash(tuple(self.value))
        self._stored_value = new
        if old != new:
            reset = new if type(old) == type(new) == bool else None
            self.notify(reset)

    
    def _register_observable(self, element):
        """Register an observable element as a dependency."""
        if isinstance(element, Observable):
            element.add_dependency(self)
            self._collect_dependencies()
    
    def _unregister_observable(self, element):
        """Unregister an observable element from dependencies."""
        if isinstance(element, Observable):
            element._expressions.discard(self)
            if hasattr(self, '_dependencies'):
                self._dependencies.discard(element)
    
    @change
    def append(self, element):
        """Append an element to the collection."""
        self.elements.append(element)
        self._register_observable(element)
        self._update_operands()
    
    @change
    def insert(self, index, element):
        """Insert an element at the specified index."""
        self.elements.insert(index, element)
        self._register_observable(element)
        self._update_operands()
    
    @change
    def pop(self, index=-1):
        """Remove and return element at index (default last)."""
        if self.elements:
            element = self.elements.pop(index)
            self._unregister_observable(element)
            self._update_operands()
            return element
        else:
            raise IndexError("pop from empty collection")
    
    @change
    def remove(self, element):
        """Remove first occurrence of element."""
        if element in self.elements:
            self.elements.remove(element)
            self._unregister_observable(element)
            self._update_operands()
        else:
            raise ValueError("element not in collection")
    
    @change
    def clear(self):
        """Remove all elements from the collection."""
        for element in self.elements:
            self._unregister_observable(element)
        self.elements.clear()
        self._update_operands()
    
    @change
    def extend(self, iterable):
        """Extend collection with elements from iterable."""
        for element in iterable:
            self.elements.append(element)
            self._register_observable(element)
        self._update_operands()
    
    @change
    def __setitem__(self, index, element):
        """Set element at index."""
        old_element = self.elements[index]
        self._unregister_observable(old_element)
        self.elements[index] = element
        self._register_observable(element)
        self._update_operands()
    
    @change
    def __delitem__(self, index):
        """Delete element at index."""
        element = self.elements[index]
        self._unregister_observable(element)
        del self.elements[index]
        self._update_operands()
    
    def __len__(self):
        """Return the length of the filtered collection."""
        return len(self.value)
    
    def length(self):
        """Return an ObservableExpression representing the length of the collection."""
        return ObservableExpression(len, self)
    
    def __iter__(self):
        """Iterate over the filtered collection."""
        return iter(self.value)
    
    def __getitem__(self, index):
        """Get item from the filtered collection."""
        return self.value[index]
    
    def __repr__(self):
        return f"ObservableCollection({self.value}) (filtered from {len(self.elements)} elements)"
    
    def __str__(self):
        return f"[{', '.join(str(v) for v in self.value)}]"


class ObservableProxy(ObservableExpression):
    """
    Use case 1: I get an element out of a collection, e.g., collection[0], and I want to observe changes to that element (i.e., if the element at position 0 changes, I want to be notified).
    Use case 2: I want to observe a specific property of a watchable object, such that if the object changes, I am notified.
    """
    
    def __init__(self, target: Observable, accessor: Any = None, attr_name: str = None):
        """
        Create a proxy that observes a specific part of an observable object.
        
        Args:
            target: The observable object to proxy
            accessor: Index or key for collection access (use case 1)  
            attr_name: Attribute name for property access (use case 2)
        """
        self.target = target
        self.accessor = accessor
        self.attr_name = attr_name
        
        # Create appropriate access operation
        if accessor is not None:
            # Use case 1: Collection element access
            def access_element(target_value):
                try:
                    return target_value[accessor]
                except (IndexError, KeyError, TypeError):
                    return None
            operation = access_element
            
        elif attr_name is not None:
            # Use case 2: Attribute access
            def access_attribute(target_value):
                try:
                    return getattr(target_value, attr_name)
                except AttributeError:
                    return None
            operation = access_attribute
            
        else:
            # Direct proxy - just return the target value
            operation = lambda x: x
        
        self.operation = operation
        super().__init__(operation, target)
    
    def recalc(self):
        """Recalculate the value and notify observers."""
        old_value = self._stored_value
        new_value = self.value
        self._stored_value = new_value
        
        if old_value != new_value:
            reset = new_value if type(old_value) == type(new_value) == bool else None
            self.notify(reset)
    
    @property
    def value(self) -> Any:
        """Get the current value by applying the operation to the target."""
        target_value = self.target.value if isinstance(self.target, Observable) else self.target
        return self.operation(target_value)
    
    @classmethod
    def item(cls, target: Observable, accessor: Any):
        """Create a proxy for collection item access (e.g., collection[0])."""
        return cls(target, accessor=accessor)
    
    @classmethod
    def attr(cls, target: Observable, attr_name: str):
        """Create a proxy for attribute access (e.g., obj.property)."""
        return cls(target, attr_name=attr_name)
    
    def item(self, accessor: Any):
        """Fluent interface: Create a chained proxy for item access."""
        return ObservableProxy(self, accessor=accessor)
    
    def attr(self, attr_name: str):
        """Fluent interface: Create a chained proxy for attribute access."""
        return ObservableProxy(self, attr_name=attr_name)
    
    def __getitem__(self, key):
        """Support chained indexing: proxy[key] -> ObservableProxy(proxy, key)."""
        return self.item(key)
    
    def __getattr__(self, name):
        """Support chained attribute access: proxy.attr -> ObservableProxy(proxy, attr)."""
        # Don't proxy internal attributes, methods, or known instance methods
        if (name.startswith('_') or 
            hasattr(ObservableExpression, name) or
            name in ['target', 'accessor', 'attr_name', 'operation', 'item', 'attr']):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        return self.attr(name)
    
    def __repr__(self):
        if self.accessor is not None:
            return f"{self.value} = {self.target}[{self.accessor}]"
        elif self.attr_name is not None:
            return f"{self.value} = {self.target}.{self.attr_name}"
        else:
            return f"{self.value} = proxy({self.target})"
    
    def __str__(self):
        if self.accessor is not None:
            return f"{self.target}[{self.accessor}]"
        elif self.attr_name is not None:
            return f"{self.target}.{self.attr_name}"
        else:
            return f"proxy({self.target})"


# Simple functions for any() and all() - no need to use ObservableExpression.any()
def obs_any(*args) -> 'ObservableExpression':
    """
    Create an ObservableExpression that returns True if any of the arguments is true.
    More convenient than ObservableExpression.any(*args).
    """
    return ObservableExpression.any(*args)

def obs_all(*args) -> 'ObservableExpression':
    """
    Create an ObservableExpression that returns True if all of the arguments are true.
    More convenient than ObservableExpression.all(*args).
    """
    return ObservableExpression.all(*args)

Obs = obs = Observable
ObsVar = obsvar = ObservableVariable
ObsExpr = obsexpr = ObservableExpression
ObsCollection = obscollection = ObservableCollection
ObsProxy = obsproxy = ObservableProxy
        
        
if __name__ == "__main__":
    print("=== Mathematical Programming Style Observable Expressions ===")
    
    # Create an environment for testing
    env = Environment()
    
    # Named variables like in optimization models
    x = ObservableVariable(10)
    y = ObservableVariable(20) 
    z = ObservableVariable(5)
    
    print(env.now)
    z_expr = 10 + x
    print(env.now)
    env.run(2)
    print(env.now)

    
    ev = z_expr <= 100
    ev.add_environment(env)
    
    coll = ObsCollection(x,y,filter_func=lambda v: v > 10)
    L = coll.length()
    x += 10
    el = ObsProxy.item(coll, 2)
    test = el + 1
    
    t2 = test < 30
    coll.append(30)
    
    
    obs.any(ev,False)
    print(obs.any(ev,False))
    q = ObservableVariable([1, 2, 3], env)
    
    oc = ObservableCollection(z_expr, filter_func=lambda x: x > 1)
    
    print(f"\nVariables: x={x.value}, y={y.value}, z={z.value}")
    print(f"Expression z_expr: {z_expr.value}")
    print(f"List q: {q.value}")
    
    # Test collection methods
    q.append(4)
    print(f"After append: {q.value}")
    
    # Test length
    print(f"len(q): {len(q)}")
    q_len = q.length()
    print(f"q.length(): {q_len.value}")
    
    env.run()
