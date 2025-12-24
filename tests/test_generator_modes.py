import pytest

try:
    import pandas as pd
except Exception:
    pd = None

from hsim.core.des.pymulate import Generator, Agent
from hsim.core.core.env import Environment


def test_default_generation_mode_empty():
    env = Environment()
    g = Generator(env)
    assert g.generation_mode == ""
    assert g.production_plan is None and g.production_mix is None


@pytest.mark.skipif(pd is None, reason="pandas not available")
def test_plan_from_dataframe():
    env = Environment()
    df = pd.DataFrame([
        {"intergen": 3, "count": 2, "agent": Agent},
        {"intergen": 5, "count": 1, "agent": Agent},
    ])
    g = Generator(env, generation_mode="plan", production_plan=df)
    assert isinstance(g.production_plan, list)
    assert len(g.production_plan) == 2
    # verify conversion preserved fields
    entry = g.production_plan[0]
    assert entry.get("intergen") == 3
    assert entry.get("count") == 2
    # verify created agents match declared agent type
    agents = g._create_agents_for_entry(entry)
    assert len(agents) == 2
    assert all(isinstance(a, Agent) for a in agents)
    # service time should reflect intergen of first entry
    st = g.calculateServiceTime()
    assert float(st) == 3.0


@pytest.mark.skipif(pd is None, reason="pandas not available")
def test_mix_from_dataframe():
    env = Environment()
    df = pd.DataFrame({"agent": [Agent, Agent], "weight": [0.7, 0.3]})
    g = Generator(env, generation_mode="mix", production_mix=df, batch_size=4)
    # converted to list of (agent, weight)
    assert isinstance(g.production_mix, list)
    assert g.production_mix == [(Agent, 0.7), (Agent, 0.3)]
    # internal mix items should reflect production_mix
    assert isinstance(g._mix_items, list)
    assert g._mix_items == g.production_mix
    # chosen factory should be callable and produce Agent instances
    f = g._choose_from_mix()
    assert callable(f)
    inst = f()
    assert isinstance(inst, Agent)
    agents = g._create_agents_for_entry(None)
    assert len(agents) == 4
    assert all(isinstance(a, Agent) for a in agents)


def test_mix_from_dict():
    env = Environment()
    mix = {Agent: 2.0}
    g = Generator(env, generation_mode="mix", production_mix=mix)
    assert isinstance(g._mix_items, list)
    assert g._mix_items == list(mix.items())


def test_mode_mismatch_assertions():
    env = Environment()
    with pytest.raises(AssertionError):
        Generator(env, generation_mode="plan", production_plan=None)

    # empty mode with plan provided should raise
    if pd is not None:
        df = pd.DataFrame([{"intergen": 1, "count": 1, "agent": Agent}])
        with pytest.raises(AssertionError):
            Generator(env, generation_mode="", production_plan=df)
