import pandas as pd
from hsim.core.des.des import DESBlock, TimedBlock
from hsim.core.core.env import Environment

import plotly.express as px


def log(env:Environment):
# Reconstruct states to get agent, state, timeIn, timeOut
    data = []
    for x in env._objects:
        if not issubclass(type(x._agent),TimedBlock):
            continue
        agent = repr(x._agent)
        state_times = {}
        for state, in_out, time in x.state_history:
            if in_out:  # True means entering the state
                state_times[state] = time
            else:  # False means exiting the state
                time_in = state_times.pop(state, None)
                if time_in is not None and time_in != time:  # Discard where timeIn == timeOut
                    data.append((agent, state, time_in, time))

    df = pd.DataFrame(data, columns=["agent", "state", "timeIn", "timeOut"])
    return df

def log2(env:Environment):
    for agent in env._agents.values():
        if hasattr(agent,"store"):
            for item in agent.store:
                print(item)

def createGantt(df):
    now=pd.Timestamp.today()
    now._hour=8
    now._minute=0
    now._second=0
    df.timeIn=pd.to_timedelta(df.timeIn,'s')+now
    df.timeOut=pd.to_timedelta(df.timeOut,'s')+now
    df.timeOut.fillna(df.timeOut.max(),inplace=True)
    fig = px.timeline(df, x_start="timeIn", x_end="timeOut", y="agent", color="state")
    return fig
