# -*- coding: utf-8 -*-
import random
import pygame

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
        self.world = None
    # def update(self):
    #     dx, dy = self.destination[0] - self.x, self.destination[1] - self.y
    #     dist = ((dx ** 2 + dy ** 2) ** 0.5)
    #     if dist > self.speed:
    #         dx = dx * self.speed / dist
    #         dy = dy * self.speed / dist
    #         # check for overlap with other agents and resolve using separation
    #         separation_dx, separation_dy = 0, 0
    #         for other_agent in self.world.agents:
    #             if other_agent != self:
    #                 if (self.x + dx + self.width > other_agent.x and self.x + dx < other_agent.x + other_agent.width) and (self.y + dy + self.height > other_agent.y and self.y + dy < other_agent.y + other_agent.height):
    #                     # calculate the separation vector
    #                     diff_x = self.x - other_agent.x
    #                     diff_y = self.y - other_agent.y
    #                     dist = ((diff_x ** 2 + diff_y ** 2) ** 0.5)
    #                     if dist > 0:
    #                         separation_dx += diff_x / dist
    #                         separation_dy += diff_y / dist
    #         # apply the separation vector to the agent's movement
    #         separation_dist = ((separation_dx ** 2 + separation_dy ** 2) ** 0.5)
    #         if separation_dist > 0:
    #             separation_dx = separation_dx / separation_dist * self.speed
    #             separation_dy = separation_dy / separation_dist * self.speed
    #             dx += separation_dx
    #             dy += separation_dy
    #         self.x += dx
    #         self.y += dy

    def update(self):
        dx, dy = self.destination[0] - self.x, self.destination[1] - self.y
        dist = ((dx ** 2 + dy ** 2) ** 0.5)
        if dist > self.speed:
            dx = dx * self.speed / dist
            dy = dy * self.speed / dist
            # check for overlap with other agents and resolve using separation
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
            self.x += dx
            self.y += dy
        if dist <= self.speed:
            if self.arrival_time == None:
                self.arrival_time = time.time()
                self.arrival_position = self.destination
            else:
                self.arrival_position = (self.x,self.y)
                print(f"agent {id(self)} arrived in position {self.arrival_position} in {time.time
world = World(800,600)  
for _ in range(20):
    world.add_agent(Agent(random.randint(0, 800), random.randint(0, 600), random.randint(10, 20), random.randint(10, 20), random.uniform(0.05,0.3), (random.randint(0, 800), random.randint(0, 600))))

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
        pygame.draw.rect(screen, (0, 0, 0), (int(agent.x), int(agent.y), agent.width, agent.height))
    pygame.display.update()