# -*- coding: utf-8 -*-

import pymulate as pym
from chfsm import CHFSM, Transition, State
import pandas as pd
import numpy as np
from simpy import AnyOf
from copy import deepcopy
from random import choices,seed,normalvariate, expovariate
from stores import Store, Box       
from scipy import stats
import dill
import utils



class Generator(pym.Generator):
    def __init__(self,env,name=None,serviceTime=2,serviceTimeFunction=None):
        super().__init__(env,name,serviceTime,serviceTimeFunction)
        self.count = 0
    def createEntity(self):
        self.count += 1
        # return Entity()
        e = Entity()
        # e.serviceTime = dict()
        e.serviceTime['front'] = 10.52
        e.serviceTime['drill'] = choices([3.5, 8.45, 9.65, 11.94],weights=[5,30,30,35])[0]
        e.serviceTime['robot'] = choices([0, 81, 105, 108 ,120],weights=[91,3,2,2,2])[0]
        # e.serviceTime['camera'] = choices([3,9,12,18,24],weights=[2,3,1,2,2])[0]
        e.serviceTime['camera'] = 3.5+expovariate(1/7.1)
        e.serviceTime['back'] = choices([3.5,10.57],weights=[0.1,0.9])[0]
        # e.serviceTime['press'] = choices([3,9,15])[0]
        if e.serviceTime['back']>0:
            e.serviceTime['press'] = 3.5+expovariate(1/9.5)
        else:
            e.serviceTime['press'] = 3.5
        e.serviceTime['manual'] = max(np.random.normal(9.2,1),0)
        return e
        
class Entity:
    def __init__(self,ID=None):
        self.ID = ID
        self.ok = True
        self.serviceTime = dict()
        # self.pt['M3'] = 1
    @property
    def require_robot(self):
        if self.serviceTime['robot']>0:
            return True
        else:
            return False
                
class LabServer(pym.Server):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None):
        self.controller = None
        # serviceTime = 10
        super().__init__(env,name,serviceTime,serviceTimeFunction)
    def calculateServiceTime(self,entity=None,attribute='serviceTime'):
        if not entity.ok:
            return 3.5
        else:
            return super().calculateServiceTime(entity,attribute)
    def completed(self):
        if self.var.entity.ok:
            self.controller.Messages.put(self.name)
    T2=Transition(pym.Server.Working, pym.Server.Blocking, lambda self: self.env.timeout(self.calculateServiceTime(self.var.entity)), action = lambda self: self.completed())

class Terminator(pym.Terminator):
    def __init__(self, env, capacity=np.inf):
        super().__init__(env, capacity)
        self.controller = None
        self.register = list()
    def completed(self):
        if not self.trigger.triggered:
            self.trigger.succeed()
    def put(self,item):
        self.register.append(self._env.now)
        self.controller.Messages.put('terminator')
        return super().put(item)
    def subscribe(self,item):
        self.register.append(self._env.now)
        self.controller.Messages.put('terminator')
        return super().subscribe(item)
        
