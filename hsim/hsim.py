# -*- coding: utf-8 -*

import simpy
from simpy import Event, FilterStore, Process
from simpy.core import BoundClass
from heapq import heappop
import pandas as pd
import plotly.express as px
import numpy as np
import random as rnd
import re

from stores import Subscription, Store, Box
from core import Environment 



    
class Entity(object):
    def __init__(self,ID,pt={},st={},route=None,Tin=None,Tout=None,ProductCode=None):
        self.ID = ID
        self.pt = pt
        self.st = st
        self.route = route
        self.Tin = Tin
        self.Tout = Tout
        self.ProductCode = ProductCode

class Batch(Entity):
    def __init__(self,listofEntities=[],route=None,Tin=None,Tout=None,ProductCode=None):
        self.entity = listofEntities
        ID = np.random.randint(1,1000)
        if not listofEntities == []:
            ID = listofEntities[0].ID
            super().__init__(ID,pt=listofEntities[0].pt,route=None,Tin=None,Tout=None,ProductCode=None)
        else:
            super().__init__(ID,pt={},route=None,Tin=None,Tout=None,ProductCode=None)


            
        
    
class Element(object):
    def __init__(self,env,_objectType,name,capacity=1):
        self.env = env
        self._objectType = _objectType
        self.name = name
        self.store = Store(env,capacity)
        # self.resource = simpy.Resource(env,capacity)
    
   
  
    
class Server(object):
    def __init__(self, env, name, route=None, serviceTime=None, serviceTimeFunction=None, queueCapacity=1):
        self.env = env
        self._objectType = 'active'
        self.name = name
        self.initialState = self.Starve
        self.store = Store(env,1)
        self.entity = [] 
        self.route = route
        self.serviceTime = serviceTime
        self.serviceTimeFunction = serviceTimeFunction
        self.connections={'before':None,'after':None}
        self.set_state(self.initialState())
    def __call__(self,state=False):
        if state:
            self.state = state
        return self.env.process(self.state)
    def _save(self):
        return {'state':self.state,'entity':self.entity}
    def _load(self,x):
        self.state, self.entity = x['state'], x['entity']
    def set_state(self,state): # identical to __call__(state)
        self.state = self.env.process(state)
    def calcServiceTime(self):
        if self.serviceTimeFunction == None:
            if type(self.serviceTime)==int or type(self.serviceTime)==float:
                return self.serviceTime
            elif self.serviceTime == None:
                return self.entity.pt[self.name]
            elif len(self.serviceTime)==0:
                return self.entity.pt[self.name]
            elif len(self.serviceTime)>0:
                return self.serviceTime[0]
        elif self.serviceTimeFunction != None:
            if type(self.serviceTime)==int or type(self.serviceTime)==float:
                return self.serviceTimeFunction(self.serviceTime)
            elif self.serviceTime==None:
                return self.serviceTimeFunction(*self.entity.pt[self.name])
            elif len(self.serviceTime)==0:
                return self.serviceTimeFunction()
            elif len(self.serviceTime)>0:
                return self.serviceTimeFunction(*self.serviceTime)
    def put(self,entity):
        return self.store.put(entity)
    def get(self,caller,route=None):
        if route != None:
            g = self.store.get(lambda item: route == item.route[0])
            self.getQueue[caller] = g
            # self.store.get_queue = sortRequests()
            return g
        else:
            g = self.store.get()
            return g
    def Starve(self):
        self.env.logF(None, self.name, None, "Starve")
        self.request = self.store.subscribe()
        yield self.request
        self.entity = self.request.read()
        return self.set_state(self.Work())
    def Work(self):
        self.env.logF(self.entity.ID, self.name, None, "Work")
        pt = self.calcServiceTime()
        yield self.env.timeout(pt)
        return self.set_state(self.Block())
    def Block(self):
        self.env.logF(self.entity.ID, self.name, None, "Block")
        yield self.connections['after'].put(self.entity)
        self.request.confirm()
        return self.set_state(self.Starve())

