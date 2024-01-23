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
#   Recompute final_elec_ts once I have new time series for space heating and cooling from Staffell et al. (2023)

import pandas as pd
import numpy as np
import pytz
import json

from datetime import datetime, date, timedelta
from pathlib import Path
from esmc.common import eu28_country_code, eu28_full_names, code_2_full, CSV_SEPARATOR, eu34_country_code_iso3166_alpha2
from esmc.utils.df_utils import clean_indices
# plotly imports
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

pio.renderers.default = 'browser'

import sys
sys.path.append(str(Path(__file__).parents[2] / 'esmc' / 'preprocessing'))
from precalc import generate_all_csp_ts

# Configuration
proj_year = 2050
ref_year = 2017

# check if ref_year is a leap year then we will get rid of 29/02
leap_yr = ((ref_year % 4) == 0)

dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
if leap_yr:
    dt_utc = dt_utc[~((dt_utc.month == 2) & (dt_utc.day == 29))]

compute_csp = False
read_csp = True
read_dommisse = False
read_actual = True
update_ts = False
plot_final = False

expected_cp_tidal = 0.2223 # from Hammons T.J. (2011)

# mapping of EU+ countries if no data in data sources
mapping_eu_plus = {'AL': 'GR',
                   'BA': 'HR',
                   'ME': 'HR',
                   'MK': 'BG',
                   'RS': 'RO',
                   'XK': 'BG'}

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

# regrouping into final_csp_ts df
final_csp_ts = pd.DataFrame(1e-4, index=dt_utc,
                            columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['CSP']]))
final_csp_ts.loc[:, final_csp_ts.columns.get_level_values(0).isin(list(csp_ts.columns))] = csp_ts.values
"""
Reading time series from Dommisse et al.
"""
r = 'ES'
r_full = 'Spain'
# TODO put into datetime
all_ts = pd.DataFrame(np.nan, index=np.arange(1,8761),
                      columns=pd.MultiIndex.from_product([eu28_country_code,
                                                          ['ELECTRICITY', 'HEAT_LOW_T_SH',
                                                           'SPACE_COOLING', 'MOBILITY_PASSENGER',
                                                           'MOBILITY_FREIGHT', 'PV', 'WIND_ONSHORE',
                                                           'WIND_OFFSHORE', 'HYDRO_DAM', 'HYDRO_RIVER',
                                                           'TIDAL', 'SOLAR', 'CSP']]))

if read_actual:
    all_ts = pd.read_csv(ex_data_dir / 'regions' / 'Time_series_2017.csv', header=[0, 1], index_col=0, sep=';')

for r, r_full in code_2_full.items():
    if read_dommisse and r != 'CH':
        print('Read Dommisse et al. ' + r_full)
        # read technologies f_min and f_max from data of J&JL
        ts_dommisse = clean_indices(pd.read_excel(dommisse_data / r / 'Data_management' / 'DATA.xlsx',
                                                  sheet_name='1.1 Time Series', header=[1], nrows=8760)) \
            .drop(columns=['period_duration [h]']).rename(columns={'Electricity (%_elec)': 'ELECTRICITY',
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

# checking validity of time series
if all_ts.isnull().values.any():
    print('There are NA values in the time series')

all_cp = all_ts.sum()

"""
Computing new heating and cooling time series + solar thermal
"""
t_bh = 14 # 15.5°C temperature from which we begin to heat
t_bc = 20 # 22°C temperature from which we begin to cool
heating_month = [9, 10, 11, 12, 1, 2, 3, 4, 5] # only month where we consider space heating
cooling_month = [5, 6, 7, 8, 9] # only month where we consider space cooling
# reading weather data
weather_ts = pd.read_csv(ex_data_dir / 'gitignored' / 'opsd-weather_data-2020-09-16' / 'weather_data.csv',
                         header=0, index_col=0, parse_dates=True)
# select ref_year
weather_ts = weather_ts.loc[weather_ts.index.year == ref_year, :]

# add EU+ countries by mapping neighbouring country
for i,j in mapping_eu_plus.items():
    weather_ts[i + '_temperature'] = weather_ts[j + '_temperature'].values
    weather_ts[i + '_radiation_direct_horizontal'] = weather_ts[j + '_radiation_direct_horizontal'].values
    weather_ts[i + '_radiation_diffuse_horizontal'] = weather_ts[j + '_radiation_diffuse_horizontal'].values
# separate ghi and temperature
temp_ts = weather_ts.loc[:, weather_ts.columns.str.endswith('temperature')].rename(columns=lambda x: x[:2])
ghi_ts = pd.DataFrame((weather_ts.loc[:, weather_ts.columns.str.endswith('direct_horizontal')].values
          + weather_ts.loc[:, weather_ts.columns.str.endswith('diffuse_horizontal')].values)/1000,  # conversion into GW/m2
                      index=temp_ts.index, columns=temp_ts.columns)

if leap_yr:
    temp_ts = temp_ts.loc[~((temp_ts.index.month == 2) & (temp_ts.index.day == 29)), :]
    ghi_ts = ghi_ts.loc[~((ghi_ts.index.month == 2) & (ghi_ts.index.day == 29)), :]

wdw = 24
# computing hdh (heating degree hour) and cdh (cooling degree hour)
hdh = t_bh - temp_ts.copy()
hdh = hdh.mask(hdh < 0, 0) # keeping only positive
# hdh.loc[~hdh.index.month.isin(heating_month), :] = 0
hdh = hdh.rolling(wdw).mean().fillna(method='bfill') # average over wdw hours to avoid high peaks
hdh = hdh.div(hdh.sum(axis=0), axis=1) # normalize

cdh = temp_ts.copy() - t_bc
# cdh['NO'] += 2 # adding 2°C to cdh in NO to have the shape of the cooling (reaching baove 22°C)
# cdh['IE'] += 2 # same for IE
cdh = cdh.mask(cdh < 0, 0) # keeping only positive
# cdh.loc[~cdh.index.month.isin(cooling_month), :] = 0 # keep only cooling season
cdh = cdh.rolling(wdw).mean().fillna(method='bfill') # average over wdw hours to avoid high peaks
cdh = cdh.div(cdh.sum(axis=0), axis=1) # normalize

# temp_day_mean = temp_ts.groupby(by=[temp_ts.index.month, temp_ts.index.day]).mean()
# temp_day_mean.index.names = ['Month', 'Day']
# temp_day_mean.index = pd.date_range(start=datetime(ref_year-1, 1, 1), end=datetime(ref_year-1, 12, 31), freq='D', tz='UTC')
#
# temp_day_max = temp_ts.groupby(by=[temp_ts.index.month, temp_ts.index.day]).max()
# temp_day_max.index.names = ['Month', 'Day']
# temp_day_max.index = pd.date_range(start=datetime(ref_year-1, 1, 1), end=datetime(ref_year-1, 12, 31), freq='D', tz='UTC')
# cdh2 = temp_ts.copy()
# for r in temp_day_max.columns:
#     cdd_list = temp_day_max.loc[temp_day_max[r] >= t_bc, r].index
#     cdh2.loc[~((cdh2.index.day.isin(cdd_list.day)) & (cdh2.index.month.isin(cdd_list.month))), r] = 0
#
# cdh2 = cdh2.div(cdh2.sum(axis=0), axis=1)

# final ts
final_sh_ts = hdh.copy()
final_sc_ts = cdh.copy()
final_st_ts = ghi_ts.copy()

# set multiindex
final_sh_ts.columns = pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['HEAT_LOW_T_SH']])
final_sc_ts.columns = pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['SPACE_COOLING']])
final_st_ts.columns = pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['SOLAR']])


