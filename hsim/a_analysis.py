# -*- coding: utf-8 -*-
"""
Created on Thu Jun  1 10:16:31 2023

@author: Lorenzo
"""

import dill
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

filename = 'resBN_pers2'
# filename = 'resBN_batched_prove_newLPT'

with open(filename, 'rb') as file:
    perf = dill.load(file)

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

# exps.to_excel('C:/Users/Lorenzo/Desktop/bn_results.xlsx')



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
plt.figure(figsize=(12, 6))
sns.catplot(data=data, x='DR', y='Average throughput', hue='OR', col='BN', kind='box', palette='Set1', height=4, aspect=0.8)
plt.suptitle('Average Throughput by BN, OR, and DR', y=1.05)
plt.xlabel('BN')
plt.ylabel('Average Throughput')
plt.tight_layout()
plt.show()


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
data['Group'] = data['BN'].astype(str) + '_' + data['OR'].astype(str) + '_' + data['DR'].astype(str)

# Perform pairwise comparisons using t-tests with common random numbers
pairwise_comp = pg.pairwise_tests(data=data, dv='Average throughput', within='Group', subject='seed',parametric=True,padjust='bonf')

pairwise_comp = pg.pairwise_tests(data=data, dv='Average throughput', within='Group', subject='seed',parametric=False,padjust='bonf',effsize='CLES')

# Print the pairwise comparison results
print(pairwise_comp)

# %%

import pandas as pd
import numpy as np
from scipy.stats import ttest_rel, t

# Assuming you have a DataFrame called 'data' with columns 'BN', 'OR', 'DR', and 'Value'

# Perform pairwise t-tests and compute confidence intervals
combinations = data[['BN', 'OR', 'DR']].apply(lambda x: '_'.join(x.astype(str)), axis=1).unique()
n_combinations = len(combinations)
alpha = 0.05  # Significance level
conf_ints = []

for i in range(n_combinations - 1):
    for j in range(i + 1, n_combinations):
        combination1 = combinations[i]
        combination2 = combinations[j]
        group1 = data[data[['BN', 'OR', 'DR']].apply(lambda x: '_'.join(x.astype(str)), axis=1) == combination1]['Average throughput']
        group2 = data[data[['BN', 'OR', 'DR']].apply(lambda x: '_'.join(x.astype(str)), axis=1) == combination2]['Average throughput']
        
        # Perform t-test
        t_stat, p_val = ttest_rel(group1, group2)
        
        # Compute standard error of the mean difference
        n1, n2 = len(group1), len(group2)
        std1, std2 = group1.std(), group2.std()
        se = np.sqrt((std1**2/n1) + (std2**2/n2))
        
        # Compute confidence interval
        dof = n1 + n2 - 2  # Degrees of freedom
        crit_val = t.ppf(1 - alpha/2, dof)  # Critical value
        mean_diff = group2.mean() - group1.mean()  # Mean difference
        lower_bound = mean_diff - crit_val * se
        upper_bound = mean_diff + crit_val * se
        
        # Append confidence interval to the list
        conf_ints.append((combination1, combination2, lower_bound, upper_bound))

# Print the confidence intervals
for conf_int in conf_ints:
    combination1, combination2, lower_bound, upper_bound = conf_int
    print(f"Comparison: {combination1} vs {combination2}")
    print(f"Confidence Interval: [{lower_bound}, {upper_bound}]")
    print()


# %%

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


# %% confidence intervals
import matplotlib.pyplot as plt
import numpy as np

# Assuming you have a list of tuples called 'conf_ints'

# Extract the group names and confidence interval values
groups = [pair[0] + ' vs ' + pair[1] for pair in conf_ints]
ci_lower = [pair[2] for pair in conf_ints]
ci_upper = [pair[3] for pair in conf_ints]

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

# %% seeds 1

drop_LPT =True
if drop_LPT:
    data=data.loc[data.DR != 'LPT']
    print('LPT dropped')
    
import matplotlib.pyplot as plt
import numpy as np

# Group the data by seed values
grouped_data = data.groupby('seed')

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

th=5
means=mean_diffs.sum(axis=1)
indexes=np.argsort(means)
seeds=seeds[indexes]

seeds[means>th]

