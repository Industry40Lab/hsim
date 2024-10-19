import pymulate as pym
import numpy as np
from random import choices, expovariate

def newEntity():
    e = Entity()
    e.serviceTime['front'] = 10.52
    e.serviceTime['drill'] = choices([3.5, 8.45, 9.65, 11.94], weights=[5,30,30,35])[0]
    e.serviceTime['robot'] = choices([0, 81, 105, 108 ,120], weights=[91,3,2,2,2])[0]
    e.serviceTime['camera'] = 3.5 + expovariate(1/7.1)
    e.serviceTime['back'] = choices([3.5,10.57], weights=[0.1,0.9])[0]
    if e.serviceTime['back'] > 0:
        e.serviceTime['press'] = 3.5 + expovariate(1/9.5)
    else:
        e.serviceTime['press'] = 3.5
    e.serviceTime['manual'] = max(np.random.normal(9.2, 1), 0)
    return e

class Generator(pym.Generator):
    def __init__(self, env, name=None, serviceTime=2, serviceTimeFunction=None):
        super().__init__(env, name, agent_function=newEntity, serviceTime=serviceTime, serviceTimeFunction=serviceTimeFunction)
        self.count = 0

class Entity:
    def __init__(self, ID=None):
        self.ID = ID
        self.rework = False
        self.serviceTime = dict()

    @property
    def require_robot(self):
        return self.serviceTime['robot'] > 0

    @property
    def ok(self):
        return not (self.rework and self.require_robot)

    def done(self):
        self.rework = False

class LabServer(pym.Server):
    def __init__(self, env, name=None, serviceTime=None, serviceTimeFunction=None):
        super().__init__(env, name, serviceTime, serviceTimeFunction)
        self.controller = None

    def calculateServiceTime(self, entity=None, attribute='serviceTime'):
        if not entity.ok:
            return 3.5
        else:
            return super().calculateServiceTime(entity, attribute)

    def completed(self):
        if self.var.item.ok:
            self.controller.Messages.put(self.name)

    class FSM(pym.Server.FSM):
        T2 = pym.TimeoutTransition.define(pym.Server.FSM.Working, pym.Server.FSM.Blocking)
        T2.on_transition = lambda self: self.completed()
        
        T3 = pym.EventTransition.define(pym.Server.FSM.Blocking, pym.Server.FSM.Starving)
        T3.on_transition = lambda self: [self.give(self.connections["next"], self.var.item),
                                         self.var.request.confirm(),
                                         self.var.item.done() if self.name == 'robot' else None]

class Terminator(pym.Terminator):
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.controller = None
        self.register = list()

    def on_receive(self):
        self.register.append(self._env.now)
        self.controller.Messages.put('terminator')
        super().on_receive()


import pymulate as pym
from hsim.core.core.event import AnyEvent

class Router(pym.Switch):
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.sent = []

    def condition_check(self, item, target):
        return True

    def pick(self, agent=None):
        return [next for next in self.connections["next"] if self.condition_check(agent, next)]

    def on_receive(self):
        item, _ = self.store.inspect()
        self.multipost(self.pick(item), item)

# The subclasses remain the same
class RobotSwitch1(Router):
    def condition_check(self, item, target):
        if item.require_robot:
            item.rework = True
        if item.require_robot and target.name == 'convRobot1S':
            return True
        elif not item.require_robot and target.name != 'convRobot1S':
            return True
        else:
            return False

class RobotSwitch2(Router):
    def condition_check(self, item, target):
        if len(target.connections["next"]) < 2:
            item.rework = False
            return True
        else:
            item.rework = True
            return False

class CloseOutSwitch(Router):
    def condition_check(self, item, target):
        if item.ok and isinstance(target, pym.Terminator):
            return True
        elif not item.ok and not isinstance(target, pym.Terminator):
            return True
        else:
            return False