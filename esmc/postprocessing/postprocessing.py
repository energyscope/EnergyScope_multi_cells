import numpy as np
import pandas as pd
import csv

def get_var_cases(var_name, cases, all_results):
    df = all_results[cases[0]][var_name].copy().drop(columns=var_name+'.val')
    for c in cases:
        df[c] = all_results[c][var_name].loc[:,var_name+'.val']
    return df

def get_used(df, col):
    return df[df[col].sum(axis=1)>0]

def subgroup(df, col, q_up, q_down):
    tresh_up = df[col].quantile(q_up)
    tresh_down = df[col].quantile(q_down)
    return df.loc[(df[col]>tresh_down) & (df[col]<tresh_up),:]

def subgroup_on_max(df, q_up, q_down):
    max_df = df.max(axis=1)
    tresh_up = max_df.quantile(q_up)
    tresh_down = max_df.quantile(q_down)
    return df.loc[(df.max(axis=1)>tresh_down) & (df.max(axis=1)<tresh_up),:]

def compute_convergence(s):
    s2 = s.copy()
    l = list(s.index)
    s[l[0]] = 0
    for i in range(len(l)-1):
        if s[l[i+1]]>0:
            s2[l[i+1]] = (s[l[i+1]] - s[l[i]])/s[l[i]]
        else:
            s2[l[i+1]] = 0
    return s2