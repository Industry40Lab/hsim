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

x1 = kuka.low_pass_filter(x1,cutoff_frequency=1,sample_rate=sample_rate,show=False)

# %% quantize values

kuka.quantize(x1,3,True)

#Sampling 1/10th of the Data
one_tenth = df.sample(frac = .1, random_state=np.random.randint(10))
# removing index name
one_tenth.index.name = None
one_tenth = one_tenth.sort_values(by=['Index'], ascending=[True])
one_tenth.head()



#axes = one_tenth.plot('Index', 'DriveMotorCurr_Act1', legend = False, title = 'Sampled Plot');
#axes.legend = None;
#axes.set_ylabel('Current');

"""fig, axes = plt.subplots(nrows = 1, ncols = 2, figsize = (10,5));
axes[0].plot('Index', 'DriveMotorCurr_Act1', data = df);
axes[0].set_title('Original Plot');
axes[1].plot('Index', 'DriveMotorCurr_Act1', data = one_tenth);
axes[1].set_title('Sampled Plot');"""


df= df.reset_index()
df.head(3)

df['Rolling_Mean'] = df['DriveMotorCurr_Act1'].rolling(window = 80).mean()
df.head(5)
x1=df[['DriveMotorCurr_Act1']]

fig, axes = plt.subplots(nrows = 1, ncols = 3, figsize = (15,5));
axes[0].plot('Index', 'DriveMotorCurr_Act1', data = df);
axes[0].set_title('Original');
axes[1].plot('Index', 'DriveMotorCurr_Act1', data = one_tenth);
axes[1].set_title('Sampled');
axes[2].plot('Index', 'Rolling_Mean', data = df);
axes[2].set_title('Smoothed (Rolling_Mean)');
plt.show()

# Almost exactly the code as above but with datetime
fig = plt.figure();
ax = fig.add_subplot(111);
ax.plot(df['Zeit'], df['DriveMotorCurr_Act1'], color = (1,0,0), label = 'Original');
ax.plot(df['Zeit'], df['Rolling_Mean'], color = (0,0,0), linewidth = 2, alpha = .9, label = 'Smoothed');
ax.set_title('Original and Smoothed values')
ax.set_xlabel('Index')
ax.set_ylabel('DriveMotorCurr_Act1')
ax.legend(loc='lower right');
plt.show()

df['Rolling_Mean']
import ruptures as rpt
# detection
algo = rpt.Pelt(model="rbf").fit(one_tenth)
result = algo.predict(pen=1)

# display
rpt.display(one_tenth,  result)
plt.show()

from sklearn.linear_model import LinearRegression
import seaborn as sns
import matplotlib.pyplot as plt  # plotting the data points
import matplotlib as mpl


model = LinearRegression().fit(df[['Index']], df[['DriveMotorCurr_Act1']])
m = model.coef_[0]
b = model.intercept_
#equation of the line
print('y = ', round(m[0],2), 'x + ', round(b[0],2))

reg = list()
for i in zip([0] + result[:-1], result):
    y =x1.values
    x =x1.index.values
    lin_reg = LinearRegression()
    lin_reg.fit(x.reshape(-1, 1), y.reshape(-1, 1))
    L = x[-1] - x[0]
    reg.append(lin_reg)
    # sns.scatterplot(x=x,y=y)
    pred=lin_reg.predict(x,y)
    sns.lineplot(x=x, y=pred)



# using the equation of the line to get y values
predictions = model.predict(df[['Index']])
predictions[0:5]

# making a DataFrame for the predictions
predictions = pd.DataFrame(data = predictions, index = df.index.values, columns = ['Pred'])
predictions.head()

joined_df = df.join(predictions, how = 'inner')
joined_df.head()

fig = plt.figure();
ax = fig.add_subplot(111);
ax.plot(joined_df['Index'], joined_df['DriveMotorCurr_Act1'], color = (0,0,0), linewidth = 4, alpha = .9, label = 'Smoothed');
ax.plot(joined_df['Index'], joined_df['Pred'], color = (1,0,0), label = 'Prediction');
ax.set_title('Rolling Mean vs Linear Regression')
ax.set_xlabel('Index')
ax.set_ylabel('DriveMotorCurr_Act1')
ax.legend(loc='lower right');

plt.show()

import sklearn

r_squared = sklearn.metrics.r2_score(joined_df['DriveMotorCurr_Act1'],joined_df['Pred'],multioutput='uniform_average')
print('r_squared', r_squared)


