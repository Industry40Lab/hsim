from math import e
from hsim.core.core.env import Environment
from hsim.core.des.pymulate import Generator, Server, Terminator
from hsim.core.agent.agent import Agent


class Job(Agent):
    """Simple Job entity that holds a routing as a list of connection keys (strings).

    The route is stored as a list of strings (names of connections on the machines).
    This keeps jobs lightweight and avoids embedding direct object references.
    """
    def __init__(self, env, name=None, route=None, **kwargs):
        super().__init__(env, name)
        # route is a list of connection keys (e.g. ['M1','M2']) or machine names
        self.route = list(route) if route is not None else []
        self.route_index = 0
        # allow arbitrary custom attributes from plan entries
        for k, v in kwargs.items():
            setattr(self, k, v)

    def next_route_key(self):
        # return next connection key or None
        if self.route_index < len(self.route):
            return self.route[self.route_index]
        return None

    def advance_route(self):
        if self.route_index < len(self.route):
            self.route_index += 1


def select_next_from_routing(connections, entity):
    """Resolve next target from `entity.route` using a `connections` mapping.

    `connections` is expected to be a dict mapping keys to target blocks. If the
    route is empty or the key is not found, fall back to `connections.get('next')`.
    """
    try:
        if hasattr(entity, "route"):
            if len(entity.route) == 0:
                return connections.get("next")
            key = entity.route.pop(0)
            return connections.get(key, connections.get("next"))
        return connections.get("next")
    except Exception:
        return connections.get("next")


def main():
    env = Environment()

    # use Generator to instantiate `Job` and let Generator map plan fields onto instances
    # production plan: use absolute release times ('time') rather than interarrival; Generator
    # will be asked to interpret plan entries as release times via plan_release_time=True.
    plan = [
        {"route": ["M2"], "job_id": "J1"},  # no time => released immediately at t=0
        {"route": ["M2"], "job_id": "J2", "time": 0.1},
        {"route": ["M2"], "job_id": "J3", "time": 0.5},
        {"route": [],      "job_id": "J4", "time": 1.0},
        {"route": ["M2"], "job_id": "J5", "time": 1.5},
        {"route": ["M2","M1"], "job_id": "J6", "time": 2.0},
    ]

    # pass Job class so Generator instantiates Job objects; enable plan release times
    g = Generator(env, "G", Job, production_plan=plan, serviceTime=0, generation_mode="plan", plan_release_time=True)

    t = Terminator(env, "T")
    s1 = Server(env, "S1", serviceTime=0.1)
    s2 = Server(env, "S2", serviceTime=0.1)

    # wire named connections used in routes; avoid self-referential connection entries
    s1.connections["M2"] = s2
    s1.connections["next"] = t

    s2.connections["M1"] = s1
    s2.connections["next"] = t

    # override exit strategy for servers to use routing (pass connections mapping)
    s1.exit_strategy = lambda entity, _c=s1.connections: select_next_from_routing(_c, entity)
    s2.exit_strategy = lambda entity, _c=s2.connections: select_next_from_routing(_c, entity)

    # connect generator to first default target (we still route based on job.route)
    g.connections["next"] = s1

    # collect completed jobs by wrapping the Terminator's _terminate_item
    completed = []
    orig_terminate = t._terminate_item
    def hooked_terminate():
        try:
            item, _ = t.store.inspect(index=-1)
            completed.append(item.job_id if hasattr(item, "job_id") else getattr(item, "name", "unknown"))
        except Exception:
            completed.append("unknown")
        return orig_terminate()
    t._terminate_item = hooked_terminate

    try:
        env.run(100)
    except Exception as e:
        print("Simulation stopped with error:", e)
    print("Completed:", completed)


if __name__ == "__main__":
    main()
