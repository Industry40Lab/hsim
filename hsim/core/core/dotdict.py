class dotdict(dict):
    """MATLAB-like dot.notation access to dictionary attributes"""
    def __getattr__(self,name):
        try:
            super().__getattr__(name)
            return super().__getitem__(name)
        except AttributeError:
            raise AttributeError()
    def __setattr__(self,name,value):
        super().__setitem__(name,value)
        super().__setattr__(name, value)
    def __delattr__(self,name):
        super().__delattr__(name)
        super().__delitem__(name)
    def __repr__(self):
        return str(vars(self))
    def keys(self):
        return vars(self).keys()
    def values(self):
        return vars(self).values()
    def __len__(self):
        return len(self.keys())