"""
Generate electricity time series
"""
# import electricity load ts
elec_load_ts = pd.read_csv(ex_data_dir / 'gitignored' / 'time_series_60min_singleindex.csv',
                           header=0, index_col=0, sep=',')
elec_load_ts.index = pd.to_datetime(elec_load_ts.index)
elec_load_ts = elec_load_ts.loc[str(ref_year), elec_load_ts.columns.str.contains('load_actual')]
elec_load_gb_ts = elec_load_ts.loc[:, 'GB_UKM_load_actual_entsoe_transparency']
elec_load_ts = elec_load_ts.loc[:, elec_load_ts.columns.str[3:] == 'load_actual_entsoe_transparency']
elec_load_ts.rename(columns=lambda x: x[:2], inplace=True)
elec_load_ts['GB'] = elec_load_gb_ts.values
elec_load_ts *= 1e-3 #put into GW
# check countries without ts
elec_load_ts = elec_load_ts.loc[:, elec_load_ts.columns.isin(eu34_country_code_iso3166_alpha2)]
elec_missing_ts = [i for i in eu34_country_code_iso3166_alpha2 if i not in list(elec_load_ts.columns)]
# check NaN data and fill them
# /!\ if there are still NaN values after this procedure should consider using other data

# if leap year do the shift with index of previous year (to avoid 29/02) and then go back to ref year

if leap_yr:
    elec_load_ts = elec_load_ts.loc[~((elec_load_ts.index.month == 2) & (elec_load_ts.index.day == 29)), :]
    ref_year -= 1
    dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
    elec_load_ts = elec_load_ts.set_index(dt_utc)

elec_na = elec_load_ts.isna().sum(axis=0)
for r in elec_na[elec_na > 0].index:
    # fill na values with values of previous week
    na_ind = elec_load_ts.loc[elec_load_ts[r].isna(), r].index
    elec_load_ts.loc[na_ind, r] = elec_load_ts.shift(24 * 7).loc[na_ind, r]
    # fill remaining na values with values of next week
    na_ind2 = elec_load_ts.loc[elec_load_ts[r].isna(), r].index
    elec_load_ts.loc[na_ind2, r] = elec_load_ts.shift(-24 * 7).loc[na_ind2, r]

if leap_yr:
    ref_year += 1
    dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
    dt_utc = dt_utc[~((dt_utc.month == 2) & (dt_utc.day == 29))]
    elec_load_ts = elec_load_ts.set_index(dt_utc)

# getting data on heating and cooling with electricity
hre4_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\Demand\data\HRE4-Exchange-Template-WP3_v22b_website.xlsx')
hre4_data = pd.read_excel(hre4_path, sheet_name='Aggregation data', header=3, index_col=[1, 5])
hre4_data = hre4_data.loc[hre4_data['Sector'] == 'Total']
elec_rows = ['Heat pumps total (electric)', 'Electric Heating']
fec_cols = ['Total heating/cooling final',  'Space heating final', 'Space cooling final']
hre4_data = hre4_data.loc[hre4_data.index.get_level_values(1).isin(elec_rows), fec_cols].groupby('Country').sum()
hre4_data = hre4_data.rename(columns={'Total heating/cooling final': 'Constant heating/cooling final'})
hre4_data['Constant heating/cooling final'] = hre4_data['Constant heating/cooling final']\
                                              - hre4_data['Space heating final'] - hre4_data['Space cooling final']
hre4_data = hre4_data.rename(index=dict(zip(eu28_full_names, eu28_country_code)))
hre4_data = hre4_data.drop(['Cyprus', 'Malta'])

