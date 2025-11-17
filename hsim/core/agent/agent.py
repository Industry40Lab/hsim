if __name__ == "__main__":
    import sys; import os
    # Cross-platform path handling
    abs_path = os.path.abspath(__file__)
    parts = abs_path.split(os.sep)
    if "hsim" in parts:
        hsim_index = parts.index("hsim")
        hsim_path = os.sep.join(parts[:hsim_index + 1])
        if hsim_path not in sys.path:
            sys.path.append(hsim_path)


from abc import ABC
from copy import copy
from typing import Any, Iterable, Union
from hsim.core.core.env import Environment
from hsim.core.fsm.FSM import FSM, get_class_dict
from hsim.core.core.msg import Message
from hsim.core.graphics import GraphicsMixin


class Agent(GraphicsMixin, ABC):
    stateMachine: FSM
    connections:dict[str,Union['Agent',Iterable['Agent']]]

    def __init__(self, env, name:str="", **graphics_kwargs):
        GraphicsMixin.__init__(self)
        self.env = env
        self.name = name
        self.var = dotdict()
        self._linkFSM()
        self.connections = {}
        env.add_agent(self)
        # Initialize graphics if any graphics parameters provided
        if graphics_kwargs:
            self.init_graphics(label=name, **graphics_kwargs)
    def _linkFSM(self):
        from hsim.core.fsm.FSM import FSM
        fsmList = get_class_dict(self, FSM)
        fsmList.append(FSM) if len(fsmList) == 0 else None
        for FSM in fsmList:
            fsm = FSM(self.env)
            name = FSM.__name__ if FSM.__name__ != "FSM" else "stateMachine"
            setattr(self, name, fsm)
            fsm._agent = self
    def activate_fsm(self):
        [fsm.start() for fsm in [x for x in self.__dict__.values() if isinstance(x,FSM)] if fsm.startable and not fsm.active]
    def deactivate_fsm(self):
        [fsm.stop() for fsm in [x for x in self.__dict__.values() if isinstance(x,FSM)] if fsm.active]
    def receive(self, message:Message):
        self.stateMachine.receive(message)
    def receiveContent(self, content:Any, sender=None) -> Message:
        return self.stateMachine.receiveContent(content, sender)
    def __lt__(self, other: Any) -> bool:
        return False
    def __repr__(self):
        name = self.name if self.name is not None else str(id(self))
        return f"{name}: {self.__class__.__name__}" 
    def mask(self,dict:dict={})->"Agent":
        newAgent = self.copy()
        for key in dict.keys():
            if not hasattr(self, key):
                raise AttributeError(f"Attribute {key} does not exists in {self}.")
            else:
                newAgent.__setattr__(key, dict[key])
        return newAgent
    def __hash__(self):
        if hasattr(self,"_copy"):
            return hash(self._copy)
        return super().__hash__()
    def copy(self):
        agentCopy = copy(self)
        agentCopy._copy = self
        return agentCopy

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
    

def test1():
    env = Environment()
    agent = Agent(env)
    print(agent.stateMachine)
    print(agent.stateMachine.states)
    print(agent.stateMachine.transitions)
    print(agent.stateMachine.current_state)
if __name__ == "__main__":
    test1()