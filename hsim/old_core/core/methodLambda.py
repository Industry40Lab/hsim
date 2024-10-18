def method_lambda(self,function):
    if not hasattr(function,'__self__'):
        return function(self)
    else:
        return function()
    # try:
    #     return function()
    # except TypeError:
    #     return function(self)
