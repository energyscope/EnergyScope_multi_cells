# -*- coding: utf-8 -*-
"""
This script reads renewable energy potentials (REPs) data from external sources and puts it into csv Data

@author: Paolo Thiran
"""
import pandas as pd
import numpy as np
from pathlib import Path
from esmc.common import CSV_SEPARATOR, eu33_country_code_iso3166_alpha2, eu33_country_code_eurostat, eu33_full_names
from esmc.utils.df_utils import clean_indices
import json



"""
Config of the script
"""
get_enspreso = True
read_dommisse = False
update_actual = True
print_update = False

# path
project_dir = Path(__file__).parents[2]
data_dir = project_dir / 'Data'
ex_data_dir = project_dir / 'Data' / 'exogenous_data'
dommisse_data = Path(r'C:\Users\pathiran\Documents\energy_system_modelling\ESTD\EnergyScope-EuropeanCountries2020')

# parameters
year_start = 2020
year_stop = 2050

# convert all the NED demand by this factor from comparison of Rixhon et al. and Dommisse et al. for BE demand
ratio_ned_BE = 53115.3311 / 102332.37

# max instalable nuclear in france (from RTE2022)
nuc_max_fr = 41.3

# country codes
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
code_2_full = dict(zip(eu33_country_code_iso3166_alpha2, eu33_full_names))






"""
ENSPRESO DATA
"""
# TODO add data for Ostende Declaration

if get_enspreso or read_dommisse or update_actual or print_update:
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

"""
Data from Dommisse et al.
"""
# tech considered (ordered)
ordered_tech_res = ['NUCLEAR',
 'PV_ROOFTOP', 'PV_UTILITY',
 'PT_POWER_BLOCK', 'ST_POWER_BLOCK', 'PT_COLLECTOR', 'ST_COLLECTOR',
 'WIND_ONSHORE', 'WIND_OFFSHORE',
 'HYDRO_DAM', 'HYDRO_RIVER',
 'TIDAL_STREAM', 'TIDAL_RANGE', 'WAVE',
 'GEOTHERMAL', 'DHN_DEEP_GEO',
 'DHN_SOLAR', 'DEC_SOLAR',
 'DAM_STORAGE', 'PHS']
# tech to get from Dommisse
tech2get = ordered_tech_res.copy()
tech2get.append('PV')
tech2get.remove('PV_ROOFTOP')
tech2get.remove('PV_UTILITY')
# resources to get
res2get = ['WASTE']

# creating dataframes to gather all data
demands_all = pd.DataFrame(np.nan,
                           index=pd.MultiIndex.from_product([['ELECTRICITY',
                                                              'HEAT_HIGH_T', 'HEAT_LOW_T_SH', 'HEAT_LOW_T_HW',
                                                              'PROCESS_COOLING', 'SPACE_COOLING',
                                                              'MOBILITY_PASSENGER', 'MOBILITY_FREIGHT',
                                                              'AVIATION_LONG_HAUL', 'SHIPPING', 'NON_ENERGY'],
                                                             eu33_country_code_iso3166_alpha2]),
                           columns=['Category', 'Subcategory',
                                    'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION ',
                                    'Units'])
resources_names = list(biomass_pot_final.columns)
resources_names.extend(res2get)
resources_all = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([['avail_local', 'c_op_local'],eu33_country_code_iso3166_alpha2]),
                             columns=resources_names)
sto_all = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([['PHS'], eu33_country_code_iso3166_alpha2]),
                       columns=['storage_charge_time', 'storage_discharge_time'])
tech_all = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([['f_min', 'f_max'], eu33_country_code_iso3166_alpha2]),
                        columns=ordered_tech_res)

