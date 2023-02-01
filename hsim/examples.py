# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 11:49:46 2023

@author: Lorenzo
"""
import pandas as pd
from pymulate import Environment
from pymulate import Generator, Queue, Server, Terminator

class Plant:
    def __init__(self):
        self.env = Environment()
        self.g = Generator(self.env)
        self.t = Terminator(self.env)
        
        self.q1 = Queue(self.env,capacity=3)
        self.q2 = Queue(self.env,capacity=3)
        
        self.s1 = Server(self.env,serviceTime=1)
        self.s2 = Server(self.env,serviceTime=1)
        self.s3 = Server(self.env,serviceTime=1)
        
        self.g.Next = self.s1 
        self.s1.Next = self.q1 
        self.q1.Next = self.s2 
        self.s2.Next = self.q2 
        self.q2.Next = self.s3
        self.s3.Next = self.t
    def run(self,time):
        self.env.run(time)

p = Plant()
p.run(10)

# %% 

env = Environment()
g = Generator(env)
t = Terminator(env)

q1 = Queue(env,capacity=3)
q2 = Queue(env,capacity=3)

s1 = Server(env,serviceTime=1)
s2 = Server(env,serviceTime=1)
s3 = Server(env,serviceTime=1)

g.Next = s1 
s1.Next = q1 
q1.Next = s2 
s2.Next = q2 
q2.Next = s3
s3.Next = t

env.run(10)