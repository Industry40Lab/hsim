from typing import Any, Callable
import salabim as sim

from hsim.core.StateMachine import StateMachine
from hsim.core.MachineState import MachineState



class Trigger(sim.Component):
    pass

class Timeout(sim.Component):
    def __init__(self, timeout=0):
        self.timeout = timeout
        self.state = sim.State("timeout")
        super().__init__()
    def process(self):
        self.hold(self.timeout)
        self.state.trigger(True)
        self.state.set(True)
        


class Car(StateMachine):
    def __init__(self, env = None, name: str = "", **kwargs):
        super().__init__(name, env, **kwargs)
        self.stopped = sim.State()
        self.stopped.trigger(True)
        self._states = [self.Moving, self.Parking]
    # def process(self):
    #     self.start()
    # def start(self):
    #     self._states[0]._do()
    class Moving(MachineState):
        initial_state = True
        def _do(self):
            while True:
                print("Car is moving %d"%self.env.now())
                self.hold(5)
                print("Car finished moving %d"%self.env.now())
                # self.wait(Timeout(10).value)
                return self.sm._states[1]()
    class Parking(MachineState):
        def _do(self):
            while True:
                print("Car is parked %d"%self.env.now())
                # self.hold(5)
                self.to = Timeout(10)
                print(self.to)
                self.a=self.wait(self.to.state)
                print("car is restarting %d"%self.env.now())
                return self.sm._states[0]()
            
class Broker(sim.Component):
    def process(self):
        # print("Broker is starting")
        self.hold(7)
        self.c.stopped.trigger(True)


env = sim.Environment(trace=1)
c=Car()
# b=Broker()
# b.c = c

env.run(till=200)
print(1)
