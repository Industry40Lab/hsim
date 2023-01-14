# -*- coding: utf-8 -*-
import random
import pygame
import time

class World:
    def __init__(self,size_x,size_y):
        self.size = (size_x,size_y)
        self.agents = []

    def add_agent(self, agent):
        self.agents.append(agent)
        agent.world = self

class Agent:
    def __init__(self, x, y, width, height, speed, destination):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.destination = destination
        self.arrival_time = None
        self.moving = True
        self.color = (0,0,0)
        self.world = None
    def separation(self,dx,dy):
        separation_dx, separation_dy = 0, 0
        for other_agent in self.world.agents:
            if other_agent != self:
                if (self.x + dx + self.width > other_agent.x and self.x + dx < other_agent.x + other_agent.width) and (self.y + dy + self.height > other_agent.y and self.y + dy < other_agent.y + other_agent.height):
                    # calculate the separation vector
                    diff_x = self.x - other_agent.x
                    diff_y = self.y - other_agent.y
                    dist = ((diff_x ** 2 + diff_y ** 2) ** 0.5)
                    if dist > 0:
                        separation_dx += diff_x / dist
                        separation_dy += diff_y / dist
        # apply the separation vector to the agent's movement
        separation_dist = ((separation_dx ** 2 + separation_dy ** 2) ** 0.5)
        if separation_dist > 0:
            separation_dx = separation_dx / separation_dist * self.speed
            separation_dy = separation_dy / separation_dist * self.speed
            dx += separation_dx
            dy += separation_dy
        return (dx, dy)
    def update(self):
        if self.moving:
            for other_agent in self.world.agents:
                if other_agent != self:
                    if (self.x + self.width > other_agent.x and self.x < other_agent.x + other_agent.width) and (self.y + self.height > other_agent.y and self.y < other_agent.y + other_agent.height):
                        dx, dy = (other_agent.x + other_agent.width/2 - self.x), (other_agent.y + other_agent.height/2 - self.y)
                        dist = ((dx ** 2 + dy ** 2) ** 0.5)
                        if dist > 0:
                            dx = dx / dist * self.speed
                            dy = dy / dist * self.speed
                        self.x -= dx
                        self.y -= dy
                        self.color = (255,0,0)
                        return
            dx, dy = self.destination[0] - self.x, self.destination[1] - self.y
            dist = ((dx ** 2 + dy ** 2) ** 0.5)
            if dist > self.speed:
                dx, dy = dx * self.speed / dist, dy * self.speed / dist
                # check for overlap with other agents and resolve using separation
            dx, dy = self.separation(dx,dy)
            self.x += dx
            self.y += dy
            print(dx,dy)
            if dx < 0.01 and dy < 0.01:
                self.color = (0,255,255)
            else:
                self.color = (0,0,255)
            if dist == 0:
                self.arrival_time = time.time()
                self.color = (0,255,0)
                self.moving = False
                

world = World(800,600)  
for _ in range(100):
    world.add_agent(Agent(random.randint(0, 800), random.randint(0, 600), random.randint(10, 20), random.randint(10, 20), 10*random.uniform(0.05,0.3), (random.randint(0, 800), random.randint(0, 600))))

pygame.init()
screen = pygame.display.set_mode((800, 600))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
    for agent in world.agents:
        agent.update()
    screen.fill((255, 255, 255))
    for agent in world.agents:
        pygame.draw.rect(screen, agent.color, (int(agent.x), int(agent.y), agent.width, agent.height))
    pygame.display.update()