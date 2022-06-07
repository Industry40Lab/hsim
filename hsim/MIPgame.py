# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 18:12:35 2022

@author: Lorenzo
"""

# MODEL

from pymulate import Environment, Generator, ServerDoubleBuffer, Operator, AssemblyStation






env = Environment()
def gen_motor():
    return 'Motor'
g_motor = Generator(env,'Motor Input',serviceTime=30,createEntity=gen_motor)
motor1 = ServerDoubleBuffer(env,'motor1')

g_motor.connections['after'] = motor1
motor1.connections['after'] = motor2
motor2.connections['after'] = motor3
           