# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


tbl=pd.read_excel('C:\\Users\\Lorenzo\\Desktop\\bn.xlsx')
tbl.fillna('0',inplace=True)
tbl[tbl.columns[2:9]]=tbl[tbl.columns[2:9]].astype(int)

r=tbl[tbl.columns[2:9]]
new=pd.DataFrame(index=['Analytical', 'Data', 'Simulation'],columns=['Static','Past', 'Present', 'Future']).fillna(0)

for i in range(len(r)):
    ind=r.iloc[i][:3].index[r.iloc[i][:3]>0]
    col = r.iloc[i][3:].index[r.iloc[i][3:]>0]
    new.loc[new.index.isin(ind),col]+=1
   
# %% hist
    
x = np.arange(len(new.index))
fig,ax = plt.subplots(1,1,figsize=(12, 6))
new.T.plot.bar(stacked=True,ax=ax)

plt.ylabel('Documents count')
plt.legend()

# Show the plot
ax.grid(which='minor', axis='y', linestyle='--', linewidth=0.25)
ax.grid(which='major', axis='y', linestyle='-', linewidth=0.5)

# Set the grid intervals
ax.yaxis.set_major_locator(plt.MultipleLocator(10))
ax.yaxis.set_minor_locator(plt.MultipleLocator(5))

for container in ax.containers:
    ax.bar_label(container, label_type='center', color='black')

plt.show()

fig.savefig('litHist.pdf', format="pdf", bbox_inches="tight",dpi=900)

# %% Applic

appl={
'Production management \n(scheduling)':	15,
'Maintenance':	9,
'System improvement':	5,
'Energy management':	1,
'Other':	4}

df=pd.DataFrame.from_dict(appl,orient='index',columns=['Documents count'])

fig,ax = plt.subplots(1,1,figsize=(8, 6))
df.plot.bar(ax=ax)
# Show the plot
plt.ylabel('Documents count')
ax.get_legend().remove()

ax.grid(which='minor', axis='y', linestyle='--', linewidth=0.25)
ax.grid(which='major', axis='y', linestyle='-', linewidth=0.5)

# Set the grid intervals
ax.yaxis.set_major_locator(plt.MultipleLocator(5))
ax.yaxis.set_minor_locator(plt.MultipleLocator(1))

for container in ax.containers:
    ax.bar_label(container, label_type='edge', color='black')


fig.savefig('applHist.pdf', format="pdf", bbox_inches="tight",dpi=900)

# %% over time
import matplotlib.pyplot as plt
tbl=pd.read_excel('C:\\Users\\Lorenzo\\Desktop\\bn.xlsx', sheet_name=1)
tbl.fillna('0',inplace=True)


timeline = []
for yy in range(tbl.Year.min()+1,tbl.Year.max()+1):
    tbl.loc[tbl.Year>=yy]
    x=tbl.loc[tbl.Year<yy,tbl.columns[[3,4,5,6,7,8,9]].values].astype(int).sum().to_dict()
    x['Year']=yy
    timeline.append(x)
    
timeline = pd.DataFrame(timeline)
timeline.set_index('Year')
    
timeline.insert(6,'Dynamic',timeline[['Past',  'Present',  'Future']].sum(axis=1))

timeline.set_index('Year',inplace=True)


t1=timeline[['Past',  'Present',  'Future']].apply(lambda row: row / row.sum(), axis=1).fillna('0',inplace=True)
t2=timeline[['Static',  'Dynamic']].apply(lambda row: row / row.sum(), axis=1).fillna('0',inplace=True)
t3=timeline[['Analytical',  'Simulation',  'Data']].apply(lambda row: row / row.sum(), axis=1)

t4 = pd.concat([timeline[['Past',  'Present',  'Future', 'Static']].apply(lambda row: row / row.sum(), axis=1)[['Past',  'Present',  'Future']],timeline[['Static',  'Dynamic']].apply(lambda row: row / row.sum(), axis=1)['Static']],axis=1)

ax1=t4.plot()
ax1.set_xlim(1995, 2022)
ax1.set_ylim(-0.005, 1.005)
ax1.set_xlabel('Year')
ax1.set_ylabel('Cumulative fraction')
ax1.grid(True)
plt.savefig('LitRevBN1.pdf')
plt.show()

ax2=t3.plot()
ax2.set_xlim(1995, 2022)
ax2.set_ylim(-0.005, 1.005)
ax2.set_xlabel('Year')
ax2.set_ylabel('Cumulative fraction')
ax2.grid(True)
plt.savefig('LitRevBN2.pdf')
plt.show()

'''
fig, axes = plt.subplots(2, 1, sharex=True, figsize=(6,8))
axes[0].set_xlim(1995, 2022)
axes[0].set_ylim(-0.005, 1.005)
axes[0].set_ylabel('Cumulative fraction')
axes[1].set_xlim(1995, 2022)
axes[1].set_ylim(-0.005, 1.005)
axes[1].set_ylabel('Cumulative fraction')
axes[1].set_xlabel('Year')
t4.plot(ax=axes[0])
t3.plot(ax=axes[1])
'''

# %% over time 2

tbl=pd.read_excel('C:\\Users\\Lorenzo\\Desktop\\bn.xlsx', sheet_name=1)
tbl.fillna('0',inplace=True)


timeline = []
for yy1, yy2 in zip(range(1985,2025,5),range(1990,2030,5)):
    x=tbl.loc[(tbl.Year>=yy1) & (tbl.Year<yy2),tbl.columns[[3,4,5,6,7,8,9]].values].astype(int).sum().to_dict()
    x['Year']=str(yy1)+' - '+str(yy2)
    timeline.append(x)
    
timeline = pd.DataFrame(timeline)
timeline.set_index('Year')
    
timeline.insert(6,'Dynamic',timeline[['Past',  'Present',  'Future']].sum(axis=1))

timeline.set_index('Year',inplace=True)

timeline[['Analytical',  'Data' , 'Simulation']]