# -*- coding: utf-8 -*-
if __name__ == "__main__":
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

import time
from hsim.core.utils.utils import log2, statelog
from scipy.stats import t as t_dist


from hsim.core.des.pymulate import Store, Environment, Generator, Server, Buffer, Terminator
from hsim.core.des.manual import Operator, ManualStation

from hsim.core.des.resources import ManualAssembly, UnreliableMachine as MachineMIP
from hsim.core.des.resources import SUMachine as AutomatedMIP
from hsim.core.des.resources import ServerDoubleBuffer, QualityServerDoubleBuffer


import pandas as pd
import numpy as np

MONITORING = False
GANTT = True

def normal_dist_bounded(val):
    mean = val[0]
    std = val[0]
    if mean < 0:
        raise BaseException()
    y = 0
    # while y <= 0:
    #     y = np.random.normal(mean,std)
    for i in range(1000):
        y = np.random.normal(mean,std)
        if y > 0:
            return y
    return mean
    # return y
    
def scores(path,throughput):
    from datetime import datetime
    folder,filename=path.rsplit('/',1)
    player = pd.read_csv(folder+'/currentSimulation.csv',header=None)[0][0]
    new = pd.read_excel(path,sheet_name='Main',header=None,index_col=0)[1:].transpose().reset_index(drop=True)
    new['Productivity'] = throughput
    new.insert(0,'Time',datetime.now())
    new.insert(0,'Name',player)
    
    resFolder = folder+'/results'
    try:
        old = pd.read_csv(resFolder+'/results.csv',index_col=0)
        new = pd.concat([old,new]).reset_index(drop=True)
    except:
        pass
    finally:
        new.to_csv(resFolder+'/results.csv')
    
    html = generate_html(new)
    open(folder+"/results/"+"results.html", "w").write(html)
        
    
def generate_html(dataframe: pd.DataFrame):
    # get the table HTML from the dataframe
    table_html = dataframe.to_html(table_id="table")
    # construct the complete HTML with jQuery Data tables
    # You can disable paging or enable y scrolling on lines 20 and 21 respectively
    html = f"""
    <html>
    <header>
        <link href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css" rel="stylesheet">
    </header>
    <body>
    {table_html}
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script type="text/javascript" src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
        $(document).ready( function () {{
            $('#table').DataTable({{
                // paging: false,    
                // scrollY: 400,
            }});
        }});
    </script>
    </body>
    </html>
    """
    # return the html
    return html

    
        
class gen_motor():
    def __init__(self):
        self.index = 0
    def __call__(self):
        self.index += 1
        return Entity(self.index)
    
class Entity():
        def __init__(self,ID):
            self.ID = ID
            self.serviceTime = 1
            
    