class Gate(CHFSM):
    def __init__(self,env,DR,OR,method,freq):
        self.real = True
        self.method = method
        self.freq = 120
        self.length = 600
        self.lookback = 120
        self.capacity = 30
        self.window = 300
        self.lab = None
        self.DR = DR
        self.OR = OR
        self.BN = 'back'
        self.monitored_DBR = list()
        self.monitored_CONWIP = None
        self.initialWIP = 12
        self.request = None
        self.message = env.event()
        self.initial_timeout = env.event()
        self.initial_timeout.succeed()
        self.WIP = 0
        self.WIPlist = list()
        self.BNlist = list()
        super().__init__(env)
    def build(self):
        self.Store = pym.Store(self.env,self.capacity)
        self.Messages = pym.Store(self.env)
    def put(self,item):
        return self.Store.put(item)
    class Loading(State):
        def _do(self):
            # print('Load: %d' %self.sm.initialWIP)
            self.sm.initialWIP -= 1
            self.fw()
    class Waiting(State):
        initial_state = True
        def _do(self):
            self.sm.message = self.Messages.subscribe()
            if self.sm.initialWIP > 0:
                self.initial_timeout = self.env.timeout(1)
            else:
                self.initial_timeout = self.env.event()
    class Forwarding(State):
        def _do(self):
            self.message.confirm()
            if self.message.value == 'terminator':
                self.sm.WIP -= 1
                self.sm.WIPlist.append([self.env.now,self.WIP])
            if self.DR == 'FIFO':
                self.FIFO()
            elif self.DR == 'SPT':
                self.SPT()
            elif self.DR == 'LPT':
                self.LPT()
            if self.OR == 'DBR':
                self.DBR()
            elif self.OR == 'CONWIP':
                self.CONWIP()
    def CONWIP(self):
        if self.message.value == 'terminator':
            self.fw()
    def DBR(self):
        if self.WIP > 14:
            return
        elif self.BN == self.message.value:
            self.fw()
        elif self.WIP < 12:
            self.fw()
    def FIFO(self):
        pass
    def SPT(self):
        self.Store.items = sorted(self.Store.items, key=lambda obj: obj.__getattribute__('serviceTime')[self.BN])        
        #self.Store.items = sorted(self.Store.items, key=lambda obj: obj.__getattribute__('serviceTime')[self.BN]/sum(obj.__getattribute__('serviceTime').values()))        
    def LPT(self):
        lpt = list()
        for e in self.Store.items:
            pt = 0
            for machine in ['front','drill','robot','camera','back','press','manual']:
                # pt += e.serviceTime[machine]
                if machine is self.BN:
                    lpt.append(pt)
                    break
                else:
                    pt += e.serviceTime[machine]
        indices = sorted(range(len(lpt)), key=lambda i: lpt[i])
        indices.reverse()
        self.Store.items = [self.Store.items[i] for i in indices]
    def fw(self):        
        if self.request is None:
            self.request = self.Store.get()
        try:
            self.Next.put(self.request.value)
            self.request = None
            self.WIP += 1
            self.WIPlist.append([self.env.now,self.WIP])
        except:
            pass
            # print('Empty at %s' %self.env.now)
    class Controlling(State):
        initial_state = True
        def _do(self):
            if self.real:
                log_file = self.env.state_log
                try:
                    BN, stats = BN_detection(log_file,self.env.now-self.window,self.env.now)
                except:
                    if len(self.BNlist)>0:
                        BN = self.BNlist[-1]
                    else:
                        BN = self.BN
                self.BNlist.append([self.env.now,BN])
                # print('BN at %f is %s'%(self.env.now,BN))
                if self.method == 'present': #run BN
                    BN, stats = BN_detection(log_file,self.env.now-self.lookback,self.env.now)
                    self.sm.BN = BN
                elif self.method == 'future':
                    dt = deepcopy(self.lab)
                    dt.g.Next = Store(dt.env)
                    dt.gate.real=False
                    dt.gate.initialWIP = 0
                    log_file = dt.run(self.env.now+self.length)
                    
                    # self.sm.BN, stats = BN_detection(log_file,self.env.now-self.lookback,self.env.now+self.length)

                    try:
                        self.sm.BN, stats = BN_detection(log_file,self.env.now-self.lookback,self.env.now+self.length)
                    except:
                        pass
                elif self.method == 'None':
                    pass
    T0 = Transition(Waiting,Loading,lambda self: self.initial_timeout)
    T1 = Transition(Waiting,Forwarding,lambda self: self.sm.message)
    T2 = Transition(Loading,Waiting,None)
    T3 = Transition(Forwarding,Waiting,None)
    TC = Transition(Controlling,Controlling,lambda self: self.env.timeout(self.freq))

class Router(pym.Router):
    def __deepcopy(self,memo):
        super().deepcopy(self,memo)
    def __init__(self, env, name=None):
        super().__init__(env, name)
        self.var.requestOut = []
        self.var.sent = []
        self.putEvent = env.event()
    def build(self):
        self.Queue = Box(self.env)
    def condition_check(self,item,target):
        return True
    def put(self,item):
        if self.putEvent.triggered:
            self.putEvent.restart()
        self.putEvent.succeed()
        return self.Queue.put(item)
    class Sending(State):
        initial_state = True
        def _do(self):
            self.sm.putEvent.restart()
            self.sm.var.requestIn = self.sm.putEvent
            self.sm.var.requestOut = [item for sublist in [[next.subscribe(item) for next in self.sm.Next if self.sm.condition_check(item,next)] for item in self.sm.Queue.items] for item in sublist]
            if self.sm.var.requestOut == []:
                self.sm.var.requestOut.append(self.sm.var.requestIn)
    S2S2 = Transition(Sending,Sending,lambda self:AnyOf(self.env,self.var.requestOut),condition=lambda self:self.var.requestOut != [])
    def action2(self):
        self.Queue._trigger_put(self.env.event())
        if not hasattr(self.var.requestOut[0],'item'):
            return
        for request in self.var.requestOut:
            if not request.item in self.Queue.items:
                request.cancel()
                continue
            if request.triggered:
                if request.check():
                    request.confirm()
                    self.Queue.forward(request.item)
                    continue
    S2S2._action = action2
