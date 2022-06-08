# -*- coding: utf-8 -*-
"""
Created on Sat Jan 15 14:54:49 2022

@author: Lorenzo
"""
from heapq import heappop

from simpy import Event, FilterStore, Resource


class Subscription(Event):
    # just like Get & Put events, but it does not get/put anything unless told to do so
    def __init__(self, resource, item=None):
        super().__init__(resource._env)
        self.resource = resource
        self.proc = self.env.active_process
        self.item = item
        self._ok = False
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
            self.resource._trigger_put(None)
            return self.value
        else:
            if item:
                self.item = item
            self.resource.put_now(self.item)
            self.resource._trigger_get(None)
    def read(self):
        return self.resource.items[0]
    def check(self):
        if self.item and len(self.resource.items) < self.resource._capacity:
            return True
        elif len(self.resource.items)>0:
            return True
        else:
            return False
    def cancel(self):
        if not self.triggered:
            self.resource.put_queue.remove(self)
    
    
class Store(FilterStore):
    def __len__(self):
        return len(self.items)
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
        # self._trigger_put(None)
        return self.items.pop(0)
    def put_now(self,item):
        self.items.append(item)
        # self._trigger_get(None)
    

class Box_v1(Store):
    def _do_put(self, event):
        if True: # put is always allowed
            if not isinstance(event,Subscription):
                # self.items.append(event.item)
                return 
            else:
                return True
    def forward(self,event):
        event.succeed()
        self.put_queue.remove(event)
    @property
    def list_items(self):
        return [event.item for event in self.put_queue]
    @property
    def requests(self):
        return [(event,event.item) for event in self.put_queue]

class Box(Store):
    def _do_put(self, event):
        if not hasattr(event,'_ok'):
            event._ok = False
        if not event.ok: # put is always allowed
            event._ok = True
            self.items.append(event.item)
        return True
    def forward(self,event):
        if event not in self.put_queue:
            for (item,new_event) in self.requests:
                if event is item:
                    event = new_event
        if event in self.put_queue:
            event.succeed()
            self.put_queue.remove(event)
    @property
    def list_items(self):
        return [event.item for event in self.put_queue]
    @property
    def requests(self):
        return [(event,event.item) for event in self.put_queue]
    def as_dict(self):
        result = dict()
        for event in reversed(self.put_queue):
            result.update({event:event.item})
        return result
    def get(self,*args):
        raise NotImplementedError
    def get_now(self):
        x = self.items.pop(0)
        self.forward(x)
        return x


class Resource(Resource):
    def __init__(self,env,capacity=1):
        super().__init__(env,capacity)
        self.items = self.users
    def __len__(self):
        return len(self.items)
    def demand(self):
        return Demand(self,None)
    def forget(self,user=object()):
        return Demand(self,user)
    def _do_put(self, event):
        if len(self.users) < self.capacity:
            event.succeed()
            if not isinstance(event,Demand):
                self.users.append(event)
                return 
            else:
                return True
    def _do_get(self, event):
        event.succeed()
        if not isinstance(event,Subscription):
            try:
                self.users.remove(event.request)
            except ValueError:
                self.users.pop(0)
            return
        else:
            event.succeed()
            return True
    def get_now(self,event):
        try:
            self.users.remove(event.request)
        except ValueError:
            self.users.pop(0)
        return
    def put_now(self,event):
        self.users.append(event)
        
        # self._trigger_get(None)

class Demand(Event):
 # just like Get & Put events, but it does not get/put anything unless told to do so
    def __init__(self, resource, user=None):
        super().__init__(resource._env)
        self.resource = resource
        self.proc = self.env.active_process
        self.user = user
        if self.user is not None:
            self.__append__(self,resource.get_queue)
            resource._trigger_get(None)
        else:
            self.__append__(self,resource.put_queue)
            resource._trigger_put(None)
    def __append__(self,obj,container):
        container.append(obj)
    def renounce(self):
        # to be triggered if refusing to get/put after subscribing
        if self.user is not None:
            self.resource._do_get()
        else:
            self.resource._do_put(self)
    def confirm(self,user=None):
        if self.user is not None:
            self._value = self.resource.get_now()
            self.resource._trigger_put(None)
            return self.value
        else:
            if user:
                self.user = user
            self.resource.put_now(self.user)
            self.resource._trigger_get(None)
    # def read(self):
    #     return self.resource.items[0]
    def cancel(self):
        if not self.triggered:
            self.resource.put_queue.remove(self)


if False:  
    from core import Environment
    from simpy import AnyOf
    env = Environment()
    R = Resource(env)
    S = Store(env,1)
    S.put(1)
    r=R.demand()
    s=S.put(1)
    r=R.demand()
    a=AnyOf(env,[s,r])

# class Subscription(Event):
#     # just like Get & Put events, but it does not get/put anything unless told to do so
#     def __init__(self, resource, item=None):
#         super().__init__(resource._env)
#         self.resource = resource
#         self.proc = self.env.active_process
#         self.item = item
#         if not self.item:
#             self.__append__(self,resource.get_queue)
#             resource._trigger_get(None)
#         else:
#             self.__append__(self,resource.put_queue)
#             resource._trigger_put(None)
#     def __append__(self,obj,container):
#         container.append(obj)
#     def renounce(self):
#         # to be triggered if refusing to get/put after subscribing
#         if self.item:
#             self.resource._do_get()
#         else:
#             self.resource._do_put(self)
#     def confirm(self,item=None):
#         if not self.item:
#             self._value = self.resource.get_now()
#             return self.value
#         else:
#             if item:
#                 self.item = item
#             self.resource.put_now(self)
#     def read(self):
#         return self.resource.items[0]

    
# class Store(FilterStore):
#     def subscribe(self,item=None):
#         return Subscription(self,item)
#     def _do_get(self, event):        
#         if self.items:
#             if not isinstance(event,Subscription):
#                 event.succeed(self.items.pop(0))
#                 return
#             else:
#                 event.succeed()
#                 return True
#     def _do_put(self, event):
#         if len(self.items) < self._capacity:
#             event.succeed()
#             if not isinstance(event,Subscription):
#                 self.items.append(event.item)
#                 return 
#             else:
#                 return True
#     def get_now(self):
#         return self.items.pop(0)
#     def put_now(self,event):
#         self.items.append(event.item)
            
if False:

    env = Environment()
    a=Box(env)
    
    print(a.items,a.put_queue)
    req=a.subscribe(1)
    print(a.items,a.put_queue)
    req2=a.subscribe(1)
    print(a.items,a.put_queue)
    
    env.run(1)
    print(req.triggered)
    r=a.subscribe()
    env.run(10)
    print(a.items)
    z=r.confirm()
    print(a.items)
    env.run(20)

