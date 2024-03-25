# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 10:59:31 2022

@author: Lorenzo
"""

from sklearn.linear_model import LinearRegression
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
from scipy import signal
import numpy as np
import pandas as pd

# %% read from r64
# warnin: it only applies to specific set of signal

sample_period = 12*10**-3 # to be set manually
sample_rate = 1/sample_period
num_run = 2
filename = 'acquisitions/energy run '+str(num_run)+'_KRCIpo'

with open(filename+'.dat','r') as f:
    d = [i.split(',') for i in f.read().split('\n')]
    n_samples = int(d[[i[0]=='220' for i in d].index(True)][1])

with open(filename+'.r64','rb') as f:
    x=np.fromfile(f)
    n_channels = int(len(x)/n_samples)
    x=x.reshape([n_samples,n_channels])
    x = pd.DataFrame(x)
    
t_axis = np.linspace(0,n_samples*sample_period,n_samples)
x.index = t_axis

# %% 

n_var = len(x)

class slicingProblem(Problem):
    def __init__(self,n_var,data):
        super().__init__(n_var=n_var, n_obj=1, n_constr=0, xl=np.zeros(len(x)), xu=np.ones(len(x)))
        self.data = data
    def _evaluate(self, x, out, *args, **kwargs):
        k=0.49
        all_scores = np.array([])
        for sol in x:
            sp = np.where((sol-k).round().astype(int)==1)[0]
            if len(sp)>10:
                all_scores = np.append(all_scores,10**len(sp))
                continue
            sp1=np.insert(sp,0,0)
            sp2=np.append(sp,len(self.data))
            score = 0
            for i,j in zip(sp1,sp2):
                dataset = self.data.iloc[i:j]
                reg = LinearRegression().fit(dataset.index.values.reshape(-1,1), dataset.values.reshape(-1,1))
                score += sum(abs(reg.predict(dataset.index.values.reshape(-1,1))-dataset.values.reshape(-1,1)))
            all_scores = np.append(all_scores,score)
        print(min(all_scores))
        out["F"] = all_scores.reshape(-1,1)
        # out["F"] = np.sum((x - 0.5) ** 2, axis=1)
        # out["G"] = 0.1 - out["F"]

problem = slicingProblem(len(x),x[1])
# print(problem._evaluate(np.random.uniform(size=len(x)).round(),1))

# %%
algorithm = GA(
    pop_size=100,
    eliminate_duplicates=True)

res = minimize(problem,
               algorithm,
               seed=1,
               verbose=False)

reg = LinearRegression().fit(x.index, x[1])