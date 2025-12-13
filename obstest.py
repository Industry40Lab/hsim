from abc import ABC, abstractmethod
from hmac import new
from typing import Any, Callable, Iterable, Optional, Type, Union
from reaktiv import Signal, Computed, Effect
import operator
import functools



class ObservableExpression(Computed):
    def __init__(self, op: Callable, *operands: Union['ObservableVariable','ObservableExpression']):
        super().__init__(lambda: op(*[operand() if isinstance(operand, (ObservableVariable, ObservableExpression)) else operand for operand in operands]))

    def __iadd__(self, other: Any):
        self.value += other
        return self
    
       
    def __isub__(self, other: Any):
        self.value -= other
        return self
    

    def __imul__(self, other: Any):
        self.value *= other
        return self
    

    def __itruediv__(self, other: Any):
        self.value /= other
        return self
    

    def __ifloordiv__(self, other: Any):
        self.value //= other
        return self
    

    def __imod__(self, other: Any):
        self.value %= other
        return self
    

    def __ipow__(self, other: Any):
        self.value **= other
        return self
    
 
    def __ishift__(self, other: Any):
        """Shift operator."""
        self.value = other
        return self
    
    def __ilshift__(self, other: Any):
        return self.__ishift__(other)
    
    def __irshift__(self, other: Any):
        return self.__ishift__(other)

class ObservableVariable(Signal):
    def __init__(self, initial: Any):
        super().__init__(initial)
        
    def link(self, event): 
        self._event = event
        self._effect = Effect(lambda: event.trigger() if self() else event.reset())  # Dummy effect to trigger updates
    
    def __repr__(self):
        return f"{self._value} (Obs: {id(self)})"
    
    def __str__(self):
        return f"{self._value} (Obs)"
    
    def __hash__(self):
        return hash(id(self))
    
    # Mathematical operators that return ObservableExpression
    def __add__(self, other: Any):
        return ObservableExpression(operator.add, self, other)
    
    def __radd__(self, other: Any):
        return self + other
    
    def __iadd__(self, other: Any):
        self.set(self._value + other)
        return self
    
    def __sub__(self, other: Any):
        return ObservableExpression(operator.sub, self, other)
    
    def __rsub__(self, other: Any):
        return ObservableExpression(operator.sub, other, self)
    
    def __isub__(self, other: Any):
        self.set(self._value - other)
        return self
    
    def __mul__(self, other: Any):
        return ObservableExpression(operator.mul, self, other)
    
    def __rmul__(self, other: Any):
        return self * other
    
    def __imul__(self, other: Any):
        self.set(self._value * other)
        return self
    
    def __truediv__(self, other: Any):
        return ObservableExpression(operator.truediv, self, other)
    
    def __rtruediv__(self, other: Any):
        return ObservableExpression(operator.truediv, other, self)
    
    def __itruediv__(self, other: Any):
        self.set(self._value / other)
        return self
    
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
        return bool(self._value)
    
    @staticmethod
    def any(*predicate: 'ObservableVariable') -> 'ObservableExpression':
        """
        Returns an ObservableExpression that is True if any element of the value is true (or satisfies the predicate).
        """
        return ObservableExpression(any,*predicate)
    
    @staticmethod    
    def all(*predicate: 'ObservableVariable') -> 'ObservableExpression':
        """
        Returns an ObservableExpression that is True if all elements of the value are true (or satisfy the predicate).
        """
        return ObservableExpression(all, *predicate)

class ObservableCollection(ObservableExpression):
    def __init__(self, initial: Optional[Iterable] = None):
        if initial is None:
            initial = []
        elif not isinstance(initial, Iterable):
            raise TypeError("Initial value must be an iterable or None.")
        super().__init__(lambda: list(initial))
    
    def append(self, element):
        """Append an element to the collection."""
        self.set(self() + [element])

    
    def insert(self, index, element):
        """Insert an element at the specified index."""
        self.set(self().insert(index, element))


    def pop(self, index=-1):
        """Remove and return element at index (default last)."""
        try:
            self.set(self().pop(index))
        except IndexError:
            raise IndexError("pop index out of range")
    

    def remove(self, element):
        """Remove first occurrence of element."""
        try:
            self.set(self().remove(element))
        except ValueError:
            raise ValueError("element not in collection")
    

    def clear(self):
        """Remove all elements from the collection."""
        self.set([])
    

    def extend(self, iterable):
        """Extend collection with elements from iterable."""
        self.set(self() + list(iterable))


if __name__ == "__main__":
    a = ObservableVariable(10)
    b = ObservableVariable(5)
    c = a * 2 + b
    b + 1
    b += 1
    d = a > b
    e = ObservableVariable.all(a > 0, b > 0)
    f = ObservableVariable.any(a < 0, b > 0)
    
    print(f"a: {a}, b: {b}")
    print(f"c (a + b * 2): {c}")
    print(f"d (a > b): {d}")
    print(f"e (all(a > 0, b > 0)): {e}")
    print(f"f (any(a < 0, b > 0)): {f}")
    
    a.set(3)
    b.set(7)
    
    print("\nAfter updating a and b:")
    print(f"a: {a}, b: {b}")
    print(f"c (a + b * 2): {c}")
    print(f"d (a > b): {d}")
    print(f"e (all(a > 0, b > 0)): {e}")
    print(f"f (any(a < 0, b > 0)): {f}")