class Assembly(Server):
    def __init__(self, env, name, route=None, maxOperators=1, serviceTime=None, serviceTimeFunction=None, queueCapacity=1):
        super().__init__(env, name, route, serviceTime, serviceTimeFunction,queueCapacity)
        self.waitOp = env.event()
        self.waitOp.succeed()
        self.operator = []
        self.operatorResource = simpy.Resource(env, capacity=maxOperators)
    def OpIn(self,operator):
        self.operator.append(operator)
        self.operatorResource.request()
        try:
            self.waitOp.succeed()
        except:
            print('WARNING: %s %s' %(self.name,operator))                
    def OpOut(self):
        self.operatorResource.release(self.operatorResource.users[0])
        operator = self.operator.pop()
        operator.ctrl.succeed()
        operator = None
    def Starve(self):
        self.env.logF(None, self.name, None, "Starve")
        self.request = self.store.subscribe()
        yield self.request
        self.entity = self.request.read()
        return self.set_state(self.Idle())
    def Idle(self):
        self.env.logF(None, self.name, None, "Idle")
        self.waitOp = self.env.event()
        yield self.waitOp
        return self.set_state(self.Work())
    def Work(self):
        self.env.logF(self.entity.ID, self.name, self.operator[0].name, "Work")
        pt = self.calcServiceTime()
        yield self.env.timeout(pt)
        self.OpOut()
        return self.set_state(self.Block())
    def Block(self):
        self.env.logF(self.entity.ID, self.name, None, "Block")
        yield self.connections['after'].put(self.entity)
        self.request.confirm()
        return self.set_state(self.Starve())

class Semiautomatic(Assembly):
    def __init__(self, env, name, route=None, maxOperators=1, serviceTime=None, serviceTimeFunction=None, queueCapacity=1, setupTime=None, setupTimeFunction=None):
        super().__init__(env, name, route, maxOperators, serviceTime, serviceTimeFunction,queueCapacity)
        self.setupTime = setupTime
        self.setupTimeFunction = setupTimeFunction
    def calcSetupTime(self):
            if self.setupTimeFunction == None:
                if type(self.setupTime)==int or type(self.setupTime)==float:
                    return self.setupTime
                elif self.setupTime == None:
                    return self.entity.st[self.name]
                elif len(self.setupTime)==0:
                    return self.entity.st[self.name]
                elif len(self.setupTime)>0:
                    return self.setupTime[0]
            elif self.setupTimeFunction != None:
                if type(self.setupTime)==int or type(self.setupTime)==float:
                    return self.setupTimeFunction(self.setupTime)
                elif self.setupTime==None:
                    return self.setupTimeFunction(*self.entity.st[self.name])
                elif len(self.setupTime)==0:
                    return self.setupTimeFunction()
                elif len(self.setupTime)>0:
                    return self.setupTimeFunction(*self.setupTime)
    def Idle(self):
        self.env.logF(None, self.name, None, "Idle")
        self.waitOp = self.env.event()
        yield self.waitOp
        return self.set_state(self.Setup())
    def Setup(self):
        self.env.logF(self.entity.ID, self.name, self.operator[0].name, "Setup")
        st = self.calcSetupTime()
        yield self.env.timeout(st)
        self.OpOut()
        return self.set_state(self.Work())
    def Work(self):
        self.env.logF(self.entity.ID, self.name, None, "Work")
        pt = self.calcServiceTime()
        yield self.env.timeout(pt)
        return self.set_state(self.Block())

class repeatMachine(Server):
    def __init__(self, env, name, route=None, failureProb=0, maxCapacity=1, serviceTime=None, serviceTimeFunction=None):
        super().__init__(env, name, route, failureProb, maxCapacity, serviceTime, serviceTimeFunction)
        self.failureProb = failureProb   
        self.TTR = 0
    def fail(self):
        x = -1 + np.random.geometric(1-self.failureProb)
        pt = self.calcServiceTime()
        self.TTR = x*pt
    def statemachine(self,before, after):
        while True:
            if self.state == 'Starve':
                logF(self.env.log, None, self.name, self.env.now, None, "Starve")
                # get entity
                if self.route == None:
                    entity, req = yield before.get(self.name) & self.acquire()
                else:
                    entity, req = yield before.get(self.name,self.name) & self.acquire()
                self.entity = entity.value
                # free before
                unlock(self.env,before,self.entity)
                self.fail()
                if self.TTR > 0:
                    self.state = 'Fail'
                else:
                    self.state = 'Work'
            # process
            if self.state == 'Work':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Work")
                pt = self.calcServiceTime()
                yield self.env.timeout(pt)
                self.state = 'Block'
            if self.state == 'Fail':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Fail")
                yield self.env.timeout(self.TTR)
                self.state = 'Work'
            # wait for next process
            if self.state == 'Block':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Block")
                self.put(self.entity)
                yield self.pause
                self.entity = []
                self.release()
                self.state = 'Starve'

