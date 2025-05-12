from typing import Iterable
import pandas as pd
from hsim.core.agent.agent import Agent
from hsim.core.des.des import TimedBlock
from hsim.core.des.frame import Frame
from hsim.core.core.env import Environment





def create_connection_chart(objects, output_file="graph.html",remove_operators=True):
    
    """
    Create an interactive directed graph based on the connections between objects.
    Handles Frames by visualizing their internal and external connections.

    :param objects: A list of objects, each having a `connections` dictionary.
    :param output_file: The name of the HTML file to save the interactive graph.
    """
    from pyvis.network import Network
    # Create a PyVis network
    net = Network(height="750px", width="100%", directed=True)

    # Add nodes and edges
    # Add nodes
    for obj in objects:
        if isinstance(obj, Frame):
            objects += obj._agents #+ list(obj.input_ports.values()) + list(obj.output_ports.values())
    if remove_operators:
        from hsim.core.des.manual import Operator
        objects_to_remove = [obj for obj in objects if isinstance(obj, Operator) or type(obj) is Operator]
        for obj in objects_to_remove:
            objects.remove(obj)
    for obj in objects:
        if obj is not None and hash(obj) not in net.nodes: 
            net.add_node(hash(obj), label=repr(obj), title=f"Object: {repr(obj)}")
        else:
            pass

    # Add edges
    for obj in objects:
        if isinstance(obj, Frame):
            for t in obj._agents:
                net.add_edge(hash(obj), hash(t), title=connection_name)
        elif hasattr(obj, "connections"):
            for connection_name, target in obj.connections.items():
                if isinstance(target, list):
                    for t in target:
                        if t is not None and hash(t) in net.node_ids:
                            net.add_edge(hash(obj), hash(t), title=connection_name)
                        else:
                            pass
                elif target is not None and hash(target) in net.node_ids:
                    net.add_edge(hash(obj), hash(target), title=connection_name)
                else:
                    pass
    # Generate the interactive graph
    net.save_graph(output_file)
    print(f"Graph saved to {output_file}. Open it in a browser to view and edit.")

def reconstruct_states(agent:Agent, input:Iterable):
    data = list()
    state_times = dict()
    for state, in_out, time in input:
        if in_out:  # True means entering
            state_times[state] = time
        else:  # False means exiting
            time_in = state_times.pop(state, None)
            if time_in is not None and time_in != time:  # Discard where timeIn == timeOut
                data.append((agent, state, time_in, time))
    return data
    
def reconstruct_messages(agent, input:Iterable):
    data = list()
    state_times = dict()
    for message, content, in_out, time in input:
        if in_out:  # True means entering
            state_times[message] = time
        else:  # False means exiting
            time_in = state_times.pop(message, None)
            if time_in is not None and time_in != time:  # Discard where timeIn == timeOut
                data.append((agent, content, time_in, time))
    return data
    
def log(env:Environment, filter:callable = lambda x: issubclass(type(x._agent),TimedBlock)):
# Reconstruct states to get agent, state, timeIn, timeOut
    data = []
    for x in env._objects:
        if not filter(x):
            continue
        agent = repr(x._agent)
        data.append(reconstruct_states(agent, x.state_history))
    data = [item for sublist in data for item in sublist]  # Flatten the list of lists
    df = pd.DataFrame(data, columns=["agent", "state", "timeIn", "timeOut"])
    return df

def statelog(env:Environment, metric="percentage", astable=False, filter:callable = lambda x: issubclass(type(x._agent),TimedBlock)):
    df = log(env, filter)
    names = [name for name in df.agent.unique() if not "Generator" in name]
    df['time'] = df['timeOut'] - df['timeIn']
    result = df.groupby(['agent', 'state'])['time'].sum().reset_index().set_index(['agent', 'state'])
    
    if metric == "percentage":
        result /= env.now
        
    if astable:
        result = result.pivot_table(index='agent', columns='state', values='time', aggfunc='sum', fill_value=0)

    return result.loc[names]

def log2(env:Environment):
    data = dict()
    for agent in env._agents.values():
        if hasattr(agent,"store"):
            if len(agent.store._queue_history) > 0 and sum([el[0] for el in agent.store._queue_history]) > 0:
                data[str(agent)] = list(zip(*agent.store._queue_history))
        elif hasattr(agent,"stores"):
            for idx, store in enumerate(agent.stores):
                if len(store._queue_history) > 0 and sum([el[0] for el in store._queue_history]) > 0:
                    data[str(agent)+str(idx)] = list(zip(*store._queue_history))   
    return data
                    
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