'''  
from pymulate import RouterNew
class Router(RouterNew):
    def __init__(self, env, name=None):
        capacity=1
        super().__init__(env, name,capacity)
'''
class RobotSwitch1(Router):
    def condition_check(self, item, target):
        if item.require_robot and target.name == 'convRobot1S':
            return True
        elif not item.require_robot and target.name != 'convRobot1S':
            return True
        else:
            return False
            
class RobotSwitch2(Router):
    def condition_check(self, item, target):
        if len(target.Next)<2:
            item.rework = False
            return True
        else:
            item.rework = True
            return False    

class CloseOutSwitch(Router):
    def condition_check(self, item, target):
        if item.ok and type(target) == Terminator:
            return True
        elif not item.ok and type(target) != Terminator:
            return True
        else:
            return False
        
# class Conveyor(pym.ParallelServer):
#     def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,capacity=1):
#         self._capacity = capacity
#         serviceTime = capacity*3.5
#         super().__init__(env,name,serviceTime,serviceTimeFunction,capacity)
class Conveyor(pym.Conveyor):
    def __init__(self,env,name=None,capacity=3):
        super().__init__(env,name,capacity,0.75)
        
def newDT():
    lab = globals()['lab']
    deepcopy(lab)

def BN_detection(log_file,start,end):
    ' Step 1: Preparation of Raw Data'
      
    #LR
    log_file=pd.DataFrame(log_file)
    log_file = log_file.loc[(log_file[4]>=start) & (log_file[4]<=end)]
    
    log_file=log_file[[1,3,4,5]]
    log_file=log_file.loc[log_file[1].isin(['front','drill','robot','camera','back','press','manual'])]
    log_file=log_file.rename(columns={1:'resource',3:'activity',4:'timeIn',5:'timeOut'})
    log_file.loc[log_file.activity=='Working','activity']='Work'
    log_file.loc[log_file.activity=='Blocking','activity']='Block'
    log_file.loc[log_file.activity=='Starving','activity']='Starve'
    from datetime import datetime
    log_file['timeIn'] = pd.to_timedelta(log_file['timeIn'],'s')+datetime.now()
    log_file['timeOut'] = pd.to_timedelta(log_file['timeOut'],'s')+datetime.now()

    
    # Rewrite the log_file as Time|Process|Status
    data = pd.DataFrame(columns = ['Time','Process','Status'])
    data[['Time','Process','Status']] = log_file[['timeIn','resource','activity']]
    
    Tmax = log_file['timeOut'].max()
    data.Status.replace("Work",1,inplace=True)     
    data.Status.replace(["Starve","Block"],0,inplace=True)
    
    #LR
    # data=data.drop_duplicates(subset=['Time'],keep='last')
    # LR alt
    data = data.pivot_table(index='Time', columns='Process', values = 'Status')
    data = data.fillna(method='ffill')
    data.fillna(0, inplace=True)
    data=data.drop_duplicates(keep='last')

    
    # Transfrom Long table (Time|Process|Staus) into Short table (Time|M1|M2|...|)
    # data = data.pivot(index='Time', columns='Process', values = 'Status')
    
    # Fill enmpty entries with data from previous entries
    data = data.fillna(method='ffill')
    data.fillna(0, inplace=True)
    ' Step 2: Accumulation Transformation'
    
    # Entering actual duration of active states
    data_interval = data.copy(deep=True)
    # data_interval['Time'] = data_interval.index
    
    data_interval['Time'] = np.append(np.diff(data_interval.index.values)/np.timedelta64(1,'s'),(Tmax-data_interval.index[-1])/np.timedelta64(1,'s'))
    data_interval=data_interval.multiply(data_interval.Time,axis="index")
    
    # Cumulative duration
    data_interval=data_interval.cumsum()
    data_interval.drop(columns=['Time'],inplace=True)
         
    # Total duration of active periods
    for s in data_interval:
        data_interval[s][data_interval[s]>0] = data_interval[s].max()

    ' Step 3: Bottleneck detection'
    
    # Momentary BN detection

    for i in range(data_interval.shape[0]):
        for j in range(data_interval.shape[1]):
            if type(data_interval.iloc[i,j]) == pd._libs.tslibs.timedeltas.Timedelta:
               data_interval.iloc[i,j] = data_interval.iloc[i,j].total_seconds()
    
    data_interval.values[range(len(data_interval.index)), np.argmax(data_interval.values, axis=1)] = -1        
               
    # Backward check
    data_interval[np.multiply(data_interval.values*np.vstack([data_interval.values[1:,:],np.zeros([1,data_interval.shape[1]])])<0,data_interval.values>0)] = -1
               
    # Forward check 
    data_interval[np.multiply(data_interval.values*np.vstack([np.zeros([1,data_interval.shape[1]]),data_interval.values[:-1,:]])<0,data_interval.values>0)] = -1
    ' Step 4: Shfting Bottleneck detection'
    
    # Shifting BN 
    s=(data_interval[data_interval==-1].fillna(0).sum(axis=1)<-1)
    
    # LR edit:
    data_interval.loc[s[s].index] = data_interval.loc[s[s].index] * 2
    # data_interval.loc[s[s].index].replace(-1,-2,inplace=True)

    ' Step 5: Bottleneck percentages computation'
    
    
    data_interval['Time'] = np.append(np.diff(data_interval.index.values)/np.timedelta64(1,'s'),(Tmax-data_interval.index[-1])/np.timedelta64(1,'s'))
    # Sole BN duration
    BN_sole = data_interval.copy(deep=True)
    BN_sole.values[BN_sole.values>0]=0
    BN_sole.values[BN_sole.values==-2]=0
    BN_sole.values[BN_sole.values==-1]=1
    BN_sole['Time'] = np.append(np.diff(data_interval.index.values)/np.timedelta64(1,'s'),(Tmax-data_interval.index[-1])/np.timedelta64(1,'s'))
    BN_sole=BN_sole.multiply(BN_sole.Time,axis="index")
    BN_sole.drop(columns=['Time'],inplace=True)
    
    # Shifting BN duration
    BN_shifting = data_interval.copy(deep=True)
    BN_shifting.values[BN_shifting.values>=-1]=0
    BN_shifting.values[BN_shifting.values==-2]=1
    BN_shifting['Time'] = np.append(np.diff(data_interval.index.values)/np.timedelta64(1,'s'),(Tmax-data_interval.index[-1])/np.timedelta64(1,'s'))
    BN_shifting=BN_shifting.multiply(BN_shifting.Time,axis="index")
    BN_shifting.drop(columns=['Time'],inplace=True)

    col = []
    for i in range(1, BN_sole.shape[1]+1):
        col.append('M%s' %i)
    
    if BN_shifting.values.sum()>1:
        print('shift')

    # BN_synthetic = pd.DataFrame(columns = col, index = ['Sole BN', 'Shifting BN', 'Tot BN'])
    BN_synthetic=pd.concat([BN_sole.sum(),BN_shifting.sum(),BN_sole.sum()+BN_shifting.sum()],axis=1).transpose()
    BN_synthetic.index=['Sole BN', 'Shifting BN', 'Tot BN']

    # Create bar chart
    BN_synthetic1 = BN_synthetic.copy(deep=True)
    BN_synthetic1 = BN_synthetic1.drop('Tot BN',axis=0)
    BN_synthetic1.transpose().plot(kind='bar', stacked=True)
    BN_synthetic1.reset_index(inplace=True)
    BN_synthetic1 = BN_synthetic1.melt(id_vars='index', var_name='Resource', value_name='Time percentage')
    BN_synthetic1.rename(columns ={ 'index' : 'BN type'}, inplace = True)

    #LR
    BN_synthetic=BN_synthetic.divide(BN_synthetic.sum(axis=1).values,axis=0).fillna(0)

    # BN finder
    BN_percentages = BN_synthetic.iloc[2,:]
    
    BN_string=[]
    maxval = np.max(BN_percentages.values)
    for i in range(len(BN_percentages.values)):
        if BN_percentages.values[i] == maxval:
            BN_string.append(BN_percentages.index[i])
        
    # [BN_synthetic, data_interval, BN_string] 
    # print(BN_string)
    # return BN_string
    

    maxval = np.max(BN_percentages.values)
    for i in range(len(BN_percentages.values)):
        if BN_percentages.values[i] == maxval:
            return BN_percentages.index[i],BN_percentages
