from collections import OrderedDict
from hsim.core.CHFSM.FSM import FSM


class CHFSM(FSM):
    def __init__(self,env,name=None):
        super().__init__(env,name)
        self._list_messages()
        self.connections = dict()
    # def __getattr__(self,attr):
    #     for state in object.__getattribute__(self,'_states'):
    #         if state._name == attr:
    #             return state
    #     if object.__getattribute__(self,'_messages').__contains__(attr):
    #         return object.__getattribute__(self,'_messages')[attr]
    #     raise AttributeError()
    def build(self):
        pass
    def _associate(self):
        for state in self._states:
            state.connections = self.connections
            state.var = self.var
            for message in self._messages:
                setattr(state,message,self._messages[message])
    def _list_messages(self):
        self._messages = OrderedDict()
        temp=list(self.__dict__.keys())
        self.build()
        for i in list(self.__dict__.keys()):
            if i not in temp:
                self._messages[i] = getattr(self,i)
