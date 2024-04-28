from salabim import Component, State
class Timeout(Component):
    def __init__(self, timeout=0):
        super().__init__()
        self.timeout = timeout
        self.state = State("timeout")
    def process(self):
        self.hold(self.timeout)
        self.state.trigger()
    def __call__(self)-> State:
        return self.state