# -*- coding: utf-8 -*-
"""
Created on Thu Jun  1 10:16:31 2023

@author: Lorenzo
"""

from sys import path
path.append('../')

import dill
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


filename = 'resBN_pers5_100'
# filename = 'resBN_batched_prove_newLPT'

with open(filename, 'rb') as file:
    perf = dill.load(file)
    
def group_sort(arr):
    # Define the keys for sorting
    none_present_future = np.array([0 if 'none' in s else 1 if 'present' in s else 2 for s in arr])
    conwip_dbr = np.array([0 if 'CONWIP' in s else 1 for s in arr])
    fifo_sptbn_lpt2bn = np.array([0 if 'FIFO' in s else 1 if 'SPTBN' in s else 2 for s in arr])
    # Sort the array based on the keys
    sorted_indices = np.lexsort((fifo_sptbn_lpt2bn, conwip_dbr, none_present_future))
    return sorted_indices

# %% data
# exps = pd.read_excel('C:/Users/Lorenzo/Desktop/bn experiments.xlsx')
data = pd.DataFrame()

data['BN'] = [p.BN for p in perf]
data['OR'] = [p.OR for p in perf]
data['DR'] = [p.DR for p in perf]
data['seed'] = [p.seed for p in perf]


data['WIP'] = [p.avgWIP for p in perf]
# exps['prod'] = [p.production for p in perf]
data['Average throughput'] = [p.productivity.values[1][0] for p in perf]
data['prodCI'] = [p.productivity.values[1][0] for p in perf]
data['std'] = [pd.DataFrame(p.arrivals).diff().dropna().std()[0] for p in perf]
data['BNmean'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).mean() for p in perf]
data['BNstd'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).std() for p in perf]
data['BNskew'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).skew() for p in perf]
data['BNkurtosis'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).kurtosis() for p in perf]
data['BNlist'] = [(pd.DataFrame([bn[1][0] for bn in p.BNlist]).value_counts()/len(p.BNlist)).to_dict() for p in perf]

data.DR.replace('LPT','LPT2BN',inplace=True)
data.DR.replace('SPT','SPTBN',inplace=True)
# exps.to_excel('C:/Users/Lorenzo/Desktop/bn_results.xlsx')

# %% validate exp num
data['Group'] = data['BN'].astype(str) + ' ' + data['OR'].astype(str) + ' ' + data['DR'].astype(str)
df = data.pivot_table(values='Average throughput', index='Group',columns='seed')
var_a = dict()
mean_a = dict()
for col in df.columns:
    var_a[col] = []
    mean_a[col] = []
    for i in range(len(df[col])):
        var_a[col].append(np.var(df[col][:i]))
        mean_a[col].append(np.mean(df[col][:i]))

# %% facet
import seaborn as sns
import matplotlib.pyplot as plt

# Assuming your data is stored in a pandas DataFrame called 'data'
# with columns for 'BN', 'OR', 'DR', and 'Average throughput'

# Creating separate pairplots for each combination of DR and OR
g = sns.FacetGrid(data=data, col='DR', row='OR', hue='BN', palette='Set1')
g.map(sns.kdeplot, 'Average throughput', shade=True, alpha=0.5)
# g.map(sns.scatterplot, 'Average throughput', 'Average throughput')
g.add_legend(title='BN')
plt.show()


# %% cat

import seaborn as sns
import matplotlib.pyplot as plt

# Assuming your data is stored in a pandas DataFrame called 'data'
# with columns for 'BN', 'OR', 'DR', and 'Average throughput'

# Creating a boxplot to compare all three factors
plt.figure(figsize=(12, 8))
ax = sns.catplot(data=data, x='DR', y='Average throughput', hue='OR', col='BN', kind='box', palette='Set1', height=4, aspect=0.8)
sns.move_legend(ax, "center right", bbox_to_anchor=(1, 0.925))
plt.suptitle('Average Throughput by BN, OR, and DR', y=1.05)
plt.xlabel('BN')
plt.ylabel('Average Throughput')
plt.tight_layout()
plt.show()

