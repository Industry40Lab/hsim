from typing import Iterable, List, Union
from agent import Agent
from event import AnyEvent, ConditionEvent
from pymulate import Server, Generator, Terminator
from env import Environment
from des import DESLocked

class Switch(DESLocked):
    """Multi-purpose switch block that can be used to route entities to different outputs based on a condition.
    MIMO by design.
    store:Queue capacity is infinite by default.
    """
    def on_receive(self) -> None:
        """Triggered when an item is received from the store. It inspects the store and posts the item to the next agents.
        """
        item, _ = self.store.inspect()
        self.multipost(self.pick(agent=item),item)
    def pick(self,agent=None) -> Union[List[Server],Server]:
        return self.connections["next"]
    def decide(self,*events):
        """Switches between available outputs, chosing the first one that is available.
        """
        index = [event.verify() for event in events].index(True)
        msg = events[index].arguments[0]
        msg.receiver._put(msg)
        self.store.receive(msg.content)
        self.store.pull(msg.content) 
    def multipost(self,nexts:Iterable[Agent], item:Agent):
        """Tries to give an item to multiple outputs.

        Args:
            nexts (Iterable[Agent])
            item (Agent)
        """
        events, _ = zip(*[next.post(item) for next in nexts])
        master = AnyEvent(self.env, events=events, priority=0, action=self.decide).add()


def test1():
    env = Environment()
    a = Generator(env,agent_function=lambda self: Agent(env))
    b = Server(env)
    s = Switch(env)
    c1 = Terminator(env)
    c2 = Terminator(env)
    a.connections["next"] = b
    b.connections["next"] = s
    s.connections["next"] = [c1,c2]
    env.run(10)
    print(1)

if __name__ == "__main__":
    test1()