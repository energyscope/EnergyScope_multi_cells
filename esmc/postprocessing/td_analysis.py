# -*- coding: utf-8 -*-
"""
This script contains useful function to analyze the impact of Typical Days (TDs)
on the time series and the energy system results

@author: Paolo Thiran
"""

import json
import math
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

from esmc.utils.esmc import Esmc


def init_my_model(t, case, regions_names, add_dir='221219_mdpi_energies'):
    """Initialize Esmc object and reads input data and temporal aggregation related data"""
    # read inputs data


    gwp_limit_overall = None
    re_share_primary = None
    f_perc = False

    # TODO Change this folder
    config = {'case_study': add_dir+'/'+str(t)+'TDs'+case,
              'comment': 'no comment',
              'regions_names': regions_names,
              'ref_region': 'FR',
              'gwp_limit_overall': gwp_limit_overall,
              're_share_primary': re_share_primary,
              'f_perc': f_perc,
              'year': 2035}
    # initialize EnergyScope Multi-cells framework
    my_model = Esmc(config, nbr_td=t)

    # initialize the different regions and reads their data
    my_model.init_regions()

    # Initialize and solve the temporal aggregation algorithm:
    # if already run, set algo='read' to read the solution of the clustering
    # else, set algo='kmedoid' to run k-medoid clustering algorithm to choose typical days (TDs)
    my_model.init_ta(algo='read')  # to have the weights

    return my_model


# FUNCTIONS RELATED TO A PRIORI ERRORS
def group_ts(my_model):
    """Group all the time series of the case study into 1 dataframe"""
    # regroup ts of all regions into 1 df
    ts_names = list(my_model.regions[my_model.regions_names[0]].data['Time_series'].columns)
    arrays = [my_model.regions_names, ts_names]
    all_ts = pd.DataFrame(0, index=np.arange(1, 8761),
                          columns=pd.MultiIndex.from_product(arrays, names=('Regions', 'Time series')))
    for r in my_model.regions_names:
        df = my_model.regions[r].data['Time_series'].copy()
        df.columns = pd.MultiIndex.from_product([[r], df.columns])
        df.columns.name = ('Regions', 'Time series')
        df.index.name = None
        all_ts.loc[:, (r, slice(None))] = df

    return all_ts


def compute_dc(ts):
    """Compute duration curve of each """
    dc = ts.copy().reset_index(drop=True)
    for col in dc:
        dc[col] = dc[col].sort_values(ascending=False, ignore_index=True)

    return dc


def read_kmedoid_tds(tds, my_model):
    """Read the kmedoid results for each td"""
    # read td_of_days
    td_of_days = pd.DataFrame(np.nan, index=np.arange(1, 366, 1), columns=tds)
    e_ts_kmedoid = pd.Series(np.nan, index=tds)
    dat_dir = my_model.dat_dir/'td_dat'

    for t in tds:
        step1_out = dat_dir/('TD_of_days_'+str(t)+'.out')
        df = pd.read_csv(step1_out, names=[t]).set_index([pd.Index(np.arange(1, 366, 1))])
        td_of_days.loc[:, t] = df

        e_ts_path = dat_dir/('e_ts'+str(t)+'.txt')
        e_ts_kmedoid.loc[t] = pd.read_csv(e_ts_path, header=None).loc[0, 0]

    return td_of_days, e_ts_kmedoid


def compute_ts_from_td(td_of_days, ts):
    """Compute the synthetic time series from typical days

    TO BE IMPROVED... too slow -> use the same methods as for ts_td in regions and from_td_to_year in temporal_aggregation"""
    ts_from_td = ts.copy()
    for day in range(365):
        td = td_of_days.loc[day + 1]
        ts_from_td.loc[day * 24 + 1:(day + 1) * 24, :] = ts.loc[(td - 1) * 24 + 1:td * 24, :].set_index(
            pd.Index(np.arange(day * 24 + 1, (day + 1) * 24 + 1)))
    # scaling the ts from td to keep the total amount over the year
    ts_from_td = ts_from_td * ts.sum() / ts_from_td.sum()

    return ts_from_td


def compute_all_ts_from_td(tds, td_of_days, all_ts):
    """Compute synthetic ts and dc from"""
    all_ts_from_td = dict()
    all_dc_from_td = dict()

    for t in tds:
        all_ts_from_td[t] = compute_ts_from_td(td_of_days.loc[:, t], all_ts)
        all_dc_from_td[t] = compute_dc(all_ts_from_td[t])

    return all_ts_from_td, all_dc_from_td