# %% descriptive table
from scipy import stats

data['Group'] = data['BN'].astype(str) + ' ' + data['OR'].astype(str) + ' ' + data['DR'].astype(str)
df = data.pivot_table(values='Average throughput', index='Group', aggfunc=[np.mean,np.std])
df=df.iloc[group_sort(df.index)]
df['N'] = 100
df['alpha']=0.95
df['ci-']=None
df['ci+']=None


df2=data.pivot_table(values='Average throughput', index='Group',columns='seed').transpose()
for col in df2.columns:
    ci = stats.t.interval(alpha=0.95, df=len(df2[col])-1, loc=np.mean(df2[col]), scale=stats.sem(df2[col]))
    df.loc[df.index==col,'ci-'],df.loc[df.index==col,'ci+'] = ci[0],ci[1]
df=df.round(2)
df['ci-']=df['ci-'].astype('float').round(2)
df['ci+']=df['ci+'].astype('float').round(2)

df['ci'] = '('+df['ci-'].astype('str')+', '+df['ci+'].astype('str')+')'
df.drop(columns=['ci+','ci-'],inplace=True)

df_toexp=df.values

# %% ci plots
from scipy import stats

data['Group'] = data['BN'].astype(str) + ' ' + data['OR'].astype(str) + ' ' + data['DR'].astype(str)
df = data.pivot_table(values='Average throughput', index='Group', aggfunc=[np.mean,np.std])
df=df.iloc[group_sort(df.index)]
sns.set_style("whitegrid")

ax = sns.pointplot(data=data, y="Group", x="Average throughput",errorbar=("ci", 95), errwidth=0.5,capsize=.5, join=False, color="blue",order=df.index,markers='.')


# df = data.pivot_table(values='Average throughput', index='Group', columns='seed').transpose()
# df = data.pivot_table(values='Average throughput', index='Group', aggfunc=[np.mean,np.std]).transpose()
# ci=df.apply(lambda x: (x[0]-1.985*x[1]/(150)**0.5,x[0]+1.985*x[1]/(150)**0.5), axis=0)
# import matplotlib.pyplot as plt
# import numpy as np

# Assuming you have multiple groups of data and their corresponding averages and confidence intervals

# Group names
# groups = df.columns

# Average values

# Confidence intervals (lower and upper bounds)

# Generate the x-axis values
# x = np.arange(len(groups))

# Plot the average values with error bars representing the confidence intervals
# plt.errorbar(x, df.iloc[0].values, yerr=ci.values, fmt='o')#, capsize=5)

# Set the x-axis tick labels
# plt.xticks(x, groups)

# Add labels and title
from matplotlib.ticker import MultipleLocator
ax.tick_params(axis='x', which='minor')
# ax.tick_params(axis='x', which='minor', bottom=False)
ax.xaxis.set_major_formatter('{x:.0f}')
ax.xaxis.set_minor_locator(MultipleLocator(5))
ax.set(title='Average throughput with 95% Confidence Intervals')
plt.show()
# plt.xticks(x, groups, rotation=90)
# plt.subplots_adjust(bottom=0.2)
# Show the plot
# plt.show()


# %%  ANOVA
import statsmodels.api as sm
from statsmodels.formula.api import ols
import seaborn as sns
import matplotlib.pyplot as plt

# Assuming your data is stored in a pandas DataFrame called 'data'
# with columns for 'BN', 'OR', 'DR', and 'Average throughput'

# Performing ANOVA
formula = 'Q("Average throughput") ~ C(BN) + C(OR) + C(DR) + C(BN):C(OR) + C(BN):C(DR) + C(OR):C(DR) + C(BN):C(OR):C(DR)'
model = ols(formula, data=data).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print(anova_table)

# %% interactions

