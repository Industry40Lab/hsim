# Native libraries
import os
import math
# Essential Libraries
import pandas as pd
from pandas import Series
import matplotlib.pyplot as plt
import numpy as np
# Preprocessing
from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler
# Algorithms

from tslearn.barycenters import dtw_barycenter_averaging
from tslearn.clustering import TimeSeriesKMeans
from sklearn.cluster import KMeans

from sklearn.decomposition import PCA
import kuka_analysis as kuka
from sklearn.decomposition import PCA

df = pd.read_csv('Run1.csv',parse_dates=["Zeit"], index_col="Zeit")
print(df.info())
data = df[['DriveMotorCurr_Act1','DriveMotorCurr_Act2', 'DriveMotorCurr_Act3', 'DriveMotorCurr_Act4', 'DriveMotorCurr_Act5', 'DriveMotorCurr_Act6']]

#df= df.reset_index()

x1=df[['DriveMotorCurr_Act1']]

sample_period = 12 * 10 ** -3  # to be set manually
sample_rate = 1 / sample_period


# filter noise
df= kuka.low_pass_filter(df, cutoff_frequency=1, sample_rate=sample_rate, show=True)
df["sum"] = df.abs().sum(axis=1)
print(df["sum"])
x=df["sum"]

print(df.head(5))

fig = plt.figure();
ax = fig.add_subplot(111);
ax.plot( df['DriveMotorCurr_Act1'], label = 'Axis1');
ax.plot( df['DriveMotorCurr_Act2'],  label = 'Axis2');
ax.plot( df['DriveMotorCurr_Act3'],  label = 'Axis3');
ax.plot( df['DriveMotorCurr_Act4'],  label = 'Axis4');
ax.plot( df['DriveMotorCurr_Act5'],  label = 'Axis5');
ax.plot( df['DriveMotorCurr_Act6'],  label = 'Axis6');

#ax.plot(df['sum'], color = (0,0,0), linewidth = 2, alpha = .9, label = 'Sum');
#ax.set_title('Sum')
ax.set_xlabel('Zeit')
ax.set_ylabel('axis')
ax.legend(loc='lower right');
plt.show()



# segment and regress
reg = list()
points = kuka.segment(x, show=True)
reg.append(kuka.seg_lin_reg(x, points, show=True))