# compute proxy of hre4 data for CH and NO by considering same shares as AT and SE,
sc_elec_cop = 2.5 # COP of space cooling with electricity
pc_cop = 1 / 0.4965 # COP of process cooling
demands = pd.read_csv(ex_data_dir / 'regions' / 'Demands.csv', header=0, index_col=[0, 1, 2], sep=CSV_SEPARATOR)
my_demands = demands.loc[(2015, ['AT', 'CH', 'SE', 'NO'],
                          ['HEAT_HIGH_T', 'HEAT_LOW_T_SH', 'HEAT_LOW_T_HW', 'PROCESS_COOLING', 'SPACE_COOLING']), :].droplevel(level=0, axis=0)
my_demands = my_demands.sum(axis=1).reset_index().pivot(index='level_0', columns='level_1').droplevel(level=0, axis=1)
my_demands.loc[:, 'SPACE_COOLING'] *= 1 / sc_elec_cop
my_demands.loc[:, 'PROCESS_COOLING'] *= 1 * pc_cop
my_demands['Constant heating/cooling final'] = my_demands.loc[:, ['HEAT_HIGH_T', 'HEAT_LOW_T_HW', 'PROCESS_COOLING']]\
    .sum(axis=1)
my_demands = my_demands.drop(columns=['HEAT_HIGH_T', 'HEAT_LOW_T_HW', 'PROCESS_COOLING'])\
    .rename(columns={'HEAT_LOW_T_SH': 'Space heating final', 'SPACE_COOLING': 'Space cooling final'})
share_by_elec = hre4_data.loc[['AT', 'SE'], :].div(my_demands.loc[['AT', 'SE'], :] / 1e3, axis=1)
hre4_data = pd.concat([hre4_data, share_by_elec.rename(index={'AT': 'CH', 'SE': 'NO'})\
    .mul(my_demands.loc[['CH', 'NO'], :]/ 1e3)], axis=0)
# not used anymore, use comparison of specific elec and elec_load_ts
# hre4_data = hre4_data.div(hre4_data.sum(axis=1), axis=0)
#
# demands_sc = demands.loc[(2015, slice(None), 'SPACE_COOLING'), :].sum(axis=1) / 1e3
#
# # compute share of non-specific elec in each demand
# elec_specific = demands.loc[(2015, slice(None), 'ELECTRICITY'), :].sum(axis=1).droplevel(level=2, axis=0).droplevel(level=0, axis=0)
# elec_other = elec_load_ts.sum() - elec_specific
# hre4_data = hre4_data.mul(elec_other, axis=0)

# generate time series of elec consumption for heating
elec_sh_ts = hdh.mul(hre4_data['Space heating final'] * 1e3, axis=1)
elec_sc_ts = cdh.mul(hre4_data['Space cooling final'] * 1e3, axis=1)
# elec_sc_ts = final_sc_ts.mul(demands_sc.droplevel(level=2, axis=0).droplevel(level=0, axis=0) * 1e3 / sc_elec_cop, axis=1)
elec_cst_heat_ts = pd.DataFrame(1, index=elec_sh_ts.index, columns=elec_sh_ts.columns)
elec_cst_heat_ts = elec_cst_heat_ts.mul(hre4_data['Constant heating/cooling final'] * 1e3/ 8760, axis=1)

# TODO for now, elec_sc_ts is ignored as it gives weird results (values < 0 in hot countries e.g. GR, IT). Try again with I. Staffell data
# compute final elec ts
final_elec_ts = elec_load_ts - elec_sh_ts - elec_cst_heat_ts #- elec_sc_ts

# filter data errors that are < 0  by taking data of the week before or after
final_elec_ts = final_elec_ts.mask(final_elec_ts <= 0, np.nan)
# if leap year do the shift with index of previous year (to avoid 29/02) and then go back to ref year
if leap_yr:
    ref_year -= 1
    dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
    final_elec_ts = final_elec_ts.set_index(dt_utc)

elec_final_na = final_elec_ts.isna().sum(axis=0)
for r in elec_final_na[elec_final_na > 0].index:
    # fill na values with values of previous week
    na_ind = final_elec_ts.loc[final_elec_ts[r].isna(), r].index
    final_elec_ts.loc[na_ind, r] = final_elec_ts.shift(24 * 7).loc[na_ind, r]
    # fill remaining na values with values of next week
    na_ind2 = final_elec_ts.loc[final_elec_ts[r].isna(), r].index
    final_elec_ts.loc[na_ind2, r] = final_elec_ts.shift(-24 * 7).loc[na_ind2, r]

    # fill na values with values of previous week
    na_ind = final_elec_ts.loc[final_elec_ts[r].isna(), r].index
    final_elec_ts.loc[na_ind, r] = final_elec_ts.shift(24 * 7).loc[na_ind, r]
    # fill remaining na values with values of next week
    na_ind2 = final_elec_ts.loc[final_elec_ts[r].isna(), r].index
    final_elec_ts.loc[na_ind2, r] = final_elec_ts.shift(-24 * 7).loc[na_ind2, r]

if leap_yr:
    ref_year += 1
    dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
    dt_utc = dt_utc[~((dt_utc.month == 2) & (dt_utc.day == 29))]
    final_elec_ts = final_elec_ts.set_index(dt_utc)

elec_load_month = elec_load_ts.groupby(by=[elec_load_ts.index.month]).sum()

# Normalize final_elec_ts
final_elec_ts = final_elec_ts.div(final_elec_ts.sum(axis=0), axis=1)

# Fill countries from EU+ with data from neighbouring countries
for i,j in mapping_eu_plus.items():
    final_elec_ts[i] = final_elec_ts[j].values

final_elec_ts.columns = pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['ELECTRICITY']])
"""
Reading PV, WIND_ONSHORE and WIND_OFFSHORE ts
"""
# reading opsd data
elec_re_ts = pd.read_csv(ex_data_dir / 'gitignored' / 'ninja_pv_wind_profiles_singleindex_filtered.csv',
                         header=0, index_col=0, parse_dates=True)