'''
class Generator(Generator):
    def createEntity(self):
        self.count += 1
        if len(self.jList)==1: #last
            self.var.serviceTime = 10e100
        return self.jList.pop(0)
    def newEntity(self):
        self.count += 1
        # return Entity()
        e = Entity()
        # e.serviceTime = dict()
        e.serviceTime['front'] = 10.52
        e.serviceTime['drill'] = choices([3.5, 8.45, 9.65, 11.94],weights=[5,30,30,35])[0]
        e.serviceTime['robot'] = choices([0, 81, 105, 108 ,120],weights=[91,3,2,2,2])[0]
        # e.serviceTime['camera'] = choices([3,9,12,18,24],weights=[2,3,1,2,2])[0]
        e.serviceTime['camera'] = 3.5+expovariate(1/7.1)
        e.serviceTime['back'] = choices([3.5,10.57],weights=[0.1,0.9])[0]
        # e.serviceTime['press'] = choices([3,9,15])[0]
        if e.serviceTime['back']>0:
            e.serviceTime['press'] = 3.5+expovariate(1/9.5)
        else:
            e.serviceTime['press'] = 3.5
        e.serviceTime['manual'] = max(np.random.normal(9.2,1),0)
        return e
'''
def newEntity():
    e = Entity()
    e.serviceTime['front'] = 10.52
    e.serviceTime['drill'] = choices([3.5, 8.45, 9.65, 11.94],weights=[5,30,30,35])[0]
    e.serviceTime['robot'] = choices([0, 81, 105, 108 ,120],weights=[91,3,2,2,2])[0]
    e.serviceTime['camera'] = 3.5+expovariate(1/7.1)
    e.serviceTime['back'] = choices([3.5,10.57],weights=[0.1,0.9])[0]
    if e.serviceTime['back']>0:
        e.serviceTime['press'] = 3.5+expovariate(1/9.5)
    else:
        e.serviceTime['press'] = 3.5
    e.serviceTime['manual'] = max(np.random.normal(9.2,1),0)
    return e

