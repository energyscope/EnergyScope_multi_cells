# -*- coding: utf-8 -*-
"""
This script reads renewable energy potentials (REPs) data from external sources and puts it into csv Data

@author: Paolo Thiran
"""
import pandas as pd
import numpy as np
from pathlib import Path
from esmc.common import CSV_SEPARATOR, eu34_country_code_iso3166_alpha2, eu34_country_code_eurostat, eu34_full_names
from esmc.utils.df_utils import clean_indices
import json


eu33_country_code_iso3166_alpha2 = eu34_country_code_iso3166_alpha2.copy()
eu33_country_code_iso3166_alpha2.remove('XK')
eu33_country_code_eurostat = eu34_country_code_eurostat.copy()
eu33_country_code_eurostat.remove('XK')
eu33_full_names = eu34_full_names.copy()
eu33_full_names.remove('Kosovo')

"""
Config of the script
"""
get_enspreso = True
compute_hydro = True
update_actual = True
print_update = False

# path
project_dir = Path(__file__).parents[2]
data_dir = project_dir / 'Data'
ex_data_dir = project_dir / 'Data' / 'exogenous_data'
installed_capa_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\Installed_capacity_elec\nrg_inf_epcrw_page_spreadsheet.xlsx')

# parameters
year_start = 2020
year_stop = 2050

# convert all the NED demand by this factor from comparison of Rixhon et al. and Dommisse et al. for BE demand
ratio_ned_BE = 53115.3311 / 102332.37

# power density of solar techs
power_density_pv = 0.170  # Density to install pv panels and csp [GW_p/km2]
power_density_solar_thermal = 0.7  # Density to install rooftop solar thermal panels [GW_p/km2]
eta_pb_pt = 0.4304  # efficiency power block csp
eta_pb_st = 0.4783  # efficiency power block csp

power_density_pt_coll = power_density_pv / eta_pb_pt  # [GW_th/km2] for Parabolic Trough
power_density_st_coll = power_density_pv / eta_pb_st  # [GW_th/km2] for Solar tower


