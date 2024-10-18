import copy
from hsim.core.core import method_lambda
from simpy.events import PENDING


class Transition():
    @classmethod
    def copy(cls, state, target=None, trigger=None, condition=None, action=None):
        class Transition(cls):
            _state = state
            _target = target
            if trigger is not None:
                _trigger = trigger
            if action is not None:
                _action = action
            _condition_eval = condition
        return Transition
    def add(self,state):
        new = copy.deepcopy(self)
        state._transitions.append(new)
        new._state = state
        return new
    def __init__(self, state, target=None, trigger=None, condition=None, action=None):
        self._state = state
        self._target = target
        if trigger is not None:
            self._trigger = trigger
        if action is not None:
            self._action = action
        self._condition_eval = condition
    # def __getattr__(self,attr):
    #     try:
    #         return object.__getattribute__(self,attr)
    #     except:
    #         state = object.__getattribute__(self,'_state')
    #         return object.__getattribute__(state,attr)
    def __getattr__(self, attr):
        try:
            return object.__getattribute__(self,attr)
        except:
            pass
        try:
            return getattr(object.__getattribute__(self,'_state'),attr)
        except:
            raise AttributeError()

        # if attr in self.__dict__.keys():
        #     return object.__getattribute__(self,attr)
        # state = object.__getattribute__(self,'_state')
        # print(type(state))
        # if attr in state.__dict__.keys():
        #     return object.__getattribute__(state,attr)
        # sm = object.__getattribute__(state,'sm')
        # if hasattr(sm,attr):
        #     return object.__getattribute__(sm,attr)
        # raise AttributeError()
        
        # try:
        #     state = self.__getattribute__('_state')
        #     try:
        #         return getattr(state,attr)
        #     except:
        #         sm = state.__getattribute__('sm')
        #         return getattr(sm,attr)
        # except:
        #     return object.__getattribute__(self,attr)
    def _trigger(self):
        pass
    def _condition(self):
        if self._condition_eval is None:
            return True
        else:
            return self._condition_eval(self)
    def _action(self):
        return None
    def _otherwise(self):
        return self()
    def cancel(self):
        self._event._value = False
    def _evaluate(self,event):
        if self._event._value == False:
            return
        if method_lambda(self,self._condition):
            method_lambda(self,self._action)
            self._state._resume(self._target)
        else:
            event._value = PENDING
            self._otherwise()
    def __call__(self):
        if self._trigger is None:
            return self._evaluate(None)
            self._target._state = self._state
        self._event = method_lambda(self,self._trigger)
        if self._event == None:
            self._event = self.env.event()
            self._event.succeed()
            # print('Missing trigger')
        try:
            self._event.callbacks.append(self._evaluate)
        except:
            self._event.callbacks = [self._evaluate]
        return self._event