def abs_err(df1, df2):
    """Compute the L1 distance between the 2 dataframes"""
    return ((df1-df2).abs()).sum()


def abs_err_corr(all_ts, all_ts_from_td, w, regions_names):
    """


    Parameters
    ----------
    all_ts
    all_ts_from_td
    w
    regions_names

    Returns
    -------

    """

    # here shape of results
    e_corr = pd.Series(np.nan, index=regions_names + ['ALL'])
    # Intra-regional correlation error
    for r in regions_names:
        ts = all_ts.loc[:, (r, slice(None))]
        ts_from_td = all_ts_from_td.loc[:, (r, slice(None))]
        e_corr[r] = ((((ts.corr() - ts_from_td.corr()).abs())
                      .mul(w.loc[(r, slice(None))], axis=0).mul(w.loc[(r, slice(None))], axis=1).sum().sum()))
        # Overall correlation error
    e_corr['ALL'] = (((all_ts.corr() - all_ts_from_td.corr()).abs())
                     .mul(w, axis=0).mul(w, axis=1).sum().sum())
    return e_corr


def compute_ts_errors(all_ts, all_dc, all_ts_from_td, all_dc_from_td, w, regions_names):
    """Compute errors on time series (time series, duration curve and correlation)

    """
    # extract tds list
    tds = list(all_ts_from_td.keys())
    # initialize the df
    err_ts = pd.DataFrame(np.nan, index=all_ts.columns, columns=tds)
    err_dc = pd.DataFrame(np.nan, index=all_ts.columns, columns=tds)
    corr_index = [('err_corr_' + r) for r in regions_names + ['ALL']]
    error_corr = pd.DataFrame(np.nan, index=corr_index, columns=tds)

    # compute total over year
    tot_ts = all_ts.sum()
    for t in tds:
        # Compute time series and duration curve errors for each number of tds and for each time series
        err_ts.loc[:, t] = abs_err(all_ts / tot_ts, all_ts_from_td[t] / tot_ts)
        err_dc.loc[:, t] = abs_err(all_dc / tot_ts, all_dc_from_td[t] / tot_ts)
        # compute correlation error for each number of tds and all time series
        error_corr.loc[:, t] = abs_err_corr(all_ts, all_ts_from_td[t], w, regions_names).rename(
            lambda x: 'err_corr_' + x)

    # dataframe to summarise the errors
    all_error_ts = pd.DataFrame(np.nan, index=['err_ts', 'err_dc'] + corr_index, columns=tds)
    # pondered sum of time series
    all_error_ts.loc['err_ts', :] = err_ts.mul(w, axis=0).sum()
    all_error_ts.loc['err_dc', :] = err_dc.mul(w, axis=0).sum()
    # add correlation errors in the dataframe
    all_error_ts.loc[corr_index, :] = error_corr

    return all_error_ts


def a_priori_error(my_model, tds):
    """Computing a priori error"""
    # group ts and compute duration curve
    all_ts = group_ts(my_model)
    # compute dc
    all_dc = compute_dc(all_ts)
    # read kmedoid outputs
    td_of_days, e_ts_kmedoid = read_kmedoid_tds(tds, my_model)
    # compute synthetic time series for each typical days configuration
    # TODO TO BE IMPROVED... too slow
    all_ts_from_td, all_dc_from_td = compute_all_ts_from_td(tds, td_of_days, all_ts)
    # compute all errors
    weights = my_model.ta.weights['Weights_n'].copy()
    weights.index.set_names(['Regions', 'Time series'], inplace=True)
    all_ts_errors = compute_ts_errors(all_ts, all_dc, all_ts_from_td, all_dc_from_td, weights, my_model.regions_names)

    # drop regions correlation error
    all_ts_errors.drop(index=[('err_corr_' + r) for r in my_model.regions_names], inplace=True)
    all_ts_errors.rename(index={'err_corr_ALL': 'err_corr'}, inplace=True)

    return all_ts_errors