# country codes (Switzerland is missing from ENSPRESSO... + getting rid of EU28, Cyprus, Malta)
eu27_country_code = ['AT', 'BE', 'BG', #  'CH',
                     # Switzerland is not in data as not part of EU,
                     'CZ', 'DE', 'DK', 'EE', 'ES', 'FI',
                     'FR',
                     'GB', 'GR', 'HR', 'HU',
                     'IE', 'IT', 'LT', 'LU', 'LV', 'NL', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK']
eu27_full_names = ['Austria', 'Belgium', 'Bulgaria',  #'Switzerland',
                   'Czech Republic', 'Germany', 'Denmark', 'Estonia', 'Spain', 'Finland', #
                   'France',
                   'United Kingdom',
                   'Greece', 'Croatia', 'Hungary', 'Ireland', 'Italy', 'Lithuania', 'Luxembourg', 'Latvia',
                   'Netherlands', 'Poland', 'Portugal', 'Romania', 'Sweden', 'Slovenia', 'Slovakia']
code_2_full = dict(zip(eu34_country_code_iso3166_alpha2, eu34_full_names))
full_2_code = dict(zip(eu34_full_names, eu34_country_code_iso3166_alpha2))

"""
Get actual data for all regions
"""
# creating dataframes to gather all data
resources_all = pd.read_csv(ex_data_dir / 'regions' / 'Resources.csv', index_col=[0, 1], header=0, sep=CSV_SEPARATOR)
sto_all = pd.read_csv(ex_data_dir / 'regions'/ 'Storage_power_to_energy.csv',
                      index_col=[0, 1], header=0, sep=CSV_SEPARATOR)
tech_all = pd.read_csv(ex_data_dir / 'regions' / 'Technologies.csv', index_col=[0, 1], header=0, sep=CSV_SEPARATOR)

"""
ENSPRESO DATA: Biomass, wind and solar
"""
if get_enspreso or update_actual or print_update:
    # config
    enspreso_dir = ex_data_dir / 'ENSPRESO'
    enspreso_sce_wind = 'Reference - Large turbines'  # enspreso scenario considered for wind turbines
    won_min_cf = 20  # minimun capacity factor [%] for WIND ONSHORE, acceptable values are (15,20,25)
    # the 170 W/m2 = 0.170 GW/km2,
    # is an assumption they take for all solar techs considered here (PV_rooftop, PV_ground and CSP)
    enspreso_solar_sce = 'MS 170 W per m2 and 3%'

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

    # biomass config
    r_biom = eu33_country_code_eurostat
    year_biom = 2050 # we take 2050 as reference year for biomass potentials

    enspreso_biomass_sce = 'ENS_Med'
    categories = {
        'WOOD': ['MINBIOWOO', 'MINBIOWOOa', 'MINBIOWOOW1', 'MINBIOWOOW1a', 'MINBIOFRSR1' , 'MINBIOFRSR1a'],
        'WET_BIOMASS': ['MINBIOSLU1', 'MINBIOGAS1'],
        'ENERGY_CROPS_2': ['MINBIOCRP31', 'MINBIOCRP41', 'MINBIOCRP41a'],
        'BIOWASTE': ['MINBIOMUN1'],
        'BIOMASS_RESIDUES': ['MINBIOAGRW1']
    }
    pj_2_gwh = 1/3600*1e15/1e9 # [GWh/PJ]
    eff_minbioslu1 = 1/3.3462 # [GWh_biogas/GWh_feedstock]


    # 1. ENSPRESO wind potentials
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
        sequence = ['CF > 25%', '20%  < CF < 25%']
        won_pot = won_pot.loc[:, (enspreso_sce_wind, won_pot.columns.isin(sequence, level=1))].sum(axis=1)
    else:
        won_pot = won_pot.loc[:, (enspreso_sce_wind, slice(None))].sum(axis=1)

    wof_pot = wof_pot.loc[:, (enspreso_sce_wind, slice(None))].sum(axis=1)

    # 2. ENSPRESO solar potentials
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
    solar_pot_ensp = pd.DataFrame(np.nan, index=solar_tech, columns=solar_area.columns)
    solar_pot_ensp.loc['PV_ROOFTOP', :] = solar_area.loc['solar_area_rooftop', :] * power_density_pv
    solar_pot_ensp.loc['PV_UTILITY', :] = solar_area.loc['solar_area_ground', :] * power_density_pv
    solar_pot_ensp.loc['PT_POWER_BLOCK', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_pv
    solar_pot_ensp.loc['ST_POWER_BLOCK', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_pv
    solar_pot_ensp.loc['PT_COLLECTOR', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_pt_coll
    solar_pot_ensp.loc['ST_COLLECTOR', :] = solar_area.loc['solar_area_ground_high_irr', :] * power_density_st_coll
    solar_pot_ensp.loc['DHN_SOLAR', :] = solar_area.loc['solar_area_rooftop', :] * power_density_solar_thermal
    solar_pot_ensp.loc['DEC_SOLAR', :] = solar_area.loc['solar_area_rooftop', :] * power_density_solar_thermal

    # regroup in esmc_pot
    res_pot_ensp = pd.concat([solar_pot_ensp, pd.DataFrame(won_pot, columns=['WIND_ONSHORE']).T], axis=0)
    res_pot_ensp = pd.concat([res_pot_ensp, pd.DataFrame(wof_pot, columns=['WIND_OFFSHORE']).T], axis=0).fillna(0)
    # countries names to 2-letter code and dropping EU28
    res_pot_ensp = res_pot_ensp.rename(columns=full_2_code).drop(columns=['EU28', 'Cyprus', 'Malta'])

    # 3. ENSPRESO biomass potentials
    biomass_pot = pd.read_excel(io=enspreso_dir / 'ENSPRESO_BIOMASS.xlsx',
                                sheet_name='ENER - NUTS0 EnergyCom',
                                header=[0])
    biomass_costs = pd.read_excel(io=enspreso_dir / 'ENSPRESO_BIOMASS.xlsx',
                                  sheet_name='COST - NUTS0 EnergyCom',
                                  header=[0])
    # correct error in the input data (missing data in 2030 is average between equivalent data in 2020 and 2040
    biomass_costs.loc[(biomass_costs['Year'] == 2030) & (biomass_costs['Scenario'] == 'ENS_High') &
                      (biomass_costs['NUTS0'] == 'NO') & (biomass_costs['Energy Commodity'] == 'MINBIOMUN1'),
    'NUTS0 Energy Commodity Cost '] = (biomass_costs.loc[(biomass_costs['Year'] == 2020)
                                                         & (biomass_costs['Scenario'] == 'ENS_High')
                                                         & (biomass_costs['NUTS0'] == 'NO')
                                                         & (biomass_costs['Energy Commodity'] == 'MINBIOMUN1'),
    'NUTS0 Energy Commodity Cost '].values + biomass_costs.loc[(biomass_costs['Year'] == 2040)
                                                               & (biomass_costs['Scenario'] == 'ENS_High')
                                                               & (biomass_costs['NUTS0'] == 'NO')
                                                               & (biomass_costs['Energy Commodity'] == 'MINBIOMUN1'),
    'NUTS0 Energy Commodity Cost '].values) / 2
    # convert into float
    biomass_costs['NUTS0 Energy Commodity Cost '] = biomass_costs['NUTS0 Energy Commodity Cost '] \
        .astype(float)

    # merging all data in one df
    biomass_pot = biomass_pot.merge(biomass_costs,
                                    left_on=['Year', 'Scenario', 'NUTS0', 'Energy Commodity'],
                                    right_on=['Year', 'Scenario', 'NUTS0', 'Energy Commodity'],
                                    how='outer')
    # select common scenarios to ENER and COST datasets
    biomass_pot = biomass_pot.loc[biomass_pot['Scenario'].isin(['ENS_High', 'ENS_Med', 'ENS_Low'])]

    # # checking NA values (without first generation energy crops) -> only data with potential=0
    # df_na = biomass_pot.loc[biomass_pot.isna().any(axis=1),:]
    # df_na = df_na[~df_na['Energy Commodity'].isin(['MINBIOLIQ1', 'MINBIOCRP11', 'MINBIOCRP21', 'MINBIORPS1'])]
    biomass_pot = biomass_pot.fillna(0)

    # selection year, scenario and regions of interest
    biomass_pot = biomass_pot.loc[(biomass_pot['Year'] == year_biom)
                                  & (biomass_pot['Scenario'] == enspreso_biomass_sce)
                                  & (biomass_pot['NUTS0'].isin(r_biom))]

    # convert sludge into biogas
    biomass_pot.loc[biomass_pot['Energy Commodity'] == 'MINBIOSLU1', 'Value'] *= eff_minbioslu1
    biomass_pot.loc[
        biomass_pot['Energy Commodity'] == 'MINBIOSLU1', 'NUTS0 Energy Commodity Cost '] *= 1 / eff_minbioslu1

    # group categories and store them into 1 df
    new_ind = pd.MultiIndex.from_product([['avail_local', 'c_op_local'], r_biom], names=['Parameter', 'Regions'])
    biomass_pot_final = pd.DataFrame(np.nan, index=new_ind, columns=list(categories.keys()))
    for c, elems in categories.items():
        elems_pot = biomass_pot.loc[biomass_pot['Energy Commodity'].isin(elems)]
        # mult cost and pot
        elems_pot = elems_pot.assign(mult=elems_pot['Value'] * elems_pot['NUTS0 Energy Commodity Cost '])
        # sum potentials and average cost
        cat_pot = elems_pot.groupby(['Year', 'NUTS0']).sum()
        cat_pot['NUTS0 Energy Commodity Cost '] = cat_pot['mult'] / cat_pot['Value']
        cat_pot = cat_pot.drop(columns=['mult']) \
            .rename(columns={'Value': 'avail_local', 'NUTS0 Energy Commodity Cost ': 'c_op_local'})
        # convert units
        cat_pot['avail_local'] *= pj_2_gwh  # PJ to GWh
        cat_pot['c_op_local'] *= 1e6 / pj_2_gwh / 1e6  # [€/GJ] to [M€/GWh]
        # put into general dataframe
        cat_pot = cat_pot.reset_index().drop(columns='Year').rename(columns={'NUTS0': 'Regions'}) \
            .melt(id_vars='Regions', value_vars=['avail_local', 'c_op_local'], var_name='Parameter', value_name=c) \
            .set_index(['Parameter', 'Regions'])
        biomass_pot_final.loc[cat_pot.index, cat_pot.columns] = cat_pot
    # fillna
    biomass_pot_final = biomass_pot_final.fillna(0)
    # renaming into iso3166
    biomass_pot_final = biomass_pot_final.rename(index={'EL': 'GR', 'UK': 'GB'}, level=1).sort_index()

    # updating with data XK taken from NUTS2 data of ENSPRESO
    biomass_pot_final.loc[('avail_local', 'XK'), :] = [777.7777784, 83.3333334, 14194.44446, 0, 527.77782]
    biomass_pot_final.loc[('c_op_local', 'XK'), :] = biomass_pot_final.loc[('c_op_local', 'RS'), :].values
    biomass_pot_final.loc[('avail_local', 'RS'), :] = biomass_pot_final.loc[('avail_local', 'RS'), :]\
                                                      - biomass_pot_final.loc[('avail_local', 'XK'), :]


"""
Adding Ostende Declaration for Wind offshore
"""
ost_woff = pd.read_csv(ex_data_dir / 'regions' / '220518_ostende_declaration_woff.csv',
                       index_col=[0, 1], header=0, sep=CSV_SEPARATOR)

"""
Computing Hydro actual capacity and potentials
"""
if compute_hydro:
    # getting actual installed capacity from JRC Hydro Power Plants db (source1)
    jrc_hydro_db = pd.read_csv((ex_data_dir / 'gitignored' / 'hydro' / 'jrc-hydro-power-plant-database.csv'), header=0)
    jrc_hydro_by_country = jrc_hydro_db.loc[:, ['installed_capacity_MW', 'pumping_MW', 'type',
           'country_code', 'storage_capacity_MWh', 'avg_annual_generation_GWh']].groupby(['type', 'country_code']).sum()\
        .rename(index={'EL': 'GR', 'UK': 'GB'}, level=1)
    # select and pivot data from JRC Hydro power plants db
    hydro_fmin_jrc = jrc_hydro_by_country.reset_index().pivot(index='country_code', columns='type')\
        .drop(columns=[(               'pumping_MW', 'HDAM'),
                       (               'pumping_MW', 'HROR'),
                       (     'storage_capacity_MWh', 'HROR'),
                       ('avg_annual_generation_GWh', 'HDAM'),
                       ('avg_annual_generation_GWh', 'HPHS'),
                       ('avg_annual_generation_GWh', 'HROR')
                       ])
    hydro_fmin_jrc.columns = ['HYDRO_DAM', 'PHS_TURB', 'HYDRO_RIVER', 'PHS_PUMP', 'DAM_STORAGE', 'PHS']
    hydro_fmin_jrc = hydro_fmin_jrc.loc[hydro_fmin_jrc.index.isin(eu34_country_code_iso3166_alpha2), :]
    # convert in GWh
    hydro_fmin_jrc = hydro_fmin_jrc / 1000

    # PHS potentials (source 2)
    hydro_phs_pot_jrc = tech_all.loc[('f_max', slice(None)), 'PHS']
    hydro_phs_pot_jrc = hydro_phs_pot_jrc.droplevel(level=0)

    # Hydro power potentials for e-highway (source 3)
    hydro_power_ehighway = pd.read_excel((ex_data_dir / 'gitignored' / 'hydro' / 'e-Highway_database_per_country-08022016.xlsx'),
                                sheet_name='T54', index_col=1, header=3)\
                               .loc[:,['RoR', 'Hydro with reservoir', 'PSP']]\
        .rename(columns={'RoR': 'HYDRO_RIVER', 'Hydro with reservoir': 'HYDRO_DAM', 'PSP': 'PHS_TURB'})
    hydro_power_ehighway =\
        hydro_power_ehighway.loc[hydro_power_ehighway.index.isin(eu34_country_code_iso3166_alpha2), :]/1000
    hydro_power_ehighway['PHS_PUMP'] = hydro_power_ehighway['PHS_TURB']
    # split RS into RS and XK
    shares_fmin_xk_rs = hydro_fmin_jrc.loc[['RS', 'XK'], hydro_power_ehighway.columns].fillna(0)
    shares_fmin_xk_rs = shares_fmin_xk_rs.div(shares_fmin_xk_rs.sum(axis=0), axis=1)
    hydro_power_ehighway.loc['XK', :] = shares_fmin_xk_rs.loc['XK', :].mul(hydro_power_ehighway.loc['RS', :])
    hydro_power_ehighway.loc['RS', :] = shares_fmin_xk_rs.loc['RS', :].mul(hydro_power_ehighway.loc['RS', :])

    # Building hydro f_max
    hydro_fmax = hydro_power_ehighway.merge(hydro_phs_pot_jrc, left_index=True, right_index=True, how='outer')\
        .merge(hydro_fmin_jrc.loc[:, 'DAM_STORAGE'], left_index=True, right_index=True, how='outer')

    # combining f_min and f_max and verify that f_max is bigger than f_min
    hydro_pot = pd.concat([hydro_fmin_jrc, hydro_fmax], axis=1, join='outer', keys=['f_min', 'f_max'])
    for col in hydro_fmax.columns:
        hydro_pot.loc[:, ('f_max', col)] = hydro_pot.loc[:, (slice(None), col)].max(axis=1)
    # neglect data smaller then 0.02 GW (or GWh)
    hydro_pot = hydro_pot.mask(hydro_pot < 0.02, np.nan)

    # converting pumping and turbing power of PHS into storage_charge_time and storage_discharge_time
    hydro_phs_charge_time = hydro_pot.loc[:, (slice(None), 'PHS')].droplevel(level=1, axis=1)\
        .div(hydro_pot.loc[:, (slice(None), 'PHS_PUMP')].droplevel(level=1, axis=1)).min(axis=1)
    hydro_phs_discharge_time = hydro_pot.loc[:, (slice(None), 'PHS')].droplevel(level=1, axis=1)\
        .div(hydro_pot.loc[:, (slice(None), 'PHS_TURB')].droplevel(level=1, axis=1)).min(axis=1)
    hydro_phs_times = pd.concat([hydro_phs_charge_time, hydro_phs_discharge_time], axis=1,
                                keys=['storage_charge_time', 'storage_discharge_time'])
    hydro_phs_times = hydro_phs_times.fillna(5) # fillna with default value of 5 (from source 2)

    # final cleaning of hydro_pot
    hydro_pot.drop(columns=['PHS_PUMP', 'PHS_TURB'], level=1, inplace=True)
    hydro_pot = hydro_pot.fillna(1e-3)

"""
Getting actual installed capacities from eurostat (except for hydro)
"""
estat_names = ['Geothermal', 'Wind on shore', 'Wind off shore',
                           'Solar thermal', 'Solar photovoltaic', 'Tide, wave, ocean']
equiv_estat = ['GEOTHERMAL', 'WIND_ONSHORE', 'WIND_OFFSHORE', 'PT_POWER_BLOCK', 'PV_ROOFTOP', 'TIDAL_STREAM']
installed_capa = pd.read_excel(installed_capa_path, sheet_name='Sheet 1', index_col=0, header=9)\
    .loc[eu34_full_names, estat_names] / 1000
installed_capa = installed_capa.rename(index=full_2_code).rename(columns=dict(zip(estat_names, equiv_estat)))
installed_capa.index = pd.MultiIndex.from_product([['f_min'],list(installed_capa.index)])

"""
Update datasets with new values
"""
if update_actual:
    # 1. update technologies data
    res_pot_ensp.columns = pd.MultiIndex.from_product([['f_max'], list(res_pot_ensp.columns)])
    tech_all.update(res_pot_ensp.T)
    tech_all.update(ost_woff)
    tech_all.update(installed_capa)
    hydro_pot = hydro_pot.reset_index().rename(columns={'index': 'Regions'})\
        .melt(id_vars=['Regions']).pivot(columns='variable_1', index=['variable_0', 'Regions']).droplevel(axis=1, level=0)
    tech_all.update(hydro_pot)
    # checking if f_max<f_min -> replace it by f_min
    tech_all.loc[('f_max', slice(None)), :] = tech_all.loc[('f_max', slice(None)), :]\
        .mask(tech_all.loc[('f_max', slice(None)), :] <
              tech_all.loc[('f_min', slice(None)), :].rename(index={'f_min': 'f_max'}, level=0),
              tech_all.loc[('f_min', slice(None)), :].rename(index={'f_min': 'f_max'}, level=0))

    # 2. compute solar area
    solar_area_all = pd.DataFrame(np.nan, index=eu34_country_code_iso3166_alpha2,
                              columns=['solar_area_rooftop', 'solar_area_ground', 'solar_area_ground_high_irr'])
    solar_area_all.loc[:, 'solar_area_rooftop'] = tech_all.loc[('f_max', slice(None)), 'PV_ROOFTOP']\
                                                      .droplevel(axis=0, level=0) / power_density_pv
    solar_area_all.loc[:, 'solar_area_ground'] = tech_all.loc[('f_max', slice(None)), 'PV_UTILITY']\
                                                      .droplevel(axis=0, level=0) / power_density_pv
    solar_area_all.loc[:, 'solar_area_ground_high_irr'] = tech_all.loc[('f_max', slice(None)), 'PT_POWER_BLOCK']\
                                                      .droplevel(axis=0, level=0) / power_density_pv

    #  3. update resources
    resources_all.update(biomass_pot_final)

    # 4. update sto
    hydro_phs_times.index = pd.MultiIndex.from_product([['PHS'], eu34_country_code_iso3166_alpha2])
    sto_all.update(hydro_phs_times)

"""
Printing data
"""
if print_update:
    # printing in grouped datasets for all regions
    tech_all.to_csv(ex_data_dir / 'regions' / 'Technologies.csv', sep=CSV_SEPARATOR)
    solar_area_all.to_csv(ex_data_dir / 'regions' / 'solar_area.csv', sep=CSV_SEPARATOR)
    resources_all.to_csv(ex_data_dir / 'regions' / 'Resources.csv', sep=CSV_SEPARATOR)
    sto_all.to_csv(ex_data_dir / 'regions' / 'Storage_power_to_energy.csv', sep=CSV_SEPARATOR)

    # printing for each region
    for r, r_full in code_2_full.items():
        r_path = data_dir / str(year_stop) / r

        # get actual data in directory
        tech_r = clean_indices(pd.read_csv(r_path / 'Technologies.csv',
                                           header=[0], index_col=[0], sep=CSV_SEPARATOR))
        resources_r = clean_indices(pd.read_csv(r_path / 'Resources.csv',
                                                       header=[0], index_col=[0], sep=CSV_SEPARATOR))
        sto_r = clean_indices(pd.read_csv(r_path / 'Storage_power_to_energy.csv',
                                                 header=[0], index_col=[0], sep=CSV_SEPARATOR))
        with open(r_path / 'Misc.json', 'r') as fp:
            misc_r = json.load(fp)


        # update the data for the res pot reevaluted
        tech_r.update(tech_all.loc[(slice(None), r), :].droplevel(axis=0, level=1).T)
        # update resources data
        resources_r.update(resources_all.loc[(slice(None), r), :].droplevel(axis=0, level=1).T)
        # update sto
        sto_r.update(sto_all.loc[(slice(None), r), :].droplevel(axis=0, level=1))
        # update solar area into misc
        for i, j in solar_area_all.loc[r, :].to_dict().items():
            misc_r[i] = j

        # printing updates
        print('print update ' + r_full)
        misc_f = r_path / 'Misc.json'
        with open(misc_f, mode='w') as my_file:
            json.dump(misc_r, my_file, indent=6)

        tech_r.to_csv(r_path / 'Technologies.csv', sep=CSV_SEPARATOR)
        resources_r.to_csv(r_path / 'Resources.csv', sep=CSV_SEPARATOR)
        sto_r.to_csv(r_path / 'Storage_power_to_energy.csv', sep=CSV_SEPARATOR)