from hsim.core.core.event import Event
from hsim.core.core.thvar import ThVar


class ev(ThVar,Event):
    def threshold_fun(self,value):
        if not self.check(value) and not self._event.triggered:
            self.succeed()
    def set_env(self,env):
        super(Event,self).__init__(env)
        return self
    def triggered(self):
        return self._ok