class AssemblyStation(Server):
    def __init__(self, env, name, route=None, failureProb=0, maxCapacity=1, serviceTime=None, serviceTimeFunction=None):
        super().__init__(env, name, route, serviceTime, serviceTimeFunction)
        self.waitOp = env.event()
        self.waitOp.succeed()
        self.operator = []
        self.operatorResource = simpy.Resource(env, capacity=maxCapacity)
    def OpIn(self,operator):
        self.operator.append(operator)
        self.operatorResource.request()
        try:
            self.waitOp.succeed()
        except:
            print('WARNING: %s %s' %(self.name,operator))                
    def OpOut(self):
        self.operatorResource.release(self.operatorResource.users[0])
        operator = self.operator.pop()
        operator.ctrl.succeed()
        operator = None
    def statemachine(self,before,after):
        while True:
            if self.state == "Starve":
                logF(self.env.log, None, self.name, self.env.now, None, "Starve")
                if self.route == None:
                    entity, req = yield before.get(self.name) & self.acquire()
                else:
                    entity, req = yield before.get(self.name,self.name) & self.acquire()
                self.entity = entity.value
                unlock(self.env,before,self.entity)
                self.state = "Idle"
            elif self.state == "Idle":
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Idle")
                self.waitOp = self.env.event()
                # print('Station %s waiting for an operator at time %f' %(self.name,self.env.now))
                yield self.waitOp
                # print('Operator arrived at station %s at time %f' %(self.name,self.env.now))
                self.state = 'Work'
            elif self.state == 'Work':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, self.operator[0].name, "Work")
                pt = self.calcServiceTime()
                yield self.env.timeout(pt)
                self.OpOut()
                self.state = 'Block'
            elif self.state == 'Block':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Block")
                self.put(self.entity)
                yield self.pause
                self.entity = []
                self.release()
                self.state = 'Starve'

class SemiautMachine(AssemblyStation):
    def __init__(self, env, name, route=None, failureProb=0, maxCapacity=1, serviceTime=None, serviceTimeFunction=None, setupTime=None, setupTimeFunction=None):
        super().__init__(env, name, route, failureProb, maxCapacity, serviceTime, serviceTimeFunction)
        self.setupTime = setupTime
        self.setupTimeFunction = setupTimeFunction
    def calcSetupTime(self):
        if self.setupTimeFunction == None:
            if type(self.setupTime)==int or type(self.setupTime)==float:
                return self.setupTime
            elif len(self.setupTime)==1:
                return self.setupTime[0]
            elif len(self.setupTime)==0:
                return self.entity.setupTime[self.name]
        else:
            if type(self.setupTime)==int or type(self.setupTime)==float:
                return self.setupTimeFunction(self.setupTime)
            elif self.serviceTime==None:
                return self.setupTimeFunction(*self.entity.setupTime[self.name])
            elif len(self.setupTime)>0:
                return self.setupTimeFunction(*self.setupTime)
    def statemachine(self,before,after):
        while True:
            if self.state == 'Starve':
                logF(self.env.log, None, self.name, self.env.now, None, "Starve")
                if self.route == None:
                    entity, req = yield before.get(self.name) & self.acquire()
                else:
                    entity, req = yield before.get(self.name,self.name) & self.acquire()
                self.entity = entity.value
                unlock(self.env,before,self.entity)
                self.state = 'Idle'
            elif self.state == 'Idle':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Idle")
                self.waitOp = self.env.event()
                # print('Station %s waiting for an operator at time %f' %(self.name,self.env.now))
                yield self.waitOp
                # print('Operator arrived at station %s at time %f' %(self.name,self.env.now))
                self.state = 'Setup'
            elif self.state == 'Setup':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, self.operator[0].name, "Setup")
                st = self.calcSetupTime()
                yield self.env.timeout(st)
                self.OpOut()
                self.state = 'Work'
            elif self.state == 'Work':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Work")
                pt = self.calcServiceTime()
                yield self.env.timeout(pt)
                self.state = 'Block'
            elif self.state == 'Block':
                logF(self.env.log, self.entity.ID, self.name, self.env.now, None, "Block")
                self.put(self.entity)
                yield self.pause
                self.entity = []
                self.release()
                self.state = 'Starve'
    
