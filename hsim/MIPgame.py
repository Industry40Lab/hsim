# -*- coding: utf-8 -*-


from pymulate import Store, Queue, Environment, Generator, Server, ServerWithBuffer, ServerDoubleBuffer, Operator, ManualStation, SwitchOut

from pymulate import MachineMIP, SwitchQualityMIP, FinalAssemblyManualMIP, FinalAssemblyMIP, AutomatedMIP

import pandas as pd
import numpy as np
from collections.abc import Iterable

env = Environment()

def normal_dist_bounded(val):
    mean = val[0]
    std = val[0]
    if mean < 0:
        raise BaseException()
    y = 0
    while y <= 0:
        y = np.random.normal(mean,std)
    return y
        
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
    
folder = 'C:/Users/Lorenzo/Dropbox (DIG)/Didattica/MIP/MIP 11-6-22/'
# folder = 'C:/Users/Lorenzo/Dropbox (DIG)/Didattica/MIP/MIP 11-6-22/MIP test Lorenzo/xDaniele/'
filename = 'MIP1.xlsx'
path = folder+filename
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
        d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)*(4*np.arctan(agv_num/agv_sat)/np.pi)

for index in range(11,12):
    if a.loc[a.index.values==index,'Material handling'].values == 1:
        d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.04)
    elif a.loc[a.index.values==index,'Material handling'].values == 2:
        d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.08)
    elif a.loc[a.index.values==index,'Material handling'].values == 3:
        d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.08)*(4*np.arctan(agv_num/agv_sat)/np.pi)
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
        d.loc[d.index==index,'Time'] = d.loc[d.index==index,'Time']*(1-0.1)*(4*np.arctan(agv_num/agv_sat)/np.pi)


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
g_case = Generator(env,'g1',serviceTime=10,createEntity=ggg)
g_case.var.createEntity = ggg

case0 = ManualStation(env,serviceTime=d.loc[d.index==1].values,serviceTimeFunction=normal_dist_bounded)
case1 = ServerDoubleBuffer(env,serviceTime=d.loc[d.index==2].values,serviceTimeFunction=normal_dist_bounded,capacityIn = 4, capacityOut = 4)

case2queueIn = Queue(env,capacity = 4)
if c.loc[c.index==3]['M/A/T'].values == 'M':
    case2 = ManualStation(env,serviceTime=d.loc[d.index==3].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==3]['M/A/T'].values == 'S':
    case2 = AutomatedMIP(env,serviceTime=d.loc[d.index==3].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==3]['M/A/T'].values == 'A':
    case2 = Server(env,serviceTime=d.loc[d.index==3].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==3]['M/A/T'].values == 'C':
    case2 = ManualStation(env,serviceTime=d.loc[d.index==3].values*0.25,serviceTimeFunction=normal_dist_bounded)

case2queueOut = Queue(env,capacity = 4)

case3queueIn = Queue(env,capacity = 4)
if c.loc[c.index==4]['M/A/T'].values == 'M':
    case3 = ManualStation(env,serviceTime=d.loc[d.index==4].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==4]['M/A/T'].values == 'S':
    case3 = AutomatedMIP(env,serviceTime=d.loc[d.index==4].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==4]['M/A/T'].values == 'A':
    case3 = Server(env,serviceTime=d.loc[d.index==4].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==4]['M/A/T'].values == 'C':
    case3 = ManualStation(env,serviceTime=d.loc[d.index==4].values*0.25,serviceTimeFunction=normal_dist_bounded)
case3queueOut = Queue(env,capacity = 4)

case4 = ServerDoubleBuffer(env,serviceTime=d.loc[d.index==5].values,serviceTimeFunction=normal_dist_bounded)
case4quality = SwitchQualityMIP(env)
case4quality.var.quality_rate = Q_case
case4scrap = Store(env)

case5queueIn = Queue(env,capacity = 4)
if c.loc[c.index==6]['M/A/T'].values == 'M':
    case5 = ManualStation(env,serviceTime=d.loc[d.index==6].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==6]['M/A/T'].values == 'S':
    case5 = AutomatedMIP(env,serviceTime=d.loc[d.index==6].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==6]['M/A/T'].values == 'A':
    case5 = Server(env,serviceTime=d.loc[d.index==6].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==6]['M/A/T'].values == 'C':
    case5 = ManualStation(env,serviceTime=d.loc[d.index==6].values*0.25,serviceTimeFunction=normal_dist_bounded)
case5queueOut = Queue(env,capacity = 4)


case6queueIn = Queue(env,capacity = 4)
if c.loc[c.index==7]['M/A/T'].values == 'M':
    case6 = ManualStation(env,serviceTime=d.loc[d.index==7].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==7]['M/A/T'].values == 'S':
    case6 = AutomatedMIP(env,serviceTime=d.loc[d.index==7].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==7]['M/A/T'].values == 'A':
    case6 = Server(env,serviceTime=d.loc[d.index==7].values,serviceTimeFunction=normal_dist_bounded)
