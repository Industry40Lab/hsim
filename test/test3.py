from hsim.core.core import Environment
from hsim.core.stores import Store, Box
from simpy import AnyOf, Resource
        
if __name__ == "__main__":  
    env = Environment()
    R = Resource(env)
    S = Store(env,1)
    S.put(1)
    r=R.demand()
    s=S.put(1)
    r=R.demand()
    a=AnyOf(env,[s,r])


    env = Environment()
    a=Box(env)
    
    print(a.items,a.put_queue)
    req=a.subscribe(1)
    print(a.items,a.put_queue)
    req2=a.subscribe(2)
    print(a.items,a.put_queue)
    
    env.run(1)
    print(req.triggered)
    r=a.subscribe()
    env.run(10)
    print(a.items)
    z=r.confirm()
    print(a.items)
    env.run(20)