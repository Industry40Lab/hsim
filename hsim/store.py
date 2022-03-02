# -*- coding: utf-8 -*-
"""
Created on Sat Jan 15 14:54:49 2022

@author: Lorenzo
"""

from simpy import Event, FilterStore
from heapq import heappop

class Subscription(Event):
    # just like Get & Put events, but it does not get/put anything unless told to do so
    def __init__(self, resource, item=None):
        super().__init__(resource._env)
        self.resource = resource
        self.proc = self.env.active_process
        self.item = item
        if not self.item:
            self.__append__(self,resource.get_queue)
            resource._trigger_get(None)
        else:
            self.__append__(self,resource.put_queue)
            resource._trigger_put(None)
    def __append__(self,obj,container):
        container.append(obj)
    def renounce(self):
        # to be triggered if refusing to get/put after subscribing
        if self.item:
            self.resource._do_get()
        else:
            self.resource._do_put(self)
    def confirm(self,item=None):
        if not self.item:
            self._value = self.resource.get_now()
            return self.value
        else:
            if item:
                self.item = item
            self.resource.put_now(self)
    def read(self):
        return self.resource.items[0]

# !! OLD !!
# class Subscription(Event):
#     # just like Get & Put events, but it does not get/put anything
#     def __init__(self, resource, get_subscription):
#         super().__init__(resource._env)
#         self.resource = resource
#         self.proc = self.env.active_process
#         if get_subscription:
#             self.__append__(self,resource.get_queue)
#             resource._trigger_get(None)
#         else:
#             self.__append__(self,resource.put_queue)
#             resource._trigger_put(None)
#     def __append__(self,obj,container):
#         if container == []:
#             container.append(obj)
#         else:
#             container.insert(container.index(next(x for x in container if not isinstance(x,Subscription))),self)
    
class Store(FilterStore):
    def subscribe(self,item=None):
        return Subscription(self,item)
    def _do_get(self, event):        
        if self.items:
            if not isinstance(event,Subscription):
                event.succeed(self.items.pop(0))
                return
            else:
                event.succeed()
                return True
    def _do_put(self, event):
        if len(self.items) < self._capacity:
            event.succeed()
            if not isinstance(event,Subscription):
                self.items.append(event.item)
                return 
            else:
                return True
    def get_now(self):
        return self.items.pop(0)
    def put_now(self,event):
        self.items.append(event.item)
            

# %% 
from simpy import Environment    

env = Environment()
a = Store(env,1)
a.put('Test')

def test_s(store):
    s = store.get()
    sub = store.subscribe()
    store.put('Ciao')
    yield store._env.timeout(1)
    print(s.value)
    yield store._env.timeout(1)
    
env.process(test_s(a))
env.run(10)

# %% 

env = Environment()
a = Store(env,10)

def test_s(store):
    # ss = store.get()
    s = store.subscribe()
    store.put('Ciao')
    yield store._env.timeout(1)
    s.confirm()
    print(s.value)
    yield store._env.timeout(1)
    
env.process(test_s(a))
env.run(10)


# %% monitored type

    
    