elif c.loc[c.index==7]['M/A/T'].values == 'C':
    case6 = ManualStation(env,serviceTime=d.loc[d.index==7].values*0.25,serviceTimeFunction=normal_dist_bounded)
case6queueOut = Queue(env,capacity = 4)


# %% electronics
ggg = gen_motor()
g_ele = Generator(env,'g2',serviceTime=10,createEntity=ggg)
g_ele.var.createEntity = ggg

ele0 = ManualStation(env,serviceTime=d.loc[d.index==8].values,serviceTimeFunction=normal_dist_bounded)
ele1queue = Queue(env,4)
ele1 = MachineMIP(env,'ele1',serviceTime=d.loc[d.index==9].values,serviceTimeFunction=normal_dist_bounded)
ele2queueIn = Queue(env,4)
ele2 = MachineMIP(env,'ele2',serviceTime=d.loc[d.index==10].values,serviceTimeFunction=normal_dist_bounded)
ele2queueOut = Queue(env,4)

for i in range(2,25,2):
    j = int(i/2+10)
    g = globals()
    if c.loc[c.index==j]['M/A/T'].values == 'M':
        g['ele_line'+str(i)] = ManualStation(env,serviceTime=d.loc[d.index==j].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==j]['M/A/T'].values == 'S':
        g['ele_line'+str(i)] = AutomatedMIP(env,serviceTime=d.loc[d.index==j].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==j]['M/A/T'].values == 'A':
        g['ele_line'+str(i)] = Server(env,serviceTime=d.loc[d.index==j].values,serviceTimeFunction=normal_dist_bounded)
    elif c.loc[c.index==j]['M/A/T'].values == 'C':
        g['ele_line'+str(i)] = ManualStation(env,serviceTime=d.loc[d.index==3].values*0.25,serviceTimeFunction=normal_dist_bounded)

    
ele_line1 = Queue(env)
# ele_line2 = ManualStation(env,serviceTime=d.loc[d.index==11].values,serviceTimeFunction=normal_dist_bounded)
ele_line3 = Queue(env)
# ele_line4 = ManualStation(env,serviceTime=d.loc[d.index==12].values,serviceTimeFunction=normal_dist_bounded)
ele_line5 = Queue(env)
# ele_line6 = ManualStation(env,serviceTime=d.loc[d.index==13].values,serviceTimeFunction=normal_dist_bounded)
ele_line7 = Queue(env)
# ele_line8 = ManualStation(env,serviceTime=d.loc[d.index==14].values,serviceTimeFunction=normal_dist_bounded)
ele_line9 = Queue(env)
# ele_line10 = ManualStation(env,serviceTime=d.loc[d.index==15].values,serviceTimeFunction=normal_dist_bounded)
ele_line11 = Queue(env)
# ele_line12 = ManualStation(env,serviceTime=d.loc[d.index==16].values,serviceTimeFunction=normal_dist_bounded)
ele_line13 = Queue(env)
# ele_line14 = ManualStation(env,serviceTime=d.loc[d.index==17].values,serviceTimeFunction=normal_dist_bounded)
ele_line15= Queue(env)
# ele_line16= ManualStation(env,serviceTime=d.loc[d.index==18].values,serviceTimeFunction=normal_dist_bounded)
ele_line17= Queue(env)
# ele_line18 = ManualStation(env,serviceTime=d.loc[d.index==19].values,serviceTimeFunction=normal_dist_bounded)
ele_line19 = Queue(env)
# ele_line20= ManualStation(env,serviceTime=d.loc[d.index==20].values,serviceTimeFunction=normal_dist_bounded)
ele_line21= Queue(env)
# ele_line22 = ManualStation(env,serviceTime=d.loc[d.index==21].values,serviceTimeFunction=normal_dist_bounded)
ele_line23 = Queue(env)
# ele_line24 = ManualStation(env,serviceTime=d.loc[d.index==22].values,serviceTimeFunction=normal_dist_bounded)
ele_line25 = Queue(env)


ele_line26in = Queue(env)
ele_line26 = Server(env,'ele_line26',serviceTime=d.loc[d.index==23].values,serviceTimeFunction=normal_dist_bounded)
ele_line26out = Queue(env)

ele_quality = SwitchQualityMIP(env)
ele_quality.var.quality_rate = Q_ele
ele_scrap = Store(env)

# %% final

final1case = Store(env)
final1ele = Store(env)
final2assebly = FinalAssemblyManualMIP(env,serviceTime=d.loc[d.index==24].values,serviceTimeFunction=normal_dist_bounded)
final2inspect = MachineMIP(env,serviceTime=d.loc[d.index==25].values,serviceTimeFunction=normal_dist_bounded)