plt.figure(figsize=(10, 6))
sns.pointplot(data=data, x='BN', y='Average throughput', hue='DR', ci='sd', palette='Set1')
plt.title('Interaction Plot: BN, OR, and DR')
plt.xlabel('BN')
plt.ylabel('Average Throughput')
plt.legend(title='DR', loc='best')
plt.show()

# %% pairwise

import pandas as pd
import pingouin as pg

# Assuming your data is stored in a pandas DataFrame called 'data'
# with columns for 'BN', 'OR', 'DR', 'Average throughput', and 'Seed'

# Create a new column for unique group identifiers
data['Group'] = data['BN'].astype(str) + ' ' + data['OR'].astype(str) + ' ' + data['DR'].astype(str)

# Perform pairwise comparisons using t-tests with common random numbers
# pairwise_comp = pg.pairwise_tests(data=data, dv='Average throughput', within='Group', subject='seed',parametric=True,padjust='bonf',effsize='CLES')

pairwise_comp = pg.pairwise_tests(data=data, dv='Average throughput', within='Group', subject='seed',parametric=False,padjust='bonf',effsize='CLES')

# Print the pairwise comparison results
print(pairwise_comp)

words_A = pairwise_comp['A'].str.split().str[1:3]
words_B = pairwise_comp['B'].str.split().str[1:3]
pairwise_reduced=pairwise_comp.loc[words_A.eq(words_B)]
pairwise_reduced=pairwise_reduced.iloc[group_sort(pairwise_reduced.A)]

pairwise_reduced['OR']=[i[1] for i in pairwise_reduced.A.str.split()]
pairwise_reduced['DR']=[i[2] for i in pairwise_reduced.A.str.split()]
pairwise_reduced['Group 1']=[i[0] for i in pairwise_reduced.A.str.split()]
pairwise_reduced['Group 2']=[i[0] for i in pairwise_reduced.B.str.split()]
pairwise_reduced.round(3)


# %% calc confidence intervals

import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, t

# Assuming you have a DataFrame called 'data' with columns 'BN', 'OR', 'DR', and 'Value'

# Perform pairwise t-tests and compute confidence intervals
combinations = data[['BN', 'OR', 'DR']].apply(lambda x: ' '.join(x.astype(str)), axis=1).unique()
combinations=list(reversed(combinations))
n_combinations = len(combinations)
alpha = 0.05  # Significance level
conf_ints = []

for i in range(n_combinations - 1):
    for j in range(i + 1, n_combinations):
        combination1 = combinations[i]
        combination2 = combinations[j]
        group1 = data[data[['BN', 'OR', 'DR']].apply(lambda x: ' '.join(x.astype(str)), axis=1) == combination1]['Average throughput']
        group2 = data[data[['BN', 'OR', 'DR']].apply(lambda x: ' '.join(x.astype(str)), axis=1) == combination2]['Average throughput']
        
        # Perform t-test
        t_stat, p_val = ttest_rel(group1, group2)
        
        # Compute standard error of the mean difference
        # n1, n2 = len(group1), len(group2)
        # std1, std2 = group1.std(), group2.std()
        # se = np.sqrt((std1**2/n1) + (std2**2/n2))
        differences = group1.values - group2.values
        n = len(differences)
        std_diff = differences.std()
        se = std_diff / np.sqrt(n)
        
        # Compute confidence interval
        dof = n - 1  # Degrees of freedom
        # dof = n1 + n2 - 2  # Degrees of freedom
        crit_val = t.ppf(1 - alpha/2, dof)  # Critical value
        # mean_diff = group2.mean() - group1.mean()  # Mean difference
        mean_diff = differences.mean()
        lower_bound = mean_diff - crit_val * se
        upper_bound = mean_diff + crit_val * se
        
        # Append confidence interval to the list
        conf_ints.append((combination1, combination2, mean_diff, dof, alpha, se, t_stat, crit_val, p_val, lower_bound, upper_bound))

# Print the confidence intervals
for conf_int in conf_ints:
    combination1, combination2, lower_bound, upper_bound = conf_int[:4]
    print(f"Comparison: {combination1} vs {combination2}")
    print(f"Confidence Interval: [{lower_bound}, {upper_bound}]")
    print()

