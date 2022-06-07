# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 18:12:35 2022

@author: Lorenzo
"""

# MODEL

from pymulate import Store, Environment, Generator, Server, ServerDoubleBuffer, Operator, ManualStation






env = Environment()
class gen_motor():
    def __init__(self):
        self.index = 0
    def __call__(self):
        self.index += 1
        return str('Motor %d' %self.index)
g_motor = Generator(env,'Motor Input',serviceTime=30,createEntity=gen_motor())
motor1 = Server(env,'motor1',serviceTime=2)
T = Store(env)

g_motor.connections['after'] = motor1
motor1.connections['after'] = T
# motor2.connections['after'] = motor3
env.run(3600)