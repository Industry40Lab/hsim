import pandas as pd
from statistics import mean
import numpy as np
import kuka_analysis as kuka
from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt
import matplotlib

mn = list()
lsegm = list()
segm=list()
import csv

def file_len(filename):
    with open(filename) as f:
        for i, l in enumerate(f):
            pass
    return i + 1



# read param files
#param = pd.DataFrame()
list_of_names=list()
df_list = []
for i in range(10):
    m = list()
    num_param = i + 1
    filename = 'param' + str(num_param) + ".csv"
    a=file_len(filename)
    segm.append(a)
    temp_df = pd.read_csv(filename, delimiter=';')
    data=temp_df[['lenght','mean','start','end']]
    df_list.append(data)

fields = ['lenght', 'mean', 'start', 'end']
with open("output.csv", 'w', newline='\n') as f:
    write = csv.writer(f, delimiter=';')
    write.writerow(fields)


S=list()
s=0
sum = list()
for j in range(4):
    #if j not in range(10):
        #df_list[i]["lenght"][j]==0
    #else:
        for i in range(len(df_list)):
            s=s+df_list[i]["lenght"][j]
        avg=s/4
        sum.append(avg)
        s = 0

S.append(sum)



s1=0
sum1=list()
for j in range(4):
    for i in range(len(df_list)):
        s1=s1+df_list[i]["mean"][j]
    avg=s1/4
    sum1.append(avg)
    s1 = 0
S.append(sum1)



s2=0
sum2=list()
for j in range(4):
    for i in range(len(df_list)):
        s2=0
        s2=s2+df_list[i]["start"][j]
    avg=s2/4
    sum2.append(avg)

S.append(sum2)



s3=0
sum3=list()
for j in range(4):

    for i in range(len(df_list)):
        s3 = 0
        s3=s3+df_list[i]["end"][j]
    avg = s3 / 4
    sum3.append(avg)
S.append(sum3)
print(S)


with open("output.csv", 'w', newline='\n') as f:
    write = csv.writer(f, delimiter=';')
    write.writerows(S)
#x=pd.read_csv("output.csv", delimiter=';')
#dist=kuka.KernelDensityEstimationG(X)

X=np.array(S)
X_plot = np.linspace(-1, 1, 10)[:, np.newaxis]


fig, ax = plt.subplots()



kde = KernelDensity(kernel='gaussian', bandwidth=0.2).fit(X)

log_dens = kde.score_samples(X)




"""print(segm)
avg=mean([a])
print(avg)
print(df_list[0]["lenght"][0])"""


"""S=list()
s=0
sum=list()
for df in df_list: #for i in range(10) number of files
    for col in df: #for i in range(4) number of columns
        for j in range(8): #min number of rows
            s=s+df[col][j]
            print('s=',s)
        sum.append(s)
        print('sum',sum)
        s = 0
S.append(sum)

print('S',S)"""