reduced_pairs=[pair for pair in conf_ints if pair[0].split()[1]==pair[1].split()[1] and pair[0].split()[2]==pair[1].split()[2]]

pairs_df=pd.DataFrame(reduced_pairs,columns=['A','B','mean_diff','dof', 'alpha', 'SE', 't_stat', 't_ref', 'p_val', 'lower_bound', 'upper_bound'])
pairs_df_unrounded=pairs_df.copy(deep=True)
pairs_df=pairs_df.round(3)


pairs_df['ci']=[(i,j) for i,j in pairs_df[['lower_bound','upper_bound']].values]

pairs_df['OR']=[i[1] for i in pairs_df.A.str.split()]
pairs_df['DR']=[i[2] for i in pairs_df.A.str.split()]
pairs_df['Group 1']=[i[0] for i in pairs_df.A.str.split()]
pairs_df['Group 2']=[i[0] for i in pairs_df.B.str.split()]

# %% inutile
pairs_df=pd.DataFrame(reduced_pairs,columns=['A','B','d','u'])

merged_df = pd.merge(pairwise_reduced, pairs_df, on=['A', 'B'], how='left')

pairs_df.rename(columns={'A':'B','B':'A'},inplace=True)
# merged_df.dropna(inplace=True)
merged_df = pd.merge(merged_df, pairs_df, on=['A', 'B'], how='left')
merged_df['d_x'].fillna(merged_df['d_y'],inplace=True)
merged_df['u_x'].fillna(merged_df['u_y'],inplace=True)
merged_df.rename(columns={'d_x':'d','u_x':'u'},inplace=True)
merged_df.drop(columns=['d_y','u_y'],inplace=True)
merged_df['mean']=merged_df[['d','u']].mean(axis=1).round(3).astype(str)
merged_df['ci']=[(round(i,3),round(j,3)) for i,j in merged_df[['d','u']].values]
merged_df=merged_df.iloc[group_sort(merged_df.A)]

# %% inutile

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Assuming you have a DataFrame called 'data' with columns 'Group', 'Value'

# Pivot the data to create a matrix of pairwise comparisons
comparison_matrix = data.pivot_table(values='Average throughput', index='Group', columns='seed')

# Plot the matrix as a heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(comparison_matrix, cmap='coolwarm', annot=True, fmt='.2f', cbar=True)
plt.title('Pairwise Comparisons')
plt.xlabel('Seed')
plt.ylabel('Group')
plt.show()


# %% plot confidence intervals
import matplotlib.pyplot as plt
import numpy as np

# Assuming you have a list of tuples called 'conf_ints'

# Extract the group names and confidence interval values
groups = [pair[0] + ' vs ' + pair[1] for pair in conf_ints]
ci_lower = [pair[-2] for pair in conf_ints]
ci_upper = [pair[-1] for pair in conf_ints]

# Generate the x-axis values
x = np.arange(len(groups))

# Plot the confidence intervals
plt.errorbar(x, np.zeros_like(x), yerr=[ci_lower, ci_upper], fmt='o')

# Set the x-axis tick labels
plt.xticks(x, groups, rotation=90)

# Add labels and title
plt.xlabel('Pairwise Comparisons')
plt.ylabel('Mean Difference')
plt.title('Pairwise Comparisons with Confidence Intervals')

# Show the plot
plt.show()


# %% plot paired confidence intervals
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Assuming you have a list of tuples called 'conf_ints'
# and a list of values called 'line_values'

# Extract the group names and confidence interval values
# groups = [pair[0] + ' vs ' + pair[1] for pair in reduced_pairs]
groups = [el1+' vs '+el2 for el1,el2 in zip(pairs_df['A'],pairs_df['B'])]
groups =list(reversed(groups))
# ci_lower = [pair[-2] for pair in reduced_pairs]
ci_lower = pairs_df['lower_bound'].values
# ci_upper = [pair[-1] for pair in reduced_pairs]
ci_upper = pairs_df['upper_bound'].values


