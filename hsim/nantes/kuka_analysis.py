# -*- coding: utf-8 -*-
"""
Created on Thu Jan 27 11:46:12 2022

@author: Lorenzo
"""
import math

from scipy import signal
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import ruptures as rpt
import seaborn as sns
import matplotlib.pyplot as plt# plotting the data points
from matplotlib import rcParams
import statsmodels.api as sm
from sklearn.neighbors import KernelDensity
from sklearn import linear_model
from numpy.polynomial import Polynomial
import numpy.polynomial.polynomial as poly
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error


#rcParams['figure.dpi'] = 300

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
        x.index = np.linspace(0,n_samples*sample_period,n_samples)
    return x


def low_pass_filter(x,cutoff_frequency,sample_rate,order=3,show=False):
    nyq = 0.5 * sample_rate # fixed
    normal_cutoff = cutoff_frequency/nyq #Hz
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

def quantize(x,n_decimals,show=False):
    y = x.copy()
    y = y.round(n_decimals)
    if show:
        x.plot()
        y.plot()
    return y

def segment(x, show=False, model="l1", min_size=3, jump=5, pen=10):
    # x must be Series or DataFrame
    # model = "l1"  # "l2", "rbf"
    res=list()
    algo = rpt.Pelt(model=model, min_size=min_size, jump=jump).fit(x.values)
    result = algo.predict(pen=pen)
    res.append(result)
    print(result)
    if show: # display
        rpt.display(x,  result)
        plt.show()
    return result

def bottomup(x, show=False, model="l1", min_size=3, jump=5, pen=10):
    # x must be Series or DataFrame
    # model = "l1"  # "l2", "rbf"
    algo = rpt.BottomUp(model=model, min_size=min_size, jump=jump).fit(x.values)
    result = algo.predict(pen=pen)
    if show: # display
        rpt.display(x,  result)
        plt.show()
    return result

def dynp(x, show=False, model="l2", min_size=3, jump=5, n_bkps=3):
    # x must be Series or DataFrame
    # model = "l1"  # "l2", "rbf"
    algo = rpt.Dynp(model=model, min_size=min_size, jump=jump).fit(x.values)
    result = algo.predict(n_bkps=n_bkps)

    if show: # display
        rpt.display(x, result)
        plt.show()
    return result

def window(x, show=False, model="l1", min_size=3, jump=5, pen=10):
    # x must be Series or DataFrame
    # model = "l1"  # "l2", "rbf"
    algo = rpt.Window(model=model, min_size=min_size, jump=jump).fit(x.values)
    result = algo.predict(pen=pen)
    if show: # display
        rpt.display(x,  result)
        plt.show()
    return result


def seg_lin_reg(dataset,points,show=False):
    reg = list()
    #mse=list()
    for i,j in zip([0]+points[:-1],points):
        r = list()
        y = dataset.iloc[i:j].values #True/expected values
        x = dataset.iloc[i:j].index.values
        lin_reg = LinearRegression()
        lin_reg.fit(x.reshape(-1, 1), y.reshape(-1, 1))
        y_pred=lin_reg.predict(x.reshape(-1,1)).reshape(1,-1)[0] #predictions
        r.append(x[-1]-x[0])
        r.append(y.mean())
        a=lin_reg.coef_
        b=lin_reg.intercept_
        r.append(float(a[0]))
        r.append(float(b[0]))
        reg.append(r)
        #loss function
        error=[y[i]-y_pred[i] for i in range(len(y))] #error per point
        mean_error = sum(error) * 1.0 / len(y) #mean_error
        mse=mean_squared_error(y,y_pred) #mse per experiment
        msep=[mean_squared_error(y,y_pred) for i in range(len(y))] #mse per point
        mae = mean_absolute_error(y, y_pred) #mae per experient

        if show:
            sns.lineplot(x=x,y=lin_reg.predict(x.reshape(-1,1)).reshape(1,-1)[0])

    print('error:%s' % error)
    print('mean_error:%s' % mean_error)
    print('MAE:%f' % mae)
    print('MSE: %f' % mse)

    if show:
        sns.scatterplot(x=dataset.index.values,y=dataset.values,s=5)
        plt.show()
    return reg


def seg_lin_ridge(dataset, points, show=False):
    reg = list()
    for i, j in zip([0] + points[:-1], points):
        r = list()
        y = dataset.iloc[i:j].values
        x = dataset.iloc[i:j].index.values

        lin1 = linear_model.Ridge(alpha=.5)
        lin1.fit(x.reshape(-1, 1), y.reshape(-1, 1))

        r.append(x[-1] - x[0])
        r.append(y.mean())
        a = lin1.coef_
        b = lin1.intercept_
        r.append(float(a[0]))
        r.append(float(b[0]))
        reg.append(r)
        if show:
            sns.lineplot(x=x, y=lin1.predict(x.reshape(-1, 1)).reshape(1, -1)[0])
    if show:
        sns.scatterplot(x=dataset.index.values, y=dataset.values, s=5)
        plt.show()
    return reg

