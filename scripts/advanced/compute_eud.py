# -*- coding: utf-8 -*-
"""
This script reads data from external sources,
computes the end-uses demands (EUD) from it
and stores it into a csv

@author: Paolo Thiran
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from esmc.common import eu33_country_code_iso3166_alpha2, eu33_full_names, eu27_country_code, eu28_country_code, CSV_SEPARATOR

full_2_code = dict(zip(eu33_full_names, eu33_country_code_iso3166_alpha2))

# case
compute_ind_shares = False
save_ind_shares = False
save_results = False

regions = ['AT', 'BE', 'BG', 'CZ', 'DE', 'DK', 'EE', 'GR', 'ES', 'FI', 'FR', 'HR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV',
           'NL', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK', 'GB']

r = 'BE'
years = np.arange(2015, 2055, 5)
save_years = [2035, 2050]

# path and files names
project_path = Path(__file__).parents[2]
data_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\Demand\data')
ned_path = Path(r'C:\Users\pathiran\OneDrive - UCL\Documents\PhD\EU_data\NED')
euc_build_energy_use_file = 'final-energy-demand-in-r'
euc_agric_energy_use_file = 'energy-use-per-type'
euref_file = 'ref2020_energy-transport-ghg_0.xlsx'
hre4_file = 'HRE4-Exchange-Template-WP3_v22b_website.xlsx'
eustat_file = 'nrg_bal_c_page_spreadsheet_eu_ind.xlsx'
ned_file = 'compute_ned.xlsx'
estat_aviation_file = 'estat_aviation_2019.csv'
eurocontrol_file = 'eurocontrol_aviation_growth.csv'

# other data
ktoe_per_twh = 85.9845 # [ktoe/Twh]
cooking_fuels_eff = 0.71 # conversion of cooking from fuels to electricity from JRC-IDEES EU 2015
sc_house_perc = 0.2568 # percentage of the space cooling in building used in residential/households form JRC-IDEES EU 2015
sc_ser_perc = 0.7432 # percentage of the space cooling in building used in services form JRC-IDEES EU 2015
sc_fuels_cop = 1.3999994 # COP of space cooling with fuels
sc_elec_cop = 2.5 # COP of space cooling with electricity
pc_cop = 1 / 0.4965 # COP of process cooling

# creat df for results
eui_names = ['ELECTRICITY', 'HEAT_HIGH_T', 'HEAT_LOW_T_SH', 'HEAT_LOW_T_HW',
             'PROCESS_COOLING', 'SPACE_COOLING',
             'MOBILITY_PASSENGER', 'MOBILITY_FREIGHT', 'EXTRA_EU_AVIATION', 'INTERNATIONAL_SHIPPING',
             'NON_ENERGY'] #end-uses inputs
eui_categories = ['Electricity', 'Heat', 'Heat', 'Heat', 'Cold', 'Cold',
                  'Mobility', 'Mobility', 'Mobility', 'Mobility', 'Non-energy']
eui_subcat = ['Electricity', 'High temperature', 'Space heating', 'Hot water', 'Process cooling', 'Space cooling',
              'Passenger', 'Freight', 'International passenger flights', 'International shipping', 'Non-energy']
sector_names = ['HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION']
all_eud = pd.DataFrame(np.nan, index=pd.MultiIndex.from_product([years, eu33_country_code_iso3166_alpha2, eui_names]),
                       columns=sector_names)
all_eud.update(pd.read_csv(project_path / 'Data' / 'exogenous_data' / 'regions' / 'Demands.csv',
                      header=0, index_col=[0, 1, 2], sep=CSV_SEPARATOR) / 1000) # fill with existing values

""" Compute shares in industry from HRE4 for all EU countries """
if compute_ind_shares:
    # reading data HRE4
    hre4_ind = pd.read_excel(data_path / hre4_file, sheet_name='Industry data', header=7, index_col="Country code")
    hre4_ind = hre4_ind.loc[hre4_ind['Technologies'] == 'Total', ['PH <100 (FED)',
           'PH 100-200 (FED)', 'PH 200-500 (FED)', 'PH >500 (FED)', 'SH (FED)',
           #'SC (DED)', 'PC <-30 (DED)', 'PC 30-0 (DED)', 'PC 0-15(DED)',
            'SC (FED)', 'PC <-30 (FED)', 'PC 30-0 (FED)', 'PC 0-15 (FED)']]
    hre4_ind.drop(index=['CY', 'MT'], inplace=True)
    hre4_ind.rename(index={'EL': 'GR', 'UK': 'GB'}, inplace=True)

    # reading eurostat industrial FEC
    eustat_ind = pd.read_excel(data_path / eustat_file, sheet_name='Sheet 1', header=9, index_col=0,
                               usecols=[0,1], engine='openpyxl').dropna().drop(index=[':'])

    eustat_ind.rename(index=full_2_code, inplace=True)
    eustat_ind.rename(index={'Czechia': 'CZ'}, inplace=True)

    # aggregate hre4 data
    agg_cols = {'HEAT_HIGH_T': ['PH 100-200 (FED)', 'PH 200-500 (FED)', 'PH >500 (FED)'],
                'HEAT_LOW_T_SH': ['SH (FED)'],
                'HEAT_LOW_T_HW': ['PH <100 (FED)'],
                # 'PROCESS_COOLING': ['PC <-30 (DED)', 'PC 30-0 (DED)', 'PC 0-15(DED)'],
                # 'SPACE_COOLING': ['SC (DED)'],
                'PROCESS_COOLING': ['PC <-30 (FED)', 'PC 30-0 (FED)', 'PC 0-15 (FED)'],
                'SPACE_COOLING': ['SC (FED)']
                }

    for key, elems in agg_cols.items():
        hre4_ind[key] = hre4_ind.loc[:, elems].sum(axis=1)
        hre4_ind = hre4_ind.drop(columns=elems)

    hre4_ind['ELECTRICITY'] = (eustat_ind.loc[hre4_ind.index, '2015'])/1000\
                              - hre4_ind.sum(axis=1)
    # hre4_ind.drop(columns=['PROCESS_COOLING_FEC', 'SPACE_COOLING_FEC'], inplace=True)

    # correction of SK negative value based on neighrbour wiht similar value (CZ)
    hre4_ind.loc['SK', 'ELECTRICITY'] = hre4_ind.loc['CZ', 'ELECTRICITY']\
                                        * (hre4_ind.loc['SK',:].drop(columns=['ELECTRICITY']).sum()
                                           / hre4_ind.loc['CZ',:].drop(columns=['ELECTRICITY']).sum())
    hre4_ind['ELECTRICITY'] = hre4_ind['ELECTRICITY'].astype(float)
    # compute ind shares
    ind_shares = hre4_ind.div(hre4_ind.sum(axis=1), axis=0)
    # adding null columns to have all eun-uses inputs
    ind_shares['MOBILITY_PASSENGER'] = 0
    ind_shares['MOBILITY_FREIGHT'] = 0
    ind_shares['EXTRA_EU_AVIATION'] = 0
    ind_shares['INTERNATIONAL_SHIPPING'] = 0
    ind_shares['NON_ENERGY'] = 0
    ind_shares = ind_shares[eui_names]
    ind_shares_stat = ind_shares.describe()

    if save_ind_shares:
        ind_shares.to_csv(data_path / 'ind_shares.csv')
else:
    ind_shares = pd.read_csv(data_path / 'ind_shares.csv', header=0, index_col=0)

""" Reading NED data """
ned_2019 = pd.read_excel(ned_path / ned_file, sheet_name='results', header=1, index_col=0, usecols="A,P:R")
ned_2019.rename(index=full_2_code, inplace=True)
ned_2019.rename(index={'Czechia': 'CZ'}, inplace=True)
ned_2019.columns = ned_2019.columns.str.rstrip('.3')
ned_2019_tot = ned_2019.sum(axis=1)
ned_shares = ned_2019.div(ned_2019_tot, axis=0)
ned_shares.sort_index(inplace=True)

""" Reading aviation data and computing projection"""
av_2019 = pd.read_csv(data_path / estat_aviation_file, header=0, index_col=0, sep=CSV_SEPARATOR)
av_growth = pd.read_csv(data_path / eurocontrol_file, header=0, index_col=0, sep=CSV_SEPARATOR) / 100
av_growth_mul = pd.DataFrame(1, index=av_growth.index, columns=years)
av_growth_mul = av_growth_mul.apply(lambda col: col.add(av_growth['Average growth per year [%]']), axis=0)
av_growth_mul = av_growth_mul.apply(lambda col: col**(col.name-2019))
av_intra_eu = av_growth_mul.copy().mul(av_2019['Intra-EU aviation demand [Gpkm](Eurostat 2019)'], axis=0)
av_extra_eu = av_growth_mul.copy().mul(av_2019['Extra-EU aviation demand [Gpkm](Eurostat 2019)'], axis=0)

for r in regions:
    print('Computing ' + r)
    """ Reading data """
    # conversion into alpha-2 EU
    if r == 'GR':
        r2 = 'EL'
    elif r == 'GB':
        r2 = 'UK'
    else:
        r2 = r
    # reading data from euref
    if r2 == 'UK':
        # for UK look at euref 2016
        euref_a = pd.read_excel(data_path / 'AppendixRefSce_0.xls', sheet_name=(r2 + '-A'), header=1, index_col=0)\
            .loc[['Population (in million)', 'Non-Energy Uses'], years].rename(index={'Non-Energy Uses': 'NON_ENERGY'})
        euref_b = pd.read_excel(data_path / 'AppendixRefSce_0.xls', sheet_name=(r2 + '-B'), header=1, index_col=0, nrows=35)\
            .loc[['Passenger transport activity (Gpkm)', 'Freight transport activity (Gtkm)',
                  'Aviation (3)',
                  'Industry', 'Residential', 'Tertiary'],years]\
            .rename(index={'Passenger transport activity (Gpkm)': 'MOBILITY_PASSENGER',
                           'Freight transport activity (Gtkm)': 'MOBILITY_FREIGHT',
                           'Aviation (3)': 'Intra-EU aviation',
                           'Industry': 'INDUSTRY', 'Residential': 'HOUSEHOLDS',
                                                  'Tertiary': 'SERVICES'})
        euref_fec = pd.concat([euref_a, euref_b.loc[['INDUSTRY', 'HOUSEHOLDS', 'SERVICES'], :]], axis=0)
        euref_fec.loc[['INDUSTRY', 'HOUSEHOLDS', 'SERVICES', 'NON_ENERGY'], :] *= 1/ktoe_per_twh
        euref_transport = euref_b.loc[['MOBILITY_PASSENGER', 'MOBILITY_FREIGHT', 'Intra-EU aviation']]
        # add internationnal shipping (assuming same ratio as IE)
        euref_transport.loc['INTERNATIONAL_SHIPPING', :] = euref_transport.loc['MOBILITY_FREIGHT', :]\
            .mul(all_eud.loc[(years, 'IE', 'INTERNATIONAL_SHIPPING'), 'TRANSPORTATION'].values / all_eud.loc[(years, 'IE', 'MOBILITY_FREIGHT'), 'TRANSPORTATION'].values)
        # add aviation
        euref_transport.loc['MOBILITY_PASSENGER', :] += (-euref_transport.loc['Intra-EU aviation', :]
                                                         + av_intra_eu.loc[r, :])
        euref_transport.loc['EXTRA_EU_AVIATION', :] = av_extra_eu.loc[r, :]
    else:
        euref_fec = pd.read_excel(data_path / euref_file, sheet_name=(r2 + '_A'), header=1, index_col=0)\
            .loc[['Population (in million)', 'Industry', 'Residential', 'Tertiary (8)', 'Non-Energy Uses (ktoe)'],
        years].rename(index={'Industry': 'INDUSTRY', 'Residential': 'HOUSEHOLDS',
                                                  'Tertiary (8)': 'SERVICES','Non-Energy Uses (ktoe)': 'NON_ENERGY'})
        euref_fec.loc[['INDUSTRY', 'HOUSEHOLDS', 'SERVICES', 'NON_ENERGY'], :] *= 1/ktoe_per_twh

        euref_transport = pd.read_excel(data_path / euref_file, sheet_name=(r2 + '_B'), header=1, index_col=0) \
            .loc[['Passenger transport activity (Gpkm)', 'Freight transport activity (Gtkm)',
                  'Intra-EU aviation', 'Freight transport (3)', 'Freight transport (toe/Mtkm) (3)'], years] \
            .rename(index={'Passenger transport activity (Gpkm)': 'MOBILITY_PASSENGER',
                           'Freight transport activity (Gtkm)': 'MOBILITY_FREIGHT',
                           'Freight transport (3)': 'TOTAL_FREIGHT_ENERGY',
                           'Freight transport (toe/Mtkm) (3)': 'TOTAL_FREIGHT_INTENSITY'})
        # computing international shipping
        euref_transport.loc['INTERNATIONAL_SHIPPING', :] = euref_transport.loc['TOTAL_FREIGHT_ENERGY', :]\
                                                              .div(euref_transport.loc['TOTAL_FREIGHT_INTENSITY', :])\
                                                          - euref_transport.loc['MOBILITY_FREIGHT', :]
        euref_transport.loc['INTERNATIONAL_SHIPPING', :] = euref_transport.loc['INTERNATIONAL_SHIPPING', :]\
            .mask(euref_transport.loc['INTERNATIONAL_SHIPPING', :] < 0.1, 0)

        euref_transport.loc['MOBILITY_PASSENGER', :] += (-euref_transport.loc['Intra-EU aviation', :]
                                                         + av_intra_eu.loc[r, :])
        euref_transport.loc['EXTRA_EU_AVIATION', :] = av_extra_eu.loc[r, :]


    if r == 'BE':
        # if region is BE putting numbers from EUref 2016 as those of 2020 are not consistent
        euref_fec.loc['NON_ENERGY', :] = [98.45, 99.35, 100.26, 100.61, 102.34, 105.08, 104.14, 106.00]


    # reading data from eucalc
    euc_build_energy_use = pd.read_csv(data_path / 'eucalc_build' / (euc_build_energy_use_file + '_' + r + '.csv'),
                                       sep=";", header=0, index_col=0,
                                       dtype=np.float64, decimal=',').loc[years, :]
    euc_build_energy_use = euc_build_energy_use.rename(columns={'Electricity space cooling\n': 'Electricity space cooling'})
    euc_build_energy_use.index = euc_build_energy_use.index.astype(int)
    euc_agric_energy_use = pd.read_csv(data_path / 'eucalc_agric' / (euc_agric_energy_use_file + '_' + r + '.csv'),
                                       sep=";", header=0, index_col=0,
                                       dtype=np.float64, decimal=',').loc[years, :]
    euc_agric_energy_use.index = euc_agric_energy_use.index.astype(int)

    """ Computing eud HOUSEHOLDS and SERVICES """
    perc_house = euref_fec.loc['HOUSEHOLDS', :] / (euref_fec.loc['HOUSEHOLDS', :] + euref_fec.loc['SERVICES', :])
    perc_ser = 1 - perc_house

    df = euc_build_energy_use.copy()
    # division of demands for HOUSEHOLDS and SERVICES
    col_div = ['Electricity home appliances ', 'Electricity hot water', 'Electricity lighting',
               'Fuels for hot water', 'District heating']
    for c in col_div:
        s = c + ' SERVICES'
        df[s] = df[c].mul(perc_ser, axis=0)
        df[c] *= perc_house

    # conversion fuels cooking
    df['Fuels for cooking'] *= cooking_fuels_eff

    # conversion and division for space cooling
    df['Electricity space cooling'] *= sc_elec_cop
    df['Fuels for space cooling'] *= sc_fuels_cop
    df['Electricity space cooling SERVICES'] = df['Electricity space cooling'] * sc_ser_perc
    df['Electricity space cooling'] *= sc_house_perc
    df['Fuels for space cooling SERVICES'] = df['Fuels for space cooling'] * sc_ser_perc
    df['Fuels for space cooling'] *= sc_house_perc

    # mapping
    mapping_house = {'ELECTRICITY': ['Electricity home appliances ', 'Electricity residential cooking',
                                   'Electricity lighting'],
                     'HEAT_HIGH_T': [],
                     'HEAT_LOW_T_SH': ['Space heating residential', 'District heating'],
                     'HEAT_LOW_T_HW': ['Electricity hot water', 'Fuels for hot water'],
                     'PROCESS_COOLING': [],
                     'SPACE_COOLING': ['Electricity space cooling', 'Fuels for space cooling'],
                     'MOBILITY_PASSENGER': [],
                     'MOBILITY_FREIGHT': [],
                     'EXTRA_EU_AVIATION': [],
                     'INTERNATIONAL_SHIPPING': [],
                     'NON_ENERGY': []
                     }
    mapping_ser = {'ELECTRICITY': ['Electricity home appliances  SERVICES', 'Electricity lighting SERVICES',
                                   'Fuels for cooking'],
                   'HEAT_HIGH_T': [],
                   'HEAT_LOW_T_SH': ['Space heating non-residential', 'District heating SERVICES'],
                   'HEAT_LOW_T_HW': ['Electricity hot water SERVICES', 'Fuels for hot water SERVICES'],
                   'PROCESS_COOLING': [],
                   'SPACE_COOLING': ['Electricity space cooling SERVICES', 'Fuels for space cooling SERVICES'],
                   'MOBILITY_PASSENGER': [],
                   'MOBILITY_FREIGHT': [],
                   'EXTRA_EU_AVIATION': [],
                   'INTERNATIONAL_SHIPPING': [],
                   'NON_ENERGY': []}

    for key, elems in mapping_house.items():
        all_eud.loc[(years, r, key), 'HOUSEHOLDS'] = df.loc[years, elems].sum(axis=1).values
    for key, elems in mapping_ser.items():
        all_eud.loc[(years, r, key), 'SERVICES'] = df.loc[years, elems].sum(axis=1).values

    # adding aggriculture into services (rough assumption on electrification of motorisation and need for heating)
    mapping_agric = {'ELECTRICITY': ['Diesel', 'Gasoline', 'Electricity', 'Natural gas'],
                     'HEAT_LOW_T_HW': ['Coal', 'Heat', 'Other', 'LPG', 'Fuel-Oil']}

    for key, elems in mapping_agric.items():
        all_eud.loc[(years, r, key), 'SERVICES'] += euc_agric_energy_use.loc[years, elems].sum(axis=1).values

    """ Computing eud for INDUSTRY """
    # putting total industrial FEC from euref
    all_eud.loc[(years, r, slice(None)), 'INDUSTRY'] = np.tile(ind_shares.loc[r, :].values, len(years))
    # splitting in shares according to HRE4
    all_eud.loc[(years, r, slice(None)), 'INDUSTRY'] *= np.repeat(euref_fec.loc['INDUSTRY', years].values, len(eui_names))
    # converting cooling into EUD (for the rest, we assume EUD=FEC)
    all_eud.loc[(years, r, 'PROCESS_COOLING'), 'INDUSTRY'] *= pc_cop
    all_eud.loc[(years, r, 'SPACE_COOLING'), 'INDUSTRY'] *= sc_elec_cop

    """ Adding NED """
    ref_year = 2015 # taking 2015 to avoid covid effect

    for y in years:
        evol = 1+ ((euref_fec.loc['NON_ENERGY', y] - euref_fec.loc['NON_ENERGY', ref_year])\
               / euref_fec.loc['NON_ENERGY', ref_year])
        all_eud.loc[(y, r, 'NON_ENERGY'), 'INDUSTRY'] = ned_2019_tot.loc[r] * evol

    """ Adding TRANSPORTATION """
    all_eud.loc[(years, r, slice(None)), 'TRANSPORTATION'] = 0
    all_eud.loc[(years, r, 'MOBILITY_PASSENGER'), 'TRANSPORTATION'] \
        = euref_transport.loc['MOBILITY_PASSENGER', years].values
    all_eud.loc[(years, r, 'MOBILITY_FREIGHT'), 'TRANSPORTATION'] =\
        euref_transport.loc['MOBILITY_FREIGHT', years].values
    all_eud.loc[(years, r, 'EXTRA_EU_AVIATION'), 'TRANSPORTATION'] =\
        euref_transport.loc['EXTRA_EU_AVIATION', years].values
    all_eud.loc[(years, r, 'INTERNATIONAL_SHIPPING'), 'TRANSPORTATION'] =\
        euref_transport.loc['INTERNATIONAL_SHIPPING', years].values

# for CH and NO
all_eud.loc[(years, 'CH', 'EXTRA_EU_AVIATION'), :] = 0
all_eud.loc[(years, 'NO', 'EXTRA_EU_AVIATION'), :] = 0
all_eud.loc[(years, 'CH', 'EXTRA_EU_AVIATION'), 'TRANSPORTATION'] = av_extra_eu.loc['CH', years].values
all_eud.loc[(years, 'NO', 'EXTRA_EU_AVIATION'), 'TRANSPORTATION'] = av_extra_eu.loc['NO', years].values


""" Computing share_intra_eu_flight"""
mob_pass_df = all_eud.loc[(years, av_intra_eu.index, 'MOBILITY_PASSENGER'), 'TRANSPORTATION'].droplevel(level=2, axis=0)\
    .reset_index().pivot(index='level_1', columns='level_0').droplevel(level=0, axis=1)
share_intra_eu_flight = av_intra_eu.div(mob_pass_df)

"""Putting all_eud in GWh, Mpkm and Mtkm"""
all_eud *= 1000

""" Saving results """
if save_results:
    # saving all demands together
    all_eud.to_csv(project_path / 'Data' / 'exogenous_data' / 'regions' / 'Demands.csv', sep=CSV_SEPARATOR)
    ned_shares.to_csv(project_path / 'Data' / 'exogenous_data' / 'regions' / 'ned_shares.csv', sep=CSV_SEPARATOR)
    share_intra_eu_flight.to_csv(project_path / 'Data' / 'exogenous_data' / 'regions' / 'share_intra_eu_flight.csv',
                                 sep=CSV_SEPARATOR)

    # saving into each year and region directory
    for y in save_years:
        for r in eu28_country_code:
            my_dir = project_path / 'Data' / str(y) / r
            my_dir.mkdir(exist_ok=True, parents=True)
            my_df = all_eud.loc[(y, r, slice(None)), :].reset_index().drop(columns=['level_0', 'level_1'])\
                .rename(columns={'level_2': 'parameter name'})
            my_df['Category'] = eui_categories
            my_df['Subcategory'] = eui_subcat
            my_df['Units'] = ['[GWh]', '[GWh]', '[GWh]', '[GWh]', '[GWh]', '[GWh]',
                              '[Mpkm]', '[Mtkm]', '[Mpkm]', '[Mtkm]', '[GWh]']
            my_df = my_df[['Category', 'Subcategory', 'parameter name',
                           'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION', 'Units']]
            my_df.to_csv(my_dir / 'Demands.csv', sep=CSV_SEPARATOR, index=False)

        # saving ned shares intra_eu_flight_shares
        for r in ned_shares.index:
            my_dir = project_path / 'Data' / str(y) / r
            my_ned_shares = ned_shares.loc[r, :].to_dict()
            with open((my_dir / 'Misc.json'), 'r') as f:
                misc = json.load(f)

            misc['share_ned'] = my_ned_shares
            misc['share_intra_eu_flight_min'] = share_intra_eu_flight.loc[r, y]
            misc['share_intra_eu_flight_max'] = share_intra_eu_flight.loc[r, y] + 1e-4

            with open((my_dir / 'Misc.json'), 'w') as f:
                json.dump(misc, f, indent=4, sort_keys=True)


    ## Changing ELECTRICITY_VAR into ELECTRICITY
    # for r in eu33_country_code_iso3166_alpha2:
    #     my_dir = project_path / 'Data' / str(2035) / r
    #     ts = pd.read_csv(my_dir / 'Time_series.csv', header=0, index_col=0, sep=CSV_SEPARATOR)\
    #         .rename(columns={'ELECTRICITY_VAR' : 'ELECTRICITY'})
    #     ts.loc[:, 'ELECTRICITY'] += 8.78*1e-4 # adding base load according to the ratio in BE between varying (11.5%) and constant (88.5%)
    #     ts.loc[:, 'ELECTRICITY'] = ts.loc[:, 'ELECTRICITY']/ts.loc[:, 'ELECTRICITY'].sum()
    #
    #     weights = pd.read_csv(my_dir / 'Weights.csv', header=0, index_col=0, sep=CSV_SEPARATOR)\
    #         .rename(index={'ELECTRICITY_VAR' : 'ELECTRICITY'})
    #
    #     ts.to_csv(my_dir / 'Time_series.csv', sep=CSV_SEPARATOR)
    #     weights.to_csv(my_dir / 'Weights.csv', sep=CSV_SEPARATOR)


