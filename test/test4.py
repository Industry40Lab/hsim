# %% TESTS

from hsim.core.core import Environment
from hsim.core.stores import Store, Box
from hsim.core.pymulate import Server, ServerWithBuffer, ServerDoubleBuffer, Generator, Queue, ManualStation, Operator, OutputSwitch, Router, StoreSelect


if __name__ == '__main__' and 1:
    env = Environment()
    a = Server(env,serviceTime=1)
    a.Next = Store(env,5)
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if a.current_state[0]._name == 'Blocking' and len(a.Next) == 5:
        print('OK server')
        
if __name__ == '__main__' and 1:
    env = Environment()
    b = ServerWithBuffer(env,serviceTime=1)
    b.Next = Store(env,5)
    for i in range(1,10):
        b.QueueIn.put(i)
    env.run(10)
    if b.current_state[0]._name == 'Blocking' and len(b.Next) == 5:
        print('OK server with buffer')

if __name__ == '__main__' and 1:
    env = Environment()
    a = ServerDoubleBuffer(env,serviceTime=1,capacityOut=5)
    a.Next = Store(env,5)
    for i in range(1,10):
        a.QueueIn.put(i)
    env.run(10)
    if a.current_state[0]._name == 'Starving' and len(a.Next) == 5 and len(a.QueueOut) == 4:
        print('OK server with 2 buffers')

if __name__ == '__main__':
    env = Environment()
    a = Generator(env,serviceTime=1)
    a.Next = Store(env,5)
    env.run(5)
    if len(a.Next) == 4:
        print('OK generator')
    env.run(10)
    if len(a.Next) == 5:
        print('OK generator 2x')
        
if __name__ == '__main__':
    env = Environment()
    a = Queue(env,capacity=4)
    a.Next = Store(env,5)
    for i in range(1,10):
        a.Store.put(i)
    env.run(10)
    if a.current_state[0]._name == 'Forwarding' and len(a.Next) == 5 and len(a.Store) == 4:
        print('OK queue')
        
if __name__ == '__main__':
    env = Environment()
    a = ManualStation(env,serviceTime=1)
    b = Operator(env)
    b.var.station=[a]
    a.Next = Store(env,5)
    for i in range(1,10):
        a.Store.put(i)
    env.run(10)
    if b.current_state[0]._name == 'Idle' and len(a.Next) == 5 and a.current_state[0]._name == 'Blocking':
        print('OK manual station')

if __name__ == '__main__':
    env = Environment()
    a = Server(env,serviceTime=1)
    b = OutputSwitch(env)
    c = Store(env,1)
    d = Store(env)
    a.Next = b.Queue
    b.Next = [c,d]
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if len(c) == 1 and len(d) == 5:
        print('OK switch')

if __name__ == '__main__':
    env = Environment()
    a = Server(env,serviceTime=1)
    b = Router(env)
    c = Store(env,1)
    d = Store(env)
    a.Next = b.Queue
    b.Next = [c,d]
    for i in range(1,7):
        b.Queue.put(i)
    env.run(20)
    if len(c) == 1 and len(d) == 5:
        print('OK router')

if __name__ == '__main__':
    env = Environment()
    b = Router(env)
    c = Store(env,1)
    d = Queue(env,capacity=3)
    e = Server(env,serviceTime = 5)
    f = Store(env)
    a.Next = b.Queue
    b.Next = [d.Store,c]
    d.Next = e.Store
    e.Next = f
    for i in range(1,10):
        b.Queue.put(i)
    env.run(20)
    if len(c) == 1 and len(d) == 3:
        print('OK router')

if __name__ == '__main__' and 1 and True:
    env = Environment()
    a = Server(env,serviceTime=1)
    b = StoreSelect(env)
    c = Store(env,5)
    a.Next = b.Queue
    b.Next = c
    for i in range(1,7):
        a.Store.put(i)
    env.run(20)
    if len(c) == 5 and len(b.Queue) == 1:
        print('OK switch')

if __name__ == '__main__' and 1 and False:
    env = Environment()
    a = Queue(env)
    b = ServerDoubleBuffer(env,serviceTime=1,capacityOut=5)
    a.Next = b
    b.Next = Store(env,5)
    for i in range(1,10):
        a.put(i)
    env.run(10)
    if a.current_state[0]._name == 'Starving' and len(a.Next) == 5 and len(a.QueueOut) == 4:
        print('OK server with 2 buffers')