# select ref year and get rid of 29/02 if leap year
elec_re_ts = elec_re_ts.loc[str(ref_year), :]
if leap_yr:
    elec_re_ts = elec_re_ts.loc[~((elec_re_ts.index.month == 2) & (elec_re_ts.index.day == 29)), :]

# read for country with missing data
woff_bg_ts = pd.DataFrame(pd.read_csv(ex_data_dir / 'gitignored' / 'BG_woff_ninja_wind_43.0000_28.3000_corrected.csv',
                         header=3, index_col=0, parse_dates=True).drop(columns=['local_time']).values,
                          index=elec_re_ts.index, columns=['BG_wind_offshore_near-termfuture'])
woff_ro_ts = pd.DataFrame(pd.read_csv(ex_data_dir / 'gitignored' / 'RO_woff_ninja_wind_44.0000_29.0000_corrected.csv',
                         header=3, index_col=0, parse_dates=True).drop(columns=['local_time']).values,
                          index=elec_re_ts.index, columns=['RO_wind_offshore_near-termfuture'])
elec_re_ts = elec_re_ts.merge(woff_bg_ts, left_index=True, right_index=True)\
    .merge(woff_ro_ts, left_index=True, right_index=True)

# separate pv and wind
pv_ts = elec_re_ts.loc[:, elec_re_ts.columns.str.contains('pv')].rename(columns=lambda x: x[:2])
wind_ts = elec_re_ts.loc[:, elec_re_ts.columns.str.contains('wind')]

# add missing XK PV ts
pv_ts['XK'] = pv_ts.loc[:, mapping_eu_plus['XK']].values

# put pv ts in proper format
final_pv_ts = pd.DataFrame(pv_ts.loc[:, eu34_country_code_iso3166_alpha2].values, index=pv_ts.index,
                           columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['PV']]))

# check countries with missing woff ts
woff_ts = elec_re_ts.loc[:, elec_re_ts.columns.str.contains('wind_offshore')]
r_with_woff_ts = list(set(woff_ts.columns.str[:2]))
missing_woff_ts = [i for i in r_with_woff if i not in r_with_woff_ts]

# check cp of wind ts
cp_wind = wind_ts.mean()

# select best time series for wind on,shore and offshore in each country
selected_wind_ts = dict()
final_wind_ts = pd.DataFrame(np.nan, index=wind_ts.index,
                             columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['WIND_ONSHORE', 'WIND_OFFSHORE']]))

won_priority = ['_wind_onshore_near-termfuture', '_wind_onshore_current', '_wind_national_current']
woff_priority = ['_wind_offshore_near-termfuture', '_wind_offshore_current']
# some exceptions in the mapping where manually checked (see documentation)
woff_exceptions = {'EE': 'EE_wind_national_long-termfuture',
                   'ES': 'ES_wind_national_long-termfuture',
                   'HR': 'IT_wind_offshore_near-termfuture',
                   'LT': 'LT_wind_national_long-termfuture',
                   'LV': 'LT_wind_national_long-termfuture',
                   'PL': 'PL_wind_national_long-termfuture'
                   }
for r in eu34_country_code_iso3166_alpha2:
    selected_wind_ts[r] = []
    li = list(wind_ts.loc[:, wind_ts.columns.str.startswith(r)].columns)
    no_won_ts = True
    no_woff_ts = True
    # selecting won ts
    for w in won_priority:
        if (((r + w) in li) & no_won_ts):
            selected_wind_ts[r].append((r + w))
            final_wind_ts.loc[:, (r, 'WIND_ONSHORE')] = wind_ts.loc[:, (r + w)]
            no_won_ts = False
    # selecting woff ts
    if r in r_with_woff:  # if has woff
        if r in woff_exceptions.keys(): # if is an exception with specific mapping
            selected_wind_ts[r].append(woff_exceptions[r])
            final_wind_ts.loc[:, (r, 'WIND_OFFSHORE')] = wind_ts.loc[:, woff_exceptions[r]]
        else: # classical mapping
            for w in woff_priority:
                if (((r + w) in li) & no_woff_ts):
                    selected_wind_ts[r].append((r + w))
                    final_wind_ts.loc[:, (r, 'WIND_OFFSHORE')] = wind_ts.loc[:, (r + w)]
                    no_woff_ts = False

    else: # if doesn't have woff
        final_wind_ts.loc[:, (r, 'WIND_OFFSHORE')] = 1e-4

# filling EU+ countries with no WON ts (i.e. all but MK)
for i,j in mapping_eu_plus.items():
    if i != 'MK':
        final_wind_ts.loc[:, (i, 'WIND_ONSHORE')] = final_wind_ts.loc[:, (j, 'WIND_ONSHORE')].values

"""
Shifting passenger mobility and tidal ts according to the region timezone
"""
base_ts = all_ts.loc[:, (slice(None), ['MOBILITY_PASSENGER', 'TIDAL'])].copy().reset_index(drop=True)
base_ts.index = np.arange(1, 8761)
# add NO
base_ts.loc[:, ('NO', 'MOBILITY_PASSENGER')] = base_ts.loc[:, ('GB', 'MOBILITY_PASSENGER')].values
base_ts.loc[:, ('NO', 'TIDAL')] = base_ts.loc[:, ('GB', 'TIDAL')].values
# add other EU+
for i,j in mapping_eu_plus.items():
    base_ts.loc[:, (i, 'MOBILITY_PASSENGER')] = base_ts.loc[:, (j, 'MOBILITY_PASSENGER')].values
    base_ts.loc[:, (i, 'TIDAL')] = base_ts.loc[:, (j, 'TIDAL')].values
