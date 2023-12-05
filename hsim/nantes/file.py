# Native libraries
import os
import math
# Essential Libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# Preprocessing
from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler
# Algorithms
import kuka_analysis as kuka


df = pd.read_csv('Run1.csv',parse_dates=["Zeit"], index_col="Zeit")
print(df.info())
data = df[['DriveMotorCurr_Act1','DriveMotorCurr_Act2', 'DriveMotorCurr_Act3', 'DriveMotorCurr_Act4', 'DriveMotorCurr_Act5', 'DriveMotorCurr_Act6']]

x1=df[['DriveMotorCurr_Act1']]
df['Index'] = range(0,len(df.index.values))
print(data.head(5))

# %% filter noise
sample_period = 12*10**-3 # to be set manually
sample_rate = 1/sample_period

data = kuka.low_pass_filter(data,cutoff_frequency=1,sample_rate=sample_rate,show=True)

# %% quantize values

kuka.quantize(data,3,False)
plt.show()