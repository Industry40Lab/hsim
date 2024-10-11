import pandas as pd
from simpy import Environment, Event
from simpy.core import BoundClass

from hsim.core.core.ev import ev


class Environment(Environment):
    def __init__(self,log=None,initial_time=0):
        super().__init__(initial_time)
        self._objects = list()
        # self.log = log
        # if log==None:
        #     self.log = createLog()        
        # self.state_log2 = pd.DataFrame(columns=['Resource','ResourceName','State','StateName','timeIn','timeOut'])
        self.state_log = list()
    def logF(self,entity,resource,operator,activity,time=True):
        if time:
            time = self.now
        [entity,operator]=[x if x is not None else "" for x in [entity,operator]]
        self.log.loc[(self.log["timeOut"]==-1) & (self.log["resource"]==resource),"timeOut"]=time
        self.log.loc[len(self.log)] = [entity,resource,operator,activity,time,-1]
    def run(self,until=None):
        at = float(until)
        if at <= self.now:
            print('Time %d <= %d (current time) --> executing until %d' %(at, self.now, at+self.now))
            at += self.now
        super().run(at)
    def add_object(self,obj):
        self._objects.append(obj)
    # state = BoundClass(State)
    event = BoundClass(Event)
    def threshold(self,value):
        th = ev(1)
        th.set_env(self)
        return th
    @property
    def log(self):
        return pd.DataFrame(self.state_log,columns=['Resource','ResourceName','State','StateName','entity','store','timeIn','timeOut'])
    #dangerous
    from warnings import warn
    warn('Bypassing "None" callbakcs')
    def step(self):
        if len(self._queue)>0:
            if self._queue[0][-1].callbacks is None:
                self._queue[0][-1].callbacks = []
        super().step()