# FUNCTIONS RELATED TO A POSTERIORI ERRORS
def read_outputs_tds(cs_dir, case, tds, regions_names, el_names, save_out=False):
    """Read the relevant outputs for each td into tds and group them

    """
    outputs = dict()
    outputs['Time'] = pd.DataFrame(0, index=tds, columns=['Solving time [s]'])
    outputs['TotalCost'] = pd.DataFrame(0, index=pd.Index(regions_names, name='Regions'), columns=tds)
    outputs['C_el'] = pd.DataFrame(0, index=pd.MultiIndex.from_product([regions_names, el_names],
                                                                       names=('Regions', 'Elements')), columns=tds)
    outputs['C_el_share'] = outputs['C_el'].copy()

    for t in tds:
        my_dir = cs_dir / (str(t) + 'TDs' + case) / 'outputs'
        outputs['Time'].loc[t, 'Solving time [s]'] = pd.read_csv(my_dir / 'Solve_time.csv', sep='\t', header=None,
                                                                 index_col=0).sum().to_numpy()
        outputs['TotalCost'].loc[:, t] = pd.read_csv(my_dir / 'TotalCost.csv', sep=',', header=0, index_col=0)[
            'TotalCost']
        df = pd.read_csv(my_dir / 'Cost_breakdown.csv', sep=',', header=0, index_col=[0, 1])
        outputs['C_el'].loc[:, t] = df.sum(axis=1)

    # compute the share of each tech into the total cost
    outputs['C_el_share'] = outputs['C_el'].div(outputs['TotalCost'].sum(), axis=1)

    if save_out:
        for key, df in outputs.items():
            df.to_csv(cs_dir / (key + '.csv'), sep=',')

    return outputs


def compute_time_gain(other_times, ref_time, save_out=False, cs_dir=None):
    """Compute the time gained between each time in times and the reference time (ref_time)

    """
    time_gain = pd.Series(ref_time, index=other_times.index, name='Time factor')
    time_gain = time_gain / other_times['Solving time [s]']

    if save_out:
        time_gain.to_csv(cs_dir / 'time_factor.csv', sep=',')

    return time_gain


def drop_not_installed(c_el, c_el_share, thresh=0.00015):
    """Drops the elements not installed

    """
    # get list of not installed
    not_installed = list(c_el_share.loc[c_el_share.max(axis=1) < thresh, :].index)
    # put it into a dictionary with keys="tech not installed" and values="in which region"
    not_installed_dict = dict(list())
    for i, j in not_installed:
        if j in not_installed_dict.keys():
            not_installed_dict[j] = not_installed_dict[j] + [i]
        else:
            not_installed_dict[j] = [i]

    # drop not installed in both df
    c_el.drop(index=not_installed, inplace=True)
    c_el_share.drop(index=not_installed, inplace=True)

    return not_installed_dict


def drop_converging_to_0(c_el, c_el_share, ref_index, thresh=1e-2):
    """Drops the elements converging to 0"""
    # select tech converging to 0
    c_el_conv0 = c_el.loc[c_el.loc[:, ref_index] <= thresh, :]
    # drop those elements from c_el and c_el_share
    c_el.drop(index=c_el_conv0.index, inplace=True)
    c_el_share.drop(index=c_el_conv0.index, inplace=True)

    return c_el_conv0


def reldiff_ref(s, ref_index, thresh=1e-2):
    """Computes the relative difference in a series compared to the last element (ref)"""
    s2 = s.copy()
    ref = float(s2.loc[ref_index])
    if ref > thresh:
        s2 = s.map(lambda x: (x - ref) / ref)
    else:
        print('Warning ', s.name, ' converges at 0. Thus the series is unchanged')

    return s2


def compute_design_error(c_el_rel_t, c_el_share_t, thresh=0.05):
    """Compute the design error"""
    error_list = list(c_el_rel_t.loc[c_el_rel_t.abs() > thresh].index)
    de = c_el_share_t.loc[error_list].sum()

    return error_list, de


def compute_de_tds(c_el_rel, c_el_share, thresh=0.05):
    """Compute the design error for each td"""
    tds = list(c_el_rel.columns)
    de_s = pd.Series(np.nan, index=tds, name='de')
    error_lists = dict()
    for t in tds:
        error_lists[int(t)], de_s[t] = compute_design_error(c_el_rel.loc[:, t], c_el_share.loc[:, t], thresh=thresh)

    return de_s, error_lists