def batchCreate(seed=1,numJobs=10):
    np.random.seed(seed)
    jList = []
    while len(jList)<numJobs:
        e=newEntity()
        num = round(np.random.triangular(1,10,15))
        for i in range(num):
            jList.append(deepcopy(e))
    return jList

class Lab:
    def __init__(self,DR:str,OR:str,method:str,freq=120):
        conveyTime = 6
        self.DR = DR
        self.OR = OR
        self.method = method
        self.freq = freq
        
        self.env = pym.Environment()
        self.BN = None
        self.g = Generator(self.env)
        self.gate = Gate(self.env,DR,OR,method,freq)
        
        # self.conv1 = Conveyor(self.env,capacity=3)
        self.conv1S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv1Q = pym.Queue(self.env,capacity=2)
        self.front = LabServer(self.env,'front')
        # self.conv2 = Conveyor(self.env,capacity=3)
        self.conv2S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv2Q = pym.Queue(self.env,capacity=2)
        self.drill = LabServer(self.env,'drill')
        # self.conv3 = Conveyor(self.env,capacity=3)
        self.conv3S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv3Q = pym.Queue(self.env,capacity=2)

        
        self.switch1 = RobotSwitch1(self.env)
        # self.convRobot1 = Conveyor(self.env,'convRobot1',capacity=3)
        self.convRobot1S = pym.Server(self.env,serviceTime=conveyTime,name='convRobot1S')
        self.convRobot1Q = pym.Queue(self.env,capacity=2)

        # self.bridge = Conveyor(self.env,capacity=3)
        self.bridgeS = pym.Server(self.env,serviceTime=conveyTime)
        self.bridgeQ = pym.Queue(self.env,capacity=2)

        # self.convRobot2 = Conveyor(self.env,'convRobot2',capacity=3)
        self.convRobot2S = pym.Server(self.env,serviceTime=conveyTime)
        self.convRobot2Q = pym.Queue(self.env,capacity=2)

        self.switch2 = RobotSwitch2(self.env)
        # self.convRobot3 = Conveyor(self.env,capacity=3)
        self.convRobot3S = pym.Server(self.env,serviceTime=conveyTime)
        self.convRobot3Q = pym.Queue(self.env,capacity=2)

        self.robot = LabServer(self.env,'robot')
        # self.convRobotOut = Conveyor(self.env,capacity=3)
        self.convRobotOutS = pym.Server(self.env,serviceTime=conveyTime)
        self.convRobotOutQ = pym.Queue(self.env,capacity=2)
        # self.conv5 = Conveyor(self.env,capacity=3)
        self.conv5S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv5Q = pym.Queue(self.env,capacity=2)

        self.camera = LabServer(self.env,'camera')
        # self.conv6 = Conveyor(self.env,capacity=3)
        self.conv6S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv6Q = pym.Queue(self.env,capacity=2)

        self.back = LabServer(self.env,'back')
        # self.conv7 = Conveyor(self.env,capacity=3)
        self.conv7S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv7Q = pym.Queue(self.env,capacity=2)

        self.press = LabServer(self.env,'press')
        # self.conv8 = Conveyor(self.env,capacity=3)
        self.conv8S = pym.Server(self.env,serviceTime=conveyTime)
        self.conv8Q = pym.Queue(self.env,capacity=2)

        self.manual = LabServer(self.env,'manual')
        self.outSwitch = CloseOutSwitch(self.env)
        self.terminator = Terminator(self.env)
        
        self.g.Next = self.gate
        self.gate.Next = self.conv1S
        
        # self.conv1.Next = self.front
        self.conv1S.Next = self.conv1Q
        self.conv1Q.Next = self.front

        self.front.Next = self.conv2S
        # self.conv2.Next = self.drill
        self.conv2S.Next = self.conv2Q
        self.conv2Q.Next = self.drill
        self.drill.Next = self.conv3S
        self.conv3S.Next = self.conv3Q
        self.conv3Q.Next = self.switch1
        # self.conv3.Next = self.switch1
        
        self.switch1.Next = [self.convRobot1S,self.bridgeS]
        self.convRobot1S.Next = self.convRobot1Q
        self.convRobot1Q.Next = self.switch2

        self.switch2.Next = [self.convRobot2S,self.convRobot3S]
        self.convRobot2S.Next = self.convRobot2Q
        self.convRobot2Q.Next = self.robot

        self.convRobot3S.Next = self.convRobot3Q
        self.convRobot3Q.Next = self.convRobotOutS

        self.robot.Next = self.convRobotOutS
        self.convRobotOutS.Next = self.convRobotOutQ

        self.convRobotOutQ.Next = self.conv5S
        self.bridgeS.Next = self.bridgeQ
        self.bridgeQ.Next = self.conv5S

        
        self.conv5S.Next = self.conv5Q
        self.conv5Q.Next = self.camera

        self.camera.Next = self.conv6S
        self.conv6S.Next = self.conv6Q
        self.conv6Q.Next = self.back

        self.back.Next = self.conv7S
        self.conv7S.Next = self.conv7Q
        self.conv7Q.Next = self.press

        self.press.Next = self.conv8S
        self.conv8S.Next = self.conv8Q
        self.conv8Q.Next = self.manual

        self.manual.Next = self.outSwitch
        self.outSwitch.Next = [self.conv1S,self.terminator]
        
        for x in [self.front,self.drill,self.robot,self.camera,self.back,self.press,self.manual]:
            x.controller = self.gate
        self.terminator.controller = self.gate
        self.gate.lab = self

    def run(self,Tend):
        self.env.run(Tend)
        # return pd.DataFrame(self.env.state_log)
        return self.env.state_log





