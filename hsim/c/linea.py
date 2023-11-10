# -*- coding: utf-8 -*-

from sys import path
path.append('C://Users//Lorenzo//GitHub//hsim')

import hsim.pymulate as pym
from hsim.chfsm import CHFSM, Transition, State
import pandas as pd
import numpy as np
from simpy import AnyOf
from copy import deepcopy
from random import choices,seed,normalvariate, expovariate
from hsim.stores import Store, Box       
from scipy import stats
import dill
import hsim.utils as utils

class Generator(pym.Generator):
    def __init__(self,env,name=None,serviceTime=2,serviceTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.count = 0
        self.WIPcount = 0
        self.WIP = 5
        self.Go = env.event()
        self.Go.succeed()
    def addUp(self):
        self.var.entity.systemTime = -self.env.now
        self.Go.restart()
        if self.current_state[0].name == 'Sending':
            self.WIPcount += 1
        if self.WIPcount < self.WIP and not self.Go.triggered:
            self.Go.succeed()
    def createEntity(self):
        self.count += 1
        # return Entity()
        e = Entity()
        # e.serviceTime = dict()
        e.serviceTime['front'] = 10.52
        e.serviceTime['drill'] = choices([3.5, 8.45, 9.65, 11.94],weights=[5,30,30,35])[0]
        e.serviceTime['robot'] = choices([0, 81, 105, 108 ,120],weights=[91,3,2,2,2])[0]
        # e.serviceTime['camera'] = choices([3,9,12,18,24],weights=[2,3,1,2,2])[0]
        e.serviceTime['camera'] = 3.5+expovariate(1/7.1)
        e.serviceTime['back'] = choices([3.5,10.57],weights=[0.1,0.9])[0]
        # e.serviceTime['press'] = choices([3,9,15])[0]
        if e.serviceTime['back']>0:
            e.serviceTime['press'] = 3.5+expovariate(1/9.5)
        else:
            e.serviceTime['press'] = 3.5
        e.serviceTime['manual'] = max(np.random.normal(9.2,1),0)
        return e
    T1=Transition(pym.Generator.Sending,pym.Generator.Creating,lambda self: self.Next.put(self.var.entity),action=lambda self:self.addUp())
    # T2=Transition(pym.Generator.Creating,pym.Generator.Sending,lambda self: self.env.timeout(self.calculateServiceTime(None)), condition=lambda self:self.count<=self.WIP)
    # T2a=Transition(pym.Generator.Creating,pym.Generator.Sending,lambda self: self.Go, action=lambda self:self.Go.restart())
    T2=Transition(pym.Generator.Creating,pym.Generator.Sending,lambda self:self.Go,action=lambda self:self.addUp())

class Entity:
    def __init__(self,ID=None):
        self.ID = ID
        self.ok = True
        self.serviceTime = dict()
        self.systemTime = 0
    @property
    def require_robot(self):
        if self.serviceTime['robot']>0:
            return True
        else:
            return False
                
class LabServer(pym.Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,failure_rate=0,TTR=60):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.var.failure_rate = failure_rate
        self.var.TTR = TTR
    def calculateServiceTime(self,entity=None,attribute='serviceTime'):
        if not entity.ok:
            return 3.5
        else:
            return super().calculateServiceTime(entity,attribute)
    class Fail(State):
        pass
    class Starving(State):
        initial_state = True
        def _do(self):
            self.var.request = self.Store.subscribe()
    T1 = None
    S2F = Transition(Starving, Fail, lambda self: self.var.request, condition=lambda self: np.random.uniform() < self.var.failure_rate)
    S2W = Transition(Starving, pym.Server.Working, lambda self: self.var.request)
    F2W = Transition(Fail, pym.Server.Working, lambda self: self.env.timeout(self.var.TTR))
    T3=Transition(pym.Server.Blocking, Starving, lambda self: self.Next.put(self.var.entity),action=lambda self: self.var.request.confirm())


class Terminator(pym.Terminator):
    def __init__(self, env, capacity=np.inf):
        super().__init__(env, capacity)
        self.controller = None
        self.register = list()
    def completed(self):
        if not self.trigger.triggered:
            self.trigger.succeed()
    def put(self,item):
        self.register.append(self._env.now)
        self.controller.Messages.put('terminator')
        return super().put(item)
    def subscribe(self,item):
        self.register.append(self._env.now)
        item.systemTime += self._env.now
        if not self.generator.Go.triggered:
            self.generator.Go.succeed()
        return super().subscribe(item)
          
class Router(pym.Router):
    def __deepcopy(self,memo):
        super().deepcopy(self,memo)
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.sent = []
        self.putEvent = env.event()
    def build(self):
        self.Queue = Box(self.env)
    def condition_check(self,item,target):
        return True
    def put(self,item):
        if self.putEvent.triggered:
            self.putEvent.restart()
        self.putEvent.succeed()
        return self.Queue.put(item)
    class Sending(State):
        initial_state = True
        def _do(self):
            self.sm.putEvent.restart()
            self.sm.var.requestIn = self.sm.putEvent
            self.sm.var.requestOut = [item for sublist in [[next.subscribe(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
            if self.sm.var.requestOut == []:
                self.sm.var.requestOut.append(self.sm.var.requestIn)
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut),condition=lambda self:self.var.requestOut != [])
    def action2(self):
        self.Queue._trigger_put(self.env.event())
        if not hasattr(self.var.requestOut[0],'item'):
            return
        for request in self.var.requestOut:
            if not request.item in self.Queue.items:
                request.cancel()
                continue
            if request.triggered:
                if request.check():
                    request.confirm()
                    self.Queue.forward(request.item)
                    continue
    S2S2._action = action2

class RobotSwitch1(Router):
    def condition_check(self, item, target):
        if item.require_robot and target.name == 'convRobot1S':
            return True
        elif not item.require_robot and target.name != 'convRobot1S':
            return True
        else:
            return False
            
class RobotSwitch2(Router):
    def condition_check(self, item, target):
        if len(target.Next)<2:
            item.rework = False
            return True
        else:
            item.rework = True
            return False    

class CloseOutSwitch(Router):
    def condition_check(self, item, target):
        if item.ok and type(target) == Terminator:
            return True
        elif not item.ok and type(target) != Terminator:
            return True
        else:
            return False
        
class Conveyor(pym.Server):
    def __init__(self,env,name=None,serviceTime=6):
        super().__init__(env,name,serviceTime)


# %%
if __name__ == '__main__':
    env = pym.Environment()
    g = Generator(env)
    
    # self.conv1 = Conveyor(self.env,capacity=3)
    conv1S = Conveyor(env)
    conv1Q = pym.Queue(env,capacity=2)
    front = LabServer(env,'front')
    # conv2 = Conveyor(env,capacity=3)
    conv2S = Conveyor(env)
    conv2Q = pym.Queue(env,capacity=2)
    drill = LabServer(env,'drill')
    # conv3 = Conveyor(env,capacity=3)
    conv3S = Conveyor(env)
    conv3Q = pym.Queue(env,capacity=2)
    
    switch1 = RobotSwitch1(env)
    # convRobot1 = Conveyor(env,'convRobot1',capacity=3)
    convRobot1S = Conveyor(env,name='convRobot1S')
    convRobot1Q = pym.Queue(env,capacity=2)
    
    # bridge = Conveyor(env,capacity=3)
    bridgeS = Conveyor(env)
    bridgeQ = pym.Queue(env,capacity=2)
    
    # convRobot2 = Conveyor(env,'convRobot2',capacity=3)
    convRobot2S = Conveyor(env)
    convRobot2Q = pym.Queue(env,capacity=2)
    
    switch2 = RobotSwitch2(env)
    # convRobot3 = Conveyor(env,capacity=3)
    convRobot3S = Conveyor(env)
    convRobot3Q = pym.Queue(env,capacity=2)
    
    robot = LabServer(env,'robot')
    # convRobotOut = Conveyor(env,capacity=3)
    convRobotOutS = Conveyor(env)
    convRobotOutQ = pym.Queue(env,capacity=2)
    # conv5 = Conveyor(env,capacity=3)
    conv5S = Conveyor(env)
    conv5Q = pym.Queue(env,capacity=2)
    
    camera = LabServer(env,'camera')
    # conv6 = Conveyor(env,capacity=3)
    conv6S = Conveyor(env)
    conv6Q = pym.Queue(env,capacity=2)
    
    back = LabServer(env,'back')
    # conv7 = Conveyor(env,capacity=3)
    conv7S = Conveyor(env)
    conv7Q = pym.Queue(env,capacity=2)
    
    press = LabServer(env,'press')
    # conv8 = Conveyor(env,capacity=3)
    conv8S = Conveyor(env)
    conv8Q = pym.Queue(env,capacity=2)
    
    manual = LabServer(env,'manual')
    outSwitch = CloseOutSwitch(env)
    terminator = Terminator(env)
    
    g.Next = conv1S
    
    # conv1.Next = front
    conv1S.Next = conv1Q
    conv1Q.Next = front
    
    front.Next = conv2S
    # conv2.Next = drill
    conv2S.Next = conv2Q
    conv2Q.Next = drill
    drill.Next = conv3S
    conv3S.Next = conv3Q
    conv3Q.Next = switch1
    # conv3.Next = switch1
    
    switch1.Next = [convRobot1S,bridgeS]
    convRobot1S.Next = convRobot1Q
    convRobot1Q.Next = switch2
    
    switch2.Next = [convRobot2S,convRobot3S]
    convRobot2S.Next = convRobot2Q
    convRobot2Q.Next = robot
    
    convRobot3S.Next = convRobot3Q
    convRobot3Q.Next = convRobotOutS
    
    robot.Next = convRobotOutS
    convRobotOutS.Next = convRobotOutQ
    
    convRobotOutQ.Next = conv5S
    bridgeS.Next = bridgeQ
    bridgeQ.Next = conv5S
    
    conv5S.Next = conv5Q
    conv5Q.Next = camera
    
    camera.Next = conv6S
    conv6S.Next = conv6Q
    conv6Q.Next = back
    
    back.Next = conv7S
    conv7S.Next = conv7Q
    conv7Q.Next = press
    
    press.Next = conv8S
    conv8S.Next = conv8Q
    conv8Q.Next = manual
    
    manual.Next = outSwitch
    outSwitch.Next = [conv1S,terminator]
    
    terminator.generator = g
    
    env.run(1800)