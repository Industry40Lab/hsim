from abc import abstractmethod
from typing import Any, Callable
from hsim.core.core.event import BaseEvent
from hsim.core.core.env import Environment
import operator


class Observable:
    
    def __init__(self, value: Any = None):
        self._value = value
    
    @property
    def value(self) -> Any:
        return self._value
    
    @value.setter
    def value(self, new_value: Any):
        if new_value != self._value:
            self._value = new_value
            self.notify()
            
    @abstractmethod
    def notify(self):
        """Notify observers of a change in value."""
        print("Observable: notify method not implemented.")
        pass
    
    def __repr__(self):
        return f"{self.value} (O: {id(self)})"
    
    def __str__(self):
        return f"{self.value} (O)"
    
    def __eq__(self, other):
        if isinstance(other, Observable):
            return self._value == other._value
        else:
            return self._value == other
    
    def __add__(self, other: Any):
        return ObservableExpression(operator.add, self, other)
            
    def __iadd__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.add, self, other)
        else:
            self.value += other
            return self
    
    def __radd__(self, other: Any):
        return self + other
    
    def __sub__(self, other: Any):
        return ObservableExpression(operator.sub, self, other)
    
    def __rsub__(self, other: Any):
        return self - other
    
    def __isub__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.sub, self, other)
        else:
            self.value -= other
            return self
    
    def __mul__(self, other: Any):
        return ObservableExpression(operator.mul, self, other)
    
    def __rmul__(self, other: Any):
        return self * other
    
    def __imul__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.mul, self, other)
        else:
            self.value *= other
            return self
    
    def __truediv__(self, other: Any):
        return ObservableExpression(operator.truediv, self, other)
    
    def __rtruediv__(self, other: Any):
        return ObservableExpression(operator.truediv, other, self)
    
    def __itruediv__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.truediv, self, other)
        else:
            self.value /= other
            return self
    
    def __floordiv__(self, other: Any):
        return ObservableExpression(operator.floordiv, self, other)
    
    def __rfloordiv__(self, other: Any):
        return ObservableExpression(operator.floordiv, other, self)
    
    def __ifloordiv__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.floordiv, self, other)
        else:
            self.value //= other
            return self
    
    def __mod__(self, other: Any):
        return ObservableExpression(operator.mod, self, other)
    
    def __rmod__(self, other: Any):
        return ObservableExpression(operator.mod, other, self)
    
    def __imod__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.mod, self, other)
        else:
            self.value %= other
            return self
    
    def __pow__(self, other: Any):
        return ObservableExpression(operator.pow, self, other)
    
    def __rpow__(self, other: Any):
        return ObservableExpression(operator.pow, other, self)
    
    def __ipow__(self, other: Any):
        if isinstance(other, Observable):
            return ObservableExpression(operator.pow, self, other)
        else:
            self.value **= other
            return self
    
    
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
    
    def __neg__(self):
        return ObservableExpression(operator.neg, self)
    
    def __pos__(self):
        return ObservableExpression(operator.pos, self)
    
    def __abs__(self):
        return ObservableExpression(operator.abs, self)
    
    def __hash__(self):
        return hash(id(self))
    


class ObservableExpression:
    
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
    }
    
    def __init__(self, op: Callable, *operands: Observable):
        self.op = op
        self.operands = operands
        self._dependencies = set()
        self._collect_dependencies()
    
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
            if self.op == operator.abs:
                return f"abs({operand_str})"
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
    
    def __add__(self, other: Any):
        return ObservableExpression(operator.add, self, other)
    
    def __radd__(self, other: Any):
        return self + other
    
    def __iadd__(self, other: Any):
        return self + other
    
    def __sub__(self, other: Any):
        return ObservableExpression(operator.sub, self, other)
    
    def __rsub__(self, other: Any):
        return self - other
    
    def __isub__(self, other: Any):
        return self - other
    
    def __mul__(self, other: Any):
        return ObservableExpression(operator.mul, self, other)
    
    def __rmul__(self, other: Any):
        return self * other
    
    def __imul__(self, other: Any):
        return self * other
    
    def __truediv__(self, other: Any):
        return ObservableExpression(operator.truediv, self, other)
    
    def __rtruediv__(self, other: Any):
        return ObservableExpression(operator.truediv, other, self)
    
    def __itruediv__(self, other: Any):
        return self / other
    
    def __eq__(self, other: Any):
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
        
        
if __name__ == "__main__":
    print("=== Mathematical Programming Style Observable Expressions ===")
    
    # Named variables like in optimization models
    x = Observable(10)
    y = Observable(20) 
    z = Observable(5)
    
    x += 10
    z = 10 + y
    
    print(f"\nVariables: x={x.value}, y={y.value}, z={z.value}")
    
    # Mathematical expressions display structure, not just values
    print(f"\nExpressions:")
    expr1 = x + y
    print(f"  {expr1} = {expr1.value}")
    
    expr2 = x * y + z  
    print(f"  {expr2} = {expr2.value}")
    
    expr3 = (x + y) * z
    print(f"  {expr3} = {expr3.value}")
    
    # Constraint-style expressions with observables
    print(f"\nConstraints:")
    const_100 = Observable(100)
    two = Observable(2)
    
    constraint = x + two * y <= const_100
    print(f"  {constraint} = {constraint.value}")
    
    # Mixed operations: Observable op constant returns value
    print(f"\nMixed operations:")
    print(f"  x + 5 = {x + 5} (returns value)")
    print(f"  x <= 50 = {x <= 50} (returns boolean)")
    
    # Change values - expressions update automatically
    print(f"\nAfter changing x to 15:")
    x.value = 15
    print(f"  {expr1} = {expr1.value}")
    print(f"  {constraint} = {constraint.value}")
    
    # Unnamed variables get auto-generated IDs
    print(f"\nUnnamed variables:")
    var1 = Observable(42)
    var2 = Observable(7)
    expr4 = var1 / var2
    print(f"  {expr4} = {expr4.value}")
    
    # Observable equality: same values are equal, but different objects
    print(f"\nEquality semantics:")
    a = Observable(10) 
    b = Observable(10)
    print(f"  a == b: {a == b} (value equality)")
    print(f"  a is b: {a is b} (object identity)")
    
    print(f"\nDependency tracking:")
    complex_expr = (x + y) * z + two
    print(f"  Expression: {complex_expr}")
    print(f"  Dependencies: {[str(dep) for dep in complex_expr.dependencies]}")