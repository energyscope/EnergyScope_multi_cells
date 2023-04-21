# -*- coding: utf-8 -*-
"""
This script reads data from external sources,
computes the hourly time series from it,
and puts them into csv Data

REM: If you change the efficiency improvement or the eta_tot_pt, you need to run it twice.
A first time to recompute mean_eta_th and a second time to get the time series

@author: Paolo Thiran
"""

# TODO
# choose another location for csp FR because this one is too low
# print time series
# make a function out of it
# learn geopandas for centroid and distances (+plots)
# solar thermal ts from opsd data + centroid + oemof.thermal
# write doc solar
# update distances and exchanges modelling
# get RES potentials from ENSPRESO
# test run
# put onto gitkraken

import pandas as pd
import numpy as np

from esmc import generate_all_csp_ts  # TODO update that to put it out of the package
from pathlib import Path
from esmc import CSV_SEPARATOR
from esmc.common import eu27_country_code, eu27_full_names, code_2_full
from esmc.utils.df_utils import clean_indices

# Configuration
proj_year = 2035
ref_year = 2015

compute_csp = True
read_csp = False
read_dommisse = True
update_ts = True

expected_cp_tidal = 0.2223 # from Hammons T.J. (2011)

# path
project_dir = Path(__file__).parents[2]
data_dir = project_dir / 'Data'
ex_data_dir = data_dir / 'exogenous_data'
dommisse_data = Path(r'C:\Users\pathiran\Documents\energy_system_modelling\ESTD\EnergyScope-EuropeanCountries2020')


# reading previously computed RES potentials
res_pot = pd.read_csv(ex_data_dir / 'regions' / 'Technologies.csv', header=[0], index_col=[0, 1], sep=CSV_SEPARATOR) \
              .loc[('f_max', slice(None)), :].droplevel(level=0)

r_with_csp = list(res_pot.loc[((res_pot.loc[:, 'PT_POWER_BLOCK'] > 0.1) | (res_pot.loc[:, 'ST_POWER_BLOCK'] > 0.1)), :]
                  .index)
r_with_woff = list(res_pot.loc[res_pot.loc[:, 'WIND_OFFSHORE'] > 0.1, :].index)
r_with_dam = list(res_pot.loc[res_pot.loc[:, 'HYDRO_DAM'] > 0.1, :].index)
r_with_tidal = list(res_pot.loc[((res_pot.loc[:, 'TIDAL_STREAM'] > 0.1) | (res_pot.loc[:, 'TIDAL_RANGE'] > 0.1)), :]
                    .index)

"""
Computing time series of CSP
"""
if compute_csp:
    # general parameters to convert into ESMC inputs (time series of [GW_th/GW_p,th]
    land_use_csp = 1 / 0.170  # [km^2/GW_p,e] (If SM=1, surface used for the entire plant per GW electrical installed)
    eta_tot_pt = 0.18  # projected efficiency of parabolic through power plants (IRENA)
    mean_eta_th = 0.41813  # average efficiency of conversion from solar energy to thermal energy computed in a first run
    eta_pb = eta_tot_pt / mean_eta_th  # efficiency of power block
    additional_losses = 0.2  # additional losses (e.g. in the pipes)
    eff_improvements = 0.09544  # overall efficiency improvement of the thermal part of the plant

    csp_ts, run_dict = generate_all_csp_ts(year=ref_year, land_use_csp=land_use_csp, eta_pb=eta_pb,
                                           additional_losses=additional_losses,
                                           eff_improvements=eff_improvements,
                                           csp_file=ex_data_dir / 'csp' / 'csp_to_compute.json',
                                           print_csv=True)

    # computing the average solar to thermal efficiency of all the considered locations
    mean_eta_th = 0
    n = 0
    for i, j in run_dict['meta'].items():
        mean_eta_th += j['eta_th']
        n += 1

    mean_eta_th = mean_eta_th / n
