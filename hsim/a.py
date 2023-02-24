# -*- coding: utf-8 -*-

import pymulate as pym
from chfsm import Transition


class Generator(pym.Generator):
    def createEntity(self):
        pass
    
class Entity:
    def __init__(self):
        self.ok = True
        
class Gate:
    pass

class GateCONWIP(Gate):
    T2=Transition.copy(Generator.Creating,Generator.Sending,lambda self: self.env.timeout(self.calculateServiceTime(None)))

class GateDBR(Gate):
    T2=Transition.copy(Generator.Creating,Generator.Sending,lambda self: self.env.timeout(self.calculateServiceTime(None)))



class Lab:
    def __init__(self,DR:str,OR:str,BN:str):
        self.env = pym.Environment()
        self.env.BN = None
        self.g = Generator(self.env)
        if OR == 'CONWIP':
            gate = GateCONWIP(self.env)
        elif OR == 'CONWIP':
            gate = GateDBR(self.env)
        
        self.conv1 = pym.ParallelServer(self.env,capacity=3)
        self.front = pym.Server(self.env)
        self.conv2 = pym.ParallelServer(self.env,capacity=3)
        self.drill = pym.Server(self.env)
        self.conv3 = pym.ParallelServer(self.env,capacity=3)
        self.switch = pym.Router(self.env)
        self.convRobot = pym.ParallelServer(self.env,capacity=3)
        self.bridge = pym.ParallelServer(self.env,capacity=3)
        self.conv4 = pym.ParallelServer(self.env,capacity=3)
        self.robot = pym.Server(self.env)
        self.conv5 = pym.ParallelServer(self.env,capacity=3)
        self.camera = pym.Server(self.env)
        self.conv6 = pym.ParallelServer(self.env,capacity=3)
        self.back = pym.Server(self.env)
        self.conv7 = pym.ParallelServer(self.env,capacity=3)
        self.press = pym.Server(self.env)
        self.conv8 = pym.ParallelServer(self.env,capacity=10)
        self.manual = pym.Server(self.env)
        
        self.conv1.Next = self.front
        self.front.Next = self.conv2
        self.conv2.Next = self.drill
        self.drill.Next = self.conv3
        self.conv3.Next = self.switch
        self.switch.Next = [self.convRobot,self.bridge]
        self.convRobot.Next = self.robot
        self.bridge.Next = self.conv5
        self.robot.Next = self.conv5
        self.conv5.Next = self.camera
        self.camera.Next = self.conv6
        self.conv6.Next = self.back
        self.back.Next = self.conv7
        self.conv7.Next = self.press
        self.press.Next = self.conv8
        self.conv8.Next = self.manual
        self.manual.Next = self.conv1





    def run(self,Tend):
        self.env.run(Tend)