final3 = Queue(env)
if a['Packaging'][26] == 0:
    final4pack = ManualStation(env,serviceTime=d.loc[d.index==26].values,serviceTimeFunction=normal_dist_bounded)
elif a['Packaging'][26] == 1:
    final4pack = Server(env,serviceTime=d.loc[d.index==26].values,serviceTimeFunction=normal_dist_bounded)
elif a['Packaging'][26] == 2:
    final4pack = Server(env,serviceTime=d.loc[d.index==26].values*0.7,serviceTimeFunction=normal_dist_bounded)

if a['Dispatching'][27] == 0:
    final5pallet = ManualStation(env,serviceTime=d.loc[d.index==27].values,serviceTimeFunction=normal_dist_bounded)
elif a['Dispatching'][27] == 1:
    final5pallet = Server(env,serviceTime=d.loc[d.index==27].values,serviceTimeFunction=normal_dist_bounded)


T = Store(env)

# %% connect
g_case.connections['after'] = case0

case0.connections['after'] = case1

case1.connections['after'] = case2queueIn

if c.loc[c.index==3]['M/A/T'].values == 'M':
    case2queueIn.connections['after'] = case2
    case2.connections['after'] = case2queueOut
else:
    case2queueIn.connections['after'] = case2
    case2.connections['after'] = case2queueOut
case2queueOut.connections['after'] = case3queueIn

if c.loc[c.index==4]['M/A/T'].values == 'M':
    case3queueIn.connections['after'] = case3
    case3.connections['after'] = case3queueOut
else:
    case3queueIn.connections['after'] = case3
    case3.connections['after'] = case5queueOut
case3queueOut.connections['after'] = case4

case4.connections['after'] = case4quality
case4quality.connections['after'] = case5queueIn
case4quality.connections['rework'] = case4scrap

if c.loc[c.index==6]['M/A/T'].values == 'M':
    case5queueIn.connections['after'] = case5
    case5.connections['after'] = case5queueOut
else:
    case5queueIn.connections['after'] = case5
    case5.connections['after'] = case5queueOut
case5queueOut.connections['after'] = case6queueIn

if c.loc[c.index==3]['M/A/T'].values == 'M':
    case6queueIn.connections['after'] = case6
    case6.connections['after'] = case6queueOut
else:
    case6queueIn.connections['after'] = case6
    case6.connections['after'] = case6queueOut
case6queueOut.connections['after'] = final1case

g_ele.connections['after'] = ele0
ele0.connections['after'] = ele1queue
ele1queue.connections['after'] = ele1
ele1.connections['after'] = ele2queueIn
ele2queueIn.connections['after'] = ele2
ele2.connections['after'] = ele2queueOut
ele2queueOut.connections['after'] = ele_line1
ele_line1.connections['after'] = ele_line2
ele_line2.connections['after'] = ele_line3
ele_line3.connections['after'] = ele_line4
ele_line4.connections['after'] = ele_line5
ele_line5.connections['after'] = ele_line6
ele_line6.connections['after'] = ele_line7
ele_line7.connections['after'] = ele_line8
ele_line8.connections['after'] = ele_line9
ele_line9.connections['after'] = ele_line10
ele_line10.connections['after'] = ele_line11
ele_line11.connections['after'] = ele_line12
ele_line12.connections['after'] = ele_line13
ele_line13.connections['after'] = ele_line14
ele_line14.connections['after'] = ele_line15
ele_line15.connections['after'] = ele_line16
ele_line16.connections['after'] = ele_line17
ele_line17.connections['after'] = ele_line18
ele_line18.connections['after'] = ele_line19
ele_line19.connections['after'] = ele_line20
ele_line20.connections['after'] = ele_line21
ele_line21.connections['after'] = ele_line22
ele_line22.connections['after'] = ele_line23
ele_line23.connections['after'] = ele_line24
ele_line24.connections['after'] = ele_line25
ele_line25.connections['after'] = ele_line26in

ele_line26in.connections['after'] = ele_line26
ele_line26.connections['after'] = ele_line26out
ele_line26out.connections['after'] = ele_quality
ele_quality.connections['after'] = final1ele
ele_quality.connections['rework'] = ele_scrap

final2assebly.connections['before1'] = final1case
final2assebly.connections['before2'] = final1ele
final2assebly.connections['after'] = final2inspect
final2inspect.connections['after'] = final3
final3.connections['after'] = final4pack
final4pack.connections['after'] = final5pallet
final5pallet.connections['after'] = T