def seg_lin_lasso(dataset, points, show=False):
    reg = list()
    for i, j in zip([0] + points[:-1], points):
        r = list()
        y = dataset.iloc[i:j].values
        x = dataset.iloc[i:j].index.values

        lin2 = linear_model.Lasso(alpha=0.1)
        lin2.fit(x.reshape(-1, 1), y.reshape(-1, 1))


        r.append(x[-1] - x[0])
        r.append(y.mean())
        a = lin2.coef_
        b = lin2.intercept_
        r.append(float(a[0]))
        r.append(float(b[0]))
        reg.append(r)
        if show:
            sns.lineplot(x=x, y=lin2.predict(x.reshape(-1, 1)).reshape(1, -1)[0])
    if show:
        sns.scatterplot(x=dataset.index.values, y=dataset.values, s=5)
        plt.show()
    return reg

def seg_lin_poly(dataset, points, show=False):
    reg = list()
    for i, j in zip([0] + points[:-1], points):
        r = list()
        y = dataset.iloc[i:j].values

        x = dataset.iloc[i:j].index.values
        #A = np.vstack([x, np.ones(len(x))]).T

        coefs = poly.polyfit(x, y, 1)
        x_new = np.linspace(x[0], x[-1], num=len(x) * 10)
        l = x[-1] - x[0]
        r.append(l)
        r.append(y.mean())

        ffit = poly.polyval(x_new, coefs)
        
        #start = coefs[0]
        C1 = coefs[0] + coefs[1]*x[0]
        r.append(float(C1))
        #C2=coefs[1]

        C2 = coefs[0] + coefs[1]*x[-1]
        r.append(float(C2))
        #C2=C1+l
        #end=start+l
        alpha=math.atan(C2/l)  #alpha in rad
        alphad = math.atan(C2 / l) * 180 / math.pi #alpha in degree

        r.append(alpha)
        reg.append(r)

        #plt.plot(x_new, ffit)
        # Or create the polynomial function #Compute polynomial values.
        #ffit1 = poly.Polynomial(coefs)  # instead of np.poly1d
        #plt.plot(x_new, ffit1(x_new))

        # or
        #p = Polynomial.fit(x, y, 1)
        #p = np.polyfit(x, y, 1)
        #m,c= np.linalg.lstsq(A, y, rcond=None)[0]


        #r.append(p.new_series.convert().coef)
        #plt.plot(*p.linspace())

        # p uses scaled and shifted x values for numerical stability. If you need the usual form of the coefficients, you will need to follow with
        #pnormal = p.convert(domain=(-1, 1))
        # r.append(lin_reg)



        if show:
            plt.plot(x_new, ffit)
            #plt.plot(x_new, ffit1(x_new))
            #plt.plot(*p.linspace())



    if show:
        sns.scatterplot(x=dataset.index.values, y=dataset.values, s=5)
        plt.show()
    return reg


def KernelDensityEstimationG(dataset):
    bw = sm.nonparametric.KDEUnivariate(dataset).fit(kernel='gau',bw='scott').bw
    return KernelDensity(kernel="gaussian",bandwidth=bw).fit(dataset.reshape(-1,1))

def integrate(series,voltage, show=False):
    data = series.abs()
    dt = data.index[1]-data.index[0]
    temp=voltage*(data.values+data.diff().values/2)[1:]*dt

    return np.cumsum(temp)



def starting_point(df,threshold=0.01,total=True):
    t0 = 0
    if total:
        t0 = df['total'].loc[df['total'].values > threshold].index[0]
        new_df = df.loc[df.index>t0]
        new_df.index = df.iloc[0:len(df.loc[df.index>t0])].index
    else:
        for col in range(6):
            t0 += df[col].loc[df[col].values > threshold].index[0]
        new_df = df.loc[df.index>t0/6]
        new_df.index = df.iloc[0:len(df.loc[df.index>t0/6])].index
    return new_df, t0/6

def end_point(df,threshold=0.01,total=True):
    t0 = 0
    if total:
        t0 = df['total'].loc[df['total'].values > threshold].index[-1]
        new_df = df.loc[df.index<t0]
        new_df.index = df.iloc[0:len(df.loc[df.index<t0])].index
    for col in range(6):
        t0 += df[col].loc[df[col].values > threshold].index[-1]
    new_df = df.loc[df.index<t0/6]
    new_df.index = df.iloc[0:len(df.loc[df.index<t0/6])].index
    return new_df, t0/6