elif read_csp:
    csp_ts = pd.read_csv(ex_data_dir / 'csp' / 'ts_csp.csv', header=[0], index_col=[0], sep=CSV_SEPARATOR)

"""
Reading time series from Dommisse et al.
"""
r = 'ES'
r_full = 'Spain'
# TODO put into datetime
all_ts = pd.DataFrame(np.nan, index=np.arange(1,8761),
                      columns=pd.MultiIndex.from_product([eu27_country_code,
                                                          ['ELECTRICITY_VAR', 'HEAT_LOW_T_SH',
                                                           'SPACE_COOLING', 'MOBILITY_PASSENGER',
                                                           'MOBILITY_FREIGHT', 'PV', 'WIND_ONSHORE',
                                                           'WIND_OFFSHORE', 'HYDRO_DAM', 'HYDRO_RIVER',
                                                           'TIDAL', 'SOLAR', 'CSP']]))

for r, r_full in code_2_full.items():
    if read_dommisse and r != 'CH':
        print('Read Dommisse et al. ' + r_full)
        # read technologies f_min and f_max from data of J&JL
        ts_dommisse = clean_indices(pd.read_excel(dommisse_data / r / 'Data_management' / 'DATA.xlsx',
                                                  sheet_name='1.1 Time Series', header=[1], nrows=8760)) \
            .drop(columns=['period_duration [h]']).rename(columns={'Electricity (%_elec)': 'ELECTRICITY_VAR',
                                                                   'Space Heating (%_sh)': 'HEAT_LOW_T_SH',
                                                                   'Space Cooling': 'SPACE_COOLING',
                                                                   'Passanger mobility (%_pass)': 'MOBILITY_PASSENGER',
                                                                   'Freight mobility (%_freight)': 'MOBILITY_FREIGHT'}) \
            .rename(columns=lambda x: x.upper())

        # adding csp on regions with csp potentials
        if r in r_with_csp:
            ts_dommisse['CSP'] = csp_ts.loc[:, r].values
        else:
            ts_dommisse['CSP'] = 0.0001

        # scaling tidal in regions with tidal potential
        if r in r_with_tidal:
            dommisse_cp_tidal = ts_dommisse.loc[:, 'TIDAL'].sum()/8760
            ts_dommisse.loc[:, 'TIDAL'] = ts_dommisse.loc[:, 'TIDAL'] * expected_cp_tidal/dommisse_cp_tidal

        # putting the same index as in Data
        ts_dommisse['{PERIODS}'] = np.arange(1, 8761)
        ts_dommisse.set_index('{PERIODS}', inplace=True)

    if update_ts:
        print('Updating time series ' + r_full)
        ts_new = pd.read_csv(data_dir / str(proj_year) / r / 'Time_series.csv',
                             header=[0], index_col=[0], sep=CSV_SEPARATOR)
        ts_new.update(ts_dommisse)
        if r != 'FR':
            ts_new.to_csv(data_dir / str(proj_year) / r / 'Time_series.csv', sep=CSV_SEPARATOR)

        all_ts.loc[:, (r, slice(None))] = ts_new.values

if update_ts:
    all_ts.to_csv(ex_data_dir / 'regions' / 'Time_series_2015.csv')

# checking validity of time series
if all_ts.isnull().values.any():
    print('There are NA values in the time series')

all_cp = all_ts.sum()
# TODO
#  1) update ts based on Dommisse et al. and csp computation module
#  2) change index of ts to datetime
#  3) update ts based on exo data

# proj_year = 2035
# region = 'FR'
# file = 'Time_series.csv'
# ser = csp_ts.loc[:,region]
# ser.name = 'SOLAR'
# ser = ser.reset_index(drop=True)
# ser.index = ser.index + 1
#
# file_path = data_dir / str(proj_year) / region / file
# my_df = pd.read_csv(file_path, sep=CSV_SEPARATOR)
# my_df.update(ser)
