from warnings import warn


class ThVar(float,object):
    def __init__(self,value):
        self._value=value
        self._threshold = dict()
    def __add__(self,x):
        return self.create(self._value + x)
    def __sub__(self,x):
        return self.create(self._value - x)
    def __pow__(self,x):
        return self.create(self._value**x)
    def __float__(self):
        return float(self._value)
    def __int__(self):
        return int(self._value)
    def __repr__(self):
        return str(self._value)
    def __iadd__(self,other):       
        return self.update(self._value + other)
    def __isub__(self,other):
        return self.update(self._value - other) 
    def __imul__(self, other):
        return self.update(self._value*other) 
    def __ipow__(self, other):
        return self.update(self._value**other) 
    def __imod__(self,other):
        return self.update(other) 
    def __ilshift__(self,other):
        self._threshold.update({'up':other})
        self.threshold_fun(self._value)
        return self
    def __irshift__(self,other):
        self._threshold.update({'down':other})
        return self
    def create(self,value):
        return self.__class__(value)
    def update(self,value):
        self.threshold_fun(value)
        self._value = value
        return self
    def threshold_fun(self,value):
        if self.check(value):
            warn(RuntimeWarning('Break threshold'))
    def check(self,value):
        if 'up' in self._threshold.keys():
            if value > self._threshold['up']:
                return True
        if 'down' in self._threshold.keys():
            if value < self._threshold['down']:
                return True
        return False