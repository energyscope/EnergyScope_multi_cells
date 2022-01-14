import numpy as np
import pandas as pd
import csv
import os
import shutil
from pathlib import Path
import logging
import git
from datetime import datetime

from amplpy import AMPL
from esmc.postprocessing import amplpy2pd as a2p
from esmc.utils import opti_probl as op


def step1_in(out_path, countries, data, N_ts=7, Nbr_TD=10):
    "step1_in reads the datas at the path of data and prints the Ndata param in Ndata.tsv and the list of timeseries used in this Ndata with their weights and norm"
    N_c = len(data)  # number of countries

    ## READ FIRST COUNTRY ##
    # reading the weights
    weights = pd.read_excel(data[0], sheet_name='2.2 User defined', header=[4], index_col=0, nrows=N_ts,
                            usecols=[0, 1, 2], engine='openpyxl').rename(
        columns={'Unnamed: 1': 'Weights', 'Cell importance': 'Cell_w'})
    weights.index.rename('Category', inplace=True)
    # from weights, create the names of ts for STEP1 and number of ts
    ts_names = list(weights.index)

    # reading the timeseries
    timeseries = pd.read_excel(data[0], sheet_name='1.1 Time Series', header=[1], index_col=0, nrows=8760,
                               engine='openpyxl')
    timeseries.drop(labels='period_duration [h]', axis=1, inplace=True)

    # adding the country suffix
    ts_names_all = [x + '_' + countries[0] for x in ts_names]
    weights.index = [str(line) + '_' + countries[0] for line in weights.index]
    timeseries.columns = [str(col) + '_' + countries[0] for col in timeseries.columns]

    ## READING THE OTHER COUNTRIES ##
    for i in np.arange(1, N_c):
        # reading the weights
        weights2 = pd.read_excel(data[i], sheet_name='2.2 User defined', header=[4], index_col=0, nrows=N_ts,
                                 usecols=[0, 1, 2], engine='openpyxl').rename(
            columns={'Unnamed: 1': 'Weights', 'Cell importance': 'Cell_w'})
        weights2.index = [str(line) + '_' + countries[i] for line in weights2.index]
        weights = pd.concat([weights,
                             weights2])  # weights = weights.merge(pd.read_excel(data[i],  sheet_name='2.2 User defined',  header=[4], index_col=0, nrows = N_ts, usecols = [0,1] ).rename(columns={'Unnamed: 1':'Weights_'+countries[i]}), left_index=True, right_index=True)
        # adding the names of each country's columns that have a weight
        ts_names_all = ts_names_all + [x + '_' + countries[i] for x in ts_names]
        # reading the timeseries
        ts2 = pd.read_excel(data[i], sheet_name='1.1 Time Series', header=[1], index_col=0, nrows=8760,
                            engine='openpyxl').drop(labels='period_duration [h]', axis=1)
        ts2.columns = [str(col) + '_' + countries[i] for col in ts2.columns]
        timeseries = timeseries.merge(ts2, left_index=True, right_index=True)

    ## NORMALIZING WEIGHTS ACCROSS COUNTRIES ##
    Cells_total = {ts: weights[weights.index.str.startswith(ts)]["Cell_w"].sum() for ts in ts_names}
    for c in countries:
        for ts in ts_names:
            row = ts + "_" + c
            weights['Weights'].loc[row] = weights['Weights'].loc[row] * weights['Cell_w'].loc[row] / Cells_total[ts]

    ## NORMALIZING TIMESERIES ##
    # compute norm = sum(ts)
    norm = timeseries.sum(axis=0)
    norm.index.rename('Category', inplace=True)
    norm.name = 'Norm'
    # normalise ts to have sum(norm_ts)=1
    norm_ts = timeseries / norm
    # fill NaN with 0
    norm_ts.fillna(0, inplace=True)

    ## WEIGHTING TIMESERIES ##
    weights = pd.Series(data=weights['Weights'], index=weights.index)
    weights.index.rename('Category', inplace=True)
    # select columns of ts that matters for STEP1
    weight_ts = norm_ts[ts_names_all]
    # multiply each timeserie by its weight
    weight_ts = weight_ts * weights

    ## CREATING DAY AND HOUR COLUMNS (for later pivoting) ##
    # creating df with 2 columns : day of the year | hour in the day
    day_and_hour_array = np.ones((24 * 365, 2))
    for i in range(365):
        day_and_hour_array[i * 24:(i + 1) * 24, 0] = day_and_hour_array[i * 24:(i + 1) * 24, 0] * (i + 1)
        day_and_hour_array[i * 24:(i + 1) * 24, 1] = np.arange(1, 25, 1)
    day_and_hour = pd.DataFrame(day_and_hour_array, index=np.arange(1, 8761, 1), columns=['D_of_H', 'H_of_D'])
    day_and_hour = day_and_hour.astype('int64')
    # merge day_and_hour with weight_ts for later pivot
    weight_ts = weight_ts.merge(day_and_hour, left_index=True, right_index=True)

    ## CREATING NDATA ##
    # pivoting timeseries to get Ndata (but not normalised and weighted)
    Ndata = weight_ts.pivot(index='D_of_H', columns='H_of_D', values=ts_names_all)
    # renumeroting Ndata columns
    Ndata.columns = np.arange(1, 24 * N_ts * N_c + 1)
    # adding AMPL syntax for param Ndata
    Ndata.rename(columns={Ndata.shape[1]: str(Ndata.shape[1]) + ' ' + ':='}, inplace=True)

    ## PRINTING NDATA AND WEIGHTS AND NORMS ##

    with open(out_path, mode='w', newline='\n') as TD_file:
        TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        TD_writer.writerow([
            '# -------------------------------------------------------------------------------------------------------------------------	'])
        TD_writer.writerow([
            '#	EnergyScope TD is an open-source energy model suitable for country scale analysis. It is a simplified representation of an urban or national energy system accounting for the energy flows'])
        TD_writer.writerow([
            '#	within its boundaries. Based on a hourly resolution, it optimises the design and operation of the energy system while minimizing the cost of the system.'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow([
            '#	Copyright (C) <2018-2019> <Ecole Polytechnique Fédérale de Lausanne (EPFL), Switzerland and Université catholique de Louvain (UCLouvain), Belgium>'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	Licensed under the Apache License, Version 2.0 (the "License");'])
        TD_writer.writerow(['#	you may not use this file except in compliance with the License.'])
        TD_writer.writerow(['#	You may obtain a copy of the License at'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	http://www.apache.org/licenses/LICENSE-2.0'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	Unless required by applicable law or agreed to in writing, software'])
        TD_writer.writerow(['#	distributed under the License is distributed on an "AS IS" BASIS,'])
        TD_writer.writerow(['#	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.'])
        TD_writer.writerow(['#	See the License for the specific language governing permissions and'])
        TD_writer.writerow(['#	limitations under the License.'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	Description and complete License: see LICENSE file.'])
        TD_writer.writerow([
            '# -------------------------------------------------------------------------------------------------------------------------	'])
        TD_writer.writerow(['	'])
        TD_writer.writerow(['# SETS depending on TD	'])
        TD_writer.writerow(['# --------------------------	'])
        TD_writer.writerow(['param Nbr_TD :=	' + str(Nbr_TD)])
        TD_writer.writerow([';		'])
        TD_writer.writerow(['		'])

    # concatenating and printing weights and norm
    weight_norm = pd.concat([weights, norm[ts_names_all]], axis=1)
    weight_norm.reset_index(inplace=True)
    weight_norm['#'] = '#'
    weight_norm = weight_norm[['#', 'Category', 'Weights', 'Norm']]
    weight_norm.to_csv(out_path, sep='\t', header=True, index=False, mode='a')

    with open(out_path, mode='a', newline='\n') as TD_file:
        TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        TD_writer.writerow([''])

    # printing param Ndata
    Ndata.to_csv(out_path, sep='\t', header=True, index=True, index_label='param Ndata :', mode='a')

    with open(out_path, mode='a', newline='\n') as TD_file:
        TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        TD_writer.writerow([';'])

    return


def step2_in(out_path, countries, data, step1_out, EUD_params=None, RES_params=None, RES_mult_params=None, N_ts=7, Nbr_TD=10):

    # Default name of timeseries in DATA.xlsx and corresponding name in ESTD data file
    if EUD_params is None:
        # for EUD timeseries
        EUD_params = {'Electricity (%_elec)': 'param electricity_time_series :=',
                      'Space Heating (%_sh)': 'param heating_time_series :=',
                      'Space Cooling': 'param cooling_time_series :=',
                      'Passanger mobility (%_pass)': 'param mob_pass_time_series :=',
                      'Freight mobility (%_freight)': 'param mob_freight_time_series :='}
    if RES_params is None:
        # for resources timeseries that have only 1 tech linked to it
        RES_params = {'PV': 'PV', 'Wind_offshore': 'WIND_OFFSHORE', 'Wind_onshore': 'WIND_ONSHORE'}
    if RES_mult_params is None:
        # for resources timeseries that have several techs linked to it
        RES_mult_params = {'Tidal': ['TIDAL_STREAM', 'TIDAL_RANGE'], 'Hydro_dam': ['HYDRO_DAM'],
                           'Hydro_river': ['HYDRO_RIVER'],
                           'Solar': ['DHN_SOLAR', 'DEC_SOLAR', 'PT_COLLECTOR', 'ST_COLLECTOR', 'STIRLING_DISH']}

    ## READING OUTPUT OF STEP1 ##
    TD_of_days = pd.read_csv(step1_out, names=['TD_of_days'])
    TD_of_days['day'] = np.arange(1, 366, 1)  # putting the days of the year beside

    ## COMPUTING NUMBER OF DAYS REPRESENTED BY EACH TD ##
    sorted_TD = TD_of_days.groupby('TD_of_days').count()
    sorted_TD.rename(columns={'day': '#days'}, inplace=True)
    sorted_TD.reset_index(inplace=True)
    sorted_TD.set_index(np.arange(1, Nbr_TD + 1), inplace=True)  # adding number of TD as index

    ## BUILDING T_H_TD MATRICE ##
    # generate T_H_TD
    TD_and_hour_array = np.ones((24 * 365, 2))
    for i in range(365):
        TD_and_hour_array[i * 24:(i + 1) * 24, 0] = np.arange(1, 25, 1)
        TD_and_hour_array[i * 24:(i + 1) * 24, 1] = TD_and_hour_array[i * 24:(i + 1) * 24, 1] * sorted_TD[
            sorted_TD['TD_of_days'] == TD_of_days.loc[i, 'TD_of_days']].index.values
    T_H_TD = pd.DataFrame(TD_and_hour_array, index=np.arange(1, 8761, 1), columns=['H_of_D', 'TD_of_day'])
    T_H_TD = T_H_TD.astype('int64')
    # giving the right syntax
    T_H_TD.reset_index(inplace=True)
    T_H_TD.rename(columns={'index': 'H_of_Y'}, inplace=True)
    T_H_TD['par_g'] = '('
    T_H_TD['par_d'] = ')'
    T_H_TD['comma1'] = ','
    T_H_TD['comma2'] = ','
    # giving the right order to the columns
    T_H_TD = T_H_TD[['par_g', 'H_of_Y', 'comma1', 'H_of_D', 'comma2', 'TD_of_day', 'par_d']]

    ## READING THE TIMESERIES IN DATA FILE ##
    N_c = len(data)  # number of countries
    # READ FIRST COUNTRY #
    # reading the timeseries
    timeseries = pd.read_excel(data[0], sheet_name='1.1 Time Series', header=[1], index_col=0, nrows=8760,
                               engine='openpyxl')
    timeseries.drop(labels='period_duration [h]', axis=1, inplace=True)
    ts_names = list(timeseries.columns)  # names of the columns
    timeseries.columns = [str(col) + '_' + countries[0] for col in timeseries.columns]

    # READING THE OTHER COUNTRIES #
    for i in np.arange(1, N_c):
        # reading the timeseries
        ts2 = pd.read_excel(data[i], sheet_name='1.1 Time Series', header=[1], index_col=0, nrows=8760,
                            engine='openpyxl').drop(labels='period_duration [h]', axis=1)
        ts2.columns = [str(col) + '_' + countries[i] for col in ts2.columns]
        timeseries = timeseries.merge(ts2, left_index=True, right_index=True)

    # COMPUTING THE NORM OVER THE YEAR ##
    norm = timeseries.sum(axis=0)
    norm.index.rename('Category', inplace=True)
    norm.name = 'Norm'

    ## BUILDING TD TIMESERIES ##
    # creating df with 2 columns : day of the year | hour in the day
    day_and_hour_array = np.ones((24 * 365, 2))
    for i in range(365):
        day_and_hour_array[i * 24:(i + 1) * 24, 0] = day_and_hour_array[i * 24:(i + 1) * 24, 0] * (i + 1)
        day_and_hour_array[i * 24:(i + 1) * 24, 1] = np.arange(1, 25, 1)
    day_and_hour = pd.DataFrame(day_and_hour_array, index=np.arange(1, 8761, 1), columns=['D_of_H', 'H_of_D'])
    day_and_hour = day_and_hour.astype('int64')
    timeseries = timeseries.merge(day_and_hour, left_index=True, right_index=True)

    # selecting timeseries of TD only
    TD_ts = timeseries[timeseries['D_of_H'].isin(sorted_TD['TD_of_days'])]

    ## COMPUTING THE NORM_TD OVER THE YEAR FOR CORRECTION ##
    # computing the sum of ts over each TD
    agg_TD_ts = TD_ts.groupby('D_of_H').sum()
    agg_TD_ts.reset_index(inplace=True)
    agg_TD_ts.set_index(np.arange(1, Nbr_TD + 1), inplace=True)
    agg_TD_ts.drop(columns=['D_of_H', 'H_of_D'], inplace=True)
    # multiplicating each TD by the number of day it represents
    for c in agg_TD_ts.columns:
        agg_TD_ts[c] = agg_TD_ts[c] * sorted_TD['#days']
    # sum of new ts over the whole year
    norm_TD = agg_TD_ts.sum()

    ## BUILDING THE DF WITH THE TS OF EACH TD FOR EACH CATEGORY ##
    # pivoting TD_ts to obtain a (24,Nbr_TD*Nbr_ts*N_c)
    all_TD_ts = TD_ts.pivot(index='H_of_D', columns='D_of_H')

    ## PRINTING 'ES_TD_'+str(Nbr_TD)+'TD.dat' ##
    # printing description of file
    with open(out_path, mode='w', newline='\n') as TD_file:
        TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        TD_writer.writerow([
            '# -------------------------------------------------------------------------------------------------------------------------	'])
        TD_writer.writerow([
            '#	EnergyScope TD is an open-source energy model suitable for country scale analysis. It is a simplified representation of an urban or national energy system accounting for the energy flows'])
        TD_writer.writerow([
            '#	within its boundaries. Based on a hourly resolution, it optimises the design and operation of the energy system while minimizing the cost of the system.'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow([
            '#	Copyright (C) <2018-2019> <Ecole Polytechnique Fédérale de Lausanne (EPFL), Switzerland and Université catholique de Louvain (UCLouvain), Belgium>'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	Licensed under the Apache License, Version 2.0 (the "License");'])
        TD_writer.writerow(['#	you may not use this file except in compliance with the License.'])
        TD_writer.writerow(['#	You may obtain a copy of the License at'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	http://www.apache.org/licenses/LICENSE-2.0'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	Unless required by applicable law or agreed to in writing, software'])
        TD_writer.writerow(['#	distributed under the License is distributed on an "AS IS" BASIS,'])
        TD_writer.writerow(['#	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.'])
        TD_writer.writerow(['#	See the License for the specific language governing permissions and'])
        TD_writer.writerow(['#	limitations under the License.'])
        TD_writer.writerow(['#	'])
        TD_writer.writerow(['#	Description and complete License: see LICENSE file.'])
        TD_writer.writerow([
            '# -------------------------------------------------------------------------------------------------------------------------	'])
        TD_writer.writerow(['	'])
        TD_writer.writerow(['# SETS depending on TD	'])
        TD_writer.writerow(['# --------------------------	'])
        TD_writer.writerow(['param peak_sh_factor	:=	'])
        peak_sh_factor = 1
        for c in countries:
            max_sh_TD = TD_ts.loc[:, 'Space Heating (%_sh)_' + c].max()
            max_sh_all = timeseries.loc[:, 'Space Heating (%_sh)_' + c].max()
            peak_sh_factor = max_sh_all / max_sh_TD
            TD_writer.writerow([c + ' ' + str(peak_sh_factor)])
        TD_writer.writerow([';		'])
        TD_writer.writerow(['		'])
        TD_writer.writerow(['#SETS [Figure 3]		'])
        TD_writer.writerow(['set TYPICAL_DAYS:= '] + list(np.arange(1, Nbr_TD + 1)) + ['; # typical days'])
        TD_writer.writerow(['set T_H_TD := 		'])

    # printing T_H_TD param
    T_H_TD.to_csv(out_path, sep='\t', header=False, index=False, mode='a', quoting=csv.QUOTE_NONE)

    # printing interlude
    with open(out_path, mode='a', newline='') as TD_file:
        TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL, lineterminator="\n")

        TD_writer.writerow([';'])
        TD_writer.writerow([''])
        TD_writer.writerow(['# -----------------------------'])
        TD_writer.writerow(['# PARAMETERS DEPENDING ON NUMBER OF TYPICAL DAYS : '])
        TD_writer.writerow(['# -----------------------------'])
        TD_writer.writerow([''])

    # if only 1 country
    if N_c == 1:
        # printing EUD timeseries param
        for l in EUD_params.keys():
            with open(out_path, mode='a', newline='\n') as TD_file:
                TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                       lineterminator="\n")
                TD_writer.writerow([EUD_params[l][0:-1]])
            for c in countries:
                name = l + '_' + c
                ts = all_TD_ts[name]
                ts.columns = np.arange(1, Nbr_TD + 1)
                ts = ts * norm[name] / norm_TD[name]
                ts.fillna(0, inplace=True)
                ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
                ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='', mode='a', quoting=csv.QUOTE_NONE)
            with open(out_path, mode='a', newline='\n') as TD_file:
                TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                       lineterminator="\n")
                TD_writer.writerow(';')
                TD_writer.writerow([''])

        # printing c_p_t param #
        with open(out_path, mode='a', newline='\n') as TD_file:
            TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                   lineterminator="\n")
            TD_writer.writerow(['param c_p_t:='])
            # printing c_p_t part where 1 ts => 1 tech
        for l in RES_params.keys():
            for c in countries:
                name = l + '_' + c
                ts = all_TD_ts[name]
                ts.columns = np.arange(1, Nbr_TD + 1)
                ts = ts * norm[name] / norm_TD[name]
                ts.fillna(0, inplace=True)
                ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
                ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='["' + RES_params[l] + '",*,*] :',
                          mode='a', quoting=csv.QUOTE_NONE)
        # printing c_p_t part where 1 ts => more then 1 tech
        for l in RES_mult_params.keys():
            for j in RES_mult_params[l]:
                for c in countries:
                    name = l + '_' + c
                    ts = all_TD_ts[name]
                    ts.columns = np.arange(1, Nbr_TD + 1)
                    ts = ts * norm[name] / norm_TD[name]
                    ts.fillna(0, inplace=True)
                    ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
                    ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='["' + j + '",*,*] :', mode='a',
                              quoting=csv.QUOTE_NONE)

        with open(out_path, mode='a', newline='\n') as TD_file:
            TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                   lineterminator="\n")
            TD_writer.writerow([';'])
    else:
        # printing EUD timeseries param
        for l in EUD_params.keys():
            with open(out_path, mode='a', newline='\n') as TD_file:
                TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                       lineterminator="\n")
                TD_writer.writerow([EUD_params[l]])
            for c in countries:
                name = l + '_' + c
                ts = all_TD_ts[name]
                ts.columns = np.arange(1, Nbr_TD + 1)
                ts = ts * norm[name] / norm_TD[name]
                ts.fillna(0, inplace=True)
                ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
                ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='["' + c + '",*,*] :', mode='a',
                          quoting=csv.QUOTE_NONE)
            with open(out_path, mode='a', newline='\n') as TD_file:
                TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                       lineterminator="\n")
                TD_writer.writerow(';')
                TD_writer.writerow([''])

        # printing c_p_t param #
        with open(out_path, mode='a', newline='\n') as TD_file:
            TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                   lineterminator="\n")
            TD_writer.writerow(['param c_p_t:='])
            # printing c_p_t part where 1 ts => 1 tech
        for l in RES_params.keys():
            for c in countries:
                name = l + '_' + c
                ts = all_TD_ts[name]
                ts.columns = np.arange(1, Nbr_TD + 1)
                ts = ts * norm[name] / norm_TD[name]
                ts.fillna(0, inplace=True)
                ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
                ts.to_csv(out_path, sep='\t', header=True, index=True,
                          index_label='["' + RES_params[l] + '","' + c + '",*,*] :', mode='a', quoting=csv.QUOTE_NONE)
        # printing c_p_t part where 1 ts => more then 1 tech
        for l in RES_mult_params.keys():
            for j in RES_mult_params[l]:
                for c in countries:
                    name = l + '_' + c
                    ts = all_TD_ts[name]
                    ts.columns = np.arange(1, Nbr_TD + 1)
                    ts = ts * norm[name] / norm_TD[name]
                    ts.fillna(0, inplace=True)
                    ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
                    ts.to_csv(out_path, sep='\t', header=True, index=True,
                              index_label='["' + j + '","' + c + '",*,*] :', mode='a', quoting=csv.QUOTE_NONE)

        with open(out_path, mode='a', newline='\n') as TD_file:
            TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                   lineterminator="\n")
            TD_writer.writerow([';'])
    return


def set_ampl(mod_path, data_path, options):
    try:

        # Create an AMPL instance
        ampl = AMPL()
        # define solver
        ampl.setOption('solver', 'cplex')
        # set options
        for o in options:
            ampl.setOption(o, options[o])
        # Read the model and data files.
        ampl.read(mod_path)
        for d in data_path:
            ampl.readData(d)

    except Exception as e:
        print(e)
        raise

    return ampl


def run_ampl(ampl):
    try:
        ampl.solve()
        ampl.eval('display solve_result;')
        ampl.eval('display _solve_elapsed_time;')
        t = ampl.getData('_solve_elapsed_time;').toList()[0]

    except Exception as e:
        print(e)
        raise
    return t


def update_version(config):
    """

    Updating the version.json file into case_studies directory to add the description of this run

    """
    # path of case_studies dir
    two_up = Path(__file__).parents[2]
    cs_versions = two_up / 'case_studies/versions.json'

    # get git commit used
    repo = git.Repo(search_parent_directories=True)
    commit_name = repo.head.commit.summary

    # get current datetime
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # read versions dict
    try:
        versions = a2p.read_json(cs_versions)
    except:
        versions = dict()

    # update the key for this case_study
    keys_to_extract = ['comment']
    versions[config['case_study']] = {key: config[key] for key in keys_to_extract}
    keys_to_extract = ['running', 'printing_out', 'printing_step2_in']
    versions[config['case_study']]['step1_config'] = {key: config['step1_config'][key] for key in keys_to_extract}
    keys_to_extract = ['running', 'printing_data', 'printing_inputs', 'printing_outputs']
    versions[config['case_study']]['step2_config'] = {key: config['step2_config'][key] for key in keys_to_extract}
    versions[config['case_study']]['commit_name'] = commit_name
    versions[config['case_study']]['datetime'] = now

    a2p.print_json(versions, cs_versions)
    return


def run_esmc(config):
    step1 = tuple()
    step2 = tuple()

    project_dir = Path(__file__).parents[2]
    # case study dir
    cs = project_dir / 'case_studies'
    (cs / config['case_study']).mkdir(parents=True, exist_ok=True)
    update_version(config)

    Nbr_TD = config['Nbr_TD']

    # setting path for step 2
    step2_config = config['step2_config']
    step2_path = step2_config['step2_path']
    data_step2 = [step2_path/('ESMC_' + str(Nbr_TD) + 'TD.dat'),
                  step2_path/'ESMC_indep.dat',
                  step2_path/'ESMC_countries.dat']
    mod_step2 = step2_path/'ESMC_model_AMPL.mod'
    step2_out = step2_path/'output'

    # step 1
    if config['step1_config']['running']:
        step1_config = config['step1_config']
        # path for step1
        step1_path = step1_config['step1_path']
        data_step1 = [step1_path/('data_' + str(Nbr_TD) + '.dat')]
        mod_step1 = step1_path/'TD_main.mod'
        step1_out = step1_path/('TD_of_days_' + str(Nbr_TD) + '.out')
        # print .dat for step1
        step1_in(data_step1[0], config['countries'], config['data_folders'], step1_config['N_ts'], Nbr_TD)
        # set ampl STEP_1
        ampl_step1 = set_ampl(mod_path=mod_step1, data_path=data_step1, options=step1_config['ampl_options_step1'])
        # run ampl STEP_1
        logging.info('Running Step 1')
        t_step1 = run_ampl(ampl_step1)
        logging.info('End of run Step 1 in ' + str(t_step1) + ' seconds')
        if step1_config['printing_out']:
            logging.info('Printing Step 1 .out')
            # print .out STEP_1
            a2p.print_step1_out(ampl_step1, step1_out)
            if step1_config['printing_step2_in']:
                logging.info('Printing ESTD' + str(Nbr_TD) + 'TD.dat')
                # print ESTD_+'Nbr_TD'+TD.dat
                step2_in(data_step2[0], config['countries'], config['data_folders'], step1_out,
                         step1_config['EUD_params'], step1_config['RES_params'], step1_config['RES_mult_params'],
                         step1_config['N_ts'], config['Nbr_TD'])
        step1 = (ampl_step1, t_step1)

    # step 2

    # copy input files
    shutil.copyfile(mod_step2,
                    cs / config['case_study'] / 'ESMC_model_AMPL.mod')
    shutil.copyfile(data_step2[0],
                    cs / config['case_study'] / ('ESMC_' + str(config['Nbr_TD']) + 'TD.dat'))
    shutil.copyfile(data_step2[1],
                    cs / config['case_study'] / 'ESMC_indep.dat')
    shutil.copyfile(data_step2[0],
                    cs / config['case_study'] / 'ESMC_countries.dat')

    # set ampl for step_2
    esom = op.OptiProbl(mod_path=mod_step2, data_path=data_step2, options=step2_config['ampl_options'])
    t = 0
    # getting inputs

    if step2_config['printing_inputs']:
        # printing sets, params and vars
        esom.print_intputs(directory=cs / config['case_study'] / 'input')

    # instantiate results
    results = dict()

    if step2_config['running']:

        # running ES
        logging.info('Running EnergyScope')
        esom.run_ampl()
        logging.info('End of run in ' + str(esom.t) + 'seconds')
        if step2_config['printing_outputs']:
            logging.info('Printing outputs')
            # getting results
            esom.get_results()
            # printing results
            esom.print_results(directory=cs/config['case_study']/'output')

    logging.info('End of run')

    return {'step1': step1, 'step2': esom}