# line_values = [pair[2] for pair in reduced_pairs]
line_values = pairs_df['mean_diff'].values

# Generate the x-axis values
x = np.arange(len(groups))

# Set the color palette to Seaborn color palette set 1
sns.set_palette("Set1")

# Create a colormap for the line colors
cmap = plt.cm.RdYlBu

# Normalize the line values to range between 0 and 1
line_norm = plt.Normalize(min(line_values), max(line_values))

# Plot the confidence intervals using horizontal bars
plt.figure(figsize=(10, len(groups)*0.8))

# Plot the bars for the confidence intervals
for i in range(len(groups)):
    plt.barh(x[i], ci_upper[i] - ci_lower[i], left=ci_lower[i], height=0.4, color='lightblue')

# Update the color of each bar based on line_values
for i, val in enumerate(line_values):
    color = cmap(line_norm(val))
    plt.barh(x[i], ci_upper[i] - ci_lower[i], left=ci_lower[i], height=0.4, color=color)

# Plot a line at x=0 to visualize if zero is included within the confidence intervals
plt.axvline(x=0, color='black', linestyle='--')

# Add labels and title
plt.xlabel('Mean Difference for TH')
plt.ylabel('Pairwise Comparisons')
plt.title('Pairwise Comparisons with Confidence Intervals')

# Set the y-axis ticks and tick labels
plt.yticks(x, groups)

# Set the x-axis limits to accommodate the confidence intervals
plt.xlim(min(ci_lower), max(ci_upper))

# Add a grid
plt.grid(axis='x', linestyle='--')
plt.grid(axis='y', linestyle='--')

# Remove the top and bottom spines
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['bottom'].set_visible(False)

# Remove the y-axis ticks and labels
plt.gca().yaxis.set_ticks_position('none')

# plt.tight_layout()
# plt.ylim(x[0]-0.5, x[-1]+0.5)
# Show the plot
plt.show()

# %% heatmap CLES

import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# Assuming your DataFrame is called 'df' with columns 'x_index', 'y_index', and 'value'
# Pivot the DataFrame to create a matrix-like structure for the heatmap
heatmap_data = pairwise_comp.pivot(index='A', columns='B', values='CLES')

# Define the custom colormap from blue to red to blue
colors = [(0, 0, 1), (1, 0, 0), (0, 0, 1)]
cmap = mcolors.LinearSegmentedColormap.from_list('CustomMap', colors)

# Create the heatmap using seaborn
ax = sns.heatmap(heatmap_data, cmap=cmap, vmin=0, vmax=1)

# Set the colorbar limits and label
cbar = ax.collections[0].colorbar
cbar.set_ticks([0, 0.5, 1])
cbar.set_ticklabels(['0', '0.5', '1'])
cbar.set_label('Value')

# Set the title and axis labels
plt.title('Heatmap')
plt.xlabel('X Index')
plt.ylabel('Y Index')
plt.tight_layout()

# Show the heatmap
plt.show()

#%% heatmap avg
pairs_df_all=pd.DataFrame(conf_ints,columns=['A','B','mean_diff','dof', 'alpha', 'SE', 't_ref','t_stat', 'p_val', 'lower_bound', 'upper_bound'])
pairs_df_all.loc[pairs_df_all.mean_diff<0,['mean_diff','A','B']] = pairs_df_all.loc[pairs_df_all.mean_diff<0,['mean_diff','B','A']]
pairs_df_all.loc[pairs_df_all.mean_diff<0,'mean_diff'] = -pairs_df_all.loc[pairs_df_all.mean_diff<0,'mean_diff']


