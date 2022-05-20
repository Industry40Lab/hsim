# -*- coding: utf-8 -*-
"""
Created on Fri May 20 16:27:22 2022

@author: Lorenzo
"""

import hfsm
import types

class CFSM(hfsm.StateMachine):
    pass



def do(instance):
    def decorator(f):
        f = types.MethodType(f, instance)
        setattr(instance, '_do', f)
        return f
    return decorator


def openport(obj,store,*args):
    setattr(obj,store(obj.env,*args),1)
    
openport(CFSM,hfsm.Store,'ciao')