def queueChart(data_dict, output_file="staircase_plots.html"):
    # Filter out empty queues
    data_dict = {k: v for k, v in data_dict.items() if v}
    if not data_dict:
        print("No data to plot.")
        return
    fig = go.Figure()
    for agent_name, data in data_dict.items():
        qty, time = data
        fig.add_trace(
            go.Scatter(x=time, y=qty, mode='lines+markers', line_shape='hv', name=agent_name)
        )
    fig.update_layout(
        title_text="Staircase Plots for Queues",
        xaxis_title="Time",
        yaxis_title="Quantity",
        height=600,
        showlegend=True
    )
    fig.write_html(output_file)
    return fig

def testlog(agent):
    if not isinstance(agent, Frame):
        agent.stateMachine._state_history
        for store in agent.store_var:
            agent.store._message_history
    else:
        for agent in agent._agents:
            agent.stateMachine._state_history
            for store in agent.store_var:
                agent.store._message_history

def joiner(df1,df2,colnames1,colnames2):
    res = pd.concat([df1[colnames1 + ["timeIn"]], df2[colnames2 + ["timeIn"]]], ignore_index=True).sort_values('timeIn').reset_index(drop=True)
    for col in colnames1+colnames2:
        res[col] = res[col].ffill()
    res['timeOut'] = res['timeIn'].shift(-1)
    res.fillna({"timeOut":max(df1['timeOut'].max(), df2['timeOut'].max())},inplace=True)
    res[colnames1+colnames2].fillna("",inplace=True)
    res = res[colnames1+colnames2+["timeIn","timeOut"]]
    return res

def merger(agent):
    data1 = reconstruct_states(agent, agent.stateMachine._state_history)
    data2 = reconstruct_messages(agent, agent.store._message_history)
    df1 = pd.DataFrame(data1, columns=["agent", "state", "timeIn", "timeOut"])
    df2 = pd.DataFrame(data2, columns=["agent", "content", "timeIn", "timeOut"])
    res = joiner(df1, df2, ["state"], ["content"])
    res.insert(0, "agent", agent)
    return res

def test2(env) -> pd.DataFrame:
    res_res = pd.DataFrame()
    for agent in env._agents.values():
        if isinstance(agent, TimedBlock) and hasattr(agent, "store"):
            res = merger(agent)
        elif isinstance(agent, Frame) and len([a for a in agent._agents if isinstance(a,TimedBlock)]):
            res = merger(next(a for a in agent._agents if isinstance(a,TimedBlock)))
        res_res = pd.concat([res_res, res.copy()], ignore_index=True)
    return res_res

def createGantt(df):
    import plotly.express as px
    now=pd.Timestamp.today()
    now._hour=8
    now._minute=0
    now._second=0
    df.timeIn=pd.to_timedelta(df.timeIn,'s')+now
    df.timeOut=pd.to_timedelta(df.timeOut,'s')+now
    df.timeOut.fillna(df.timeOut.max(),inplace=True)
    fig = px.timeline(df, x_start="timeIn", x_end="timeOut", y="agent", color="state")
    return fig

def GSOMGantt(env, agentList=None, html=False):
    res = test2(env)
    res["agent"] = res["agent"].apply(lambda x:repr(x))
    res["content"] = res["content"].apply(lambda x:id(x))
    res.rename(columns={"agent":"Station"}, inplace=True)
    now=pd.Timestamp.today()
    res.timeIn=pd.to_timedelta(res.timeIn,'s')+now
    res.timeOut=pd.to_timedelta(res.timeOut,'s')+now
    reprlist = list()
    for a in agentList:
        if isinstance(a, TimedBlock) and hasattr(a, "store"):
            reprlist.append(repr(a))
        elif isinstance(a, Frame) and len([a for a in a._agents if isinstance(a,TimedBlock)]):
            reprlist.append(repr(next(a for a in a._agents if isinstance(a,TimedBlock))))
    res["Station"] = res["Station"].apply(lambda x: pd.NA if x not in reprlist else reprlist.index(x)+1)
    res.dropna(inplace=True)
    if html:
        return px.timeline(res, x_start="timeIn", x_end="timeOut", y="Station", color="state", hover_data="content").to_html()
    else: 
        px.timeline(res, x_start="timeIn", x_end="timeOut", y="Station", color="state", hover_data="content").show()


def GSOMGanttOp(env, agentList=None, html=False):
    res = list()
    for agent in agentList:
        res += reconstruct_states(agent, agent.stateMachine._state_history)
    res = pd.DataFrame(res,columns=["agent","state","timeIn","timeOut"])
    res["agent"] = res["agent"].apply(lambda x:repr(x))
    now=pd.Timestamp.today()
    res.timeIn=pd.to_timedelta(res.timeIn,'s')+now
    res.timeOut=pd.to_timedelta(res.timeOut,'s')+now
    # res.dropna(inplace=True)
    if html:
        return px.timeline(res, x_start="timeIn", x_end="timeOut", y="agent", color="state").to_html()
    else: 
        px.timeline(res, x_start="timeIn", x_end="timeOut", y="agent", color="state").show()