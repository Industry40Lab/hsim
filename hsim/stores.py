# -*- coding: utf-8 -*-
"""
Created on Sat Jan 15 14:54:49 2022

@author: Lorenzo
"""
from heapq import heappop

from simpy import Event, FilterStore, Resource
from numpy import inf

class Subscription(Event):
    # just like Get & Put events, but it does not get/put anything unless told to do so
    def __init__(self, resource, item=None, filter=None):
        super().__init__(resource._env)
        self.resource = resource
        self.proc = self.env.active_process
        self.item = item
        self._ok = False
        self.filter = lambda x: True
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
            self.resource._trigger_get(self)
        else:
            self.resource._trigger_put(self)
    def confirm(self,item=None):
        self._ok = True
        if self.item in self.resource.items:
            return
        if not self.item:
            self._value = self.resource.get_now(self)
            self.resource._trigger_put(None)
            return self.value
        else:
            if item:
                self.item = item
            if type(self.resource) is not Box:
                self.resource.put_now(self.item)
            self.resource._trigger_get(None)
    def read(self): #useless
        if self.check() is not False:
            for item in self.resource.items:
                if self.filter(item):
                    return item
                return True
    def check(self,get_all=False):
        if self.item and len(self.resource.items) < self.resource._capacity:
            return True
        elif not self.item:
            if not get_all:
                for item in self.resource.items:
                    if self.filter(item):
                        return item
            else:
                y = [item for item in self.resource.items if self.filter(item)]
                if y is not []:
                    return y
        return False
    def cancel(self):
        if self.item:
            if not self.triggered:
                self.resource.put_queue.remove(self)
            else:
                self.renounce()
            if self.item in self.resource.items:
                self.resource.items.remove(self.item)
        else:
            if not self.triggered:
                self.resource.get_queue.remove(self)
            else:
                self.renounce()
    def choose(self,item):
        if not self.item:
            self.filter = lambda x: x is item
            self.confirm()
        else:
            raise Exception()

    
class Store(FilterStore):
    def __init__(self, env, capacity=inf):
        super().__init__(env, capacity)
        self.put_event = env.event()
        self.subscription_get_queue = list()
    def __len__(self):
        return len(self.items)
    def subscribe(self,item=None,filter=None):
        return Subscription(self,item)
    def _do_get(self, event):        
        for item in self.items:
            if event.filter(item):
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
                if not self.put_event.triggered:
                    self.put_event.succeed()
                return 
            else:
                return True
    def _trigger_get(self, put_event):
        idx = 0
        while idx < len(self.get_queue):
            get_event = self.get_queue[idx]
            proceed = self._do_get(get_event)
            if not get_event.triggered:
                idx += 1
            elif self.get_queue.pop(idx) != get_event:
                raise RuntimeError('Get queue invariant violated')
                
            #keep track of triggered requests
            if type(get_event) is Subscription:
                self.subscription_get_queue.append(get_event)

            if not proceed:
                break
    @property
    def next_subscription_get(self):
        if len(self.subscription_get_queue)>0:
            return self.subscription_get_queue[0]
        else:
            raise(IndexError('Subscription get queue is empty'))
    def get_now(self,event):
        # self._trigger_put(None)
        for item in self.items:
            if event.filter(item):
                self.items.remove(item)
                return item
        self.subscription_get_queue.remove(event)
            
    def put_now(self,item):
        self.items.append(item)
        # self._trigger_get(None)

class StoreU(Store):
    pass
    

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
    def put(self,item=None): #debug
        return super().put(item)
    def _do_put(self, event):
        if len(self.items) < len(self.put_queue):
            self.items.append(event.item)
            # event.item = None
        self._trigger_get(event)
        if not self.put_event.triggered:
            self.put_event.succeed()
        return True
    def _do_get(self,event):
        super()._do_get(event) 
    def forward(self,event):
        if event not in self.put_queue:
            for (new_event,item) in self.requests:
                if event is item:
                    event = new_event
                    break
        event.succeed()
        self.put_queue.remove(event)
        self.items.remove(event.item)
        # self.put_event.restart()
    def subscribe(self,item=None,filter=None):
        return Subscription(self,item)
    def _trigger_put(self,get_event):
        idx = len(self.put_queue) - 1
        while idx < len(self.put_queue):
            put_event = self.put_queue[idx]
            proceed = self._do_put(put_event)
            if not put_event.triggered:
                idx += 1
            elif self.put_queue.pop(idx) != put_event:
                raise RuntimeError('Put queue invariant violated')
            if not proceed:
                break
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
    def get_now(self,event):
        item = super().get_now(event)
        self.forward(item)
        return item


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


# %% tests 
        
if __name__ == "__main__":  
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


    env = Environment()
    a=Box(env)
    
    print(a.items,a.put_queue)
    req=a.subscribe(1)
    print(a.items,a.put_queue)
    req2=a.subscribe(2)
    print(a.items,a.put_queue)
    
    env.run(1)
    print(req.triggered)
    r=a.subscribe()
    env.run(10)
    print(a.items)
    z=r.confirm()
    print(a.items)
    env.run(20)