# %% operators
n_max = e['# of operators'].values[0]
n_max=min(n_max,15)
list_stations_case = [case0,case1,case2,case3,case4,case5,case6]
list_stations_ele = [ele0,ele1,ele2,ele_line2,ele_line4,ele_line6,ele_line8,ele_line10,ele_line12,ele_line14,ele_line16,ele_line18,ele_line20,ele_line22,ele_line24,ele_line26]
list_stations_final = [final2assebly,final2inspect,final4pack,final5pallet]
list_stations = list_stations_case + list_stations_ele + list_stations_final
op_list = list()
for i in range(1,n_max+1):
    if b[i].sum():
        op = Operator(env)
        # op_list.append(Operator(env))
        for j in b[i].index:
            if b[i][j]>0:
                if c['M/A/T'][j]=='M' or c['M/A/T'][j]=='S' or c['M/A/T'][j]=='C':
                    # if isinstance(list_stations[int(j-1)],Iterable):
                    #     for s in list_stations[int(j-1)]:
                    #         op.add_station(s)
                    # else:
                    # op.add_station(list_stations[int(j-1)])
                    op.var.station.append(list_stations[int(j-1)])
                    # op_list[-1].var.station.append(list_stations[int(j-1)])
            # elif c['M/A/T'][j]=='M' or c['M/A/T'][j]=='S': #remove
            #     if isinstance(list_stations[int(j-1)],Iterable):
            #         for s in list_stations[int(j-1)]:
            #             op.add_station(s)
            #     else:
            #         op.add_station(list_stations[int(j-1)])
        
        op_list.append(op)
        del(op)
        
# raise BaseException
        
# %% maintenance
TTR = 300
std_machines = [9,10,25]
for index in std_machines:
    A = M[index]
    list_stations[index-1].var.TTR = TTR
    list_stations[index-1].var.failure_rate = 1/(TTR+TTR*(A/(1-A)))*100



# %% run

import time
step = 1800
time_end = 24*3600
prod_parts = list();
time_start = time.time()
print('Good luck!')
for i in range(step,time_end,step):
    env.run(i)
    prod_parts.append(len(T))
    if False: # monitoring
        print('Time elapsed: %d [s]' %i)
        if len(T)==0:
            print('Warning - no output')
        else:
            print(len(T))
        elapsed = time.time()-time_start
        if elapsed>30:
            print('timeout')
            break
        else:
            print(elapsed)
print('Done!')
env.state_log2 = pd.DataFrame(env.state_log,columns = env.state_log2.columns)
    
th2=pd.Series(prod_parts).diff().dropna()
th2 = th2*3600*24/step
th = th2.describe()[1:]
th[1] = th[1].round()


from utils import stats
s = stats(env)

from collections import OrderedDict
statistics = OrderedDict()
for machine in list_stations_case:
    try:
        for m in machine:
            statistics[m._name] = [{key._name:s[m][key]} for key in s[m]]
    except:
        statistics[machine._name] = [{key._name:s[machine][key]} for key in s[machine]]

for machine in list_stations_ele:
    try:
        for m in machine:
            statistics[m._name] = [{key._name:s[m][key]} for key in s[m]]
    except:
        statistics[machine._name] = [{key._name:s[machine][key]} for key in s[machine]]


for machine in list_stations_final:
    try:
        for m in machine:
            statistics[m._name] = [{key._name:s[m][key]} for key in s[m]]
    except:
        statistics[machine._name] = [{key._name:s[machine][key]} for key in s[machine]]

states = pd.DataFrame([])
for machine in statistics:
    new_dict={k:v for element in statistics[machine] for k,v in element.items()}
    new_df = pd.DataFrame(new_dict,index=[0])
    states = pd.concat([states,new_df])
states = states.fillna(0)
states.drop(columns='GetIn',inplace=True)
states.drop(columns='GetOut',inplace=True)

list_all = list_stations_case + list_stations_ele + list_stations_final
list_labels = list()
for i in b.index:
    try:
        iter(list_all[i-1])
        list_labels.append(str('%da'%i))
        list_labels.append(str('%db'%i))
        list_labels.append(str('%dc'%i))
    except:
        list_labels.append(str(i))
states['index']=list_labels
states.set_index('index',inplace=True)


i = 1
while True:
    try:
        string = str('results_%d.xlsx' %i)
        pd.read_excel(folder+string)
        i +=1
    except PermissionError:
        i += 1
    except:
        break
writer = pd.ExcelWriter(folder+string, engine = 'xlsxwriter')
th.to_excel(writer, sheet_name = 'TH')
states.to_excel(writer, sheet_name = 'U')
writer.save()
# writer.close()

import dill
def check_recursive(obj):
    if dill.pickles(obj):
        pass
        # print('%s is ok' %repr(obj))
    else:
        print('%s NOT ok' %repr(obj))
    try:
        for i in vars(obj):
            check_recursive(i)
    except:
        pass
        # print('not checked: %s' %repr(obj))
            