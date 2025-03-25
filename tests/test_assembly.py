import unittest
from hsim.core.core.env import Environment
from hsim.core.des.assembly import Assembly, Frame
from hsim.core.agent.q import Queue
from hsim.core.agent.agent import Agent
from hsim.core.des.pymulate import Generator, Store, Server, Terminator, EmptyBuffer

class TestAssembly(unittest.TestCase):
    def test1(self):
        env = Environment()
        a = Assembly(env, size=2)
        q = Queue(env, 10)
        a.connections["next"] = q
        env.run(10)
        a.take(Agent(env, "test1"))
        a.take(Agent(env, "test2"), 1)
        env.run(20)

    def test2(self):
        env = Environment()
        g1 = Generator(env, Agent)
        g2 = Generator(env, Agent)
        a = Assembly(env)
        q = Queue(env, 10)
        g1.connections["next"] = a
        g2.connections["next"] = a
        a.connections["next"] = q
        env.run(10)
        x1 = Agent(env, "test1")
        a.take(x1)
        env.run(20)
        x2 = Agent(env, "test2")
        a.take(x2)
        env.run(30)

    def test3(self):
        env = Environment()
        g = Generator(env, Agent, serviceTime=1)
        q = EmptyBuffer(env, capacity=10)
        q2 = EmptyBuffer(env, capacity=10)
        s = Server(env, serviceTime=4.9)
        t = Terminator(env)
        g.connections["next"] = q
        q.connections["next"] = q2
        q2.connections["next"] = s
        s.connections["next"] = t
        env.run(1)
        env.run(20)
        print("Test 3 done")

    def test4(self):
        env = Environment()

        class F1(Frame):
            def define(self):
                A = Store(self.env, "A")
                B = Server(self.env, "B", serviceTime=1)
                C = Store(self.env, "C")
                self.input_ports[0].connections["next"] = A
                A.connections["next"] = B
                B.connections["next"] = C
                C.connections["next"] = self.output_ports[0]
                return {A, B, C}

        a = F1(env, inputPorts=1, outputPorts=1)
        g = Generator(env, Agent)
        t = Terminator(env)

        g.connections["next"] = a.input_ports[0]
        a.output_ports[0].connections["next"] = t
        env.run(30)
        print("done")


if __name__ == "__main__":
    unittest.main()