class Operator(object):
    def __init__(self, env, name, station):
        self.env = env
        self.ctrl = env.event()
        self.state = 'idle'
        self.position = [0]
        self.station = station
        self.name = name
        self.currentStation = []
        self.target = None
        self.env.process(self.statemachine())
    def monitor(self):
        for i in reversed(self.station):
            if re.search('\(([^)]+)', i.state.__repr__()).group(1) == 'Idle' and i.operatorResource.users == []:
                self.target = i
                return
        self.target = None
        return
    def statemachine(self):
        while True: # setup come processo.
            # do monitoring routine
            # print('Operator %s activates at time %f' %(self.name,self.env.now))
            self.monitor()
            # yield self.env.process(self.monitor())
            if self.target==None:
                yield self.env.process(self.wait())
            else:
                yield self.env.process(self.work())   
    def work(self):
        # print('Operator %s enters station %s at time %f' %(self.name,self.target.name,self.env.now))
        self.target.OpIn(self)
        self.currentStation = self.target
        self.ctrl = self.env.event()
        yield self.ctrl
        # print('Operator %s leaves station %s at time %f' %(self.name,self.target.name,self.env.now))
        # # print('?')
        # return self.env.process(self.statemachine())
        return self.statemachine()
    def wait(self):
        lag = 1 # was working with: lag = 0.0123456789
        # # print('Operator %s passivates at %f to %f' %(self.name,self.env.now,self.env.peek()))
        timeList = [i[0] for i in self.env._queue if i[3].value != 'Operator']
        timeList = sorted(i for i in timeList if i>=self.env.now  and i < max(timeList)) #i-env.now>0
        if timeList == []:
            time = lag
        else:
            time = min(timeList) - self.env.now + lag
        yield self.env.timeout(time,'Operator')
        return self.statemachine()

class LineOperator(Operator):
    def __init__(self, env, name, station):
        super().__init__(env, name, station)
    def monitor(self):
        if self.station[-1].state == 'Block': # if last blocked, all blocked
            self.target = None
            return
        for i in reversed(self.station):
            if i.state == 'Idle' and i.operatorResource.users == []:
                self.target = i
                return
        self.target = None
        return

class QueueOld(object):
    def __init__(self, env, name, maxCapacity,route=None):
        self.env = env
        self._objectType = 'passive'
        self.name = name
        self.route = route
        self.entity = []
        self.store = Store(env, capacity=maxCapacity)
        self.resource = simpy.Resource(env, capacity=maxCapacity)
        self.pause = env.event()
        self.state = 0
    def __save__(self):
        return {'entity':self.store.items,'state':self.state}
    def __restore__(self,x):
        self.state = x['state']
        for entity in x['entity']:
            self.put(entity)
    def put(self,entity):
        # print('Entity %d was put in queue %s at %f' % (entity.ID, self.name, self.env.now))
        self.env.logF(None, self.name, None, +1 + len(self.store.items))
        self.state += 1
        return self.store.put(entity)
    def get(self,caller,route=None):
        self.env.logF(None, self.name, None, -1 + len(self.store.items))
        self.state -= 1
        if route != None:
            return self.store.get(lambda item: route == item.route[0])
        else:
            return self.store.get()
    def acquire(self):
        return self.resource.request()
    def release(self):
        self.resource.release(self.resource.users[0])
    def active(self,before,after):
        while True:
            # get entity
            if self.route == None:
                entity, req = yield before.get(self.name) & self.acquire()
            else:
                entity, req = yield before.get(self.name,self.route) & self.acquire()
            self.entity = entity.value
                            
            # free before
            unlock(self.env,before,self.entity)
            # process
            yield self.put(self.entity)
            self.release()
            if self.store.capacity == len(self.store.items):
                yield self.pause
            # wait for next process

class Queue(object):
    def __init__(self, env, name, maxCapacity,route=None):
        self.env = env
        self._objectType = 'passive'
        self.name = name
        self.route = route
        self.entity = []
        self.store = Store(env, capacity=maxCapacity)
        self.state = 0
        self.connections={'before':None,'after':None}
        self.set_state(self.Active())
    def __save__(self):
        return {'entity':self.store.items,'state':self.state}
    def __restore__(self,x):
        self.state = x['state']
        for entity in x['entity']:
            self.put(entity)
    def set_state(self,state):
        self.env.process(state)
    def put(self,entity):
        self.env.logF(None, self.name, None, +1 + len(self.store.items))
        self.state += 1
        return self.store.put(entity)
    def get(self,caller=None,route=None):
        self.env.logF(None, self.name, None, -1 + len(self.store.items))
        self.state -= 1
        if route != None:
            return self.store.get(lambda item: route == item.route[0])
        else:
            return self.store.get()
    def Active(self):
        request = self.store.subscribe()
        yield request
        yield self.connections['after'].put(request.read())
        request.confirm()
        return self.set_state(self.Active())