# create final df with datetime index
# if leap year do timezone change with previous year and change index at the end
if leap_yr:
    ref_year -= 1
dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
final_mob_ts = pd.DataFrame(np.nan, index=dt_utc,
                            columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['MOBILITY_PASSENGER']]))
final_tidal_ts = pd.DataFrame(np.nan, index=dt_utc,
                            columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ['TIDAL']]))

# change timezone for each country
for r in eu34_country_code_iso3166_alpha2:
    # get tz of country
    if r != 'XK':
        tz = pytz.country_timezones(r)[0]
    else:
        tz = pytz.country_timezones('RS')[0]
    # add 2 first and trailing hours for tz change
    df = base_ts.loc[:, (r, slice(None))]
    df = pd.concat([df.loc[8759:, :], (pd.concat([df, df.loc[:2, :]]))])
    # convert timezone
    dt = pd.date_range(start=datetime(ref_year - 1, 12, 31, 22), end=datetime(ref_year + 1, 1, 1, 1), freq='H', tz=tz)
    df = df.set_index(dt.tz_convert(pytz.utc))
    final_mob_ts.loc[:, (r, 'MOBILITY_PASSENGER')] = df.loc[dt_utc, (r, 'MOBILITY_PASSENGER')]
    final_tidal_ts.loc[:, (r, 'TIDAL')] = df.loc[dt_utc, (r, 'TIDAL')]

if leap_yr:
    ref_year += 1
    dt_utc = pd.date_range(start=datetime(ref_year, 1, 1), end=datetime(ref_year, 12, 31, 23), freq='H', tz=pytz.utc)
    dt_utc = dt_utc[~((dt_utc.month == 2) & (dt_utc.day == 29))]
    final_mob_ts = final_mob_ts.set_index(dt_utc)
    final_tidal_ts = final_tidal_ts.set_index(dt_utc)
# set tidal ts to 1e-4 for countries without tidal
final_tidal_ts.loc[:, (~final_tidal_ts.columns.get_level_values(level=0).isin(r_with_tidal), slice(None))] = 1e-4

"""
Generate hydro dam and hydro river ts from JRC-EFAS-Hydropower
"""
# read data and select ref_year
daily_ror_ts = pd.read_csv(ex_data_dir / 'gitignored' / 'hydro' / 'jrc-efas-hydropower-ror.csv',
                             header=0).rename(columns={'run_of_river_mwh' : 'HYDRO_RIVER'})
daily_ror_ts['date'] = pd.to_datetime(daily_ror_ts['date'])
daily_ror_ts = daily_ror_ts.pivot(columns='country_iso2', index='date')
# select date range and convert in GWh
daily_ror_ts = daily_ror_ts.loc[(str(ref_year - 1) + '-12-31') : (str(ref_year + 1) + '-01-01'), :] / 1000
# check f-max and ts concordance
ror_year_prod = daily_ror_ts.loc[str(ref_year), :].sum().droplevel(0)
ror_prod_max = (daily_ror_ts.max() / 24).droplevel(level=0)
ror_cp = ror_year_prod / (ror_prod_max * 8760)
ror_f_max = res_pot.loc[:, 'HYDRO_RIVER']
# resample and interpolate data to have 8760 points
hourly_ror_ts = (daily_ror_ts/24).resample('H').interpolate(method='time').shift(12, freq='H').loc[str(ref_year), :]
# swaplevel in columns and localize index
hourly_ror_ts = hourly_ror_ts.swaplevel(axis=1)
hourly_ror_ts.index = hourly_ror_ts.index.tz_localize(tz='UTC')
# get rid of 29/02 if leap year
if leap_yr:
    hourly_ror_ts = hourly_ror_ts.loc[~((hourly_ror_ts.index.month == 2) & (hourly_ror_ts.index.day == 29)), :]

# HYDRO_DAM inflow ts read data and select ref_year
weekly_dam_inflow_ts = pd.read_csv(ex_data_dir / 'gitignored' / 'hydro' / 'jrc-efas-hydropower-inflow.csv',
                             header=0).rename(columns={'inflow_mwh' : 'HYDRO_DAM'})
last_week = date(ref_year, 12, 28).isocalendar().week
last_week_previous_year = date(ref_year - 1, 12, 28).isocalendar().week
weekly_dam_inflow_ts = weekly_dam_inflow_ts.loc[((weekly_dam_inflow_ts['year'] == ref_year-1)
                                                 & (weekly_dam_inflow_ts['week'] == last_week_previous_year)) |
                                                ((weekly_dam_inflow_ts['year'] == ref_year)
                                                 & (weekly_dam_inflow_ts['week'] <= last_week)) |
                                                ((weekly_dam_inflow_ts['year'] == ref_year+1)
                                                 & (weekly_dam_inflow_ts['week'] == 1))
                                                , :]
# convert date format
weekly_dam_inflow_ts['date'] = pd.to_datetime(weekly_dam_inflow_ts\
    .apply(lambda row : date.fromisocalendar(int(row['year']), int(row['week']), 1), axis = 1))
weekly_dam_inflow_ts.drop(columns=['year', 'week'], inplace=True)
# pivot and convert into GWh
weekly_dam_inflow_ts = weekly_dam_inflow_ts.pivot(columns='country_iso2', index='date') / 1000