# import sys
# sys.path.insert(0,'C:/Users/Lorenzo/Dropbox (DIG)/Tesisti/Giovanni Zanardo/Python')
# from Foresighted_DT_function import BN_detection

# BN_detection(lab.env.state_log,0,lab.env.now)

class Result:
    def __init__(self,time,BN,OR,DR,production,arrivals,WIPlist,BNlist,state_log):
        self.time=time
        self.BN=BN
        self.OR=OR
        self.DR=DR
        self.production=production
        self.arrivals=arrivals
        self.WIPlist = WIPlist
        self.state_log=state_log
        self.BNlist = BNlist
    @property
    def avgWIP(self):
        integral = 0.0
        prev_time = None
        prev_value = None
        # Iterate over the data points and compute the integral
        for time, value in self.WIPlist:
            if prev_time is not None and prev_value is not None:
                dt = time - prev_time
                integral += prev_value * dt
            prev_time = time
            prev_value = value
        return integral/time
    @property
    def productivity(self):
        return (3600/pd.DataFrame(self.arrivals).diff()).describe()
    @property
    def CI(self):
        prod = self.productivity
        tinv = stats.t.ppf(1-0.05/2, prod[0][0])
        return prod[0][1] - prod[0][2]*tinv/np.sqrt(prod[0][0]), prod[0][1] + prod[0][2]*tinv/np.sqrt(prod[0][0])



# %% prove varie

if False:
    lab=Lab('none','CONWIP','FIFO')
    lab.run(600)
    print(len(lab.terminator.items))
    
    lab2=deepcopy(lab)
    for el in [lab2.switch1,lab2.switch2,lab2.outSwitch]:
        el.start()
    lab2.run(600)
    print(len(lab2.terminator.items))
    import utils
    fig=utils.createGantt(lab2.env.log)
    fig.write_html('cancella.html')