class Switch(object):
    def __init__(self,env):
        self.env = env
        self.store = Box(env)
        self.pause = env.event()
        self.connections={'before':None,'after':None}
        self.set_state(self.Passive())
        self.list_of_req = list()
    def set_state(self,state):
        self.state = self.env.process(state)
    def put(self,entity):
        if not self.pause.triggered:
            self.pause.succeed()
        self.state.interrupt()
        return self.store.put(entity)
    def Passive(self):
        try:
            if self.store.list_items == []:
                self.pause = self.env.event()
            yield self.pause
        except:
            pass
        finally:
            return self.set_state(self.Active())
    def Active(self):
        try:
            request, entity = self.store.requests[0]
            self.list_of_req = [after.store.subscribe(entity) for after in self.connections['after']]
            yield simpy.AnyOf(self.env,self.list_of_req)
            for req in self.list_of_req:
                if req.triggered:
                    req.confirm()
                    self.list_of_req.remove(req)
                    break
            self.store.forward(request)
        except:
            pass
        finally:
            for req in self.list_of_req:
                req.cancel()
            return self.set_state(self.Passive())

    
class SwitchIn(Switch):
    def Active(self):
        try:
            event, entity = self.store.requests[0]
            req = self.connections['after'].store.subscribe(entity)
            yield req
            req.confirm()
            self.store.forward(event)
        except:
            req.cancel()
        finally:
            return self.set_state(self.Passive())



class BatchCreator(Queue):
    def __init__(self, env, name, maxCapacity, batchSize):
        super().__init__(env, name, maxCapacity)
        self.batchSize = batchSize
        self.listofEntities = []
    def statemachine(self,before,after):
        while True:
            # get entity
            if self.route == None:
                entity = yield before.get(self.name)
            else:
                entity = yield before.get(self.name,self.name)
            self.listofEntities.append(entity)
            # free before
            unlock(self.env,before,self.entity)
            # process
            if not self.listofEntities[0].ProductCode==self.listofEntities[-1].ProductCode:
                entity, self.listofEntities = self.entity[0:-1], self.listofEntities[-1]
                entity = Batch(entity)
                yield self.put(entity)
            else:
                if len(self.listofEntities)==self.batchSize:
                    entity = Batch(self.listofEntities)
                    self.listofEntities = []
                    yield self.put(entity)

            # wait for next process
        
class BatchSplitter(Queue):
    def __init__(self, env, name):
        super().__init__(env, name, maxCapacity=1)
        self.listofEntities = []
    def statemachine(self,before,after):
        while True:
            # get entity
            if self.route == None:
                entity = yield before.get(self.name)
            else:
                entity = yield before.get(self.name,self.name)
            self.listofEntities = entity.entity
            # free before
            unlock(self.env,before,self.entity)
            # process
            while len(self.listofEntities)>0:
                entity = self.listofEntities.pop(0)
                self.put(entity)
                yield self.pause
            # wait for next process
        
class EntityTerminator(object):
    def __init__(self, env, name):
        self.env = env
        self.name = name
        self._objectType = "active"
        self.store = simpy.Store(env)
        self.route = None
    def put(self,entity):
        # print('Entity %d was destroyed by entity terminator %s at %f' % (entity.ID, self.name, self.env.now))
        return self.store.put(entity)
    def terminator(self, before):
        while True:
            entity = yield before.get(self.name)
            unlock(self.env,before,entity)
            self.put(entity)

class EntityTerminatorWithOrders(EntityTerminator):
    def terminator(self, before, orders):
        while True:
            # Get event for message pipe
            entity = yield before.get(self.name)
            # before.resource.release(before.resource.users[0]) # to be validated, was working when on
            unlock(self.env,before,entity)
            orders.data.loc[orders.data["ID"]==entity.ID,"Dispatched"] = self.env.now
            self.put(entity)
            # print('Completed entity %s at %f' % (entity.ID, env.now))

class EntityGenerator(object):
    def __init__(self, env, name, timeoutValue=1,maxCapacity=1):
        self.env = env
        self.name = name
        self._objectType = "active"
        self.store = simpy.FilterStore(env,maxCapacity)
        self.pause = env.event()
        self.waitOrders = env.event()
        self.timeoutValue = timeoutValue
        self.counter = 0
        self.connections={'before':None,'after':None}
    def set_state(self,state):
        self.state = self.env.process(state)
    def put(self,entity):
        return self.store.put(entity)
    def get(self,caller):
        return self.store.get()
    def timeoutFcn(self):
        return self.timeoutValue
    def generator(self):
        while True:
            self.counter += 1
            entity = Entity(self.counter)
            self.put(entity)
            yield self.env.timeout(self.timeoutFcn())
            