df = pairs_df_all[['A','B','mean_diff']]
new = []
for i in range(len(df)):
    A,B,diff=df.iloc[i][['A','B','mean_diff']].values
    if len(df.loc[(df.A==B) & (df.B==A)])==0:
        data = {'A': B, 'B': A, 'mean_diff': -diff}
        df = pd.concat([df,pd.DataFrame(data,columns=['A','B','mean_diff'],index=[0])])
    if len(df.loc[(df.A==A) & (df.B==A)])==0:
        data = {'A': A, 'B': A, 'mean_diff': 0}
        df = pd.concat([df,pd.DataFrame(data,columns=['A','B','mean_diff'],index=[0])])


zero = 'none CONWIP FIFO'
data = {'A': zero, 'B': zero, 'mean_diff': 0}
df = pd.concat([df,pd.DataFrame(data,columns=['A','B','mean_diff'],index=[0])])

heatmap_data = df.pivot(index='A', columns='B', values='mean_diff')
heatmap_data=heatmap_data.iloc[group_sort(heatmap_data.index)]
heatmap_data=heatmap_data[heatmap_data.columns[group_sort(heatmap_data.columns)]]


ax = sns.heatmap(heatmap_data,center=0,cmap='RdYlBu')
plt.title('Heatmap for TH differences')




# %% seeds 1

drop_LPT =True
if drop_LPT:
    data2=data.loc[data.DR != 'LPT']
    print('LPT dropped')
else:
    data2 = data
    
import matplotlib.pyplot as plt
import numpy as np

# Group the data by seed values
grouped_data = data2.groupby('seed')

# Initialize lists to store the mean differences and seed values
mean_diffs = []
seeds = []

# Iterate over each group
for group_name, group_data in grouped_data:

    # Calculate the mean differences between BN levels
    mean_diff_high_low = group_data.loc[group_data['BN'] == 'future', 'Average throughput'].mean() - group_data.loc[group_data['BN'] == 'none', 'Average throughput'].mean()
    mean_diff_high_med = group_data.loc[group_data['BN'] == 'future', 'Average throughput'].mean() - group_data.loc[group_data['BN'] == 'present', 'Average throughput'].mean()
    mean_diff_med_low = group_data.loc[group_data['BN'] == 'present', 'Average throughput'].mean() - group_data.loc[group_data['BN'] == 'none', 'Average throughput'].mean()
    
    # Append the mean differences and seed value to the lists
    mean_diffs.append([mean_diff_high_low, mean_diff_high_med, mean_diff_med_low])
    seeds.append(group_name)

# Convert the lists to numpy arrays
mean_diffs = np.array(mean_diffs)
seeds = np.array(seeds)

sorted_index = np.lexsort(mean_diffs.T[: : -1])
mean_diffs = mean_diffs[sorted_index]
seeds=seeds[sorted_index]

# Get the number of BN levels
num_bn_levels = mean_diffs.shape[1]

# Create an array of indices for the bar positions
indices = np.arange(len(seeds))

# Plot the grouped bar plot
width = 0.2  # Width of each bar
colors = ['steelblue', 'darkorange', 'limegreen']  # Colors for each BN level

BNlevels = ['future-none','future-present','present-none']
fig, ax = plt.subplots(figsize=(30, 18))
for i in range(num_bn_levels):
    ax.bar(indices + i * width, mean_diffs[:, i], width=width, color=colors[i], edgecolor='black', label=BNlevels[i])

# Add labels and title
plt.xlabel('Seed Value')
plt.ylabel('Mean Difference')
plt.title('Mean Differences between BN Levels for Seed Values')

# Set the x-axis tick positions and labels
ax.set_xticks(indices + (num_bn_levels - 1) * width / 2)
ax.set_xticklabels(seeds)

# Add a legend
ax.legend()

# Show the plot
# plt.tight_layout()
plt.show()


# %% seeds 2

th=16

mean_diffs=np.vstack([mean_diffs[:,0],mean_diffs[:,1]*4,mean_diffs[:,2]]).T

means=mean_diffs.sum(axis=1)
indexes=np.argsort(means)
seeds=seeds[indexes]

seeds[means>th]
print(len(seeds[means>th]))