# check f-max and ts concordance
dam_year_prod = weekly_dam_inflow_ts.loc[str(ref_year), :].sum()
dam_prod_max = (weekly_dam_inflow_ts.max() / (24*7)).droplevel(level=0)
dam_cp = dam_year_prod / (dam_prod_max * 8760)
dam_f_max = res_pot.loc[:, 'HYDRO_DAM']
# resample and interpolate data to have 8760 points
hourly_dam_ts = (weekly_dam_inflow_ts/ (24 * 7)).resample('H').interpolate(method='time').shift(24*7/2, freq='H').loc[str(ref_year), :]
# swaplevel in columns and localize index
hourly_dam_ts = hourly_dam_ts.swaplevel(axis=1)
hourly_dam_ts.index = hourly_dam_ts.index.tz_localize(tz='UTC')
# get rid of 29/02 if leap year
if leap_yr:
    hourly_dam_ts = hourly_dam_ts.loc[~((hourly_dam_ts.index.month == 2) & (hourly_dam_ts.index.day == 29)), :]

"""
Import PECD Hydro time series (to compare with JRC)
"""
# read data and select ref_year
daily_ror_ts_pecd = pd.read_csv(ex_data_dir / 'gitignored' / 'hydro' / 'PECD-hydro-daily-ror-generation.csv',
                             header=0).rename(columns={'Run of River Hydro Generation in GWh per day' : 'HYDRO_RIVER'})

daily_ror_ts_pecd['date'] = pd.to_datetime(daily_ror_ts_pecd\
    .apply(lambda row : date(int(row['year']), 1, 1) + timedelta(days=int(row['Day']) - 1), axis = 1))
daily_ror_ts_pecd = daily_ror_ts_pecd.drop(columns=['Day', 'week', 'year']).pivot(columns='zone', index='date')
# select date range
daily_ror_ts_pecd = daily_ror_ts_pecd.loc[(str(ref_year - 1) + '-12-31') : (str(ref_year + 1) + '-01-01'), :]

# if ref_year - 1 is a leap year, should take into account the fact that the dataset doesn't have day 366...
if ((ref_year - 1) % 4 == 0):
    daily_ror_ts_pecd = pd.concat([daily_ror_ts_pecd.iloc[[0], :].set_index(pd.DatetimeIndex([(str(ref_year - 1) + '-12-31')],
                                                              freq='D')),
                                   daily_ror_ts_pecd])
# sum over each country
daily_ror_ts_pecd_country = pd.DataFrame(np.nan, index=daily_ror_ts_pecd.index,
                                         columns=pd.MultiIndex.from_product([['HYDRO_RIVER'],
                                                                              eu34_country_code_iso3166_alpha2]))
for r in eu34_country_code_iso3166_alpha2:
    daily_ror_ts_pecd_country.loc[:, (slice(None), r)] = daily_ror_ts_pecd.loc[:,
                                daily_ror_ts_pecd.columns.get_level_values(level=1).str.startswith(r)].sum(axis=1)
# check f-max and ts concordance
ror_year_prod_pecd = daily_ror_ts_pecd_country.loc[str(ref_year), :].sum().droplevel(0)
ror_prod_max_pecd = (daily_ror_ts_pecd_country.max() / 24).droplevel(level=0)
ror_cp_pecd = ror_year_prod_pecd / (ror_prod_max_pecd * 8760)
ror_f_max = res_pot.loc[:, 'HYDRO_RIVER']
ror_comp = pd.concat([ror_f_max, ror_prod_max, ror_prod_max_pecd], axis=1)
# resample and interpolate data to have 8760 points
hourly_ror_ts_pecd = (daily_ror_ts_pecd_country/24).resample('H').interpolate(method='time').shift(12, freq='H').loc[str(ref_year), :]
# swaplevel in columns and localize index
hourly_ror_ts_pecd = hourly_ror_ts_pecd.swaplevel(axis=1)
hourly_ror_ts_pecd.index = hourly_ror_ts_pecd.index.tz_localize(tz='UTC')
# get rid of 29/02 if leap year
if leap_yr:
    hourly_ror_ts_pecd = hourly_ror_ts_pecd.loc[~((hourly_ror_ts_pecd.index.month == 2) & (hourly_ror_ts_pecd.index.day == 29)), :]

# if ref_year is the last of the dataset, add last missing days of the year by taking the ones one week before
if ref_year == 2017:
    missing_dt = pd.date_range(start=list(hourly_ror_ts_pecd.index)[-1] + pd.to_timedelta(1, unit='h'),
                               end=pd.Timestamp(year=ref_year, month=12, day=31, hour=23, tz=pytz.utc, unit='h'),
                               freq='H', tz=pytz.utc)
    delta_t = int((pd.Timestamp(year=ref_year, month=12, day=31, hour=23, tz=pytz.utc, unit='h')
               - list(hourly_ror_ts_pecd.index)[-1]) / pd.Timedelta(hours=1))
    my_df = hourly_ror_ts_pecd.iloc[-delta_t:, :].set_index(missing_dt)
    hourly_ror_ts_pecd = pd.concat([hourly_ror_ts_pecd, my_df], axis=0)

# HYDRO_DAM inflow ts read data and select ref_year
weekly_dam_inflow_ts_pecd = pd.read_csv(ex_data_dir / 'gitignored' / 'hydro' / 'PECD-hydro-weekly-inflows.csv',
                             header=0).rename(columns={'Cumulated inflow into reservoirs per week in GWh' : 'HYDRO_DAM',
                                                       'Cumulated NATURAL inflow into the pump-storage reservoirs per week in GWh': 'PHS'})
last_week = date(ref_year, 12, 28).isocalendar().week
last_week_previous_year = date(ref_year - 1, 12, 28).isocalendar().week
weekly_dam_inflow_ts_pecd = weekly_dam_inflow_ts_pecd.loc[((weekly_dam_inflow_ts_pecd['year'] == ref_year-1)
                                                 & (weekly_dam_inflow_ts_pecd['week'] == last_week_previous_year)) |
                                                ((weekly_dam_inflow_ts_pecd['year'] == ref_year)
                                                 & (weekly_dam_inflow_ts_pecd['week'] <= last_week)) |
                                                ((weekly_dam_inflow_ts_pecd['year'] == ref_year+1)
                                                 & (weekly_dam_inflow_ts_pecd['week'] == 1))
                                                , :]