class EntityGeneratorWithOrders(EntityGenerator):
    def generator(self, orders):
        i = 0
        while True:
            # entity = Entity(i,[np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180)])
            if i < len(orders.data):
                entity = Entity(orders.data["ID"][i])
                for j in range(9):
                    M = str()
                    M = str("M%d" %(j+1))
                    entity.pt[M]=orders.data[M][i]
                entity.route = orders.data["Route"][i]
                orders.data["Released"][i] = self.env.now
                # readEntityData()
                self.put(entity)
                yield self.pause
                i += 1
            else:
                yield self.waitOrders
            # logF(entity.ID,after.name,self.env.now,"Wait",1)
            # while True: # CONWIP
            #     yield terminator.next()
            #     # aggiungi input terminator
            # aggiungi al terminator l'evento come attribute e inizializzalo. 
            # Ogni entity che arriva fai .succeed() e riavvialo.  


        
class SwitchIn_old(object):
    def __init__(self,env,name,route=None):
        self.env = env
        self._objectType = 'temporary'
        self.name = name
        self.store = simpy.FilterStore(env,1)
        self.resource = simpy.Resource(env,1)
        self.request = []
        self.state = 'Idle'
        self.pause = self.env.event()
        self.flag = True
        self.route = route    
    def get(self,caller,route=None):
        self.pause.succeed()
        if route != None:
            return self.store.get(lambda item: route == item.route[0])
        else:
            return self.store.get()
    def put(self,entity):
        self.store.put(entity)
    def statemachine(self,list_of_before,after):
        pass
    def Idle(self):
        self.pause = self.env.event()
        yield self.pause
        self.set_state(self.Active())
    def Active(self):
        self.flag = True
        list_of_before = self.connections['before']
        rnd.shuffle(list_of_before) # random active input port
        self.list_of_req = []
        for before in list_of_before:
            self.list_of_req.append(before.subscribe())
        entity = yield simpy.AnyOf(self.env, self.list_of_req)
        # select one, cancel the rest
        self.put(entity)
        self.set_state(self.Active())

                
class SwitchOut(object):
    def __init__(self,env,name,route=False):
        self.env = env
        self._objectType = 'temporary'
        self.name = name
        self.store = simpy.FilterStore(env,1)
        self.resource = simpy.Resource(env,1)
        self.request = []
        self.state = 'Idle'
        self.pause = self.env.event()
        self.list_of_callers = []
        self.flag = True
        self.route = route
    def get(self,caller,route=None):
        if not self.pause.triggered:
            self.pause.succeed()
        get = self.store.get()
        get.details = (caller, route, self.env.now)
        return get
    def put(self,entity):
        self.store.put(entity)
    def Waiting(self):
        self.pause = self.env.event()
        yield self.pause
        return self.set_state(self.Searching())
    def Searching(self):
        sub = yield self.connections['before'].subscribe()
        entity = sub.read()
        if not self.switch(entity):
            return self.set_state(self.Waiting())
        self.put(entity)
        sub.confirm()
        if self.store.get_queue:
            return self.set_state(self.Searching())
        else:
            return self.set_state(self.Waiting())
    def switch(self,entity):
        
        for req in self.store.get_queue:
            pass
        return True
        
        
    def statemachine(self,before,list_of_after):
        while True:
            
            self.state = 'Waiting'
            # if before st
            self.flag = False
            if before.store.items == []:
                entity = yield before.get(None)
            else:
                self.flag = True
                entity = before.store.items[0]
            
            self.state = 'Triggered'
                            
            # remove triggered requests
            # old_req = [i for i in self.list_of_callers if i[0].triggered]
            old_req = [req for req in self.list_of_callers if req[0] not in req[0].resource.get_queue]
            for i in old_req:
                self.list_of_callers.remove(i)
            # self.list_of_callers = [req for req in self.list_of_callers if req[0] in req[0].resource.get_queue]
            
            # sort according to list_of_after
            res = [tuple for x in [i.name for i in list_of_after] for tuple in self.list_of_callers if tuple[1] == x]
          
            # routing
            if self.route:
                if entity.route != None and entity.route != []:
                    # with_routing = [after.route for after in list_of_after if after.route]
                    res = [r for r in res if r[2] not in [after.route for after in list_of_after if after.route] or r[2] in entity.route[0]]
                # temp
                res = [r for r in res if r[1] not in [after.name for after in list_of_after if after.route==[]] or entity.route == [[]]]
            
            # save get_queue with sorted req
            # self.store.get_queue = [i[0] for i in res]
            
            # test-working
            new_queue = [i[0] for i in res]
            self.store.get_queue = new_queue + [req for req in self.store.get_queue if req not in new_queue]

            if new_queue != []: # it was self.store.get_queue and it was not working
                if self.flag:
                    before.get(None)
                self.put(entity)
                unlock(self.env,before,entity)
            elif new_queue == []: # it was self.store.get_queue and it was not working
                if not self.flag:
                    before.store.items.insert(0,entity)
                self.state = 'Paused'
                yield self.pause