def a_posteriori_error(c_el, c_el_share, ref_index=365, thresh_not_installed=0.00015,
                       thresh_conv0=1e-2, thresh_de=0.05, save_out=False, cs_dir=None):
    """Wrapper function for the entire a posteriori error computation"""
    # check and drop not installed
    not_installed_dict = drop_not_installed(c_el, c_el_share, thresh=thresh_not_installed)
    # check and drop converging to 0
    c_el_conv0 = drop_converging_to_0(c_el, c_el_share, ref_index=ref_index, thresh=thresh_conv0)
    # compute relative error
    c_el_rel = c_el.apply(reldiff_ref, axis=1, args=(ref_index, thresh_conv0))
    # compute design error and error lists
    de_s, error_lists = compute_de_tds(c_el_rel, c_el_share, thresh=thresh_de)

    if save_out:
        with open(cs_dir / 'not_installed.json', mode='w') as fp:
            json.dump(not_installed_dict, fp, indent=4)
        c_el_conv0.to_csv(cs_dir / 'c_el_conv0.csv', sep=',')
        c_el_rel.to_csv(cs_dir / 'c_el_rel.csv', sep=',')
        de_s.to_csv(cs_dir / 'de.csv', sep=',')
        with open(cs_dir / 'error_lists.json', mode='w') as fp:
            json.dump(error_lists, fp, indent=4)

    return not_installed_dict, c_el_conv0, c_el_rel, de_s, error_lists


def smooth_de_min(de_s):
    """Smooth the design error
    by replacing each value by the minimum value with equal or lower number of typical days """
    # smoothing de_s
    de_min = de_s.copy()
    tds = list(de_s.index)
    for t in range(len(tds)):
        de_min.loc[tds[t]] = de_s.loc[tds[:t + 1]].min()

    return de_min


def smooth_de(de_s):
    """Smooth the design error
    by replacing each value by the maximum value with equal or higher number of typical days """
    # smoothing de_s
    de_max = de_s.copy()
    tds = list(de_s.index)
    for t in range(len(tds)):
        de_max.loc[tds[t]] = de_s.loc[tds[t:]].max()

    return de_max


def replace_outliers_de(de, win=5, thresh=0.5):
    """Return a copy of the design error with outliers replace by previous value"""
    tds = list(de.index)
    # compute moving average
    ma = de.rolling(window=win, center=True).mean()
    ma.iloc[:math.floor(win / 2)] = de.loc[tds[:math.floor(win / 2)]]
    ma.iloc[-math.floor(win / 2):] = de.loc[tds[-math.floor(win / 2):]]
    # sort out the values with a relative difference higher than thresh with moving average
    diff = ((de - ma) / ma).abs().fillna(value=0)
    de_filtered = pd.Series(np.nan, index=de.index)
    de_filtered[diff < thresh] = de[diff < thresh]
    # replace outliers by previous value
    de_filtered.fillna(method='ffill', inplace=True)

    return de_filtered


def fit_tse_de(tse, de, points=[2, 14, 365]):
    """Fit a linear regression on tse and de"""
    x = tse.loc[points].values.reshape((-1, 1))
    y = de.loc[points].values
    my_linreg = LinearRegression().fit(x, y)
    a = my_linreg.coef_[0]
    b = my_linreg.intercept_
    x_test = np.arange(0, tse.max(), 0.0001)
    y_test = x_test*a+b
    linreg_pred = pd.DataFrame([x_test, y_test], index=['tse', 'de']).transpose()
    return a, b, linreg_pred


def get_td_apriori(linreg_pred, tse, thresh=0.1):
    """Get the number of typical days to reach a certain threshold on the design error
    based on the linear relationship between time series error and design error and the a priori time series error"""
    if linreg_pred.tail(1).loc[:, 'de'].values > thresh:
        tse_pred = linreg_pred.loc[linreg_pred['de'] >= thresh].iloc[0, 0]
        n_td = tse.loc[tse <= tse_pred].index[0]
    else:
        n_td = 2
    return n_td


def select_td_on_de(x, tf, thresh=0.2):
    """Selects the number of TDs based on the design error and a threshold
    and returns the selected TD, DE and Time factor as a pandas series"""
    space_id = x.name
    # select td
    selected_td = x[x < thresh].reset_index().iloc[0]
    # rename index and series
    selected_td.name = space_id
    selected_td.rename({'index': 'Selected TD', space_id: 'Design error'}, inplace=True)
    # add time factor
    selected_td['Time factor'] = tf.loc[selected_td.loc['Selected TD']]
    return selected_td
