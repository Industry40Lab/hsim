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

df = pd.read_csv('Run1.csv')
print(df.info())
data = df[['DriveMotorCurr_Act1','DriveMotorCurr_Act2', 'DriveMotorCurr_Act3', 'DriveMotorCurr_Act4', 'DriveMotorCurr_Act5', 'DriveMotorCurr_Act6']]

df= df.reset_index()
sample_period = 12 * 10 ** -3  # to be set manually
sample_rate = 1 / sample_period

# filter noise
df= kuka.low_pass_filter(df, cutoff_frequency=1, sample_rate=sample_rate, show=True)
df["sum"] = df.abs().sum(axis=1)
print(df["sum"])
sum=df["sum"]


import scipy.integrate as integrate
from scipy.interpolate import InterpolatedUnivariateSpline
import scipy.special as special

V=48

x = df['Zeit'].to_numpy()
y = df['DriveMotorCurr_Act1'].to_numpy()

max = np.max(x)
min = np.min(x)

#f = InterpolatedUnivariateSpline(x, y, k=1)  # k=1 gives linear interpolation
#f.integral(min , max)

intStep = 1    # Interpolation step
# Interpolated x and y
xInt = np.arange(min, max + 1, intStep).reshape(-1,1)
yInt = (np.interp(xInt, x, y) - x).clip(min=0)
fig, ax = plt.subplots()
ax.grid(True)
plt.plot(xInt, yInt)
plt.show()

f = InterpolatedUnivariateSpline(xInt, yInt, k=1)
result = f.integral(min, max)
print(result)


# segment and regress
reg = list()
points = kuka.segment(sum, show=True)
reg.append(kuka.seg_lin_reg(sum, points, show=True))