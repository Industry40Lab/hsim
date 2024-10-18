from typing import Any, Iterable

class ListNode(dict):
    def __init__(self) -> None:
        self._keys = list()
        self._values = list()
        super().__init__()
    def __setitem__(self, key: Any, value: Any) -> None:
        if self.__isIterable(key):
            raise TypeError("Key must be a single value")
        if key not in self._keys:
            self._keys.append(key)
            super().__setitem__(key,list())
        if not isinstance(value,Iterable):
            value = [value]
        for v in value:
            if v not in self._values:
                self._values.append(v)
                super().__setitem__(v,list())
            self[key].append(v)
            self[v].append(key)
        return self
    def __getitem__(self, key: Any) -> Any:
        if not self.__isIterable(key):
            return super().__getitem__(key)
        elif len(key) == 2 and not self.__isIterable(key[0]):
            self.__setitem__(key[0], key[1])
        elif len(key) == 2 and not self.__isIterable(key[1]):
            self.__setitem__(key[1], key[0])
        else:
            raise TypeError("Key must be a single value or a tuple of two values, one of which must be a single value")  
    def __isIterable(self, obj) -> bool:
        return isinstance(obj, Iterable) and not isinstance(obj, str)
        


    
    
if __name__ == '__main__':
    pass