# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 11:49:46 2023

@author: Lorenzo
"""
from pymulate import Environment
from pymulate import Generator, Queue, Server, Terminator

env = Environment()
g = Generator(env)
t = Terminator(env)
g.Next = t 


env.run(10)