class SwitchOutSafer(SwitchOut):
    def get(self,caller,route=None):
        if not self.pause.triggered:
            self.pause.succeed()
            self.pause = self.env.event()
        if route != None:
            time = self.env.now
            try:
                x = min([len(i.route[0]) for i in self.store.items])
                get = self.store.get(lambda item: route == item.route[0])
            except:
                get = self.store.get()
            self.list_of_callers.append((get,caller,route,time))
            return get
        else:
            time = self.env.now
            get = self.store.get()
            self.list_of_callers.append((get,caller,time))
            return get
            
class Orders():
    def __init__(self,n_orders,n_pt=9):
        self.n_pt = n_pt
        self.data = self.newOrders(n_orders,n_pt,n0=0,curTime=0)    
    def newOrders(self,n,n_pt,n0,curTime):
        x = []
        for i in range(n):
            x.append([])
            x[i].append(i+1+n0)
            for j in range(n_pt):
                x[i].append(60+np.random.exponential(60))
            x[i].append(curTime)
            x[i].append(None)
            x[i].append(None)
            x[i].append(self.setRoute(x[i]))
        return pd.DataFrame(np.array(x), columns = ['ID','M1','M2','M3','M4','M5','M6','M7','M8','M9','Recieved','Released','Dispatched','Route'])
    def addOrders(self,n,curTime=0):
        n0=len(self.data)
        x = self.newOrders(n,self.n_pt,n0,curTime)
        self.data = self.data.append(x,ignore_index=True)
    def clear(self):
        self.data=[]
    def getValues(self,line):
        return self.data.values[line].tolist()
    def setRoute(self,values):
        y = []
        for i in [i for i, x in enumerate([i>0 for i in values[1:10]]) if x]:
            M = str()
            M = str("M%d" %(i+1))
            y.append(M)
        return y

def genOrders(env,generator,orders):
    while True:
        yield env.timeout(10000)
        orders.addOrders(10,env.now)
        try:
            generator.waitOrders.succeed()
            generator.waitOrders = env.event()
        except:
            pass

def generator(env, generator, orders):
    i = 0
    while True:
        # entity = Entity(i,[np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180),np.random.exponential(180)])
        if i < len(orders.data):
            entity = Entity(orders.data["ID"][i])
            for j in range(9):
                M = str()
                M = str("M%d" %(j+1))
                entity.pt[M]=orders.data[M][i]
            entity.route = orders.data["Route"][i]
            orders.data["Released"][i] = env.now
            # readEntityData()
            generator.put(entity)
            yield generator.pause
            i += 1
        else:
            yield generator.waitOrders
        # logF(entity.ID,after.name,self.env.now,"Wait",1)
    # while True: # CONWIP
    #     yield terminator.next()
    #     # aggiungi input terminator
        # aggiungi al terminator l'evento come attribute e inizializzalo. 
        # Ogni entity che arriva fai .succeed() e riavvialo.     
    
def terminator(env, terminator, before, orders):
    while True:
        # Get event for message pipe
        entity = yield before.get(terminator.name)
        # before.resource.release(before.resource.users[0]) # to be validated, was working when on
        unlock(env,before,entity)
        orders.data.loc[orders.data["ID"]==entity.ID,"Dispatched"] = env.now
        terminator.put(entity)
        # print('Completed entity %s at %f' % (entity.ID, env.now))
      


def connectSwitch_2_1(env, switch, before, after): # before --> list of before
    while True:
        if after._objectType == 'active':
            req, dummy = yield after.startWorking() & switch.acquire()
        else:
            req, dummy = yield after.acquire() & switch.acquire()
        for i in range(len(before)):
            entity = before[i].get(switch.name)
            served = before[i]
            if entity.triggered:
                entity = entity.value
                break
            elif i==-1+len(before):
                before[i].store.get_queue.remove(entity)
                # --- edit this to add as many output ports as needed
                with before[0].get(switch.name) as req0, before[1].get(switch.name) as req1:
                    entity = yield simpy.AnyOf(env, [req0,req1])
                # ---
                x = [entity.events[0].resource == x.store for x in before].index(True)
                # if entity.events[0].resource == before[1].store:
                served = before[x]
                entity = entity.events[0].value
                break
            else:
                before[i].store.get_queue.remove(entity)
        switch.put(entity)
        # print('Entity %d was grabbed by switch %s at time %f' % (entity.ID, switch.name, env.now))
        unlock(env,served,entity)
        if after._objectType == 'active':
            after.stopWorking()
        else:
            after.release()
        switch.release()

