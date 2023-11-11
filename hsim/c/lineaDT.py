# -*- coding: utf-8 -*-
from .linea import LabServer
import pandas as pd

class LabServer(LabServer):
    def __init__(self,env,name=None,serviceTime=None,serviceTimeFunction=None,failure_rate=0,TTR=60,run_as_DT=False):
        self.run_as_DT = run_as_DT
        super().__init__(env,name,serviceTime,serviceTimeFunction,failure_rate,TTR)
    def calculateServiceTime(self,entity=None,attribute='serviceTime'):
        if not self.run_as_DT:
            return super().calculateServiceTime(entity,attribute)
        else:
            return self.getServiceTime()
    def getServiceTime(self):
        self.env
        return

class Stream:
    def __init__(self):
        self.source = pd.read_csv('dataset.csv')
    
class DataAcquisition:
    def __init__(self):
        self.source = None
    def connect(self,stream):
        self.source = stream
    def getData(self,timestamp,server):
        timestamp = timestamp%self.source.TS.max()
        return self.source.loc[self.source.index<timestamp,server].iloc[0]
    def getProcessingTime(self,timestamp,server):
        timestamp = timestamp%self.source.TS.max()
        tOut = self.source.loc[(self.source.TS<timestamp) & (self.source[server]==1),'TS'].max()
        tIn = self.source.loc[(self.source.TS<timestamp) & (self.source.TS<tOut) & (self.source[server]==0),'TS'].max()
        return tOut-tIn