from typing import Any, Iterable, Union
from env import Environment
from abc import ABC
from FSM import FSM, get_class_dict
from msg import Message

          
class Agent(ABC):
    stateMachine: FSM
    connections:dict[str,Union['Agent',Iterable['Agent']]] = {}

    def __init__(self, env, name:str=""):
        self.env = env
        self.name = name
        self.var = dotdict()
        self._linkFSM()
        env.add_agent(self)
    def _linkFSM(self):
        from FSM import FSM
        fsmList = get_class_dict(self, FSM)
        fsmList.append(FSM) if len(fsmList) == 0 else None
        for FSM in fsmList:
            fsm = FSM(self.env)
            name = FSM.__name__ if FSM.__name__ != "FSM" else "stateMachine"
            setattr(self, name, fsm)
            fsm._agent = self
    def activate_fsm(self):
        [fsm.start() for fsm in [x for x in self.__dict__.values() if isinstance(x,FSM)] if fsm.startable and not fsm.active]
    def receive(self, message:Message):
        self.stateMachine.receive(message)
    def receiveContent(self, content:Any, sender=None) -> Message:
        return self.stateMachine.receiveContent(content, sender)
    def __lt__(self, other: Any) -> bool:
        return False


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