from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

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
    
    def __init__(self, env: Environment):
        """Initialize shared observable infrastructure"""
        self._env = env
        self._event = BaseEvent(env).add()
    
    @property
    @abstractmethod
    def value(self) -> Any:
        """Get the current value - must be implemented by subclasses"""
        pass
    
    def notify(self):
        """Notify observers of value change"""
        self._event.trigger()
        self._event.reset()
    
    def __repr__(self):
        return f"{self.value} (O: {id(self)})"
    
    def __str__(self):
        return f"{self.value} (O)"
    
    def __eq__(self, other):
        if isinstance(other, Observable):
            return self.value == other.value
        else:
            return self.value == other
    
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
    
    # Unary operators
    def __neg__(self):
        return ObservableExpression(operator.neg, self)
    
    def __pos__(self):
        return ObservableExpression(operator.pos, self)
    
    def __abs__(self):
        return ObservableExpression(operator.abs, self)


class ObservableVariable(Observable):
    def __init__(self, value: Any = None, env: Optional[Environment] = None):
        if env is None:
            raise ValueError("Environment must be provided to Observable")
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
    
    def __len__(self):
        if not hasattr(self._value, "__len__"):
            raise TypeError(f"object of type '{type(self._value).__name__}' has no len()")
        return len(self._value)
    
    def length(self):
        assert hasattr(self._value, "__len__"), TypeError(f"object of type '{type(self._value).__name__}' has no len()")
        return ObservableExpression(len, self)
         
    @change
    def append(self, item):
        self._value.append(item)
    
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
        operator.neg: '-',
        operator.pos: '+',
        operator.abs: 'abs',
        len: 'len'
    }
    
    def __init__(self, op: Callable, *operands: Observable):
        # Find environment from operands first
        env = None
        for operand in operands:
            if hasattr(operand, '_env') and operand._env is not None:
                if env is None:
                    env = operand._env
                else:
                    assert operand._env is env, f"All operands must share the same environment"
        
        assert env is not None, "ObservableExpression must have an environment"
        super().__init__(env)
        
        self.op = op
        self.operands = operands
        self._dependencies = set()
        self._collect_dependencies()
        
        # Connect to operand events for reactivity
        for operand in operands:
            if isinstance(operand, Observable) or isinstance(operand, ObservableExpression):
                if hasattr(operand, '_event'):
                    operand._event.add_action(self._event.trigger)

    def _collect_dependencies(self):
        """Collect all observable dependencies recursively."""
        for operand in self.operands:
            if isinstance(operand, Observable):
                self._dependencies.add(operand)
            elif isinstance(operand, ObservableExpression):
                self._dependencies.update(operand._dependencies)   
                    
    @property
    def value(self) -> Any:
        """Evaluate the expression using current values of operands."""
        values = []
        for operand in self.operands:
            if isinstance(operand, (Observable, ObservableExpression)):
                values.append(operand.value)
            else:
                values.append(operand)
        
        if len(values) == 1:
            return self.op(values[0])
        else:
            return self.op(values[0], values[1])
    
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
        
        if len(self.operands) == 1:
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
        # Operator precedence (higher number = higher precedence)
        precedence = {
            operator.pow: 6,
            operator.neg: 5, operator.pos: 5, operator.abs: 5,
            operator.mul: 4, operator.truediv: 4, operator.floordiv: 4, operator.mod: 4,
            operator.add: 3, operator.sub: 3,
            operator.eq: 2, operator.ne: 2, operator.lt: 2, operator.le: 2, operator.gt: 2, operator.ge: 2,
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
    
ObsVar = obsvar = ObservableVariable
ObsExpr = obsexpr = ObservableExpression
        
        
if __name__ == "__main__":
    print("=== Mathematical Programming Style Observable Expressions ===")
    
    # Create an environment for testing
    env = Environment()
    
    # Named variables like in optimization models
    x = ObservableVariable(10, env)
    y = ObservableVariable(20, env) 
    z = ObservableVariable(5, env)
    
    print(env.now)
    z_expr = 10 + x
    print(env.now)
    env.run(2)
    print(env.now)
    x += 10
    env.run(29)
    
    q = ObservableVariable([1, 2, 3], env)
    
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
