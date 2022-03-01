# -*- coding: utf-8 -*-

# import pysim as ps
# pysim
# global log

# %% test switchOut FirstPortAvailable

import pysim_new as sim
import numpy as np

# %% single server

if 1:

    env = sim.Environment()
    Q1 = sim.Queue(env,'Q1',100)
    M1 = sim.Server(env,'M1',serviceTime=1)
    Q2 = sim.Store(env)
    
    M1.connections = {'after':Q2}
    Q1.connections = {'after':M1}
    
    for i in range(1,10,1):
        e=sim.Entity(i)
        Q1.put(e)
        
    env.run(100)
    
    data = sim.refineLog(env.log,env.now)
    sim.createGantt(data)

# %% Switch-in

if 1:

    env = sim.Environment()
    Q1 = sim.Queue(env,'Q1',100)
    Q2 = sim.Queue(env,'Q2',100)
    M1 = sim.Server(env,'M1',serviceTime=1)
    Q3 = sim.Store(env)
    S=sim.SwitchIn(env)
    
    M1.connections = {'after':Q3}
    Q1.connections = {'after':S}
    Q2.connections = {'after':S}
    S.connections = {'after':M1}
    
    for i in range(1,10,1):
        e=sim.Entity(i)
        Q1.put(e)
    for i in range(1,10,1):
        ee=sim.Entity(i-100)
        Q2.put(ee)
    env.run(100)
    
    data = sim.refineLog(env.log,env.now)
    sim.createGantt(data)

# %% Switch-out
if 1:
    env = sim.Environment()
    Q1 = sim.Queue(env,'Q',100)
    M1 = sim.Server(env,'M1',serviceTime=1)
    M2 = sim.Server(env,'M2',serviceTime=1)
    
    Q2 = sim.Store(env)
    Q3 = sim.Store(env)
    
    S=sim.SwitchFirst(env)
    
    M1.connections = {'after':Q3}
    M2.connections = {'after':Q3}
    
    Q1.connections = {'after':S}
    S.connections = {'after':[M1,M2]}
    
    for i in range(1,10,1):
        e=sim.Entity(i)
        Q1.put(e)
    env.run(10)
    
    data = sim.refineLog(env.log,env.now)
    sim.createGantt(data)

# %%

raise Exception()

env = sim.Environment()



Q1 = sim.Queue(env,'Q',100)
M1 = sim.Server(env,'M1',serviceTime=1)
M1.connections = {'before':Q1}

for i in range(10):
    e = sim.Entity(i)
    if np.random.uniform()<0.5:
        e.route=['M2']
    else:
        e.route =['M3']
    Q1.put(e)

env.run(10)

# %%

env = sim.Environment()

Q1 = sim.Queue(env,'Q1',100)
M1 = sim.Machine(env,'M1',serviceTime=1)
Q2 = sim.Queue(env,'Q2',2,route='M2')
M2 = sim.Machine(env,'M2',serviceTime=2,route=True)
Q3 = sim.Queue(env,'Q3',100,route='M3')
M3 = sim.Machine(env,'M3',serviceTime=2,route=True)
S = sim.SwitchOut(env, 'S')
Q4 = sim.Queue(env,'Q4',100)
Q5 = sim.Queue(env,'Q5',100)

env.process(M1.statemachine(Q1, S))
env.process(S.statemachine(M1, [M2,M3]))
# env.process(Q2.statemachine(S, M2))
# env.process(Q3.statemachine(S, M3))
env.process(M2.statemachine(S, Q4))
env.process(M3.statemachine(S, Q5))
env.process(Q4.statemachine(M2, []))
env.process(Q5.statemachine(M3, []))

for i in range(10):
    e = sim.Entity(i)
    if np.random.uniform()<0.5:
        e.route=['M2']
    else:
        e.route =['M3']
    Q1.put(e)

env.run(until=1000)


data = sim.refineLog(env.log,env.now)
queues = sim.readQueues(env.log,env.now)
sim.createGantt(data)


# %% test switchIn
import pysim as sim
import numpy as np

np.random.seed(2)

env = sim.Environment()

G1 = sim.EntityGenerator(env,'G1')
G2 = sim.EntityGenerator(env,'G2')
M1 = sim.Machine(env,'M1',serviceTime=10,serviceTimeFunction=np.random.exponential)
M2 = sim.Machine(env,'M2',serviceTime=10,serviceTimeFunction=np.random.exponential)
M3 = sim.Machine(env,'M3',serviceTime=5,serviceTimeFunction=np.random.exponential)
Q3 = sim.Queue(env,'Q3',20)
S = sim.SwitchIn(env, 'S')
T = sim.EntityTerminator(env,'T')

env.process(G1.generator())
env.process(G2.generator())


