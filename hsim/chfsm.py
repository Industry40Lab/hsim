# -*- coding: utf-8 -*-
"""
Created on Fri May 20 16:27:22 2022

@author: Lorenzo
"""

import hfsm
import types
from core import Environment
from stores import Store


class CFSM(hfsm.StateMachine):
    def __init__(self,env,name):
        super().__init__(env)
        self.message_ports = self.create_ports()
        for port in self.message_ports:
            setattr(self, port._name, port)


class Boh3(CFSM):
    def create_ports(self):
        return Store(self.env,'name',2)
    
env = Environment()
foo = Boh3(env,'foo')