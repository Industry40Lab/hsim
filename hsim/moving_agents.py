# -*- coding: utf-8 -*-
import random
import pygame
import time
from math import pi
from chfsm import CHFSM, State, Transition, Environment

class Environment(Environment):
    def __init__(self,size_x,size_y,log=None,initial_time=0):
        super().__init__(log,initial_time)
        self.agents = []
        self.size_x = size_x
        self.size_y = size_y
    def add_agent(self, agent):
        self.agents.append(agent)
        agent.world = self

class MovingAgent(CHFSM):
    def __init__(self,env,x,y,max_speed,name=None):
        super().__init__(env,name)
        self.x = x
        self.y = y
        self.max_speed = max_speed
        self.destintation = None
        self.env.agents.append(self)
    class Moving(State):
        initial_state=True
    class NotMoving(State):
        pass
    def _update(self):
        dx, dy = self.destination[0] - self.x, self.destination[1] - self.y
        dist = ((dx ** 2 + dy ** 2) ** 0.5)
        if dist > self.speed:
            dx, dy = dx * self.speed / dist, dy * self.speed / dist
        for agent in self.env.agents:
            agent.x += dx
            agent.y += dy
    TM = Transition.copy(Moving,action=lambda self: self._update())


class World:
    def __init__(self,size_x,size_y):
        self.size = (size_x,size_y)
        self.agents = []

    def add_agent(self, agent):
        self.agents.append(agent)
        agent.world = self

class Agent:
    def __init__(self, x, y, theta, width, height, max_speed, max_rotational_speed, destination, color=(0,0,0)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = max_speed
        self.max_rotational_speed = max_rotational_speed
        self.destination = destination
        self.moving = True
        self.color = color
        self.world = None
    @property
    def destination_occupied(self):
        for other_agent in self.world.agents:
            if other_agent != self:
                if other_agent.x <= self.destination[0] <= other_agent.x + other_agent.width and other_agent.y <= self.destination[1] <= other_agent.y + other_agent.height:
                    return True
        return False
    @property
    def close_agents(self):
        distance = 0.1*(self.width/2 + self.height/2)
        for other_agent in self.world.agents:
            if other_agent != self:
                if (other_agent.x - distance <= self.destination[0] <= other_agent.x + other_agent.width + distance) and (other_agent.y - distance <= self.destination[1] <= other_agent.y + other_agent.height + distance):
                    return True
        return False
    @property
    def destination_crowding(self):
        close_area = 0
        for other_agent in self.world.agents:
            if other_agent != self:
                x_overlap = max(0, min(other_agent.x + other_agent.width, self.destination[0] + self.width) - max(other_agent.x, self.destination[0]))
                y_overlap = max(0, min(other_agent.y + other_agent.height, self.destination[1] + self.height) - max(other_agent.y, self.destination[1]))
                close_area += x_overlap * y_overlap
        destination_area = self.width * self.height
        return close_area / destination_area

    def update(self):
        # scan area
        pass

env = Environment(800,600)
world = World(800,600)  
for _ in range(50):
    # world.add_agent(Agent(random.randint(0, 800), random.randint(0, 600), random.uniform(0,2*pi), random.randint(10, 20), random.randint(10, 20), 10*random.uniform(0.05,0.3), random.uniform(0,2*pi), (random.randint(0, 800), random.randint(0, 600), random.uniform(0,2*pi))))
    env.add_agent(MovingAgent(env,random.randint(0, 800), random.randint(0, 600), random.randint(10, 20)))

pygame.init()
screen = pygame.display.set_mode(world.size)
map_offset = [0, 0]
left_button_down = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                left_button_down = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                left_button_down = False
        elif event.type == pygame.MOUSEMOTION:
            if left_button_down:
                # Update the map offset based on the mouse movement
                map_offset[0] += event.rel[0]
                map_offset[1] += event.rel[1]
    screen.fill((255, 255, 255))
    for agent in world.agents:
        pygame.draw.rect(screen, agent.color, (int(agent.x) + map_offset[0], int(agent.y) + map_offset[1], agent.width, agent.height))
    pygame.display.update()