# convert date format
weekly_dam_inflow_ts_pecd['date'] = pd.to_datetime(weekly_dam_inflow_ts_pecd\
    .apply(lambda row : date.fromisocalendar(int(row['year']), int(row['week']), 4), axis = 1))
weekly_dam_inflow_ts_pecd.drop(columns=['year', 'week'], inplace=True)
# sum 2 data columns (assume all is HYDRO_DAM
weekly_dam_inflow_ts_pecd['HYDRO_DAM'] = weekly_dam_inflow_ts_pecd.loc[:, ['HYDRO_DAM', 'PHS']].sum(axis=1)

# pivot and convert into GWh
weekly_dam_inflow_ts_pecd = weekly_dam_inflow_ts_pecd.drop(columns=['PHS']).pivot(columns='zone', index='date')

# sum over each country
weekly_dam_inflow_ts_pecd_country = pd.DataFrame(np.nan, index=weekly_dam_inflow_ts_pecd.index,
                                         columns=pd.MultiIndex.from_product([['HYDRO_DAM'],
                                                                              eu34_country_code_iso3166_alpha2]))
for r in eu34_country_code_iso3166_alpha2:
    weekly_dam_inflow_ts_pecd_country.loc[:, (slice(None), r)] = weekly_dam_inflow_ts_pecd.loc[:,
                                weekly_dam_inflow_ts_pecd.columns.get_level_values(level=1).str.startswith(r)].sum(axis=1)

# check f-max and ts concordance
dam_year_prod_pecd = (weekly_dam_inflow_ts_pecd_country.loc[str(ref_year), :].sum()
                      ).droplevel(0)
dam_prod_max_pecd = (weekly_dam_inflow_ts_pecd_country.max() / (24 * 7)).droplevel(level=0)
dam_cp_pecd = dam_year_prod_pecd / (dam_prod_max_pecd * 8760)
dam_f_max = res_pot.loc[:, 'HYDRO_DAM']
dam_comp = pd.concat([dam_f_max, dam_prod_max, dam_prod_max_pecd], axis=1)
# resample and interpolate data to have 8760 points
hourly_dam_ts_pecd = (weekly_dam_inflow_ts_pecd_country / (24 * 7)).resample('H').interpolate(method='time').loc[str(ref_year), :]
# swaplevel in columns and localize index
hourly_dam_ts_pecd = hourly_dam_ts_pecd.swaplevel(axis=1)
hourly_dam_ts_pecd.index = hourly_dam_ts_pecd.index.tz_localize(tz='UTC')
# get rid of 29/02 if leap year
if leap_yr:
    hourly_dam_ts_pecd = hourly_dam_ts_pecd.loc[~((hourly_dam_ts_pecd.index.month == 2) & (hourly_dam_ts_pecd.index.day == 29)), :]

# if ref_year is the last of the dataset, add last missing days of the year by taking the ones one week before
if ref_year == 2017:
    missing_dt = pd.date_range(start=list(hourly_dam_ts_pecd.index)[-1] + pd.to_timedelta(1, unit='h'),
                               end=pd.Timestamp(year=ref_year, month=12, day=31, hour=23, tz=pytz.utc, unit='h'),
                               freq='H', tz=pytz.utc)
    delta_t = int((pd.Timestamp(year=ref_year, month=12, day=31, hour=23, tz=pytz.utc, unit='h')
               - list(hourly_dam_ts_pecd.index)[-1]) / pd.Timedelta(hours=1))
    my_df = hourly_dam_ts_pecd.iloc[-delta_t:, :].set_index(missing_dt)
    hourly_dam_ts_pecd = pd.concat([hourly_dam_ts_pecd, my_df], axis=0)

# Regrouping all hydro time series data,
# sources have been chosen based on avalaibility of data and inspection of ts with JRC-EFAS as default db
dam_from_pecd = ['AL', 'HR', 'XK']
dam_from_all_ts = ['CH']
dam_mapping = {'XK': 'RS'}
r_with_dam = list(res_pot.loc[res_pot.loc[:, 'HYDRO_DAM'] > 0.01, :].index)
r_without_dam = [i for i in eu34_country_code_iso3166_alpha2 if i not in r_with_dam]

ror_from_pecd = ['AL', 'BA', 'BE', 'GR', 'HR', 'HU', 'LT', 'LU', 'ME', 'MK', 'NL']
ror_from_all_ts = ['CH']
ror_mapping = {'SE': 'NO', 'EE': 'LV', 'DK': 'DE', 'XK': 'RS'}
r_with_ror = list(res_pot.loc[res_pot.loc[:, 'HYDRO_RIVER'] > 0.01, :].index)
r_without_ror = [i for i in eu34_country_code_iso3166_alpha2 if i not in r_with_ror]

# create and fill final_hydro_ts_df
final_hydro_ts = pd.DataFrame(np.nan, index=dt_utc,
                              columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2,
                                                                  ['HYDRO_DAM', 'HYDRO_RIVER']]))
final_hydro_ts.loc[:, hourly_dam_ts.columns] = hourly_dam_ts
final_hydro_ts.loc[:, (dam_from_pecd, 'HYDRO_DAM')] = hourly_dam_ts_pecd.loc[:, (dam_from_pecd, 'HYDRO_DAM')]
final_hydro_ts.loc[:, (dam_from_all_ts, 'HYDRO_DAM')] = all_ts.loc[:, (dam_from_all_ts, 'HYDRO_DAM')].values
final_hydro_ts.loc[:, (list(dam_mapping.keys()), 'HYDRO_DAM')] = final_hydro_ts.loc[:,
                                                             (list(dam_mapping.values()), 'HYDRO_DAM')].values