for r, r_full in code_2_full.items():
    r_path = data_dir / str(year_stop) / r
    if read_dommisse and r in eu27_country_code:
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
        resources_dommisse.index.name = 'parameter name'

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
    else:
        # if not read_dommisse put actual data instead
        demands_dommisse = clean_indices(pd.read_csv(r_path / 'Demands.csv',
                                                     header=[0], index_col=[2], sep=CSV_SEPARATOR))
        if r == 'FR':
            # FR as ref regions has different csv
            resources_dommisse = clean_indices(pd.read_csv(r_path / 'Resources.csv',
                                                           header=[2], index_col=[2], sep=CSV_SEPARATOR))\
                                     .loc[res2get, ['avail_local', 'c_op_local']]
            sto_dommisse = clean_indices(pd.read_csv(r_path / 'Storage_power_to_energy.csv',
                                                     header=[0], index_col=[0], sep=CSV_SEPARATOR))\
                               .loc['PHS',:]
            tech_dommisse = clean_indices(pd.read_csv(r_path / 'Technologies.csv',
                                                      header=[0], index_col=[3], skiprows=[1], sep=CSV_SEPARATOR))\
                .loc[ordered_tech_res, ['f_min', 'f_max']]
        else:
            resources_dommisse = clean_indices(pd.read_csv(r_path / 'Resources.csv',
                                                           header=[0], index_col=[0], sep=CSV_SEPARATOR)).loc[res2get, :]
            sto_dommisse = clean_indices(pd.read_csv(r_path / 'Storage_power_to_energy.csv',
                                                     header=[0], index_col=[0], sep=CSV_SEPARATOR))

            tech_dommisse = clean_indices(pd.read_csv(r_path / 'Technologies.csv',
                                                      header=[0], index_col=[0], sep=CSV_SEPARATOR))

    # set f_max NUCLEAR to 0 by default (except for FR)
    if r != 'FR':
        tech_dommisse.loc['NUCLEAR', 'f_max'] = 0
    else:
        tech_dommisse.loc['NUCLEAR', 'f_max'] = nuc_max_fr

    """
    Update and print actual data
    """
    if update_actual:
        # add columns defining demand
        demands_new = clean_indices(pd.read_csv(r_path / 'Demands.csv', header=[0], index_col=[2], sep=CSV_SEPARATOR))
        demands_new.update(demands_dommisse)


        # get misc (for now only solar_area)
        with open(r_path / 'Misc.json', 'r') as fp:
            misc_new = json.load(fp)
        if r in eu27_country_code:
            for i,j in solar_area.loc[:, r_full].to_dict().items():
                misc_new[i] = j

        # resource new
        resources_new = biomass_pot_final.loc[(slice(None), r), :].droplevel(level=1, axis=0).T
        resources_new.loc['WASTE', :] = resources_dommisse.loc['WASTE', :]

        # sto new
        sto_new = sto_dommisse.copy()

        # update the data for the res pot reevaluted
        if r in eu27_country_code:
            my_df = res_pot_esmc.loc[:, r_full].to_frame(name='f_max')
            tech_new = tech_dommisse.copy()
            tech_new.update(my_df)
        else:
            tech_new = tech_dommisse.copy()


        tech_new = tech_new.loc[ordered_tech_res, :]
        tech_new.index.name = 'Technologies param'
        # if f_max is smaller then f_min, we put f_min to f_max
        tech_new.loc[:, 'f_max'] = tech_new.loc[:, 'f_max'].mask(tech_new.loc[:, 'f_max'] < tech_new.loc[:, 'f_min'],
                                                                 tech_new.loc[:, 'f_min'])

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

if update_actual and print_update:
    # save into dataframes all
    demands_all.to_csv(ex_data_dir / 'regions' / 'Demands.csv', sep=CSV_SEPARATOR)
    resources_all.to_csv(ex_data_dir / 'regions' / 'Resources.csv', sep=CSV_SEPARATOR)
    sto_all.to_csv(ex_data_dir / 'regions' / 'Storage_power_to_energy.csv', sep=CSV_SEPARATOR)
    tech_all.to_csv(ex_data_dir / 'regions' / 'Technologies.csv', sep=CSV_SEPARATOR)