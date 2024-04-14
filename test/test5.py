import numpy as np
from hsim.core.core import Environment
from hsim.core.pymulate import Server, ServerWithBuffer, ServerDoubleBuffer, Generator, Queue, ManualStation, Operator, OutputSwitch, Router, StoreSelect
from hsim.core.MIP import MachineMIP
from hsim.core.stores import Store
from hsim.core.utils import stats

if True:
    env = Environment()
    a = MachineMIP(env,serviceTime=1,failure_rate=1,TTR=3)
    a.Next = Store(env,10)
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if a.current_state[0]._name == 'Working' and len(a.Next) == 4:
        print('OK server') 
    
if True:
    env = Environment()
    a = ServerDoubleBuffer(env,'1',1,np.random.exponential)
    # a.put([1])
    # op = Operator(env, 'op1')
    # op.var.station = [a]
    b = Store(env,20)
    a.connections['after']=b
    g = Generator(env, 'g',0.5)
    g.connections['after'] = a
    env.run(20)

if True:
    env = Environment()
    g = Generator(env,serviceTime=1)
    b = Queue(env)
    c = Store(env)
    g.connections['after'] = b
    b.connections['after'] = c
    env.run(10)
    s = stats(env)

