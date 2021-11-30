import numpy as np
import pandas as pd
import os
import json
from amplpy import AMPL, DataFrame

def get_vars(ampl):
    var = list()
    for name, values in ampl.getVariables():
        var.append(name)
    return var

def get_params(ampl):
    parameters = list()
    for n, p in ampl.getParameters():
        parameters.append(n)
    return parameters

def get_subset(my_set):
    d = dict()
    for n,o in my_set.instances():
        try:
            d[n] = o.getValues().toList()
        except:
            d[n] = list()
    return d

def get_sets(ampl):
    my_sets = dict()
    for name, obj in ampl.getSets():
        if len(obj.instances()) <= 1:
            my_sets[name] = obj.getValues().toList()
        else:
            my_sets[name] = get_subset(obj)
    return my_sets

def to_pd_pivot(amplpy_df):
    # function to transform an amplpy df into a pd df
    nindices = amplpy_df.getNumIndices()
    headers = amplpy_df.getHeaders()
    columns = {header: list(amplpy_df.getColumn(header)) for header in headers}
    df = pd.DataFrame(columns)

    if nindices == 1:
        df = df.set_index(headers[0])
        df.index.name = None  # get rid of the name of the index (multilevel)
    elif nindices == 2:
        df = df.pivot(index=headers[0], columns=headers[1], values=headers[2])
        df.index.name = None  # get rid of the name of the index (multilevel)
    elif nindices == 3:
        dic = dict()
        for i in set(columns[headers[0]]):
            dic[i] = df[df[headers[0]] == i].pivot(index=headers[2], columns=headers[1], values=headers[3])
            dic[i].index.name = None  # to get rid of name (multilevel)
        df = dic
    elif nindices == 4:
        dic = dict()
        for i in set(columns[headers[0]]):
            dic[i] = dict()
            for j in set(columns[headers[3]]):
                dic[i][int(j)] = df.loc[(df[headers[0]] == i) & (df[headers[3]] == j), :].pivot(index=headers[2],
                                                                                                columns=headers[1],
                                                                                                values=headers[4])
                dic[i][int(j)].index.name = None  # to get rid of name (multilevel)
        df = dic

    return df

def get_results_pivot(ampl):
    # function to get the results of ampl under the form of a dict filled with one df for each variable
    amplpy_sol = ampl.getVariables()
    results_pivot = dict()
    for name,var in amplpy_sol:
            results_pivot[name] = to_pd_pivot(var.getValues())
    return results_pivot

def to_pd(amplpy_df):
    # function to transform an amplpy df into a pd df
    nindices = amplpy_df.getNumIndices()
    headers = amplpy_df.getHeaders()
    columns = {header: list(amplpy_df.getColumn(header)) for header in headers}
    df = pd.DataFrame(columns)

    return df

def get_results(ampl):
    # function to get the results of ampl under the form of a dict filled with one df for each variable
    amplpy_sol = ampl.getVariables()
    results = dict()
    for name,var in amplpy_sol:
            results[name] = to_pd(var.getValues())
    return results

def get_thtd(ampl):
    return to_pd(ampl.getSet('T_H_TD').getValues())

def print_step1_out(ampl, step1_out):
    # printing .out file
    results_step1 = get_results(ampl)
    cm = results_step1['Cluster_matrix'].pivot(index='index0', columns='index1', values='Cluster_matrix.val')
    cm.index.name = None
    out = pd.DataFrame(cm.mul(np.arange(1, 366), axis=0).sum(axis=0)).astype(int)
    out.to_csv(step1_out, header=False, index=False, sep='\t')
    return

def print_case(dic, directory):
    # prints the dictionnary of pd.DataFrame() dic into the directory as one csv per DataFrame
    for key in dic:
        dic[key].to_csv(os.path.join(directory, key + '.csv'))
    return

def print_json(my_sets, file):    # printing the dictionnary containing all the sets into directory/sets.json
    with open(file, 'w') as fp:
        json.dump(my_sets, fp, indent=4, sort_keys=True)
    return

def read_json(file):
    # reading the saved dictionnary containing all the sets from directory/sets.json
    with open(file, 'r') as fp:
        data = json.load(fp)
    return data


def read_output(modelDirectory, case_study, var):
    d = dict()
    outDir = os.path.join(modelDirectory,'output_'+case_study+'TD')
    for v in var:
        d[v] =  pd.read_csv(os.path.join(outDir,v+'.csv'), index_col=0)
    return d

def read_T_H_TD(modelDirectory, case_study):
    inputsDir = os.path.join(modelDirectory,'output_'+case_study+'TD'+'/inputs')
    return pd.read_csv(os.path.join(inputsDir,'T_H_TD.csv'), index_col=0)