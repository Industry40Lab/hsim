from pymulate import Server, Generator, Terminator
from env import Environment
from des import DESLocked

class Switch(DESLocked):
    pass



def test1():
    env = Environment()
    a = Generator(env)
    b = Server(env)
    s = Switch(env)
    c1 = Terminator(env)
    c2 = Terminator(env)
    a.connections["Next"] = b
    b.connections["Next"] = s
    s.connections["Next"] = [c1,c2]
    env.run(10)

if __name__ == "__main__":
    test1()