if False:
    import dill
    import time
    lab=Lab('FIFO','DBR','present')
    while lab.env.now < 1000:
        print(lab.env.now)
        lab.env.run(10)
        u = list()
        # for obj in lab.__dict__.values():
        #     print(obj)
        #     time.sleep(0.05)
        #     u.append(deepcopy(obj))
        deepcopy(lab)
    # lab.run(360)
    
    print(lab.terminator.items)
    
if False:
    explore = list()
    OR = 'DBR'
    DR = 'FIFO'
    freq = 60
    length =  180
    for BN in ['present','future']:
        if BN == 'present':
            lookback = 0
        else:
            lookback = 60
        for seedValue in range(1,11):
            print(BN,OR,DR,lookback,freq,length,seedValue)
            seed(seedValue)
            lab=Lab(DR,OR,BN)
            lab.gate.lookback, lab.gate.freq, lab.gate.length = lookback, freq, length
            lab.run(7200)
            explore.append(Result(lab.env.now,BN,OR,DR,len(lab.terminator.items),lab.terminator.register,lab.gate.WIPlist,lab.gate.BNlist,pd.DataFrame(lab.env.state_log)[[1,3,4,5]]))


# %% testing

'''

perf = list()
for BN in ['none','future','present']:
    for OR in ['CONWIP','DBR']:
        for DR in ['FIFO','SPT','LPT']:
            if DR == 'FIFO' and OR == 'CONWIP' and BN != 'none':
                pass
            elif BN == 'future':
                for lookback in [0,60,120]:
                    for freq in [60,180,300]:
                        for length in [180,300,420]:
                            for seedValue in [1,2,3,4,5]:
                                print(BN,OR,DR,lookback,freq,length,seedValue)
                                seed(seedValue)
                                lab=Lab(DR,OR,BN)
                                lab.gate.lookback, lab.gate.freq, lab.gate.length = lookback, freq, length
                                lab.run(7200)
                                perf.append(Result(lab.env.now,BN,OR,DR,len(lab.terminator.items),lab.terminator.register,lab.gate.WIPlist,lab.gate.BNlist,pd.DataFrame(lab.env.state_log)[[1,3,4,5]]))
            else:
                lookback = 0
                    for length in [180,300,420]:
                        for seedValue in [1,2,3,4,5]:
                            print(BN,OR,DR,lookback,freq,length,seedValue)
                            seed(seedValue)
                            lab=Lab(DR,OR,BN)
                            lab.gate.lookback, lab.gate.freq, lab.gate.length = lookback, freq, length
                            lab.run(7200)
                            perf.append(Result(lab.env.now,BN,OR,DR,len(lab.terminator.items),lab.terminator.register,lab.gate.WIPlist,lab.gate.BNlist,pd.DataFrame(lab.env.state_log)[[1,3,4,5]]))
            with open("performance_analysisBN2", "wb") as dill_file:
                dill.dump(perf, dill_file)
    '''        
# %% experiments
 
if __name__ == 'main':

    import os
    filename = 'resBN_pers6'
    
    
    if filename in os.listdir():
        with open(filename, "rb") as dill_file:
            results = dill.load(dill_file)
    else:
        results=list()
        
    
        
    for BN in ['none','present','future']:
        for OR in ['CONWIP','DBR']:
            for DR in ['FIFO','SPT','LPT']:
                if BN != 'future':
                    continue
                if DR == 'FIFO' and OR == 'CONWIP' and BN != 'none':
                    continue
                for seedValue in range(1,151):
                    print(seedValue,DR,OR,BN)
                    seed(seedValue)
                    lab=Lab(DR,OR,BN)
                    lab.gate.Store.items = batchCreate(seedValue,numJobs=400) #batchedExp
                    if BN == 'future':
                        lab.gate.lookback, lab.gate.freq, lab.gate.length = 60, 60, 180 #era 60,60,180 per pers3
                    elif BN=='none':
                        lab.gate.freq, lab.gate.length, lab.gate.BN = 60,3600, 'back'
                        if DR == 'LPT':
                            lab.gate.BN = 'back'
                    elif BN=='present':
                        lab.gate.lookback, lab.gate.freq, lab.gate.length = 120, 60, 0
                    lab.run(1*60*60)
                    
                    state_log=pd.DataFrame(lab.env.state_log)
                    state_log=state_log.rename(columns={1:'Resource',3:'State',4:'timeIn',5:'timeOut'})
                    
                    
                    newR = Result(lab.env.now,BN,OR,DR,len(lab.terminator.items),lab.terminator.register,lab.gate.WIPlist,lab.gate.BNlist,pd.DataFrame(lab.env.state_log)[[1,3,4,5]])
                    newR.seed=seedValue
                    newR.Cmax = lab.env.log.loc[lab.env.log.ResourceName=='manual','timeIn'].max()
                    results.append(newR)
        with open(filename, "wb") as dill_file:
            dill.dump(results, dill_file)
                
    raise(BaseException())       


