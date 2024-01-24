# -*- coding: utf-8 -*-
"""
This script reads data from clever scenario,
computes the low end-uses demands (EUD) from it
and stores it into a csv

@author: Paolo Thiran
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from esmc.common import eu33_country_code_iso3166_alpha2, eu28_country_code, full_2_code, \
    CSV_SEPARATOR

# plotly imports
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
pio.renderers.default = 'browser'

# handles on scripts
plotting = True
corrections = True
saving = True

# path and file names
project_path = Path(__file__).parents[2]

clever_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\Data&Results CLEVER\extract_umair')
house_file = "clever_Residential_2050.csv"
ser_file = "clever_Tertairy_2050.csv"
agric_file = "clever_Agriculture_2050.csv"
ind_file = "clever_Industry_2050.csv"
transport_file = "clever_Transport_2050.csv"
macro_file = "clever_Macro_2050.csv"

ind_shares_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\Demand\data')
ind_shares_file = 'ind_shares.csv'

ned_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\NED')
ned_file = 'compute_ned.xlsx'

# creat df for results
eui_names = ['ELECTRICITY', 'HEAT_HIGH_T', 'HEAT_LOW_T_SH', 'HEAT_LOW_T_HW',
             'PROCESS_COOLING', 'SPACE_COOLING',
             'MOBILITY_PASSENGER', 'MOBILITY_FREIGHT', 'AVIATION_LONG_HAUL', 'SHIPPING',
             'NON_ENERGY']  # end-uses inputs
eui_categories = ['Electricity', 'Heat', 'Heat', 'Heat', 'Cold', 'Cold',
                  'Mobility', 'Mobility', 'Mobility', 'Mobility', 'Non-energy']
eui_subcat = ['Electricity', 'High temperature', 'Space heating', 'Hot water', 'Process cooling', 'Space cooling',
              'Passenger', 'Freight', 'Long-haul passenger flights', 'International shipping', 'Non-energy']
sector_names = ['HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION']
all_low_eud = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([eu33_country_code_iso3166_alpha2, eui_names]),
                           columns=sector_names)

# other input data
sc_elec_cop = 2.5 # COP of space cooling with electricity
pc_cop = 1 / 0.4965 # COP of process cooling

# read high eud data
years = np.arange(2015, 2055, 5)
all_eud = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([years, eu33_country_code_iso3166_alpha2, eui_names]),
                       columns=sector_names)
all_eud.update(pd.read_csv(project_path / 'Data' / 'exogenous_data' / 'regions' / 'Demands.csv',
                           header=0, index_col=[0, 1, 2], sep=CSV_SEPARATOR) / 1000)  # fill with existing values

"""
Computing HOUSEHOLDS EUD
"""
# READ DATA
house_data = pd.read_csv(clever_path / house_file, header=0, index_col=0, sep=CSV_SEPARATOR).sort_index()

house_final = all_low_eud.loc[(house_data.index, slice(None)), 'HOUSEHOLDS'].copy().reset_index() \
    .pivot(index='level_0', columns=['level_1']).droplevel(level=0, axis=1)

energy_carriers = ['solid fossil fuels', 'solid biomass', 'oil', 'gas',
                   'electricity', 'heating networks', 'ambient heat', 'thermal solar']

# COMPUTE ELEC EUD
house_final.loc[:, 'ELECTRICITY'] = house_data.loc[:,
                                    ['Total domestic consumption of specific electricity',
                                     'Total final energy consumption for domestic cooking']].sum(axis=1)

# COMPUTE SH EUD
house_sh_fec_names = [
    'Final energy consumption from solid fossil fuels (coal ...) for space heating in the residential sector',
    'Final energy consumption from solid biomass for space heating in the residential sector',
    'Final oil consumption for space heating in the residential sector',
    'Final energy consumption from gas grid / gas consumed locally for space heating in the residential sector',
    'Final electricity consumption for space heating in the residential sector',
    'Final energy consumption from heating networks for space heating in the residential sector',
    'Final energy consumption from ambient heat (heat pumps…) for space heating in the residential sector',
    'Final energy consumption from thermal solar for space heating in the residential sector']
house_sh_perf_names = ['Performance of domestic heating systems using solid fossil fuels (coal...)',
                       'Performance of domestic heating systems using solid biomass',
                       'Performance of domestic oil-fired heating systems',
                       'Performance of domestic heating systems using gas grid / gas consumed locally',
                       'Performance of domestic electric heating systems',
                       'Performance of domestic heating systems using heating network',
                       'Performance of domestic heating systems using ambient heat (heat pumps…)']

house_sh_fec = house_data.loc[:, house_data.columns.isin(house_sh_fec_names)]
house_sh_perf = house_data.loc[:, house_data.columns.isin(house_sh_perf_names)]

# renaming
house_sh_fec = house_sh_fec.rename(columns=dict(zip(house_sh_fec_names, energy_carriers)))
house_sh_perf = house_sh_perf.rename(columns=dict(zip(house_sh_perf_names, energy_carriers[:-1])))

# adding solar thermal in perf
house_sh_perf['thermal solar'] = 1

# correcting perf ambient heat = 1
house_sh_perf['ambient heat'] = 1

# computing eud = sum(fec * perf)
house_final.loc[:, 'HEAT_LOW_T_SH'] = house_sh_fec.mul(house_sh_perf).sum(axis=1)

# COMPUTING HW EUD
house_hw_fec_names = [
    'Final energy consumption from solid fossil fuels (coal ...) for domestic hot water',
    'Final energy consumption from solid biomass for domestic hot water',
    'Final oil consumption for domestic hot water',
    'Final energy consumption from gas grid / gas consumed locally for domestic hot water',
    'Final electricity consumption for domestic hot water',
    'Final energy consumption from heating networks for domestic hot water',
    'Final energy consumption from ambient heat (heat pumps…) for domestic hot water',
    'Final energy consumption from thermal solar for domestic hot water']
house_hw_perf_names = ['Performance of domestic water heaters using solid fossil fuels (coal...)',
                       'Performance of domestic water heaters using solid biomass',
                       'Performance of domestic oil-fired water heaters',
                       'Performance of domestic water heaters using gas grid / gas consumed locally',
                       'Performance of domestic electric water heaters',
                       'Performance of domestic water heaters using heating network',
                       'Performance of domestic thermodynamic water heaters']

house_hw_fec = house_data.loc[:, house_data.columns.isin(house_hw_fec_names)]
house_hw_perf = house_data.loc[:, house_data.columns.isin(house_hw_perf_names)]

# renaming
house_hw_fec = house_hw_fec.rename(columns=dict(zip(house_hw_fec_names, energy_carriers)))
house_hw_perf = house_hw_perf.rename(columns=dict(zip(house_hw_perf_names, energy_carriers[:-1])))

# adding solar thermal in perf
house_hw_perf['thermal solar'] = 1

# correcting perf ambient heat = 1
house_hw_perf['ambient heat'] = 1

# computing eud = sum(fec * perf)
house_final.loc[:, 'HEAT_LOW_T_HW'] = house_hw_fec.mul(house_hw_perf).sum(axis=1)

# COMPUTE SC EUD
house_final.loc[:, 'SPACE_COOLING'] = house_data.loc[:,
                                      'Final electricity consumption for cooling in the residential sector'] \
    .mul(house_data.loc[:, 'Performance of domestic cooling systems'])

# SET OTHER EUD AT 0 FOR HOUSEHOLDS
house_final.loc[:, ['AVIATION_LONG_HAUL', 'HEAT_HIGH_T', 'MOBILITY_FREIGHT', 'MOBILITY_PASSENGER',
                    'NON_ENERGY', 'PROCESS_COOLING', 'SHIPPING']] = 0

"""
Computing SERVICES EUD
"""
# READ DATA
# reading tertiary data
ser_data = pd.read_csv(clever_path / ser_file, header=0, index_col=0, sep=CSV_SEPARATOR).sort_index()

ser_final = all_low_eud.loc[(ser_data.index, slice(None)), 'SERVICES'].copy().reset_index() \
    .pivot(index='level_0', columns=['level_1']).droplevel(level=0, axis=1)

# reading agriculture data (put agric energy consumption is in services)
agric_data = pd.read_csv(clever_path / agric_file, header=0, index_col=0, sep=CSV_SEPARATOR).sort_index()

# COMPUTE ELEC EUD
ser_final.loc[:, 'ELECTRICITY'] = ser_data.loc[:, 'Total consumption of specific electricity in the tertiary sector']

# COMPUTE SC EUD
ser_final.loc[:, 'SPACE_COOLING'] = ser_data.loc[:,
                                    'Total final energy consumption for cooling in the tertiary sector'] \
    .mul(ser_data.loc[:, 'Performance of cooling systems (for the tertiary sectror)'])

# COMPUTE SH AND HW EUDs
# get all FEC by energy carrier (EC)
ser_fec_by_ec_names = ['Final energy consumption from solid fossil fuels (coal ...) in the tertiary sector.1',
                       'Final energy consumption from solid biomass in the tertiary sector.1',
                       'Final oil consumption in the tertiary sector.1',
                       'Final energy consumption from gas grid / gas consumed locally in the tertiary sector.1',
                       'Final electricity consumption in the tertiary sector',
                       'Final energy consumption from heating networks in the tertiary sector',
                       'Final energy consumption from ambient heat (heat pumps…) in the tertiary sector.1',
                       'Final energy consumption from thermal solar in the tertiary sector.1']
ser_fec_by_ec = ser_data.loc[:, ser_fec_by_ec_names]
ser_fec_by_ec = ser_fec_by_ec.rename(columns=dict(zip(ser_fec_by_ec_names, energy_carriers)))

# substract specific elec and cooling from FEC electricity consumption (and put to 0 if negative)
ser_fec_by_ec.loc[:, 'electricity'] += \
    -ser_data.loc[:, 'Total consumption of specific electricity in the tertiary sector'] \
    - ser_data.loc[:, 'Total final energy consumption for cooling in the tertiary sector']
ser_fec_by_ec = ser_fec_by_ec.mask(ser_fec_by_ec < 0, 0)

# compute shares by ec
ser_ec_shares = ser_fec_by_ec.div(ser_fec_by_ec.sum(axis=1), axis=0)

# split sh and hw fec according to shares
ser_sh_fec = ser_ec_shares.mul(ser_data.loc[:,
                               'Total final energy consumption for space heating in the tertiary sector (with climatic corrections) '],
                               axis=0)
ser_hw_fec = ser_ec_shares.mul(ser_data.loc[:,
                               'Total final energy consumption for hot water in the tertiary sector'], axis=0)

# get sh nd hw performances
ser_sh_perf_names = ['Performance of solid fossil fuels (coal...) based heating systems in the tertiary sector',
                     'Performance of solid-biomass based heating systems in the tertiary sector',
                     'Performance of oil heating systems in the tertiary sector',
                     'Performance of heating systems gas grid / gas consumed locally in the tertiary sector',
                     'Performance of electric heating systems in the tertiary sector',
                     'Performance of heating systems using heating network in the tertiary sector',
                     'Performance of ambient heat based heating systems (heat pumps…) in the tertiary sector']

ser_hw_perf_names = ['Performance of water heaters using solid fossil fuels (coal...) in the tertiary sector',
                     'Performance of water heaters using solid biomass in the tertiary sector',
                     'Performance of oil-fired water heaters in the tertiary sector',
                     'Performance of water heaters using gas grid / gas consumed locally in the tertiary sector',
                     'Performance of electric water heaters in the tertiary sector',
                     'Performance of water heaters using heating network in the tertiary sector',
                     'Performance of thermodynamic water heaters in the tertiary sector']

ser_sh_perf = ser_data.loc[:, ser_sh_perf_names]
ser_hw_perf = ser_data.loc[:, ser_hw_perf_names]

# renaming
ser_sh_perf = ser_sh_perf.rename(columns=dict(zip(ser_sh_perf_names, energy_carriers[:-1])))
ser_hw_perf = ser_hw_perf.rename(columns=dict(zip(ser_hw_perf_names, energy_carriers[:-1])))

# adding thermal solar in perf
ser_sh_perf['thermal solar'] = 1
ser_hw_perf['thermal solar'] = 1

# correcting perf ambient heat = 1
ser_sh_perf['ambient heat'] = 1
ser_hw_perf['ambient_heat'] = 1

# computing eud=sum(fec*perf)
ser_final.loc[:, 'HEAT_LOW_T_SH'] = ser_sh_fec.mul(ser_sh_perf).sum(axis=1)
ser_final.loc[:, 'HEAT_LOW_T_HW'] = ser_hw_fec.mul(ser_hw_perf).sum(axis=1)

# ADDING AGRICULTURE ENERGY CONSUMPTION
agric_elec_names = ['Final oil consumption in agriculture', 'Final electricity consumption in agriculture']
agric_hw_names = ['Final energy consumption from solid fossil fuels (coal ...) in agriculture',
                  'Final energy consumption from solid biomass in agriculture',
                  'Final energy consumption from gas grid / gas consumed locally in agriculture',
                  'Final energy consumption from thermal solar in agriculture',
                  'Final energy consumption from heating network in agriculture',
                  'Final energy consumption from ambient heat (heat pumps…) in agriculture']

ser_final.loc[:, 'ELECTRICITY'] += agric_data.loc[:, agric_elec_names].sum(axis=1)
ser_final.loc[:, 'HEAT_LOW_T_HW'] += agric_data.loc[:, agric_hw_names].sum(axis=1)

# SET OTHER EUD AT 0 FOR SERVICES
ser_final.loc[:, ['AVIATION_LONG_HAUL', 'HEAT_HIGH_T', 'MOBILITY_FREIGHT', 'MOBILITY_PASSENGER',
                  'NON_ENERGY', 'PROCESS_COOLING', 'SHIPPING']] = 0


"""
Computing INDUSTRY EUD
"""
# READ DATA
# read clever data
ind_data = pd.read_csv(clever_path / ind_file, header=0, index_col=0, sep=CSV_SEPARATOR).sort_index()

#  read ned_shares 2019 data (assuming similar values as 2015)
ned_2019 = pd.read_excel(ned_path / ned_file, sheet_name='results', header=1, index_col=0, usecols="A,P:R")
ned_2019.rename(index=full_2_code, inplace=True)
ned_2019.rename(index={'Czechia': 'CZ'}, inplace=True)
ned_2019.columns = ned_2019.columns.str.rstrip('.3')
ned_2019_tot = ned_2019.sum(axis=1)
ned_shares = ned_2019.div(ned_2019_tot, axis=0)
ned_shares.sort_index(inplace=True)

# read ind shares data (HRE4)
ind_shares = pd.read_csv(ind_shares_path / ind_shares_file, header=0, index_col=0, sep=CSV_SEPARATOR)

ind_final = all_low_eud.loc[(ind_data.index, slice(None)), 'INDUSTRY'].copy().reset_index() \
    .pivot(index='level_0', columns=['level_1']).droplevel(level=0, axis=1)

# COMPUTE INDUSTRIAL ENERGY FEC
# compute total industrial energy fec
ind_fec_names = ['Total Final energy consumption from solid fossil fuels (coal ...) in industry',
                 'Total Final energy consumption from solid biomass in industry',
                 'Total Final oil consumption in industry',
                 'Total Final energy consumption from gas grid / gas consumed locally in industry',
                 'Total Final electricity consumption in industry',
                 'Total Final heat consumption in industry',
                 'Total Final hydrogen consumption in industry',
                 'Total Final non-renewable waste consumption in industry',
                 'Total Final energy consumption from ambient heat (heat pumps…) in industry',
                 'Total Final energy consumption from thermal solar in industry']
ind_fec = ind_data.loc[:, ind_fec_names].sum(axis=1)

# correction for DE from CLEVER website
if corrections:
    ind_fec.loc['DE'] = 393.2

# divide with ind_shares
ind_final = ind_shares.mul(ind_fec, axis=0)

# multiply cooling demand by COP
ind_final.loc[:, 'SPACE_COOLING'] *= sc_elec_cop
ind_final.loc[:, 'PROCESS_COOLING'] *= pc_cop

# COMPUTE INDUSTRIAL NED
# ned reduction from clever documentation
ned_reduction = pd.Series([0.785, 0.785, 0.69], index=ned_shares.columns)
# compute ned in 2015 by category
ned_2015 = ned_shares.mul(all_eud.loc[(2015, ned_shares.index, 'NON_ENERGY'), 'INDUSTRY'].droplevel(level=2, axis=0) \
                          .droplevel(level=0, axis=0),
                          axis=0)

# compute ned in 2050 (and shares) based on reduction compared to 2015
ned_2050 = ned_2015.mul(ned_reduction, axis=1)
ned_shares_low_eud = ned_2050.div(ned_2050.sum(axis=1), axis=0)
ind_final.loc[:, 'NON_ENERGY'] = ned_2050.sum(axis=1)

"""
Computing TRANSPORTATION EUD
"""
# READ DATA
trans_data = pd.read_csv(clever_path / transport_file, header=0, index_col=0, sep=CSV_SEPARATOR).sort_index()

trans_final = all_low_eud.loc[(trans_data.index, slice(None)), 'SERVICES'].copy().reset_index() \
    .pivot(index='level_0', columns=['level_1']).droplevel(level=0, axis=1)

# COMPUTING MOBILITY_PASSENGER EUD
active_mob = 0.11
trans_final.loc[:, 'MOBILITY_PASSENGER'] = trans_data.loc[:, 'Total number of passenger-kilometres'] * (1 - active_mob)

# COMPUTING AVIATION_LONG_HAUL EUD
trans_final.loc[:, 'AVIATION_LONG_HAUL'] = trans_data.loc[:, 'Passenger-kilometres travelled on international flights']

# COMPUTING MOBILITY_FREIGHT EUD
trans_final.loc[:, 'MOBILITY_FREIGHT'] = trans_data.loc[:,
                                         ['Tonne-kilometres travelled by liquid fuels (diesel) trucks',
                                          'Tonne-kilometres travelled by LPG trucks',
                                          'Tonne-kilometres travelled by trucks running on NGV / biomethane',
                                          'Tonne-kilometres travelled by hydrogen trucks',
                                          'Tonne-kilometres travelled by electric trucks',
                                          'Tonne-kilometres transported by rail',
                                          'Total tonne-kilometres for national water freight transport']].sum(axis=1)

# COMPUTING SHIPPING EUD
trans_final.loc[:, 'SHIPPING'] = trans_data.loc[:, 'Total tonne-kilometres for international water freight transport']

# SET OTHER EUD TO 0 FOR TRANSPORTATION
trans_final.loc[:, ['ELECTRICITY', 'HEAT_HIGH_T', 'HEAT_LOW_T_HW',
                    'HEAT_LOW_T_SH', 'NON_ENERGY',
                    'PROCESS_COOLING', 'SPACE_COOLING']] = 0

"""
Fill result matrix
"""
all_low_eud.update(house_final.reset_index().melt(id_vars=['level_0'], var_name='level_1', value_name='HOUSEHOLDS')\
    .set_index(['level_0', 'level_1']))
all_low_eud.update(ser_final.reset_index().melt(id_vars=['level_0'], var_name='level_1', value_name='SERVICES')\
    .set_index(['level_0', 'level_1']))
all_low_eud.update(ind_final.reset_index().melt(id_vars=['index'], var_name='level_1', value_name='INDUSTRY')\
    .set_index(['index', 'level_1']))
all_low_eud.update(trans_final.reset_index().melt(id_vars=['level_0'], var_name='level_1', value_name='TRANSPORTATION')\
    .set_index(['level_0', 'level_1']))

"""
Cross-check matrices
"""
twh2kwh = 1e9
gpkm2pkm = 1e9
# import population in 2015 and 2050
pop_2015 = pd.read_excel(project_path / 'Data' / 'exogenous_data' / 'gitignored' / 'pop_2015-2022.xlsx',
                         sheet_name='Sheet 1',
                         header=9, index_col=0).drop(index=['GEO (Labels)']).loc[:, '2015']
pop_2050 = pd.read_excel(project_path / 'Data' / 'exogenous_data' / 'gitignored' / 'pop_proj.xlsx',
                         sheet_name='Sheet 1',
                         header=10, index_col=0).drop(index=['GEO (Labels)']).loc[:, '2050']

# rename and select eu 28
pop_2015.rename(index=full_2_code, inplace=True)
pop_2015.rename(index={'Czechia': 'CZ'}, inplace=True)
pop_2015 = pop_2015.loc[eu28_country_code]
pop_2015 = pop_2015.astype(int)
pop_2050.rename(index=full_2_code, inplace=True)
pop_2050 = pop_2050.loc[eu28_country_code]
pop_2050 = pop_2050.astype(int)

# 1. CHECK CORRIDORS
# insert corridors data from CLEVER report
corridors = pd.DataFrame(np.nan, index=['Min', 'Max'], columns=house_final.columns)
corridors.loc[:, 'ELECTRICITY'] = [400, 700]
corridors.loc[:, 'HEAT_LOW_T_SH'] = [800, 2400] # [32*25, 40*60] in [m²/pers]*[kWh/m²] = [kWh/pers]
corridors.loc[:, 'HEAT_LOW_T_HW'] = [270, 680]
corridors.loc[:, 'MOBILITY_PASSENGER'] = [9500.0, 13500.0]
corridors.loc[:, 'AVIATION_LONG_HAUL'] = [600, 1500]

# adding min and max cooking to elec in corridor
corridors.loc['Min', 'ELECTRICITY'] += (house_data.loc[:, 'Total final energy consumption for domestic cooking']
                                        .div(pop_2050, axis=0) * twh2kwh).min()
corridors.loc['Max', 'ELECTRICITY'] += (house_data.loc[:, 'Total final energy consumption for domestic cooking']
                                        .div(pop_2050, axis=0) * twh2kwh).max()

# substracting acitve mobility to passenger mob corridor
corridors.loc[:, 'MOBILITY_PASSENGER'] *= (1 - active_mob)

# compute per capita demand
house_final_percap = house_final.div(pop_2050, axis=0) * twh2kwh
house_elec_fec_percap = house_final_percap.loc[:, 'ELECTRICITY']
house_sh_fec_percap = house_sh_fec.sum(axis=1).div(pop_2050, axis=0) * twh2kwh
house_hw_fec_percap = house_hw_fec.sum(axis=1).div(pop_2050, axis=0) * twh2kwh

trans_final_percap = trans_final.div(pop_2050, axis=0) * gpkm2pkm

# PLOTTING
if plotting:
    # house elec specific
    fig = px.bar(house_elec_fec_percap.sort_values().reset_index(), x="index", y='ELECTRICITY', template='simple_white')
    fig.update_traces(marker_color='grey', marker_line_color='grey')
    fig.add_hline(y=corridors.loc['Min', 'ELECTRICITY'],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.add_hline(y=corridors.loc['Max', 'ELECTRICITY'],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Residential specific electricity and cooking per capita [kWh/pers]'),
        font=dict(
            family="Calibri",
            size=20
        )
    )
    fig.show()

    # house sh
    fig = px.bar(house_sh_fec_percap.sort_values().reset_index(), x="index", y=0, template='simple_white')
    fig.update_traces(marker_color='grey', marker_line_color='grey')
    fig.add_hline(y=corridors.loc['Min', 'HEAT_LOW_T_SH'],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.add_hline(y=corridors.loc['Max', 'HEAT_LOW_T_SH'],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Residential space heating per capita [kWh/pers]'),
        font = dict(
            family="Calibri",
            size=20
        )
    )
    fig.show()

    # house hw
    fig = px.bar(house_hw_fec_percap.sort_values().reset_index(), x="index", y=0, template='simple_white')
    fig.update_traces(marker_color='grey', marker_line_color='grey')
    fig.add_hline(y=corridors.loc['Min', 'HEAT_LOW_T_HW'],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.add_hline(y=corridors.loc['Max', 'HEAT_LOW_T_HW'],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Residential how water per capita [kWh/pers]'),
        font=dict(
            family="Calibri",
            size=20
        )
    )
    fig.show()

    # trans mob pass
    my_col = 'MOBILITY_PASSENGER'
    fig = px.bar(trans_final_percap.sort_values(by=my_col).reset_index(), x="index", y=my_col, template='simple_white')
    fig.update_traces(marker_color='grey', marker_line_color='grey')
    fig.add_hline(y=corridors.loc['Min', my_col],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.add_hline(y=corridors.loc['Max', my_col],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Passenger mobility per capita [pkm/pers]'),
        font=dict(
            family="Calibri",
            size=20
        )
    )
    fig.show()

    # trans av.
    my_col = 'AVIATION_LONG_HAUL'
    fig = px.bar(trans_final_percap.sort_values(by=my_col).reset_index(), x="index", y=my_col, template='simple_white')
    fig.update_traces(marker_color='grey', marker_line_color='grey')
    fig.add_hline(y=corridors.loc['Min', my_col],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.add_hline(y=corridors.loc['Max', my_col],
                  line_dash="dot", line_color="black", line_width=2, opacity=1)
    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Aviation per capita [pkm/pers]'),
        font=dict(
            family="Calibri",
            size=20
        )
    )
    fig.show()

# 2. COMPUTE TOTAL FEC AND FEC PER CAPITA PER SECTOR (to compare with paper clever)
house_fec = house_final.loc[:, 'ELECTRICITY'] \
            + house_sh_fec.sum(axis=1) + house_hw_fec.sum(axis=1) + \
            house_data.loc[:, 'Final electricity consumption for cooling in the residential sector']
ser_fec = ser_data.loc[:, ser_fec_by_ec_names].sum(axis=1)
agric_fec = agric_data.loc[:, agric_elec_names].sum(axis=1) + agric_data.loc[:, agric_hw_names].sum(axis=1)
trans_fec = trans_data.loc[:, 'Total final energy consumption in the transport sector']
tot_fec = house_fec + ser_fec + agric_fec + ind_fec + trans_fec # neglect ned, and int. mobility

house_fec_percap = house_fec.div(pop_2050, axis=0) * twh2kwh
tot_fec_percap = tot_fec.div(pop_2050, axis=0) * twh2kwh

if plotting:
    # plot
    my_col = 'AVIATION_LONG_HAUL'
    fig = px.bar((tot_fec_percap/1000).sort_values().reset_index(), x="index", y=0, template='simple_white')
    fig.update_traces(marker_color='grey', marker_line_color='grey')
    fig.update_layout(
        xaxis=dict(title='Countries'),
        yaxis=dict(title='Total FEC per capita [MWh/pers]'),
        font=dict(
            family="Calibri",
            size=20
        )
    )
    fig.show()

# 3. COMPARE EUD PER CAPITA WITH ESMC DATA
# take data 2015 and 2050 from ESMC
eud_2015 = all_eud.loc[(2015, eu28_country_code, slice(None)), :].droplevel(axis=0, level=0)
eud_2050 = all_eud.loc[(2050, eu28_country_code, slice(None)), :].droplevel(axis=0, level=0)
eud_2050_low = all_low_eud.loc[(eu28_country_code, slice(None)), :]

# compute total by end-uses input (eui) and by sector (sec
eud_eui_2015 = eud_2015.sum(axis=1).reset_index().pivot(index='level_0', columns='level_1').droplevel(axis=1, level=0)
eud_eui_2050 = eud_2050.sum(axis=1).reset_index().pivot(index='level_0', columns='level_1').droplevel(axis=1, level=0)
eud_eui_2050_low = eud_2050_low.sum(axis=1).reset_index().pivot(index='level_0', columns='level_1').droplevel(axis=1, level=0)
eud_sec_2015 = eud_2015.drop(columns=['TRANSPORTATION']).groupby(level=0).sum()
eud_sec_2050 = eud_2050.drop(columns=['TRANSPORTATION']).groupby(level=0).sum()
eud_sec_2050_low = eud_2050_low.drop(columns=['TRANSPORTATION']).groupby(level=0).sum()

eud_eui_all = pd.concat([eud_eui_2015.sum(axis=0),
           eud_eui_2050.sum(axis=0),
           eud_eui_2050_low.sum(axis=0)], axis=1)
eud_eui_all.columns = ['Actual', 'High demand', 'Low demand']

# per capita
eud_eui_2015_percap = eud_eui_2015.div(pop_2015, axis=0) * twh2kwh
eud_eui_2050_percap = eud_eui_2050.div(pop_2050, axis=0) * twh2kwh
eud_eui_2050_low_percap = eud_eui_2050_low.div(pop_2050, axis=0) * twh2kwh

eud_sec_2015_percap = eud_sec_2015.div(pop_2015, axis=0) * twh2kwh
eud_sec_2050_percap = eud_sec_2050.div(pop_2050, axis=0) * twh2kwh
eud_sec_2050_low_percap = eud_sec_2050_low.div(pop_2050, axis=0) * twh2kwh

eud_eui_all_percap = eud_eui_all.copy()
eud_eui_all_percap['Actual'] = eud_eui_all_percap['Actual'].div(pop_2015.sum()) * twh2kwh
eud_eui_all_percap.loc[:, ['High demand', 'Low demand']] = eud_eui_all_percap.loc[:, ['High demand', 'Low demand']]\
                                                               .div(pop_2050.sum()) * twh2kwh

# compute evolution from 2015 to 2050
ev_eud_eui_2050 = eud_eui_2050_percap / eud_eui_2015_percap
ev_eud_eui_2050_low = eud_eui_2050_low_percap / eud_eui_2015_percap
ev_eud_eui_all = eud_eui_all_percap.div(eud_eui_all_percap['Actual'], axis=0).drop(columns=['Actual'])

ev_eud_sec_2050 = eud_sec_2050_percap / eud_sec_2015_percap
ev_eud_sec_2050_low = eud_sec_2050_low_percap / eud_sec_2015_percap

# compute ratio low/high
ratio_eud_eui_2050 = eud_eui_2050_low / eud_eui_2050
ratio_eud_sec_2050 = eud_sec_2050_low /  eud_sec_2050

if plotting:
    # plotting
    df1 = ev_eud_eui_2050.reset_index().melt(id_vars='index', var_name='eui', value_name='eud')
    df1['scenario'] = 'High demand'
    df2 = ev_eud_eui_2050_low.reset_index().melt(id_vars='index', var_name='eui', value_name='eud')
    df2['scenario'] = 'Low demand'
    ev_eud_eui_2050_long = pd.concat([df1, df2], axis=0)

    fig = px.strip(ev_eud_eui_2050_long, x='eui', y='eud', color='scenario', hover_data=['index', 'eud'],
                   template='simple_white', color_discrete_map={'High demand': 'indianred', 'Low demand': 'seagreen'})
    fig.show()

    # fig = px.strip(ratio_eud_eui_2050.)

    # plotting
    df1 = eud_eui_2015_percap.reset_index().melt(id_vars='index', var_name='eui', value_name='eud')
    df1['scenario'] = 'Actual'
    df2 = eud_eui_2050_percap.reset_index().melt(id_vars='index', var_name='eui', value_name='eud')
    df2['scenario'] = 'High demand'
    df3 = eud_eui_2050_low_percap.reset_index().melt(id_vars='index', var_name='eui', value_name='eud')
    df3['scenario'] = 'Low demand'
    eud_eui_2050_percap_long = pd.concat([df1, df2, df3], axis=0)

    fig = px.strip(eud_eui_2050_percap_long, x='eui', y='eud', color='scenario', hover_data=['index', 'eud'],
                   template='simple_white',
                   color_discrete_map={'Actual': 'grey', 'High demand': 'indianred', 'Low demand': 'seagreen'})
    fig.show()

    for my_eui in eud_eui_2015_percap.columns:
        fig = go.Figure(data=[
            go.Bar(name='Actual', x=eud_eui_2015_percap.index, y=eud_eui_2015_percap[my_eui].values,
                   marker={'color':'grey'}),
            go.Bar(name='High demand', x=eud_eui_2015_percap.index, y=eud_eui_2050_percap[my_eui].values,
                   marker={'color':'indianred'}),
            go.Bar(name='Low demand', x=eud_eui_2015_percap.index, y=eud_eui_2050_low_percap[my_eui].values,
                   marker= {'color':'seagreen'})
        ])
        fig.add_hline(y=eud_eui_2015_percap[my_eui].mean(),
                      line_dash="dot", line_color="grey", line_width=2, opacity=1,
                      annotation_text="EU mean",
                      annotation_position="bottom right",
                      annotation_font_color = "grey"
                      )
        fig.add_hline(y=eud_eui_2050_percap[my_eui].mean(),
                      line_dash="dot", line_color="indianred", line_width=2, opacity=1,
                      annotation_text="EU mean",
                      annotation_position="bottom right",
                      annotation_font_color="indianred"
                      )
        fig.add_hline(y=eud_eui_2050_low_percap[my_eui].mean(),
                      line_dash="dot", line_color="seagreen", line_width=2, opacity=1,
                      annotation_text="EU mean",
                      annotation_position="bottom right",
                      annotation_font_color="seagreen"
                      )
        fig.update_layout(
            barmode='group',
            template='simple_white',
            xaxis=dict(title='Countries'),
            yaxis=dict(title='Total EUD in ' + my_eui.lower() +' per capita [MWh/pers]'),
            font=dict(
                family="Calibri",
                size=20
            )
        )
        fig.show()

    for my_sec in eud_sec_2015_percap.columns:
        fig = go.Figure(data=[
            go.Bar(name='Actual', x=eud_sec_2015_percap.index, y=eud_sec_2015_percap[my_sec].values,
                   marker={'color':'grey'}),
            go.Bar(name='High demand', x=eud_sec_2015_percap.index, y=eud_sec_2050_percap[my_sec].values,
                   marker={'color':'indianred'}),
            go.Bar(name='Low demand', x=eud_sec_2015_percap.index, y=eud_sec_2050_low_percap[my_sec].values,
                   marker={'color':'seagreen'})
        ])
        fig.add_hline(y=eud_sec_2015_percap[my_sec].mean(),
                      line_dash="dot", line_color="grey", line_width=2, opacity=1,
                      annotation_text="EU mean",
                      annotation_position="bottom right",
                      annotation_font_color = "grey"
                      )
        fig.add_hline(y=eud_sec_2050_percap[my_sec].mean(),
                      line_dash="dot", line_color="indianred", line_width=2, opacity=1,
                      annotation_text="EU mean",
                      annotation_position="bottom right",
                      annotation_font_color="indianred"
                      )
        fig.add_hline(y=eud_sec_2050_low_percap[my_sec].mean(),
                      line_dash="dot", line_color="seagreen", line_width=2, opacity=1,
                      annotation_text="EU mean",
                      annotation_position="bottom right",
                      annotation_font_color="seagreen"
                      )
        fig.update_layout(
            barmode='group',
            template='simple_white',
            xaxis=dict(title='Countries'),
            yaxis=dict(title='Total EUD in ' + my_sec.lower() +' per capita [MWh/pers]'),
            font=dict(
                family="Calibri",
                size=20
            )
        )
        fig.show()



    for my_eui in ev_eud_eui_2050.columns:
        fig = go.Figure(data=[
            go.Bar(name='High demand', x=ev_eud_eui_2050.index, y=ev_eud_eui_2050[my_eui].values,
                   marker={'color':'indianred'}),
            go.Bar(name='Low demand', x=ev_eud_eui_2050.index, y=ev_eud_eui_2050_low[my_eui].values,
                   marker={'color':'seagreen'})
        ])
        fig.add_hline(y=1,
                      line_dash="dot", line_color="black", line_width=2, opacity=1
                      )
        fig.update_layout(
            barmode='group',
            template='simple_white',
            xaxis=dict(title='Countries'),
            yaxis=dict(title='Evolution of EUD in ' + my_eui.lower()),
            font=dict(
                family="Calibri",
                size=20
            )
        )
        fig.update_layout()
        fig.show()

    for my_eui in ev_eud_sec_2050.columns:
        fig = go.Figure(data=[
            go.Bar(name='High demand', x=ev_eud_sec_2050.index, y=ev_eud_sec_2050[my_eui].values,
                   marker={'color':'indianred'}),
            go.Bar(name='Low demand', x=ev_eud_sec_2050.index, y=ev_eud_sec_2050_low[my_eui].values,
                   marker={'color':'seagreen'})
        ])
        fig.add_hline(y=1,
                      line_dash="dot", line_color="black", line_width=2, opacity=1
                      )
        fig.update_layout(
            barmode='group',
            template='simple_white',
            xaxis=dict(title='Countries'),
            yaxis=dict(title='Evolution of EUD in ' + my_eui.lower()),
            font=dict(
                family="Calibri",
                size=20
            )
        )
        fig.update_layout()
        fig.show()

"""
Correction in data according to analysis
"""
if corrections:
    # IE and LU have an anormally big aviation demand
    all_low_eud.loc[('IE', 'AVIATION_LONG_HAUL'), 'TRANSPORTATION'] = 9.8  # taken from CLEVER website
    all_low_eud.loc[('LU', 'AVIATION_LONG_HAUL'), 'TRANSPORTATION'] = 1.5 # taken from CLEVER website
    # move SH in residential for PT up to corridor
    all_low_eud.loc[('PT', 'HEAT_LOW_T_SH'), 'HOUSEHOLDS'] = 800/twh2kwh * pop_2050['PT']
    # correction of CH space cooling in services

    all_low_eud.loc[('CH', 'SPACE_COOLING'), 'SERVICES'] = all_low_eud.loc[('AT', 'SPACE_COOLING'), 'SERVICES']/ pop_2050['AT'] * pop_2050['CH']
    # correction of shipping demand takin evolution of GTkm from CLEVER and historical data from EUref (2015)
    ship_clever = pd.DataFrame(np.nan, index=trans_final.index, columns=[2015, 2050])
    ship_clever[2050] = trans_final.loc[:, 'SHIPPING']
    trans_data_2015 = pd.read_csv(clever_path / "clever_Transport_2015.csv",
                                  header=0, index_col=0, sep=CSV_SEPARATOR).sort_index()
    ship_clever[2015] = trans_data_2015.loc[:,
                                     'Total tonne-kilometres for international water freight transport']
    ship_clever_ev = (ship_clever[2050]).div(ship_clever[2015]).fillna(0)
    all_low_eud.loc[(slice(None), 'SHIPPING'), 'TRANSPORTATION'] =\
        all_eud.loc[(2015, slice(None), 'SHIPPING'), 'TRANSPORTATION']\
            .droplevel(level=0, axis=0).mul(ship_clever_ev, level=0)

if saving:
    all_low_eud.to_csv((project_path / 'Data' / 'exogenous_data' / 'regions' / 'Low_demands_2050.csv'),
                       sep=CSV_SEPARATOR)