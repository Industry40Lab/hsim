# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 13:28:31 2022

@author: Lorenzo
"""

# Data pipeline

from scipy import signal
import numpy as np
import pandas as pd

# %% read from r64
# warnin: it only applies to specific set of signal

sample_period = 12*10**-3 # to be set manually
sample_rate = 1/sample_period

# %% 

    
def read_r64(filename):
    with open(filename+'.dat','r') as f:
        d = [i.split(',') for i in f.read().split('\n')]
        n_samples = int(d[[i[0]=='220' for i in d].index(True)][1])
        sample_period = float(d[[i[0]=='241' for i in d].index(True)][1])
    with open(filename+'.r64','rb') as f:
        x=np.fromfile(f)
        n_channels = int(len(x)/n_samples)
        x=x.reshape([n_samples,n_channels])
        x = pd.DataFrame(x)
        x.index=t_axis = np.linspace(0,n_samples*sample_period,n_samples)
    return x


exp=dict()
for i in range(1,5):
    num_run = i
    filename = 'acquisitions/energy run '+str(num_run)+'_KRCIpo'
    exp[i] = read_r64(filename)
        
    

# %% import from excel
exp=dict()
for i in range(10):
    df = pd.read_excel('Data_file.xlsx',sheet_name=i).drop(index=[0,1,2,3]).set_index("Zeit")
    exp[i]=df

n_channels = len(exp[0].columns)

# %% noise filtering?


def low_pass_filter(x,cutoff_frequency,sample_rate,order=3,show=False):
    nyq = 0.5 * sample_rate # fixed
    normal_cutoff = desired_cutoff/nyq #Hz
    b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)

    y = x.copy()
    if len(y.keys())==len(y.index): # series
        y.loc[y.index] = signal.filtfilt(b, a, x)
    else:
        for i in x.columns:
            y[i] = signal.filtfilt(b, a, x[i])
            # test=pd.DataFrame([x[i],y[i]]).transpose().plot()
    if show:
        x.plot()
        y.plot()
    return y
    
desired_cutoff = 1 #Hz # 0.5 Hz looks good, 0
y = low_pass_filter(exp[1][0],desired_cutoff,sample_rate,show=True)

# alternative: try Spectral Smoothing with Fourier Transform - available in tsmoothie


# %% quantize?

# rounding test

def quantize(x,n_decimals,show=True):
    y = x.copy()
    y = y.round(n_decimals)
    if show:
        x.plot()
        y.plot()
    return y

y = quantize(www,2,True)


# %% cross-correlation

cc = 0
for i in range(n_channels):
    cc += signal.correlate(exp[1].iloc[:,0],exp[0].iloc[:,0])
cc = round(cc.argmax()/n_channels)

def calc_lag(x,y):
    lag = 0
    for i in range(n_channels):
        lag += signal.correlate(x.iloc[:,i],y.iloc[:,i])
    lag = round(lag.argmax()/n_channels)
    return lag
    
for e in exp:
    if e>0:
        # compute lag wrt previous
        lag = 0
        for i in range(e):
            lag += calc_lag(exp[i],exp[e])
        # align
        lag = lag/e
        
        
        
        

# %% slicing/clustering

# works, hate noise but is not perfect
from sktime.annotation.clasp import ClaSPSegmentation
window = 20
n_cps= 10
found_cps = ClaSPSegmentation(window,n_cps=n_cps).fit_predict(y[2])
a=found_cps[1]
pd.DataFrame([y[2][:a],y[2][a:]]).transpose().plot()

# not working
from tslearn.clustering import TimeSeriesKMeans
model = TimeSeriesKMeans(n_clusters=3, metric="dtw", max_iter=10)
model.fit(y[1].values.reshape(-1,1))

# label time series data in py


# %% piecewise linear approx

import numpy as np
import matplotlib.pylab as plt
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression

# parameters for setup
n_data = 20

# segmented linear regression parameters
n_seg = 15

np.random.seed(0)
fig, (ax0, ax1) = plt.subplots(1, 2)


# example 1
#xs = np.sort(np.random.rand(n_data))
#ys = np.random.rand(n_data) * .3 + np.tanh(5* (xs -.5))

# example 2
xs = np.linspace(-1, 1, 20)
ys = np.random.rand(n_data) * .3 + np.tanh(3*xs)

xs = x.index.values
ys = x[0].values

dys = np.gradient(ys, xs)

rgr = DecisionTreeRegressor(max_leaf_nodes=n_seg, min_samples_split=2, min_weight_fraction_leaf=0.05)
rgr.fit(xs.reshape(-1, 1), dys.reshape(-1, 1))
dys_dt = rgr.predict(xs.reshape(-1, 1)).flatten()

ys_sl = np.ones(len(xs)) * np.nan
for y in np.unique(dys_dt):
    msk = dys_dt == y
    lin_reg = LinearRegression()
    lin_reg.fit(xs[msk].reshape(-1, 1), ys[msk].reshape(-1, 1))
    ys_sl[msk] = lin_reg.predict(xs[msk].reshape(-1, 1)).flatten()
    ax0.plot([xs[msk][0], xs[msk][-1]],
             [ys_sl[msk][0], ys_sl[msk][-1]],
             color='r', zorder=1)

ax0.set_title('values')
ax0.scatter(xs, ys, label='data')
ax0.scatter(xs, ys_sl, s=1, label='seg lin reg', color='g', zorder=5)
ax0.legend()

ax1.set_title('slope')
ax1.scatter(xs, dys, label='data')
ax1.scatter(xs, dys_dt, label='DecisionTree', s=1)
ax1.legend()

plt.show()


# %% off-line change point detection
import ruptures as rpt
# detection

def segment(x,show=False):
    # x must be Series or DataFrame
    algo = rpt.Pelt(model="rbf").fit(x.values)
    result = algo.predict(pen=5)
    if show: # display
        rpt.display(x,  result)
        plt.show()
    return result


# %% 

from sklearn.linear_model import LinearRegression
import seaborn as sns
import matplotlib.pyplot as plt# plotting the data points
import matplotlib as mpl
mpl.rcParams['figure.dpi'] = 300


def seg_lin_reg(dataset,points,show=False):
    reg = list()
    for i,j in zip([0]+points[:-1],points):
        y = dataset.iloc[i:j].values
        x = dataset.iloc[i:j].index.values
        lin_reg = LinearRegression()
        lin_reg.fit(x.reshape(-1,1),y.reshape(-1,1))
        reg.append(lin_reg)
        if show:
            sns.lineplot(x=x,y=lin_reg.predict(x.reshape(-1,1)).reshape(1,-1)[0])
    if show:
        sns.scatterplot(x=exp[1][0].index.values,y=exp[1][0].values,s=2)
        plt.show()
    return reg
    
 


   

    

# %% 

from statsmodels.api import OLS

reg = list()
for i,j in zip([0]+result[:-1],result):
    y = data.iloc[i:j].values
    x = data.iloc[i:j].index.values
   
    lin_reg = OLS(y,x).fit()
    reg.append(lin_reg)
    L = x[-1]-x[0]


import seaborn as sns
import matplotlib.pyplot as plt# plotting the data points
sns.scatterplot(x, y=y)#plotting the line
sns.lineplot(x,y=y_pred, color='red')#axes
plt.xlim(0)
plt.ylim(0)
plt.show()
