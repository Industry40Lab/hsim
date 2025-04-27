import pandas as pd
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

def log(env:Environment, filter:callable = lambda x: issubclass(type(x._agent),TimedBlock)):
# Reconstruct states to get agent, state, timeIn, timeOut
    data = []
    for x in env._objects:
        if not filter(x):
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


def statelog(env:Environment, metric="percentage", astable=False, filter:callable = lambda x: issubclass(type(x._agent),TimedBlock)):
    df = log(env, filter)
    df['time'] = df['timeOut'] - df['timeIn']
    result = df.groupby(['agent', 'state'])['time'].sum().reset_index().set_index(['agent', 'state'])
    
    if metric == "percentage":
        result /= env.now
        
    if astable:
        result = result.pivot_table(index='agent', columns='state', values='time', aggfunc='sum', fill_value=0)

    return result

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


