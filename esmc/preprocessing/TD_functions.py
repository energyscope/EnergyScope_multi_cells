# -*- coding: utf-8 -*-
"""
Created on Thu Aug 12 17:11:50 2021

@author: Paolo Thiran
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def compute_ts_from_td(TD_of_days, ts):
    ts_from_td = ts.copy()
    for day in range(365):
        td = TD_of_days.loc[day+1,'TD_of_days']
        ts_from_td.loc[day*24+1:(day+1)*24,:] = ts.loc[(td-1)*24+1:td*24,:].set_index(pd.Index(np.arange(day*24+1,(day+1)*24+1)))
    # scaling the ts from td to keep the total amount over the year
    ts_from_td = ts_from_td*ts.sum()/ts_from_td.sum()
    
    return ts_from_td


def compute_dc(ts):
    dc = ts.copy().reset_index(drop=True)
    for col in dc:
        dc[col] =  dc[col].sort_values(ascending=False, ignore_index=True)
    
    return dc

def compute_metrics(all_ts, all_ts_from_td, all_dc, all_dc_from_td, w, regions):
    metrics = pd.Series(dtype='object')
    
    tot_ts = all_ts.sum()
    Np = all_ts.shape[1]
    Nr = len(regions)
    
    # normalize ts
    all_ts = all_ts/tot_ts
    all_ts_from_td = all_ts_from_td/tot_ts
    all_dc = all_dc/tot_ts
    all_dc_from_td = all_dc_from_td/tot_ts
    
    # M1 Relative energy error
    metrics['e_ree'] = (w*((all_ts.sum()-all_ts_from_td.sum()).abs())).sum()/Np
    # M2 Clustering error or Time series error
    E_cl = (((w*((all_ts-all_ts_from_td).pow(2))).sum()).sum())**0.5
    E_cl_2 = (((w*((all_ts-all_ts_from_td).pow(2))).sum()).pow(0.5)).sum()
    E_cl_3 = (((w*((all_ts-all_ts_from_td).pow(2))).sum()).pow(1)).sum()
    E_cl_ref = (((w*((all_ts-all_ts.mean()).pow(2))).sum()).sum())**0.5
    e_cl = E_cl/E_cl_ref
    metrics['e_cl'] = E_cl_3#/Np

    # M3 Duration curve error
    E_dc = ((w*(((all_dc-all_dc_from_td).pow(2)).sum())).sum())**0.5
    E_dc_2 = ((w*((((all_dc-all_dc_from_td).pow(2)).sum()).pow(0.5))).sum())
    E_dc_ref = ((w*(((all_dc-all_dc.mean()).pow(2)).sum())).sum())**0.5
    e_dc = E_dc/E_dc_ref
    metrics['e_dc'] = E_dc_2/Np

    # M4 Variability error
    metrics['e_var'] = (((w*(((all_ts.var()-all_ts_from_td.var())/all_ts.var())
                             .pow(2))).sum())/Np)**0.5
    # M5 Intraregional correlation error
    e_corr = dict()
    for r in regions:
        ts = all_ts.loc[:,all_ts.columns.str.endswith(r)]
        ts_from_td = all_ts_from_td.loc[:,all_ts_from_td.columns.str.endswith(r)]
        e_corr[r] = ((((ts.corr()-ts_from_td.corr()).pow(2))
                      .mul(w,axis=0).mul(w,axis=1).sum().sum())/ts.shape[1])**0.5
    metrics['e_corr'] = sum(e_corr.values())
    # M6 Overall correlation error
    metrics['e_corr_all'] = ((((all_ts.corr()-all_ts_from_td.corr()).pow(2))
                              .mul(w,axis=0).mul(w,axis=1).sum().sum())/Np)**0.5
    
    return metrics