final_hydro_ts.loc[:, (r_without_dam, 'HYDRO_DAM')] = 1e-4

final_hydro_ts.loc[:, hourly_ror_ts.columns] = hourly_ror_ts
final_hydro_ts.loc[:, (ror_from_pecd, 'HYDRO_RIVER')] = hourly_ror_ts_pecd.loc[:, (ror_from_pecd, 'HYDRO_RIVER')]
final_hydro_ts.loc[:, (list(ror_mapping.keys()), 'HYDRO_RIVER')] = final_hydro_ts.loc[:,
                                                             (list(ror_mapping.values()), 'HYDRO_RIVER')].values
final_hydro_ts.loc[:, (r_without_ror, 'HYDRO_RIVER')] = 1e-4

# normalize time series
hydro_max_prod = final_hydro_ts.max(axis=0)
final_hydro_ts = final_hydro_ts.div(final_hydro_ts.max(axis=0), axis=1)

"""
Fill all ts with new values
"""
# creating and filling all_new_ts
ts_list = list(all_ts.columns.get_level_values(1).unique())
all_new_ts = pd.DataFrame(np.nan, index=dt_utc,
                          columns=pd.MultiIndex.from_product([eu34_country_code_iso3166_alpha2, ts_list]))
all_new_ts.loc[:, final_elec_ts.columns] = final_elec_ts
all_new_ts.loc[:, final_sh_ts.columns] = final_sh_ts
all_new_ts.loc[:, final_sc_ts.columns] = final_sc_ts
all_new_ts.loc[:, final_mob_ts.columns] = final_mob_ts
all_new_ts.loc[:, (slice(None), 'MOBILITY_FREIGHT')] = 1 / 8760
all_new_ts.loc[:, final_pv_ts.columns] = final_pv_ts
all_new_ts.loc[:, final_wind_ts.columns] = final_wind_ts
all_new_ts.loc[:, final_hydro_ts.columns] = final_hydro_ts
all_new_ts.loc[:, final_tidal_ts.columns] = final_tidal_ts
all_new_ts.loc[:, final_st_ts.columns] = final_st_ts
all_new_ts.loc[:, final_csp_ts.columns] = final_csp_ts

# checking validity of time series
if all_new_ts.isnull().values.any():
    print('There are NA values in the time series')

"""
Compute weights of time series for TD selection
"""
# 1 . For RES
# Import mapping of ts from Misc_indep
file = data_dir / str(proj_year) / '00_INDEP' / 'Misc_indep.json'
with open(file, 'r') as fp:
    data = json.load(fp)
ts_mapping = data['time_series_mapping']
res_with_ts = list(ts_mapping['res_params'].values()) \
              + [i for sublist in list(ts_mapping['res_mult_params'].values()) for i in sublist]
weights_all = res_pot.loc[:, res_with_ts].copy().T
# Regroup potentials by mapped ts
for i, j in ts_mapping['res_mult_params'].items():
    weights_all.loc[i, :] = weights_all.loc[j, :].sum()
    weights_all = weights_all.drop(j)
# dropping SOLAR and CSP as solar influence is already represented by PV
weights_all = weights_all.drop(index=['CSP', 'SOLAR'])

# 2. For demands
weights_demands_all = demands.loc[(proj_year, slice(None),
                                   ['ELECTRICITY', 'HEAT_LOW_T_SH', 'SPACE_COOLING']), :].sum(axis=1)\
    .droplevel(level=0, axis=0)
weights_demands_all = weights_demands_all.reset_index().pivot(index=['level_1'],
                                                              columns=['level_0']).droplevel(axis=1, level=0)
weights_all = pd.concat([weights_demands_all, weights_all], axis=0)

# mask with 1 or 0
weights_all = weights_all.mask(weights_all > 0.1, 1)
weights_all = weights_all.mask(weights <= 0.1, 0)

# change values for heating and cooling according to efficiency
weights_all.loc['HEAT_LOW_T_SH', :] *= 0.204
weights_all.loc['SPACE_COOLING', :] *= 0.087


"""
Plotting and saving
"""
# plotting all final time series
if plot_final:
    fig = px.line(all_new_ts.reset_index().melt(id_vars='index', var_name=['Regions', 'Time series']),
                  x='index', y='value', color='Regions', animation_frame='Time series',
                  markers='*-', title='Time series by category')
    fig.show()
    fig = px.line(all_new_ts.reset_index().melt(id_vars='index', var_name=['Regions', 'Time series']),
                  x='index', y='value', color='Time series', animation_frame='Regions',
                  markers='*-', title='Time series by region')
    fig.show()

if update_ts:
    all_new_ts.to_csv(ex_data_dir / 'regions' / ('Time_series_' + str(ref_year) + '.csv'), sep=CSV_SEPARATOR)
    weights_all.to_csv(ex_data_dir / 'regions' / 'Weights.csv', sep=CSV_SEPARATOR)

    for r in eu34_country_code_iso3166_alpha2:
        all_new_ts.loc[:, (r, slice(None))].droplevel(level=0, axis=1)\
            .to_csv(data_dir / str(proj_year) / r / 'Time_series.csv', sep=CSV_SEPARATOR)
        weights = weights_all.loc[:, r]
        weights.name = 'Weights'
        weights.index.name = 'Time_series'
        weights.to_csv(data_dir / str(proj_year) / r / 'Weights.csv', sep=CSV_SEPARATOR)

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
