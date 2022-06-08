# -*- coding: utf-8 -*-


from pymulate import Store, Queue, Environment, Generator, Server, ServerWithBuffer, ServerDoubleBuffer, Operator, ManualStation, SwitchOut

from pymulate import SwitchQualityMIP


env = Environment()

class gen_motor():
    def __init__(self):
        self.index = 0
    def __call__(self):
        self.index += 1
        return [str('Motor %d' %self.index)]
    
    

# %% case 
    
g_case = Generator(env,'Motor Input',serviceTime=1,createEntity=gen_motor())

case0 = ManualStation(env)
case1 = ServerDoubleBuffer(env,'motor1',serviceTime=1,capacityIn = 4, capacityOut = 4)

case2queueIn = Queue(env,capacity = 4)
case2switch = SwitchOut(env)
case2a = ManualStation(env,serviceTime=600)
case2b = ManualStation(env,serviceTime=600)
case2c = ManualStation(env,serviceTime=700)
case2queueOut = Queue(env,capacity = 4)

case3queueIn = Queue(env,capacity = 4)
case3switch = SwitchOut(env)
case3a = ManualStation(env,serviceTime=600)
case3b = ManualStation(env,serviceTime=600)
case3c = ManualStation(env,serviceTime=700)
case3queueOut = Queue(env,capacity = 4)

case4queueIn = Queue(env,capacity = 4)
case4 = Server(env,serviceTime=600)
case4queueOut = Queue(env,capacity = 4)
case4quality = SwitchQualityMIP(env)

case5queueIn = Queue(env,capacity = 4)
case5switch = SwitchOut(env)
case5a = ManualStation(env,serviceTime=600)
case5b = ManualStation(env,serviceTime=600)
case5c = ManualStation(env,serviceTime=700)
case5queueOut = Queue(env,capacity = 4)

case6queueIn = Queue(env,capacity = 4)
case6switch = SwitchOut(env)
case6a = ManualStation(env,serviceTime=600)
case6b = ManualStation(env,serviceTime=600)
case6c = ManualStation(env,serviceTime=700)
case6queueOut = Queue(env,capacity = 4)


# %% electonics

g_ele = Generator(env,'Motor Input',serviceTime=100,createEntity=gen_motor())

ele1 = ServerWithBuffer(env,'ele1',serviceTime=1,capacityIn = 4)
ele2 = ServerDoubleBuffer(env,'ele2',serviceTime=1,capacityIn = 4, capacityOut = 4)

ele_line1 = Queue(env)
ele_line2 = ManualStation(env,serviceTime=600)
ele_line3 = Queue(env)
ele_line4 = ManualStation(env,serviceTime=600)
ele_line5 = Queue(env)
ele_line6 = ManualStation(env,serviceTime=600)
ele_line7 = Queue(env)

ele_line8 = ServerDoubleBuffer(env,'ele2',serviceTime=1,capacityIn = 4, capacityOut = 4)
ele_scrap = Store(env)

# %% final

final1case = Store(env)
final1ele = Store(env)
final2assebly = AssemblyMIP(env)
final2inspect = Server(env,serviceTime=1)

final3 = Queue(env)
final4pack = ManualStation(env)
final5pallet = ManualStation(env)

# %% connect
g_case.connections['after'] = case0

case0.connections['after'] = case1

case1.connections['after'] = case2queueIn

case2queueIn.connections['after'] = case2switch
case2switch.connections['after'] = [case2a,case2b,case2c]
case2a.connections['after'] = case2queueOut
case2b.connections['after'] = case2queueOut
case2c.connections['after'] = case2queueOut
case2queueOut.connections['after'] = case3queueIn

case3queueIn.connections['after'] = case3switch
case3switch.connections['after'] = [case3a,case3b,case3c]
case3a.connections['after'] = case3queueOut
case3b.connections['after'] = case3queueOut
case3c.connections['after'] = case3queueOut
case3queueOut.connections['after'] = case4queueIn



case4queueOut.connections['after'] = case5queueIn

case5queueIn.connections['after'] = case5switch
case5switch.connections['after'] = [case5a,case5b,case5c]
case5a.connections['after'] = case5queueOut
case5b.connections['after'] = case5queueOut
case5c.connections['after'] = case5queueOut
case5queueOut.connections['after'] = case6queueIn

case6queueIn.connections['after'] = case6switch
case6switch.connections['after'] = [case6a,case6b,case6c]
case6a.connections['after'] = case6queueOut
case6b.connections['after'] = case6queueOut
case6c.connections['after'] = case6queueOut
case6queueOut.connections['after']

g_motor2 = Generator(env,'Motor Input',serviceTime=100,createEntity=gen_motor())
T2 = Store(env)
T3 = Store(env)
sw=SwitchQualityMIP(env,'a')
g_motor2.connections['after'] = sw
sw.connections['after'] = T2
sw.connections['rework'] = T3

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