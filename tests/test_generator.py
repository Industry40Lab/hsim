import pytest
from hsim.core.des.pymulate import Generator, Terminator
from hsim.core.core.env import Environment
from hsim.core.agent.q import Queue
from hsim.core.agent.agent import Agent


def queue_count(q):
    i = 0
    while True:
        try:
            q.inspect(index=i)
            i += 1
        except Exception:
            break
    return i


def test_generator_single_creates_agents():
    env = Environment()
    q = Queue(env, capacity=100)
    g = Generator(env, Agent, serviceTime=1)
    g.connections["next"] = q
    env.run(5)
    cnt = queue_count(q)
    assert cnt >= 1, f"Expected at least 1 agent in queue, got {cnt}"


def test_generator_plan_release_time_and_counts():
    env = Environment()
    q = Queue(env, capacity=100)
    plan = [
        {"time": 1, "agent": Agent, "count": 2},
        {"time": 4, "agent": Agent, "count": 1},
    ]
    g = Generator(env, Agent, generation_mode="plan", production_plan=plan, plan_release_time=True)
    g.connections["next"] = q
    env.run(5)
    cnt = queue_count(q)
    assert cnt == 3, f"Expected 3 agents from plan, got {cnt}"


def test_generator_mix_and_batch():
    class A(Agent):
        def __init__(self, env):
            super().__init__(env, name="A")

    class B(Agent):
        def __init__(self, env):
            super().__init__(env, name="B")

    env = Environment()
    q = Queue(env, capacity=100)
    mix = [(A, 1), (B, 1)]
    g = Generator(env, Agent, generation_mode="mix", production_mix=mix, batch_size=3)
    g.connections["next"] = q
    env.run(2)
    cnt = queue_count(q)
    assert cnt == 3, f"Expected batch of 3 agents from mix, got {cnt}"

if __name__ == "__main__":
    test_generator_mix_and_batch()
    test_generator_single_creates_agents()
    test_generator_plan_release_time_and_counts()