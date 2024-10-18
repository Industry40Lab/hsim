# -*- coding: utf-8 -*-

# %% 
from simpy import Environment    

env = Environment()
a = Store(env,1)
a.put('Test')

def test_s(store):
    s = store.get()
    sub = store.subscribe()
    store.put('Ciao')
    yield store._env.timeout(1)
    print(s.value)
    yield store._env.timeout(1)
    
env.process(test_s(a))
env.run(10)

# %% 

env = Environment()
a = Store(env,10)

def test_s(store):
    # ss = store.get()
    s = store.subscribe()
    store.put('Ciao')
    yield store._env.timeout(1)
    s.confirm()
    print(s.value)
    yield store._env.timeout(1)
    
env.process(test_s(a))
env.run(10)


# %% monitored type