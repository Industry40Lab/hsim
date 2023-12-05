# -*- coding: utf-8 -*-

import kuka_analysis as kuka
from collections import OrderedDict
import csv
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.integrate as integrate
from scipy.interpolate import InterpolatedUnivariateSpline
import scipy.special as special
from sklearn.linear_model import LinearRegression
import seaborn as sns

sample_period = 12*10**-3 # to be set manually
sample_rate = 1/sample_period

# %% load data
'''
exp=list()
for i in range(1):
    num_run = i+1
    filename = 'acquisitions/energy run '+str(num_run)+'_KRCIpo'
    exp.append(kuka.read_r64(filename))
    
    '''
    
# %% load data
# from acquisition file
exp=list()
exp_num = 1
for i in range(2):
    num_run = i+1
    filename = 'Experiments/EXP_'+str(exp_num).zfill(3)+'_'+str(num_run).zfill(3)+'_KRCIpo'
    print(filename)
    exp.append(kuka.read_r64(filename))

# %% create sum column
for i in range(len(exp)):
    exp[i]=exp[i].assign(total = exp[i].abs().sum(axis=1))


# %% identify starting/end point

for i in range(len(exp)):
    df = kuka.starting_point(exp[i],threshold=0.1,total=True)[0]
    exp[i] = kuka.end_point(df,threshold=0.1,total=True)[0]
    

# %% filter noise
for df in exp:
    for col in df:
        df[col] = kuka.low_pass_filter(df[col],cutoff_frequency=2,sample_rate=sample_rate,show=False)

# %% quantize values
for df in exp:
    df = kuka.quantize(df,1,True)

dfs=pd.DataFrame()


# %% integrate

exp_energy = list()
for df in exp:
    df_energy = df.copy()
    for column in df:
        df_energy.loc[df_energy.index>0,column] = (kuka.integrate(df[column],voltage=48))/1000
        df_energy.loc[df_energy.index==0,column] = 0
    exp_energy.append(df_energy)

for df_energy in exp_energy:
    print(df_energy)
    df_energy.plot()
    plt.show()
    #p = kuka.segment(df_energy["total"], show=True)
    #kuka.seg_lin_reg(df_energy["total"], p, show=True)



# %% segment and regress - test 1
reg = list()
poly=list()
p = list()

k=0
fields = ['lenght', 'mean', 'start', 'end']
for df in exp:
    #points = kuka.segment(df["total"], show=True)
    points = kuka.dynp(df["total"], show=False)
    p.append(points)
    reg.append(kuka.seg_lin_reg(df["total"], points, show=False))
    poly.append(kuka.seg_lin_poly(df["total"], points, show=False))

    #print(reg)
    #print(poly[0])
"""
    k += 1
    newfile_name = "param" + str(k) + ".csv"
    with open(newfile_name, 'w', newline='\n') as f:
         write = csv.writer(f,delimiter=';')
         write.writerow(fields)
         write.writerows(reg[0])

    reg.clear()
"""



# %% refine
# test=reg[9]
# points2 = [i for i in points]
n_max = min([len(i) for i in reg])

for j in range(len(reg)):
    test = reg[j]
    points = p[j]

    # remove similar
    slope_similarity_th = 0.15
    mean_similarity_th = 0.15

    for i in range(1,len(test)):
        if np.abs(test[i][2]-test[i-1][2]) < slope_similarity_th:
            if np.abs(test[i][1]-test[i-1][1]) < mean_similarity_th:
                points[i-1]=0

    # remove vertical
    slope_verticality_th = 0.3
    for i in range(len(test)):
        if np.abs(test[i][2]) > slope_verticality_th:
            points[i]=0


    points = list(filter(lambda a: a != 0, points))
    p[j] = points


# %% re-fitting

# poly: run, segment, vector
# vector: duration, mean, C1, C2
"""
poly=list()

for i in range(len(exp)):
    poly.append(kuka.seg_lin_poly(exp[i]["total"], points, show=True))

    print(poly)"""





# %% kde
import seaborn as sns
program_steps = list()
for segment in range(4):
    performances=list()
    for perf in range(4):
        sns.kdeplot([poly[i][segment][perf] for i in range(len(poly))])

        mdl = kuka.KernelDensityEstimationG(np.array([poly[i][segment][perf] for i in range(len(poly))]))

        performances.append(mdl)
    program_steps.append(performances)



# %% re-fit and save
"""
poly=list()
poly.append(kuka.seg_lin_poly(df["total"], points, show=True))

k += 1
save_file = False
if save_file:
    newfile_name = "param" + str(k) + ".csv"
    with open(newfile_name, 'w', newline='\n') as f:
        write = csv.writer(f,delimiter=';')
        write.writerow(fields)
        write.writerows(poly[0])


# %% get start and end points
start=list()
end=list()
start.append(kuka.starting_point(points,threshold=0.01))
end.append(kuka.end_point(points,threshold=0.01))"""


""""
# %% iterative segment-regress

reg = list()
k=0
fields = ['lenght', 'mean', 'coef', 'intercept']
L=list()
for df in exp:
    points = kuka.segment(df, show=False, pen=30)
    L.append(points.__len__())"""