#pers2
# pres 60 60 0 best
# future 
# none ko

#pers3 
# pres 120 60 0 
# future 120 60 240
# none ok

#pers4
# future 60 60 180 
# none ok
   

#pers5
# future 45 60 150 best
# none ok
    
# %%  read data
'''
import dill
import pandas as pd

filename = 'resBN_batched12bisLPT'
# filename = 'resBN_batched_prove_newLPT'

with open(filename, 'rb') as file:
    perf = dill.load(file)

# exps = pd.read_excel('C:/Users/Lorenzo/Desktop/bn experiments.xlsx')
exps = pd.DataFrame()

exps['BN'] = [p.BN for p in perf]
exps['OR'] = [p.OR for p in perf]
exps['DR'] = [p.DR for p in perf]
exps['seed'] = [p.seed for p in perf]


exps['WIP'] = [p.avgWIP for p in perf]
# exps['prod'] = [p.production for p in perf]
exps['prod'] = [p.productivity.values[1][0] for p in perf]
exps['prodCI'] = [p.productivity.values[1][0] for p in perf]
exps['std'] = [pd.DataFrame(p.arrivals).diff().dropna().std()[0] for p in perf]
exps['BNmean'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).mean() for p in perf]
exps['BNstd'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).std() for p in perf]
exps['BNskew'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).skew() for p in perf]
exps['BNkurtosis'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).kurtosis() for p in perf]
exps['BNlist'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).to_dict() for p in perf]

# exps.to_excel('C:/Users/Lorenzo/Desktop/bn_results.xlsx')

for BN in exps.BN.unique():
    for OR in exps.OR.unique():
        for DR in exps.DR.unique():
            pass
        
# %%

with open('resBN_full', 'rb') as file:
    perf3 = dill.load(file)

df = pd.DataFrame(columns=['BN','OR','DR','BNlist','WIPlist','production','productivity','CI','avgWIP'])

for res in perf:
    l = dict()
    for el in df.columns:
        l[el] = getattr(res,el)
    df=df.append(l,ignore_index=True)
        
df.to_excel('C:/Users/Lorenzo/Desktop/test.xlsx')
        
x.state_log.rename(columns={1:'Resource',3:'State',4:'timeIn',5:'timeOut'},inplace=True)

# %%
import pandas as pd
import numpy as np

df = pd.read_excel("C:\\Users\\Lorenzo\\Desktop\\BNfinalresults.xlsx")

import itertools
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import ttest_rel

# Subset the DataFrame for the desired factor levels
sub_df = df[['BN', 'OR', 'DR', 'prod']]

# Generate all possible combinations of the unique BN values
bn_combinations = list(itertools.combinations(sub_df['BN'].unique(), 2))

# Perform pairwise comparisons and statistical test
pairwise_comparisons = []
p_values = []
for bn_comb in bn_combinations:
    bn1, bn2 = bn_comb
    mask = (sub_df['BN'].isin([bn1, bn2]))
    sub_data = sub_df.loc[mask]
    
    # Perform the statistical test (t-test in this example)
    stat, p_value = ttest_rel(sub_data.loc[sub_data['BN'] == bn1, 'prod'],
                              sub_data.loc[sub_data['BN'] == bn2, 'prod'])
    
    pairwise_comparisons.append((bn1, bn2))
    p_values.append(p_value)

# Create a DataFrame to store the pairwise comparisons and p-values
results_df = pd.DataFrame({'Pairwise Comparisons': pairwise_comparisons, 'p-value': p_values})

# Plot the results
sns.set(style="whitegrid")
plt.figure(figsize=(8, 6))
sns.barplot(data=results_df, x='Pairwise Comparisons', y='p-value')
plt.xlabel('Pairwise Comparisons (BN)')
plt.ylabel('p-value')
plt.title('Pairwise Comparisons of BN with the same DR and OR')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

'''