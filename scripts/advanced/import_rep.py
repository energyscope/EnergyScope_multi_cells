# -*- coding: utf-8 -*-
"""
This script reads renewable energy potentials (REPs) data from external sources and puts it into csv Data

@author: Paolo Thiran
"""
import pandas as pd
import numpy as np
from pathlib import Path
from esmc.common import CSV_SEPARATOR
from esmc.utils.df_utils import clean_indices
import json

"""
Config of the script
"""
get_enspreso = True
read_dommisse = True
update_actual = True
print_update = True

# path
project_dir = Path(__file__).parents[2]
data_dir = project_dir / 'Data'
ex_data_dir = project_dir / 'Data' / 'exogenous_data'
dommisse_data = Path(r'C:\Users\pathiran\Documents\energy_system_modelling\ESTD\EnergyScope-EuropeanCountries2020')

# parameters
year_start = 2020
year_stop = 2035

# convert all the NED demand by this factor from comparison of Rixhon et al. and Dommisse et al. for BE demand
ratio_ned_BE = 53115.3311 / 102332.37

eu27_country_code = ['AT', 'BE', 'BG', #  'CH',
                     # Switzerland is not in data as not part of EU,
                     # for now, putting data of AT
                     'CZ', 'DE', 'DK', 'EE', 'ES', 'FI',
                     'FR', #not updating automatically FR as it is the reference country
                     # it should have data in another format
                     'GB', 'GR', 'HR', 'HU',
                     'IE', 'IT', 'LT', 'LU', 'LV', 'NL', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK']
eu27_full_names = ['Austria', 'Belgium', 'Bulgaria',  #'Switzerland',
                   'Czech Republic', 'Germany', 'Denmark', 'Estonia', 'Spain', 'Finland', #
                   'France',
                   'United Kingdom',
                   'Greece', 'Croatia', 'Hungary', 'Ireland', 'Italy', 'Lithuania', 'Luxembourg', 'Latvia',
                   'Netherlands', 'Poland', 'Portugal', 'Romania', 'Sweden', 'Slovenia', 'Slovakia']
# Switzerland is missing from ENSPRESSO... + getting rid of EU28, Cyprus, Malta
full_2_code = dict(zip(eu27_full_names, eu27_country_code))
code_2_full = dict(zip(eu27_country_code, eu27_full_names))

"""
ENSPRESO DATA
"""
if get_enspreso:
    # config
    enspreso_dir = ex_data_dir / 'ENSPRESO'
    enspreso_sce_wind = 'Reference - Large turbines'  # enspreso scenario considered for wind turbines
    won_min_cf = 20  # minimun capacity factor [%] for WIND ONSHORE, acceptable values are (15,20,25)
    # the 170 W/m2 = 0.170 GW/km2,
    # is an assumption they take for all solar techs considered here (PV_rooftop, PV_ground and CSP)
    enspreso_solar_sce = 'MS 170 W per m2 and 3%'
    power_density_pv = 0.170  # Density to install pv panels and csp [GW_p/km2]
    power_density_solar_thermal = 0.7  # Density to install rooftop solar thermal panels [GW_p/km2]
    eta_pb_pt = 0.4304  # efficiency power block csp
    eta_pb_st = 0.4783  # efficiency power block csp

    power_density_pt_coll = power_density_pv / eta_pb_pt  # [GW_th/km2] for Parabolic Trough
    power_density_st_coll = power_density_pv / eta_pb_st  # [GW_th/km2] for Solar tower

    # classifiaciton of solar poential inputs from ENSPRESO
    rooftop_cat = ['residential areas roof-top 45 degree south',
                   'residential areas roof-top 45 degree east',
                   'residential areas roof-top 45 degree west',
                   'residential areas roof-top latitude tilt',
                   'residential areas facade south', 'residential areas facade east',
                   'residential areas facade west',
                   'industrial areas roof-top 45 degree south',
                   'industrial areas roof-top 45 degree east',
                   'industrial areas roof-top 45 degree west',
                   'industrial areas roof-top latitude tilt',
                   'industrial areas facade south', 'industrial areas facade east',
                   'industrial areas facade west']
    ground_cat = ['natural areas agriculture high irradiation',
                  'natural areas agriculture low irradiation',
                  'natural areas non-agriculture high irradiation',
                  'natural areas non-agriculture low irradiation']
    ground_high_irr_cat = ['natural areas agriculture high irradiation',
                           'natural areas non-agriculture high irradiation']

    # ENSPRESO wind potentials
    won_pot = pd.read_excel(io=enspreso_dir / 'ENSPRESO_WIND_ONSHORE_OFFSHORE.xlsx',
                            sheet_name='ONSHORE SUMMARY + graph',
                            header=[2, 3], index_col=[19], nrows=29).dropna(how='all', axis=1)
    wof_pot = pd.read_excel(io=enspreso_dir / 'ENSPRESO_WIND_ONSHORE_OFFSHORE.xlsx',
                            sheet_name='OFFSHORE SUMMARY + graph',
                            header=[2, 3], index_col=[19], nrows=23).dropna(how='all', axis=1)

    # selecting potentials according to scenario and hypothesis
    if won_min_cf >= 25:
        won_pot = won_pot.loc[:, (enspreso_sce_wind, 'CF > 25%')].sum(axis=1)
    elif won_min_cf >= 20:
        # won_pot = won_pot.loc[:,(enspreso_sce_wind, ['CF > 25%', '20% < CF < 25%'])].sum(axis=1)
        sequence = ['CF > 25%', '20% < CF < 25%']
        won_pot = won_pot.loc[:, (enspreso_sce_wind, won_pot.columns.isin(sequence, level=1))].sum(axis=1)
    else:
        won_pot = won_pot.loc[:, (enspreso_sce_wind, slice(None))].sum(axis=1)

    wof_pot = wof_pot.loc[:, (enspreso_sce_wind, slice(None))].sum(axis=1)

    # ENSPRESO solar potentials
    solar_pot = pd.read_excel(io=enspreso_dir / 'ENSPRESO_SOLAR_PV_CSP.xlsx', sheet_name=enspreso_solar_sce,
                              header=[4], index_col=[1], nrows=20).drop(columns=['Technology']) \
        .dropna(how='all', axis=1).dropna(how='all', axis=0) \
        .rename(columns={'Hungaria': 'Hungary', 'Luxemburg': 'Luxembourg'})
    # convert in km2 and compute different solar areas
    solar_pot_km2 = solar_pot / power_density_pv
    solar_area = pd.DataFrame(np.nan, index=['solar_area_rooftop', 'solar_area_ground', 'solar_area_ground_high_irr'],
                              columns=solar_pot_km2.columns)
    solar_area.loc['solar_area_rooftop', :] = solar_pot_km2.loc[rooftop_cat, :].sum()
    solar_area.loc['solar_area_ground', :] = solar_pot_km2.loc[ground_cat, :].sum()
    solar_area.loc['solar_area_ground_high_irr', :] = solar_pot_km2.loc[ground_high_irr_cat, :].sum()

    solar_tech = ['PV_ROOFTOP', 'PV_UTILITY',
                  'PT_POWER_BLOCK', 'ST_POWER_BLOCK', 'PT_COLLECTOR', 'ST_COLLECTOR',
                  'DHN_SOLAR', 'DEC_SOLAR']
    # compute equivalent potentials in GW
    solar_pot_esmc = pd.DataFrame(np.nan, index=solar_tech, columns=solar_area.columns)
    solar_pot_esmc.loc['PV_ROOFTOP', :] = solar_area.loc['solar_area_rooftop', :] * power_density_pv
    solar_pot_esmc.loc['PV_UTILITY', :] = solar_area.loc['solar_area_ground', :] * power_density_pv
    solar_pot_esmc.loc['PT_POWER_BLOCK', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_pv
    solar_pot_esmc.loc['ST_POWER_BLOCK', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_pv
    solar_pot_esmc.loc['PT_COLLECTOR', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_pt_coll
    solar_pot_esmc.loc['ST_COLLECTOR', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_st_coll
    solar_pot_esmc.loc['DHN_SOLAR', :] = solar_area.loc['solar_area_rooftop', :] * power_density_solar_thermal
    solar_pot_esmc.loc['DEC_SOLAR', :] = solar_area.loc['solar_area_rooftop', :] * power_density_solar_thermal

    # regroup in esmc_pot
    res_pot_esmc = pd.concat([solar_pot_esmc, pd.DataFrame(won_pot, columns=['WIND_ONSHORE']).T], axis=0)
    res_pot_esmc = pd.concat([res_pot_esmc, pd.DataFrame(wof_pot, columns=['WIND_OFFSHORE']).T], axis=0).fillna(0)

"""
Data from Dommisse et al.
"""
# tech considered (ordered)
ordered_tech_res = ['NUCLEAR',
 'PV_ROOFTOP', 'PV_UTILITY',
 'PT_POWER_BLOCK', 'ST_POWER_BLOCK', 'PT_COLLECTOR', 'ST_COLLECTOR',
 'WIND_ONSHORE', 'WIND_OFFSHORE',
 'HYDRO_DAM', 'HYDRO_RIVER',
 'NEW_TIDAL_STREAM', 'TIDAL_STREAM', 'TIDAL_RANGE', 'WAVE',
 'GEOTHERMAL', 'DHN_DEEP_GEO',
 'DHN_SOLAR', 'DEC_SOLAR',
 'DAM_STORAGE', 'PHS']
# tech to get from Dommisse
tech2get = ordered_tech_res.copy()
tech2get.append('PV')
tech2get.remove('PV_ROOFTOP')
tech2get.remove('PV_UTILITY')
# resources to get
res2get = ['WOOD', 'WET_BIOMASS', 'WASTE']

# creating dataframes to gather all data
demands_all = pd.DataFrame(np.nan,
                           index=pd.MultiIndex.from_product([['ELECTRICITY', 'ELECTRICITY_VAR',
                                                              'HEAT_HIGH_T', 'HEAT_LOW_T_SH', 'HEAT_LOW_T_HW',
                                                              'PROCESS_COOLING', 'SPACE_COOLING',
                                                              'MOBILITY_PASSENGER', 'MOBILITY_FREIGHT', 'NON_ENERGY'],
                                                             eu27_country_code]),
                           columns=['Category', 'Subcategory',
                                    'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION ',
                                    'Units'])
resources_all = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([['avail_local', 'c_op_local'],eu27_country_code]),
                             columns=res2get)
sto_all = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([['PHS'], eu27_country_code]),
                       columns=['storage_charge_time', 'storage_discharge_time'])
tech_all = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([['f_min', 'f_max'], eu27_country_code]),
                        columns=ordered_tech_res)

for r, r_full in code_2_full.items():
    if read_dommisse:
        print('Read Dommisse et al. ' + r_full)
        # read technologies f_min and f_max from data of J&JL
        tech_dommisse = clean_indices(pd.read_excel(dommisse_data / r / 'Data_management' / 'DATA.xlsx', sheet_name='3.2 TECH',
                                      header=[0], index_col=[1], nrows=115).loc[tech2get, ['f_min', 'f_max:=']] \
            .rename(columns={'f_max:=': 'f_max'}))
        # split PV into PV_ROOFTOP and PV_UTILITY by keeping the installed capacity into PV_ROOFTOP
        tech_dommisse.rename(index={'PV': 'PV_ROOFTOP'}, inplace=True)
        tech_dommisse.loc['PV_UTILITY', :] = 0

        if r_full=='Switzerland':
            solar_area['Switzerland'] = 0
            solar_area.loc['solar_area_rooftop', 'Switzerland'] =\
                tech_dommisse.loc['PV_ROOFTOP', 'f_max'] / power_density_pv


        # read resources
        resources_dommisse = clean_indices(pd.read_excel(dommisse_data / r / 'Data_management' / 'DATA.xlsx', sheet_name='2.1 RESOURCES',
                                           header=[1], index_col=[0], nrows=26) \
            .rename(columns={'Unnamed: 1': 'avail_local', 'c_op [M€/GWh]': 'c_op_local'}) \
            .loc[res2get, ['avail_local', 'c_op_local']])

        # read demands
        # TODO get rid of ELECTRICITY_VAR
        demands_dommisse = clean_indices(pd.read_excel(dommisse_data / r / 'Data_management' / 'DATA.xlsx', sheet_name='2.3 EUD',
                                         header=[1], index_col=[0], nrows=10) \
            .rename(index={'LIGHTING': 'ELECTRICITY_VAR'}).rename(columns={'Unnamed: 5': 'Units'}))
        demands_dommisse.loc[['PROCESS_COOLING', 'SPACE_COOLING'], 'Units'] = '[GWh]'
        # rescaling the NED demand as we consider demand in alredy transformed products (HVC, Ammonia and Methanol)
        demands_dommisse.loc['NON_ENERGY', 'INDUSTRY'] = ratio_ned_BE * demands_dommisse.loc['NON_ENERGY', 'INDUSTRY']

        # read storage
        sto_dommisse = clean_indices(pd.read_excel(dommisse_data / r / 'Data_management' / 'DATA.xlsx', sheet_name='3.3 STO',
                                     header=[59], index_col=0, nrows=3) \
            .loc[['PHS'], ['storage_charge_time', 'storage_discharge_time']])
        sto_dommisse.index.name = 'Storage'

    """
    Update and print actual data
    """
    if update_actual:
        r_path = data_dir / str(year_stop) / r

        # add columns defining demand
        demands_new = clean_indices(pd.read_csv(r_path / 'Demands.csv', header=[0], index_col=[2], sep=CSV_SEPARATOR))
        demands_new.update(demands_dommisse)


        # get misc (for now only solar_area)
        misc_new = solar_area.loc[:, r_full].to_dict()

        # resource new
        resources_new = resources_dommisse.copy()
        resources_new.index.name = 'parameter name'

        # sto new
        sto_new = sto_dommisse.copy()

        # update the data for the res pot reevaluted
        if r_full=='Switzerland':
            tech_new = tech_dommisse.copy()
        else:
            my_df = res_pot_esmc.loc[:, r_full].to_frame(name='f_max')
            tech_new = tech_dommisse.copy()
            tech_new.update(my_df)
        ordered_tech_res = ['NUCLEAR',
                            'PV_ROOFTOP', 'PV_UTILITY',
                            'PT_POWER_BLOCK', 'ST_POWER_BLOCK', 'PT_COLLECTOR', 'ST_COLLECTOR',
                            'WIND_ONSHORE', 'WIND_OFFSHORE',
                            'HYDRO_DAM', 'HYDRO_RIVER',
                            'NEW_TIDAL_STREAM', 'TIDAL_STREAM', 'TIDAL_RANGE', 'WAVE',
                            'GEOTHERMAL', 'DHN_DEEP_GEO',
                            'DHN_SOLAR', 'DEC_SOLAR',
                            'DAM_STORAGE', 'PHS']
        tech_new = tech_new.loc[ordered_tech_res, :]
        tech_new.index.name = 'Technologies param'

        # update weights according to the potential for res
        file = data_dir / str(year_stop) / '00_INDEP' / 'Misc_indep.json'
        with open(file, 'r') as fp:
            data = json.load(fp)
        ts_mapping = data['time_series_mapping']
        res_with_ts = list(ts_mapping['res_params'].values()) \
                      + [i for sublist in list(ts_mapping['res_mult_params'].values()) for i in sublist]
        weights = tech_new.loc[res_with_ts, ['f_max']].copy().rename(columns={'f_max': 'Weights'})
        weights.index.name = 'Time_series'
        for i, j in ts_mapping['res_mult_params'].items():
            weights.loc[i, :] = weights.loc[j, :].sum()
            weights = weights.drop(j)
        weights = weights.mask(weights > 0.1, 1)
        weights = weights.mask(weights <= 0.1, 0)
        # add space cooling
        if demands_new.loc['SPACE_COOLING', ['HOUSEHOLDS', 'SERVICES', 'INDUSTRY']].sum() > 0.1:
            weights.loc['SPACE_COOLING'] = 0.087
        else:
            weights.loc['SPACE_COOLING'] = 0
            # update new
        weights_new = clean_indices(pd.read_csv(r_path / 'Weights.csv', header=[0], index_col=[0], sep=CSV_SEPARATOR))
        weights_new.update(weights)

        # save into dataframes all
        demands_all.loc[(slice(None), r), :] = demands_new.values
        resources_all.loc[(slice(None), r), :] = resources_new.T.values
        sto_all.loc[(slice(None), r), :] = sto_new.values
        tech_all.loc[(slice(None), r), :] = tech_new.T.values

        if print_update and r!='FR':
            print('print update ' + r_full)
            demands_new.reset_index().set_index(['Category', 'Subcategory', 'parameter name'])\
                .to_csv(r_path / 'Demands.csv', sep=CSV_SEPARATOR)
            misc_f = r_path / 'Misc.json'
            with open(misc_f, mode='w') as my_file:
                json.dump(misc_new, my_file, indent=6)
            resources_new.to_csv(r_path / 'Resources.csv', sep=CSV_SEPARATOR)
            sto_new.to_csv(r_path / 'Storage_power_to_energy.csv', sep=CSV_SEPARATOR)
            tech_new.to_csv(r_path / 'Technologies.csv', sep=CSV_SEPARATOR)
            weights_new.to_csv(r_path / 'Weights.csv', sep=CSV_SEPARATOR)

if update_actual:
    # save into dataframes all
    demands_all.to_csv(ex_data_dir / 'regions' / 'Demands.csv', sep=CSV_SEPARATOR)
    resources_all.to_csv(ex_data_dir / 'regions' / 'Resources.csv', sep=CSV_SEPARATOR)
    sto_all.to_csv(ex_data_dir / 'regions' / 'Storage_power_to_energy.csv', sep=CSV_SEPARATOR)
    tech_all.to_csv(ex_data_dir / 'regions' / 'Technologies.csv', sep=CSV_SEPARATOR)