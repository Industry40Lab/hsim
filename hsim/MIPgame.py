# -*- coding: utf-8 -*-


from pymulate import Store, Environment, Generator, Server, ServerDoubleBuffer, Operator, ManualStation, SwitchOut



env = Environment()

class gen_motor():
    def __init__(self):
        self.index = 0
    def __call__(self):
        self.index += 1
        return [str('Motor %d' %self.index)]
    
    

    
    
g_motor = Generator(env,'Motor Input',serviceTime=1,createEntity=gen_motor())
motor1 = Server(env,'motor1',serviceTime=1)
motor2a = ManualStation(env,serviceTime=600)
motor2b = ManualStation(env,serviceTime=600)
motor2c = ManualStation(env,serviceTime=700)
s_out = SwitchOut(env)



T = Store(env)

g_motor.connections['after'] = motor1
motor1.connections['after'] = s_out
s_out.connections['after'] = [motor2a,motor2b,motor2c]

for s in [motor2a,motor2b,motor2c]:
    s.connections['after']=T 
# motor2.connections['after'] = motor3
# s0=s_out.Queue.sub1
env.run(2000)

from utils import stats
s = stats(env)