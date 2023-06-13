# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 11:49:46 2023

@author: Lorenzo
"""

from sys import path
path.append('../')

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