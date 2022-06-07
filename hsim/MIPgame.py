# -*- coding: utf-8 -*-
"""
Created on Mon Jun  6 18:12:35 2022

@author: Lorenzo
"""

# MODEL

from pymulate import Store, Environment, Generator, Server, ServerDoubleBuffer, Operator, ManualStation, SwitchOut



env = Environment()

class gen_motor():
    def __init__(self):
        self.index = 0
    def __call__(self):
        self.index += 1
        return str('Motor %d' %self.index)
    
g_motor = Generator(env,'Motor Input',serviceTime=30,createEntity=gen_motor())
motor1 = Server(env,'motor1',serviceTime=2)
motor2a = ManualStation(env,serviceTime=2)
motor2b = ManualStation(env,serviceTime=2)
motor2c = ManualStation(env,serviceTime=2)
s_out = SwitchOut(env)

op1 = Operator(env, 'o1')
T = Store(env)

g_motor.connections['after'] = motor1
op1.var.station = [motor2a,motor2b,motor2c]
motor1.connections['after'] = s_out
s_out.connections['after'] = [motor2a,motor2b,motor2c]
# motor2.connections['after'] = motor3
s_out.put([1])
env.run(1000)