def main(filename, folder='', fullpath='',app=True):
    if not app:
        with open('target.txt') as f:
            fullpath = f.read()
        folder,filename=fullpath.rsplit('/',1)
        folder=folder+'/'
    if folder == '':
        path = filename
    else:
        path = folder+filename
        
    env = Environment()
    
    a=pd.read_excel(path,sheet_name='Redesign_in',header=1,index_col=0)
    a=a.fillna(int(0))
    
    b=pd.read_excel(path,sheet_name='Operators table',header=1,index_col=0)
    b=b.fillna(int(0))
    
    c=pd.read_excel(path,sheet_name='Tasks_in',header=0,usecols=[0,3,4,5],index_col=0)
    d=pd.read_excel(path,sheet_name='Tasks_in',header=0,usecols=[0,4,5],index_col=0)
    
    e = pd.read_excel(path,sheet_name='Resources',header=0)
    
    
    
    # %% changes
    
    agv_num = e['# of AGVs (if any)'].values[0]
    agv_sat = a['Material handling'].sum()/4
    
    for index in range(1,3):
        if a.loc[a.index.values==index,'Material handling'].values > 0:
            remove_load_case = 1
        else:
            remove_load_case = 0
    
    for index in [3,4,6,7]:
        if a.loc[a.index.values==index,'Feeding'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.04)
        elif a.loc[a.index.values==index,'Feeding'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.11)
        if a.loc[a.index.values==index,'Material handling'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.05)
        elif a.loc[a.index.values==index,'Material handling'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)
        elif a.loc[a.index.values==index,'Material handling'].values == 3 and agv_num>0:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)/(4*np.arctan(agv_num/agv_sat)/np.pi)
    
    for index in range(11,12):
        if a.loc[a.index.values==index,'Material handling'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.04)
        elif a.loc[a.index.values==index,'Material handling'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.08)
        elif a.loc[a.index.values==index,'Material handling'].values == 3 and agv_num>0:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.08)/(4*np.arctan(agv_num/agv_sat)/np.pi)
        if a.loc[a.index.values==index,'Feeding'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.04)
        elif a.loc[a.index.values==index,'Feeding'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)
    
    for index in range(12,23):
        if a.loc[a.index.values==index,'Feeding'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.04)
        elif a.loc[a.index.values==index,'Feeding'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)
        if a.loc[a.index.values==index,'Material handling'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.03)
    
    for index in range(24,28):
        if a.loc[a.index.values==index,'Feeding'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.04)
        elif a.loc[a.index.values==index,'Feeding'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)
        if a.loc[a.index.values==index,'Material handling'].values == 1:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.05)
        elif a.loc[a.index.values==index,'Material handling'].values == 2:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)
        elif a.loc[a.index.values==index,'Material handling'].values == 3 and agv_num>0:
            d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)/(4*np.arctan(agv_num/agv_sat)/np.pi)
    
    
    Q_case = (15-a['AI-augmented quality'][2:4].sum()*5/6)/100
    Q_ele = (15-6*np.arctan(a['AI-augmented quality'][11:22].sum()*np.random.uniform()*0.25)/np.pi)/100
    
    
    M=dict()
    for index in c.index:
        if c.loc[c.index==index,'M/A/T'].values == 'A' and index != 2:
            Mcase = 0.86
            if a['Smart maintenance solutions'][index] == 1:
                Mcase = 0.90
            elif a['Smart maintenance solutions'][index] == 2:
                Mcase = 0.94
            elif a['Smart maintenance solutions'][index] == 3:
                Mcase = 0.975
            M.update({index:Mcase})
    
    
    
    
    # %% case 
    ggg = gen_motor()
    g_case = Generator(env,'g1',serviceTime=10)
    g_case.createEntity = ggg
    
    case0 = ManualStation(env, name="case0", serviceTime=d.loc[d.index == 1].values, serviceTimeFunction=normal_dist_bounded)
    case1 = ServerDoubleBuffer(env, name="case1", serviceTime=d.loc[d.index == 2].values, serviceTimeFunction=normal_dist_bounded, inputBufferCapacity=4, outputBufferCapacity=4)
    
    case2queueIn = Buffer(env,"case2queueIn",capacity = 4)
    if c.loc[c.index==3]['M/A/T'].values == 'M':
        case2 = ManualStation(env,"case2",serviceTime=d.loc[d.index == 3].values, serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==3]['M/A/T'].values == 'S':
        case2 = AutomatedMIP(env,"case2",serviceTime=d.loc[d.index==3].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==3]['M/A/T'].values == 'A':
        case2 = Server(env,"case2",serviceTime=d.loc[d.index==3].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==3]['M/A/T'].values == 'C':
        case2 = ManualStation(env,"case2",serviceTime=d.loc[d.index==3].values*0.25,serviceTimeFunction=normal_dist_bounded)
    case2queueOut = Buffer(env,"case2queueOut",capacity = 4)
    
    case3queueIn = Buffer(env,capacity = 4)
    if c.loc[c.index==4]['M/A/T'].values == 'M':
        case3 = ManualStation(env,"case3",serviceTime=d.loc[d.index == 4].values, serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==4]['M/A/T'].values == 'S':
        case3 = AutomatedMIP(env,"case3",serviceTime=d.loc[d.index==4].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==4]['M/A/T'].values == 'A':
        case3 = Server(env,"case3",serviceTime=d.loc[d.index==4].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==4]['M/A/T'].values == 'C':
        case3 = ManualStation(env,"case3",serviceTime=d.loc[d.index==4].values*0.25,serviceTimeFunction=normal_dist_bounded)
    case3queueOut = Buffer(env,capacity = 4)
    
    """case4 = ServerDoubleBuffer(env,serviceTime=d.loc[d.index==5].values,serviceTimeFunction=normal_dist_bounded)
    case4quality = SwitchQualityMIP(env)
    case4quality.var.quality_rate = Q_case
    case4scrap = Store(env)"""
    case4 = QualityServerDoubleBuffer(env,"case4",serviceTime=d.loc[d.index==5].values,serviceTimeFunction=normal_dist_bounded,inputBufferCapacity = 4, outputBufferCapacity = 4,qualityThreshold=1-Q_case)
    
    case5queueIn = Buffer(env,"case5queueIn",capacity = 4)
    if c.loc[c.index==6]['M/A/T'].values == 'M':
        case5 = ManualStation(env,"case5",serviceTime=d.loc[d.index == 6].values, serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==6]['M/A/T'].values == 'S':
        case5 = AutomatedMIP(env,"case5",serviceTime=d.loc[d.index==6].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==6]['M/A/T'].values == 'A':
        case5 = Server(env,"case5",serviceTime=d.loc[d.index==6].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==6]['M/A/T'].values == 'C':
        case5 = ManualStation(env,"case5",serviceTime=d.loc[d.index==6].values*0.25,serviceTimeFunction=normal_dist_bounded)
    case5queueOut = Buffer(env,"case5queueOut",capacity = 4)
    
    
    case6queueIn = Buffer(env,"case6queueIn",capacity = 4)
    if c.loc[c.index==7]['M/A/T'].values == 'M':
        case6 = ManualStation(env, "case6", serviceTime=d.loc[d.index == 7].values, serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==7]['M/A/T'].values == 'S':
        case6 = AutomatedMIP(env,"case6",serviceTime=d.loc[d.index==7].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==7]['M/A/T'].values == 'A':
        case6 = Server(env,"case6",serviceTime=d.loc[d.index==7].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==7]['M/A/T'].values == 'C':
        case6 = ManualStation(env,"case6",serviceTime=d.loc[d.index==7].values*0.25,serviceTimeFunction=normal_dist_bounded)
    case6queueOut = Buffer(env,"case6queueOut",capacity = 4)
    
    
    # %% electronics
    ggg = gen_motor()
    g_ele = Generator(env,'g2',serviceTime=10)
    g_ele.createEntity = ggg
    
    ele0 = ManualStation(env, serviceTime=d.loc[d.index == 8].values, serviceTimeFunction=normal_dist_bounded, name="ele0")
    ele1queue = Buffer(env,"ele1queue",capacity=4)
    ele1 = MachineMIP(env,'ele1',serviceTime=d.loc[d.index==9].values,serviceTimeFunction=normal_dist_bounded)
    ele2queueIn = Buffer(env,"ele2queueIn",capacity=4)
    ele2 = MachineMIP(env,'ele2',serviceTime=d.loc[d.index==10].values,serviceTimeFunction=normal_dist_bounded)
    ele2queueOut = Buffer(env,'ele2queueOut',capacity=4)
    
    
    
    for i in range(2,25,2):
        j = int(i/2+10)
        glob = globals()
        if c.loc[c.index==j]['M/A/T'].values == 'M':
            glob['ele_line'+str(i)] = ManualStation(env,'ele_line'+str(i),serviceTime=d.loc[d.index==j].values,serviceTimeFunction=normal_dist_bounded)
        elif c.loc[c.index==j]['M/A/T'].values == 'S':
            glob['ele_line'+str(i)] = AutomatedMIP(env,'ele_line'+str(i),serviceTime=d.loc[d.index==j].values,serviceTimeFunction=normal_dist_bounded)
        elif c.loc[c.index==j]['M/A/T'].values == 'A':
            glob['ele_line'+str(i)] = Server(env,'ele_line'+str(i),serviceTime=d.loc[d.index==j].values,serviceTimeFunction=normal_dist_bounded)
        elif c.loc[c.index==j]['M/A/T'].values == 'C':
            glob['ele_line'+str(i)] = ManualStation(env,'ele_line'+str(i),serviceTime=d.loc[d.index==3].values*0.25,serviceTimeFunction=normal_dist_bounded)
    
    for i in range(1,26,2):
        glob = globals()   
        glob['ele_line'+str(i)] = Buffer(env,'ele_line'+str(i),capacity=4)
    ele_line26 = QualityServerDoubleBuffer(env, "ele_line26", serviceTime=d.loc[d.index == 23].values, serviceTimeFunction=normal_dist_bounded, inputBufferCapacity=4, outputBufferCapacity=4, qualityThreshold=1-Q_ele)
    
    # %% final
    
    final1case = Buffer(env,"final1case")
    final1ele = Buffer(env,"final1ele")
    final2assebly = ManualAssembly(env, name="finalAssembly", serviceTime=d.loc[d.index == 24].values, serviceTimeFunction=normal_dist_bounded, size=2)
    final2inspect = MachineMIP(env, "final2inspect",serviceTime=d.loc[d.index == 25].values, serviceTimeFunction=normal_dist_bounded)
    
    final3 = Buffer(env,"final3")
    if a['Packaging'][26] == 0:
        final4pack = ManualStation(env,"final4pack",serviceTime=d.loc[d.index==26].values,serviceTimeFunction=normal_dist_bounded)
    elif a['Packaging'][26] == 1:
        final4pack = Server(env,"final4pack",serviceTime=d.loc[d.index==26].values,serviceTimeFunction=normal_dist_bounded)
    elif a['Packaging'][26] == 2:
        final4pack = Server(env,"final4pack",serviceTime=d.loc[d.index==26].values*0.7,serviceTimeFunction=normal_dist_bounded)
    
    if a['Dispatching'][27] == 0:
        final5pallet = ManualStation(env,"final5pallet",serviceTime=d.loc[d.index==27].values,serviceTimeFunction=normal_dist_bounded)
    elif a['Dispatching'][27] == 1:
        final5pallet = Server(env,"final5pallet",serviceTime=d.loc[d.index==27].values,serviceTimeFunction=normal_dist_bounded)
    
    
    T = Terminator(env)
    
    # %% connect
    Q=Store(env)
    
    g_case.connections["next"] = case0
    
    case0.connections["next"] = case1.input_ports[0]
    
    case1.output_ports[0].connections["next"] = case2queueIn
    
    if c.loc[c.index==3]['M/A/T'].values == 'M':
        case2queueIn.connections["next"] = case2
        case2.connections["next"] = case2queueOut
    else:
        case2queueIn.connections["next"] = case2
        case2.connections["next"] = case2queueOut
    case2queueOut.connections["next"] = case3queueIn
    
    if c.loc[c.index==4]['M/A/T'].values == 'M':
        case3queueIn.connections["next"] = case3
        case3.connections["next"] = case3queueOut
    else:
        case3queueIn.connections["next"] = case3
        case3.connections["next"] = case3queueOut
    case3queueOut.connections["next"] = case4.input_ports[0]
    
    case4.output_ports[0].connections["next"] = case5queueIn
    
   
    if c.loc[c.index==6]['M/A/T'].values == 'M':
        case5queueIn.connections["next"] = case5
        case5.connections["next"] = case5queueOut
    else:
        case5queueIn.connections["next"] = case5
        case5.connections["next"] = case5queueOut
    case5queueOut.connections["next"] = case6queueIn
    
    if c.loc[c.index==3]['M/A/T'].values == 'M':
        case6queueIn.connections["next"] = case6
        case6.connections["next"] = case6queueOut
    else:
        case6queueIn.connections["next"] = case6
        case6.connections["next"] = case6queueOut
    case6queueOut.connections["next"] = final1case

    g_ele.connections["next"] = ele0
    ele0.connections["next"] = ele1queue
    ele1queue.connections["next"] = ele1
    ele1.connections["next"] = ele2queueIn
    ele2queueIn.connections["next"] = ele2
    ele2.connections["next"] = ele2queueOut
    ele2queueOut.connections["next"] = ele_line1 # type: ignore
    for i in range(1, 25):
        globals()[f'ele_line{i}'].connections["next"] = globals()[f'ele_line{i+1}']  # type: ignore
    ele_line25.connections["next"] = ele_line26.input_ports[0] # type: ignore
    
    ele_line26.output_ports[0].connections["next"] = final1ele
    
    final1ele.connections["next"] = final2assebly.toStore(0)
    final1case.connections["next"] = final2assebly.toStore(1)
    
    final2assebly.connections["next"] = final2inspect
    final2inspect.connections["next"] = final3
    final3.connections["next"] = final4pack
    final4pack.connections["next"] = final5pallet
    final5pallet.connections["next"] = T
    
    # %% operators
    n_lim = e['# of operators'].values[0]
    n_max = 15
    list_stations_case = [case0,case1,case2,case3,case4,case5,case6]
    list_stations_ele = [ele0,ele1,ele2,ele_line2,ele_line4,ele_line6,ele_line8,ele_line10,ele_line12,ele_line14,ele_line16,ele_line18,ele_line20,ele_line22,ele_line24,ele_line26] # type: ignore
    list_stations_final = [final2assebly,final2inspect,final4pack,final5pallet]
    list_stations = list_stations_case + list_stations_ele + list_stations_final
    op_list = list()
    
    for i in range(1,n_max+1):
        if b[i].sum():
            # op = Operator(env)
            op_list.append(Operator(env))
            for j in b[i].index:
                if b[i][j]>0:
                    if c['M/A/T'][j]=='M' or c['M/A/T'][j]=='S' or c['M/A/T'][j]=='C':
                        op_list[-1].connections["stations"].append(list_stations[int(j-1)])
            # op_list.append(op)
            # del(op)
            if len(op_list)==n_lim:
                break
     
    # raise BaseException
            
    # %% maintenance
    TTR = 300 #300
    std_machines = [9,10,25]
    for index in std_machines:
        A = M[index]
        list_stations[index-1].var.TTR["value"] = TTR/50
        list_stations[index-1].var.failure_rate = 1/(TTR+TTR*(A/(1-A)))*100 #100
        
        # A = M[index]
        # list_stations[index-1].var.TTR = TTR/(A**10)
        # list_stations[index-1].var.failure_rate = 1/(TTR+TTR*(A/(1-A)))*100*500 #100
        # if index == 25:
        #     list_stations[index-1].var.TTR = TTR/50
        #     list_stations[index-1].var.failure_rate = 1/(TTR+TTR*(A/(1-A)))*100 #100

    
    
    # %% run
    
    step = 600
    time_end = 24*3600
    prod_parts = list()
    time_start = time.time()
    print('Good luck!')
   
    # utils.create_connection_chart(list(env._agents.values()))
    
    for i in range(step,time_end,step):
        env.run(i)
        prod_parts.append(len(T.store))
        if MONITORING: # monitoring
            print('Time elapsed: %d [s]' %i)
            if len(T.store)==0:
                print('Warning - no output')
            else:

                print(len(T.store))
            elapsed = time.time()-time_start
            log2(env)
            if elapsed>180:
                print('timeout')
                break
            else:
                print(elapsed)
    print('Done!')
    print('Wall clock time: %f [s]' %(time.time()-time_start))
    
    prod_parts=prod_parts[round(len(prod_parts)/10):]
    print(prod_parts)
    th2=pd.Series(prod_parts).diff().dropna()
    th2 = th2*3600*24/step
    th = th2.describe()
    # th[1] = th[1].round()
    th.rename('Throughput [products/day]',inplace=True)
    

    th[5]=th[1]+t_dist.ppf(0.05,th[0])*th[2]/th[0]**(1/2)
    th[6]=th[1]+t_dist.ppf(0.95,th[0])*th[2]/th[0]**(1/2)
    th[4]=th[7]
    th.rename({th.index[4]:'max',th.index[5]:'lower bound - 95% confidence interval',th.index[6]:'upper bound - 95% confidence interval'},inplace=True)
    th=th[1:-1]
    
    
    states = statelog(env, astable=True)
    states = states.iloc[:-2]
    states.index = list(range(1,1+len(states.index)))
    states.index.name = "index"
    
    states_op = statelog(env, astable=True, filter=lambda x: isinstance(x._agent, Operator))
    states_op.rename(columns={"Sleep": "Idle"}, inplace=True)
    states_op.index = list(range(1,1+len(states_op.index)))
    states_op.index.name = "index"

        
    if GANTT:
        from hsim.core.utils.utils import GSOMGantt
        gantt = GSOMGantt(env,agentList=list_stations,html=True)
    if folder == '':
        string = 'result.xlsx'
    else:
        string = folder+'result.xlsx'

    if app==False:
        writer = pd.ExcelWriter(string, engine = 'xlsxwriter')
        states.to_excel(writer, sheet_name = 'U')
        states_op.to_excel(writer, sheet_name = 'U (operators)')
        th.to_excel(writer, sheet_name = 'TH')
        writer.save()
    else:
        result = {'TH':th,'U':states,'Uop':states_op,'T':T}
        if GANTT:
            result['GANTT'] = gantt
        return result


if __name__ == '__main__':
    filename = r"C:\Users\Lorenzo\DIG Dropbox\Lorenzo Ragazzini\Didattica\MIP-GSOM Game\20230323 GSOM MBA 2023 INDUSTRY40 SIMULATION CASE\GSOM_original.xlsx"
    main(filename,app=True)