env.process(M1.statemachine(G1,S))
env.process(M2.statemachine(G2,S))

env.process(S.statemachine([M1,M2],Q3))
env.process(Q3.statemachine(S,M3))
env.process(M3.statemachine(Q3,T))

# env.process(S.statemachine([M1,M2],M3))
# env.process(M3.statemachine(S,T))

env.process(T.terminator(M3))

Tend = 60
log = sim.createLog()

env.run(until=Tend) 
data = sim.refineLog(env.log,env.now)
sim.createGantt(data)

# %%  test base linea

import pysim as sim
import numpy as np

class EntityGenerator(sim.EntityGenerator):
    def generator(self):
        while True:
            self.counter += 1
            T = dict()
            for i in self.listOfMachineNames:
                T[i] = round(np.random.exponential(10))
            entity = sim.Entity(self.counter,pt=T)
            self.put(entity)
            yield self.env.timeout(self.timeoutFcn())


env = sim.Environment()

Q1 = sim.Queue(env,'Q1',2)
Q2 = sim.Queue(env,'Q2',5)
Q3 = sim.Queue(env,'Q3',3)
Q4 = sim.Queue(env,'Q3',2)
M1 = sim.Machine(env,'M1')
M2 = sim.Machine(env,'M2')
M3 = sim.Machine(env,'M3')
M4 = sim.Machine(env,'M4')
M5 = sim.Machine(env,'M5')
M6 = sim.Machine(env,'M6')
M7 = sim.Machine(env,'M7')

G = EntityGenerator(env,'G')
G.listOfMachineNames = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7']

T = sim.EntityTerminator(env,'T')

env.process(G.generator())
env.process(M1.statemachine(G, Q1))
env.process(Q1.statemachine(M1,M2))
env.process(M2.statemachine(Q1,M3))
env.process(M3.statemachine(M2,Q3))
env.process(Q3.statemachine(M3,M4))
env.process(M4.statemachine(Q3,M5))
env.process(M5.statemachine(M4,Q4))
env.process(Q4.statemachine(M5,M6))
env.process(M6.statemachine(Q4,M7))
env.process(M7.statemachine(M6,T))

env.process(T.terminator(M7))


Tend = 0.5*60*60
log = sim.createLog()

env.run(until=Tend) 
data = sim.refineLog(env.log,env.now)
sim.createGantt(data)



# %% test base operatori

import pysim as sim
import numpy as np

class EntityGenerator(sim.EntityGenerator):
    def generator(self):
        while True:
            self.counter += 1
            T = dict()
            for i in self.listOfMachineNames:
                T[i] = round(np.random.exponential(10))
            entity = sim.Entity(self.counter,pt=T)
            self.put(entity)
            yield self.env.timeout(self.timeoutFcn())

env = sim.Environment()

M1 = sim.AssemblyStation(env, 'M1')
M2 = sim.SemiautMachine(env,'M2',setupTime=33)
M3 = sim.AssemblyStation(env, 'M3')
M4 = sim.AssemblyStation(env, 'M4')
M5 = sim.AssemblyStation(env, 'M5')
M6 = sim.SemiautMachine(env,'M6',setupTime=30)
M7 = sim.AssemblyStation(env, 'M7')
M8 = sim.AssemblyStation(env, 'M8')
M9 = sim.AssemblyStation(env, 'M9')

Q1 = sim.Queue(env,'Q1',100)
Q2 = sim.Queue(env,'Q2',5)
Q3 = sim.Queue(env,'Q3',10010)
Q4 = sim.Queue(env,'Q3',10010)

O1 = sim.Operator(env,'O1',[M1,M2,M3])
O2 = sim.Operator(env,'O2',[M4,M5,M6])
O3 = sim.Operator(env,'O3',[M7,M8,M9])

T = sim.EntityTerminator(env,'T')

G = EntityGenerator(env,'G')
G.listOfMachineNames = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7','M8','M9']

env.process(O1.statemachine())
env.process(O2.statemachine())
env.process(O3.statemachine())
env.process(G.generator())
env.process(M1.statemachine(G, Q1))
env.process(Q1.statemachine(M1,M2))
env.process(M2.statemachine(Q1,M3))
env.process(M3.statemachine(M2,Q3))
env.process(Q3.statemachine(M3,M4))
env.process(M4.statemachine(Q3,M5))
env.process(M5.statemachine(M4,Q4))
env.process(Q4.statemachine(M5,M6))
env.process(M6.statemachine(Q4,M7))
env.process(M7.statemachine(M6,M8))
env.process(M8.statemachine(M7,M9))
env.process(M9.statemachine(M8,T))

env.process(T.terminator(M9))

Tend = 0.5*60*60
env.run(until=Tend) 
data = sim.refineLog(env.log,env.now)
sim.createGantt(data)


