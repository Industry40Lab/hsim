# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 15:43:09 2022

@author: Lorenzo
"""

from simpy import Environment
import pandas as pd
import numpy as np
from pysim_new import Environment, Server, Queue, Subscription, Store

class DataPoint():
    pass  

class Program(object):
    def __init__(self,name=None):
        self.name = name
        self._count = -1
        self.steps = list()
        self.active = False
        self.done = False
    def start(self):
        self.count = -1
        self.active = True
    def stop(self):
        self.active = False
    def step(self):
        self.count += 1
        if self.count == len(self.steps):
            self.stop()
            self.done = True
    def count(self):
        return self._count
    def get(self):
        self.step()
        if self.active:
            parameters = self.steps[self._count]
            return parameters, self.active
        else:
            return None, self.active   
        
class Entity():
    def __init__(self,ID,program=None):
        self.ID = ID
        self.program = program

class Robot(Server):
    def __init__(self,env,name):
        super().__init__(env, name)
        self.trigger = env.event()
        self.power = pd.DataFrame([],columns=['program','timeIn','powerIn','timeOut','powerOut'])
        self.programs = dict()
        self.active_program = None
    def start_program(self,*args):
        self.active_program = self.entity.program # TEMPORARY
        self.active_program.start()
    def stop_program(self):
        self.active_program.stop()
        self.active_program = None
    def compute_parameters(self,parameters): # TEMPORARY
        # delay = 10*np.random.uniform()
        # E0 = np.random.uniform()
        # E1 = np.random.uniform()
        delay = parameters[0].sample().item()
        E0 = parameters[2].sample().item()
        E1 = parameters[3].sample().item()
        return delay, E0, E1
    def Starve(self):
        self.env.logF(None, self.name, None, "Starve")
        # self.entity = yield self.connections['before'].get(self)
        self.req = self.connections['before'].store.subscribe()
        yield self.req
        self.entity = self.req.confirm()
        print('Entity %s in station %s at %f' %(self.entity.ID,self.name,self.env.now))
        return self.set_state(self.Work())
    def Work(self):
        self.env.logF(self.entity.ID, self.name, None, "Work")
        self.start_program() 
        while True:
            parameters, new_operation = self.active_program.get()
            if new_operation:
                yield self.env.process(self.operation(parameters))
            else:
                break
        req = self.connections['after'].store.subscribe(self.entity)
        print('Entity %s out station %s at %f' %(self.entity.ID,self.name,self.env.now))
        return self.set_state(self.Block(req))
    def Block(self,req):
        self.env.logF(self.entity.ID, self.name, None, "Block")
        yield req
        req.confirm()
        return self.set_state(self.Starve())
    def operation(self,parameters):
        try:
            delay, E0, E1= self.compute_parameters(parameters)
            self.power = self.power.append({'program':self.active_program.name,'timeIn':self.env.now,'powerIn':E0},ignore_index=True)
            yield self.env.timeout(delay)
            self.power.loc[len(self.power)-1,['timeOut','powerOut']] = [self.env.now, E1]
        except:
            pass

# %%         

# p = Program('P1')  
# p.steps=[[],[],[],[],[],[]]    

env = Environment()
K1 = Robot(env,'KUKA_1')
K2 = Robot(env,'KUKA_2')

# K1.programs[p.name] = p
# A.active_program = p.name

Q1 = Queue(env,'Q1',10)
Q2 = Queue(env,'Q2',2)
Q3 = Queue(env,'Q3',10)

for i in range(10):
    program = Program('a')
    # program.steps = [[i] for i in range(np.random.randint(1,10))]
    program.steps = program_steps
    entity = Entity(i+1,program)
    Q1.put(entity)



K1.connections = {'before': Q1, 'after':Q2}
K2.connections = {'before': Q2, 'after':Q3}

        
env.run(1)
env.run(600)

from pysim_new import refineLog, createGantt

data = refineLog(env.log,env.now)
createGantt(data)

# %% temp
data=data.loc[data.resource=='KUKA_2']
data.loc[data.resource=='KUKA_2','resource']="KUKA"
createGantt(data)
