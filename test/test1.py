from hsim.core import Environment, ev, thvar

try:
    a=thvar(2)
    a<<=1
except:
    pass

try:
    env=Environment()

    a=ev(1)
    a.set_env(env)
except:
    pass

try:
    env=Environment()
    b=env.threshold(1)
except:
    pass
    
try:
    a<<=3
    a+=3
except:
    pass