# -*- coding: utf-8 -*-

import pymulate as pym
from chfsm import CHFSM, Transition, State
import pandas as pd
import numpy as np
from simpy import AnyOf

class Generator(pym.Generator):
    def __init__(self,env,name=None,serviceTime=1,serviceTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.count = 0
    def createEntity(self):
        self.count += 1
        # return Entity()
        return object()
        
    
class Entity:
    def __init__(self,ID=None):
        self.ID = ID
        self.ok = True
        self.pt = dict()
        self.pt['M3'] = 0
    @property
    def require_robot(self):
        if self.pt['M3']>0:
            return True
        else:
            return False
        
class Server(pym.Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        self.trigger = env.event()
        serviceTime = 10
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def completed(self):
        print(self,self.var.entity,self.env.now)
        if self.var.entity.ok:
            self.trigger.succeed()
            self.trigger.restart()
    T2=Transition.copy(pym.Server.Working, pym.Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)), action = lambda self: self.completed())

class Terminator(pym.Terminator):
    def __init__(self, env, capacity=np.inf):
        super().__init__(env, capacity)
        self.trigger = env.event()
    def completed(self):
        self.trigger.succeed()
        self.trigger.restart()
    def put(self,item):
        super().put(item)
        self.completed()
        
class Gate(CHFSM):
    def __init__(self,env,DR,OR):
        self.real = True
        self.freq = 120
        self.length = 300
        self.capacity = 20
        self.lab = None
        self.DR = DR
        self.OR = OR
        self.monitored_DBR = list()
        self.monitored_CONWIP = None
        self.initialWIP = 12
        super().__init__(env)
    def build(self):
        self.Store = pym.Store(self.env,self.capacity)
    def put(self,item):
        return self.Store.put(item)
    def load(self):
        self.initialWIP = self.initialWIP - 1
    class Waiting(State):
        initial_state = True
        def _do(self):
            try:
                e = self.Store.get()
                self.Next.put(e.value)
            except:
                print('Empty at %s' %self.env.now)
    class Controlling(State):
        initial_state = True
        def _do(self):
            if self.real:
                pass #run BN
    T0 = Transition.copy(Waiting,Waiting,lambda self: self.env.timeout(1) ,lambda self: self.initialWIP>0, lambda self: self.load())
    TA = Transition.copy(Waiting,Waiting,lambda self: AnyOf(self.env,self.monitored_DBR),lambda self: self.OR=='DBR')
    TB = Transition.copy(Waiting,Waiting,lambda self: self.monitored_CONWIP,lambda self: self.OR=='CONWIP')
    TC = Transition.copy(Controlling,Controlling,lambda self: self.env.timeout(self.freq))


class RobotSwitch1(pym.Router):
    def condition_check(self, item, target):
        if item.require_robot and type(target) == Server:
            return True
        elif not item.require_robot and type(target) != Server:
            return True
        else:
            return False
            
class RobotSwitch2(pym.Router):
    def condition_check(self, item, target):
        if len(target)<2:
            item.rework = False
            return True
        else:
            item.rework = True
            return False    

class CloseOutSwitch(pym.Router):
    def condition_check(self, item, target):
        if item.ok and type(target) == Terminator:
            return True
        elif not item.ok and type(target) != Terminator:
            return True
        else:
            return False
        
class Conveyor(pym.ParallelServer):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacity=1):
        self._capacity = capacity
        serviceTime = capacity*3.5
        super().__init__(env,name,serviceTime,serviceTimeFunction,capacity)

class Lab:
    def __init__(self,DR:str,OR:str,BN:str):
        self.env = pym.Environment()
        self.env.BN = None
        self.g = Generator(self.env)
        self.gate = Gate(self.env,DR,OR)
        
        self.conv1 = Conveyor(self.env,capacity=3)
        self.front = Server(self.env,'front')
        self.conv2 = Conveyor(self.env,capacity=3)
        self.drill = Server(self.env,'drill')
        self.conv3 = Conveyor(self.env,capacity=3)
        
        self.switch1 = RobotSwitch1(self.env)
        self.convRobot1 = Conveyor(self.env,capacity=3)
        self.bridge = Conveyor(self.env,capacity=3)
        self.convRobot2 = Conveyor(self.env,capacity=3)
        self.switch2 = RobotSwitch2(self.env)
        self.convRobot2 = Conveyor(self.env,capacity=3)
        self.convRobot3 = Conveyor(self.env,capacity=3)
        self.robot = Server(self.env,'robot')
        self.convRobotOut = Conveyor(self.env,capacity=3)
        self.conv5 = Conveyor(self.env,capacity=3)
        self.camera = Server(self.env,'camera')
        self.conv6 = Conveyor(self.env,capacity=3)
        self.back = Server(self.env,'back')
        self.conv7 = Conveyor(self.env,capacity=3)
        self.press = Server(self.env,'press')
        self.conv8 = Conveyor(self.env,capacity=10)
        self.manual = Server(self.env,'manual')
        self.outSwitch = CloseOutSwitch(self.env)
        self.terminator = Terminator(self.env)
        
        self.g.Next = self.gate
        self.gate.Next = self.conv1
        
        self.conv1.Next = self.front
        self.front.Next = self.conv2
        self.conv2.Next = self.drill
        self.drill.Next = self.conv3
        self.conv3.Next = self.switch1
        
        self.switch1.Next = [self.convRobot1,self.bridge]
        self.convRobot1.Next = self.switch2
        self.switch2.Next = [self.convRobot2,self.convRobot3]
        self.convRobot2.Next = self.robot
        self.convRobot3.Next = self.convRobotOut
        self.robot.Next = self.convRobotOut
        self.convRobotOut.Next = self.conv5
        self.bridge.Next = self.conv5
        
        self.conv5.Next = self.camera
        self.camera.Next = self.conv6
        self.conv6.Next = self.back
        self.back.Next = self.conv7
        self.conv7.Next = self.press
        self.press.Next = self.conv8
        self.conv8.Next = self.manual
        self.manual.Next = self.outSwitch
        self.outSwitch.Next = [self.conv1,self.terminator]
        
        self.gate.monitored_DBR = [x.trigger for x in [self.front,self.drill,self.robot,self.camera,self.back,self.press,self.manual]]
        self.gate.monitored_CONWIP = self.terminator.trigger

    def run(self,Tend):
        self.env.run(Tend)
        return pd.DataFrame(self.env.state_log)


lab=Lab('FIFO','CONWIP','PAST')
for i in range(3):
    lab.conv1.put(Entity())
lab.run(10000)