def unlock(env, before, entity=None):
    if before._objectType == 'active':
        before.pause.succeed()
        before.pause = env.event()
    elif before._objectType == 'temporary':
        pass
        # before.pause.succeed()
        # before.pause = env.event()
    elif before._objectType == 'passive':
        before.pause.succeed()
        before.pause = env.event()
        # before.release()
    else:
        print('Warning - unlock fcn')
        before.pause.succeed()
        before.pause = env.event()
        # logF(entity.ID, before.name, env.now, "Wait", 0)





def refineLog(log,now):
    data = log.copy(deep=True)
    data = data.drop(data.loc[data.timeOut-data.timeIn<=1e-6].index).reset_index(drop=True)
    data.loc[(data["timeOut"]<=0) & (data["timeIn"]<=0),"timeOut"] = now # or now to close every log to end of sim time
    data.loc[data["timeOut"]<=0,"timeOut"] = now # or now to close every log to end of sim time
    data["timeIn"]=pd.to_timedelta(data.timeIn,unit='s')
    data["timeOut"]=pd.to_timedelta(data.timeOut,unit='s')
    today = pd.Timestamp(year=pd.Timestamp("today").year,month=pd.Timestamp("today").month, day=pd.Timestamp("today").day, hour=8)
    data["timeIn"] += today
    data["timeOut"] += today
    data = data.drop(data.loc[[type(i) == int for i in data.activity.values.tolist()]].index) # drop queueing
    data = data.drop(data.loc[data.timeOut-data.timeIn==pd.Timedelta(0)].index).reset_index(drop=True)
    return data

def readQueues(log,now):
    data = log.copy(deep=True)
    data.loc[data["timeOut"]<=0,"timeOut"] = now # or now to close every log to end of sim time
    data["timeIn"]=pd.to_timedelta(data.timeIn,unit='s')
    data["timeOut"]=pd.to_timedelta(data.timeOut,unit='s')
    today = pd.Timestamp(year=pd.Timestamp("today").year,month=pd.Timestamp("today").month, day=pd.Timestamp("today").day, hour=8)
    data["timeIn"] += today
    data["timeOut"] += today    
    queue = data.loc[[type(i) == int for i in data.activity.values.tolist()]].copy(deep=True)
    return queue

def createGantt(data):
    fig = px.timeline(data, x_start="timeIn", x_end="timeOut", y="resource", color="activity", text='entity', opacity=0.5)
    fig.write_html('gantt.html')

def build():
    env = simpy.Environment()
    # global log
    # log = pd.DataFrame(columns = ["entity","resource","activity","timeIn","timeOut"])       
    orders=Orders(50)
    Q1 = Queue(env,'Q1',1)
    Q2 = Queue(env,'Q2',1)
    Q3 = Queue(env,'Q3',1)
    Q4 = Queue(env,'Q4',1)
    M1 = Machine(env,'M1',failureProb=0.3)
    M2 = Machine(env,'M2',failureProb=0.1,route='M2')
    M3 = Machine(env,'M3',failureProb=0.2)
    M4 = Machine(env,'M4')
    M5 = Machine(env,'M5')
    M6 = Machine(env,'M6')
    M7 = Machine(env,'M7')
    T = EntityTerminator(env,'T')
    S = Switch(env,'S')
    G = EntityGenerator(env,'G')
    # env.process(generator(env, G, orders))
    # env.process(connect(env,M1,G,Q1))
    # env.process(connect(env,Q1,M1,M2))
    # env.process(connect(env,M2,Q1,M3))
    # env.process(connect(env,M3,M2,Q3))
    # env.process(connect(env,Q3,M3,M4))
    # env.process(connect(env,M4,Q3,M5))
    # env.process(connect(env,M5,M4,Q4))
    # env.process(connect(env,Q4,M5,[]))
    # env.process(connect(env,M6,Q4,S))
    # env.process(connectSwitch_2_1(env,S,[M6,Q4],M7))
    # env.process(connect(env,M7,S,T))
    # env.process(terminator(env,T,M7,orders))
    # env.process(genOrders(env, G, orders))
    obj = [Q1,Q2,Q3,Q4,M1,M2,M3,M4,M5,M6,M7,T,S,G]
    return env, obj, orders
# env, obj, orders = build()


global log
def createLog():
    global log
    log = pd.DataFrame(columns = ["entity","resource","operator","activity","timeIn","timeOut"])  
    return log
createLog()

