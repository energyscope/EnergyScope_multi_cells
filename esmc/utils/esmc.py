"""
This file contains a class to define an energy system

"""
import logging
import copy

import numpy as np

from esmc.utils.region import Region
from esmc.utils.opti_probl import OptiProbl
from esmc.preprocessing.temporal_aggregation import TemporalAggregation
import esmc.preprocessing.dat_print as dp
import esmc.postprocessing.amplpy2pd as a2p
import shutil
import git
import pandas as pd
import csv
from pathlib import Path
from datetime import datetime

#TODO
# add logging and time different steps
# dat_files not on github -> extern person cannot use them...
# add error when no ampl license
# check error DHN into sankey
# to compute yearly exchanges -> sum over the year positive and negative part of each link
# try approach of exchanges more on the link point of view
# add into .mod some variables to have general results (ex: total prod over year:
# Tech_wnd [y,l,tech] = sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} layers_in_out [y,tech,l] * F_t [y,tech, h, td];))
# /!\ data into xlsx not the same as in indep.dat and countries.dat (at least for layers_in_out)


# TODO check 18TDs


class Esmc:
    """

    TODO Update documentation

    Parameters
    ----------


    """

    def __init__(self, config, Nbr_TD=10):
        # identification of case study
        self.case_study = config['case_study']
        self.comment = config['comment']
        self.regions_names = config['regions_names']
        self.regions_names.sort()
        self.space_id = '_'.join(self.regions_names)  # identification of the spatial case study in one string
        self.Nbr_TD = Nbr_TD
        self.gwp_limit_overall = config['gwp_limit_overall']
        self.year = config['year']

        # path definition
        self.project_dir = Path(__file__).parents[2]
        self.dat_dir = self.project_dir/'case_studies'/'dat_files'/self.space_id
        self.cs_dir = self.project_dir/'case_studies'/self.space_id/self.case_study
        # create directories
        self.dat_dir.mkdir(parents=True, exist_ok=True)
        self.cs_dir.mkdir(parents=True, exist_ok=True)

        # create and initialize regions
        self.ref_region = config['ref_region']
        self.regions = dict()
        self.data_exch = dict()


        # initialize TemporalAggregation object
        # TODO self.spatial_aggreg = object spatial_aggreg
        #

        # create energy system optimization problem (esom)
        self.esom = None

        return

# TODO add an automated initialization for specific pipeline

    def init_regions(self):
        data_dir = self.project_dir/'Data'/str(self.year)
        self.regions[self.ref_region] = Region(nuts=self.ref_region, data_dir=data_dir, ref_region=True)
        for r in self.regions_names:
            if r!=self.ref_region:
                self.regions[r] = copy.deepcopy(self.regions[self.ref_region])
                self.regions[r].__init__(nuts=r, data_dir=data_dir, ref_region=False)

        return

    def init_ta(self, algo='kmedoid'):
        """Initialize the temporal aggregator

        """
        self.ta = TemporalAggregation(self.regions, self.dat_dir, Nbr_TD=self.Nbr_TD, algo=algo)
        return

    def update_version(self):
        """Updating version file

        Updating the version.json file into case_studies directory to add the description of this run

        """
        # path of case_studies dir
        cs_versions = self.cs_dir.parent/'versions.json'

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
        versions[self.case_study] = dict()
        versions[self.case_study]['comment'] = self.comment
        versions[self.case_study]['space_id'] = self.space_id
        # keys_to_extract = ['running', 'printing_out', 'printing_step2_in']
        # versions[config['case_study']]['step1_config'] = {key: config['step1_config'][key] for key in keys_to_extract}
        # keys_to_extract = ['running', 'printing_data', 'printing_inputs', 'printing_outputs']
        # versions[config['case_study']]['step2_config'] = {key: config['step2_config'][key] for key in keys_to_extract}
        versions[self.case_study]['commit_name'] = commit_name
        versions[self.case_study]['datetime'] = now

        a2p.print_json(versions, cs_versions)
        return

    def print_data(config, case='deter'):
        """
        TODO adapt to multi-cells

        add doc
        """

        # # make dir and parents
        # data = config['all_data']
        #
        # eud = data['Demand']
        # resources = data['Resources']
        # technologies = data['Technologies']
        # end_uses_categories = data['End_uses_categories']
        # layers_in_out = data['Layers_in_out']
        # storage_characteristics = data['Storage_characteristics']
        # storage_eff_in = data['Storage_eff_in']
        # storage_eff_out = data['Storage_eff_out']
        # time_series = data['Time_series']
        #
        # if config['printing']:
        #     logging.info('Printing ESTD_data.dat')
        #
        #     # Prints the data into .dat file (out_path) with the right syntax for AMPL
        #     out_path = cs / config['case_study'] / 'ESTD_data.dat'
        #     # config['es_path'] + '/ESTD_data.dat'
        #     gwp_limit = config['GWP_limit']
        #
        #     # Pre-processing df #
        #
        #     # pre-processing resources
        #     resources_simple = resources.loc[:, ['avail', 'gwp_op', 'c_op']]
        #     resources_simple.index.name = 'param :'
        #     resources_simple = resources_simple.astype('float')
        #     # pre-processing eud
        #     eud_simple = eud.drop(columns=['Category', 'Subcategory', 'Units'])
        #     eud_simple.index.name = 'param end_uses_demand_year:'
        #     eud_simple = eud_simple.astype('float')
        #     # pre_processing technologies
        #     technologies_simple = technologies.drop(columns=['Category', 'Subcategory', 'Technologies name'])
        #     technologies_simple.index.name = 'param:'
        #     technologies_simple = technologies_simple.astype('float')
        #
        #     # Economical inputs
        #     i_rate = config['all_data']['Misc']['i_rate']  # [-]
        #     # Political inputs
        #     re_share_primary = config['all_data']['Misc'][
        #         're_share_primary']  # [-] Minimum RE share in primary consumption
        #     solar_area = config['all_data']['Misc']['solar_area']  # [km^2]
        #     power_density_pv = config['all_data']['Misc'][
        #         'power_density_pv']  # PV : 1 kW/4.22m2   => 0.2367 kW/m2 => 0.2367 GW/km2
        #     power_density_solar_thermal = config['all_data']['Misc'][
        #         'power_density_solar_thermal']  # Solar thermal : 1 kW/3.5m2 => 0.2857 kW/m2 => 0.2857 GW/km2
        #
        #     # Technologies shares
        #     share_mobility_public_min = config['all_data']['Misc']['share_mobility_public_min']
        #     share_mobility_public_max = config['all_data']['Misc']['share_mobility_public_max']
        #     share_freight_train_min = config['all_data']['Misc']['share_freight_train_min']
        #     share_freight_train_max = config['all_data']['Misc']['share_freight_train_max']
        #     share_freight_road_min = config['all_data']['Misc']['share_freight_road_min']
        #     share_freight_road_max = config['all_data']['Misc']['share_freight_road_max']
        #     share_freight_boat_min = config['all_data']['Misc']['share_freight_boat_min']
        #     share_freight_boat_max = config['all_data']['Misc']['share_freight_boat_max']
        #     share_heat_dhn_min = config['all_data']['Misc']['share_heat_dhn_min']
        #     share_heat_dhn_max = config['all_data']['Misc']['share_heat_dhn_max']
        #
        #     share_ned = pd.DataFrame.from_dict(config['all_data']['Misc']['share_ned'], orient='index',
        #                                        columns=['share_ned'])
        #
        #     # Electric vehicles :
        #     # km-pass/h/veh. : Gives the equivalence between capacity and number of vehicles.
        #     # ev_batt, size [GWh]: Size of batteries per car per technology of EV
        #     keys_to_extract = ['EVs_BATT', 'vehicule_capacity', 'batt_per_car']
        #     evs = pd.DataFrame({key: config['all_data']['Misc']['evs'][key] for key in keys_to_extract},
        #                        index=config['all_data']['Misc']['evs']['CAR'])
        #     state_of_charge_ev = pd.DataFrame.from_dict(config['all_data']['Misc']['state_of_charge_ev'],
        #                                                 orient='index',
        #                                                 columns=np.arange(1, 25))
        #     # Network
        #     loss_network = config['all_data']['Misc']['loss_network']
        #     c_grid_extra = config['all_data']['Misc'][
        #         'c_grid_extra']  # cost to reinforce the grid due to intermittent renewable energy penetration. See 2.2.2
        #     import_capacity = config['all_data']['Misc'][
        #         'import_capacity']  # [GW] Maximum power of electrical interconnections
        #
        #     # Storage daily
        #     STORAGE_DAILY = config['all_data']['Misc']['STORAGE_DAILY']
        #
        #     # Building SETS from data #
        #     SECTORS = list(eud_simple.columns)
        #     END_USES_INPUT = list(eud_simple.index)
        #     END_USES_CATEGORIES = list(end_uses_categories.loc[:, 'END_USES_CATEGORIES'].unique())
        #     RESOURCES = list(resources_simple.index)
        #     RES_IMPORT_CONSTANT = ['GAS', 'GAS_RE', 'H2_RE', 'H2']  # TODO automatise
        #     BIOFUELS = list(resources[resources.loc[:, 'Subcategory'] == 'Biofuel'].index)
        #     RE_RESOURCES = list(
        #         resources.loc[(resources['Category'] == 'Renewable'), :].index)
        #     EXPORT = list(resources.loc[resources['Category'] == 'Export', :].index)
        #
        #     END_USES_TYPES_OF_CATEGORY = []
        #     for i in END_USES_CATEGORIES:
        #         li = list(end_uses_categories.loc[
        #                       end_uses_categories.loc[:, 'END_USES_CATEGORIES'] == i, 'END_USES_TYPES_OF_CATEGORY'])
        #         END_USES_TYPES_OF_CATEGORY.append(li)
        #
        #     # TECHNOLOGIES_OF_END_USES_TYPE -> # METHOD 2 (uses layer_in_out to determine the END_USES_TYPE)
        #     END_USES_TYPES = list(end_uses_categories.loc[:, 'END_USES_TYPES_OF_CATEGORY'])
        #
        #     ALL_TECHS = list(technologies_simple.index)
        #
        #     layers_in_out_tech = layers_in_out.loc[~layers_in_out.index.isin(RESOURCES), :]
        #     TECHNOLOGIES_OF_END_USES_TYPE = []
        #     for i in END_USES_TYPES:
        #         li = list(layers_in_out_tech.loc[layers_in_out_tech.loc[:, i] == 1, :].index)
        #         TECHNOLOGIES_OF_END_USES_TYPE.append(li)
        #
        #     # STORAGE and INFRASTRUCTURES
        #     ALL_TECH_OF_EUT = [item for sublist in TECHNOLOGIES_OF_END_USES_TYPE for item in sublist]
        #
        #     STORAGE_TECH = list(storage_eff_in.index)
        #     INFRASTRUCTURE = [item for item in ALL_TECHS if item not in STORAGE_TECH and item not in ALL_TECH_OF_EUT]
        #
        #     # EVs
        #     EVs_BATT = list(evs.loc[:, 'EVs_BATT'])
        #     V2G = list(evs.index)
        #
        #     # STORAGE_OF_END_USES_TYPES ->  #METHOD 2 (using storage_eff_in)
        #     STORAGE_OF_END_USES_TYPES_DHN = []
        #     STORAGE_OF_END_USES_TYPES_DEC = []
        #     STORAGE_OF_END_USES_TYPES_ELEC = []
        #     STORAGE_OF_END_USES_TYPES_HIGH_T = []
        #
        #     for i in STORAGE_TECH:
        #         if storage_eff_in.loc[i, 'HEAT_LOW_T_DHN'] > 0:
        #             STORAGE_OF_END_USES_TYPES_DHN.append(i)
        #         elif storage_eff_in.loc[i, 'HEAT_LOW_T_DECEN'] > 0:
        #             STORAGE_OF_END_USES_TYPES_DEC.append(i)
        #         elif storage_eff_in.loc[i, 'ELECTRICITY'] > 0:
        #             STORAGE_OF_END_USES_TYPES_ELEC.append(i)
        #         elif storage_eff_in.loc[i, 'HEAT_HIGH_T'] > 0:
        #             STORAGE_OF_END_USES_TYPES_HIGH_T.append(i)
        #
        #     STORAGE_OF_END_USES_TYPES_ELEC.remove('BEV_BATT')
        #     STORAGE_OF_END_USES_TYPES_ELEC.remove('PHEV_BATT')
        #
        #     # etc. still TS_OF_DEC_TECH and EVs_BATT_OF_V2G missing... -> hard coded !
        #
        #     COGEN = []
        #     BOILERS = []
        #
        #     for i in ALL_TECH_OF_EUT:
        #         if 'BOILER' in i:
        #             BOILERS.append(i)
        #         if 'COGEN' in i:
        #             COGEN.append(i)
        #
        #     # Adding AMPL syntax #
        #     # creating Batt_per_Car_df for printing
        #     batt_per_car_df = evs[['batt_per_car']]
        #     vehicule_capacity_df = evs[['vehicule_capacity']]
        #     state_of_charge_ev = ampl_syntax(state_of_charge_ev, '')
        #     loss_network_df = pd.DataFrame(data=loss_network.values(), index=loss_network.keys(), columns=[' '])
        #     # Putting all the df in ampl syntax
        #     batt_per_car_df = ampl_syntax(batt_per_car_df,
        #                                   '# ev_batt,size [GWh]: Size of batteries per car per technology of EV')
        #     vehicule_capacity_df = ampl_syntax(vehicule_capacity_df, '# km-pass/h/veh. : Gives the equivalence between '
        #                                                              'capacity and number of vehicles.')
        #     eud_simple = ampl_syntax(eud_simple, '')
        #     share_ned = ampl_syntax(share_ned, '')
        #     layers_in_out = ampl_syntax(layers_in_out, '')
        #     technologies_simple = ampl_syntax(technologies_simple, '')
        #     technologies_simple[technologies_simple > 1e+14] = 'Infinity'
        #     resources_simple = ampl_syntax(resources_simple, '')
        #     resources_simple[resources_simple > 1e+14] = 'Infinity'
        #     storage_eff_in = ampl_syntax(storage_eff_in, '')
        #     storage_eff_out = ampl_syntax(storage_eff_out, '')
        #     storage_characteristics = ampl_syntax(storage_characteristics, '')
        #     loss_network_df = ampl_syntax(loss_network_df, '')
        #
        #     # Printing data #
        #     # printing signature of data file
        #     header_file = (Path(__file__).parents[1] / 'headers' / 'header_data.txt')
        #     print_header(header_file=header_file, dat_file=out_path)
        #
        #     # printing sets
        #     print_set(SECTORS, 'SECTORS', out_path)
        #     print_set(END_USES_INPUT, 'END_USES_INPUT', out_path)
        #     print_set(END_USES_CATEGORIES, 'END_USES_CATEGORIES', out_path)
        #     print_set(RESOURCES, 'RESOURCES', out_path)
        #     print_set(RES_IMPORT_CONSTANT, 'RES_IMPORT_CONSTANT', out_path)
        #     print_set(BIOFUELS, 'BIOFUELS', out_path)
        #     print_set(RE_RESOURCES, 'RE_RESOURCES', out_path)
        #     print_set(EXPORT, 'EXPORT', out_path)
        #     newline(out_path)
        #     n = 0
        #     for j in END_USES_TYPES_OF_CATEGORY:
        #         print_set(j, 'END_USES_TYPES_OF_CATEGORY' + '["' + END_USES_CATEGORIES[n] + '"]', out_path)
        #         n += 1
        #     newline(out_path)
        #     n = 0
        #     for j in TECHNOLOGIES_OF_END_USES_TYPE:
        #         print_set(j, 'TECHNOLOGIES_OF_END_USES_TYPE' + '["' + END_USES_TYPES[n] + '"]', out_path)
        #         n += 1
        #     newline(out_path)
        #     print_set(STORAGE_TECH, 'STORAGE_TECH', out_path)
        #     print_set(INFRASTRUCTURE, 'INFRASTRUCTURE', out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# Storage subsets'])
        #     print_set(EVs_BATT, 'EVs_BATT', out_path)
        #     print_set(V2G, 'V2G', out_path)
        #     print_set(STORAGE_DAILY, 'STORAGE_DAILY', out_path)
        #     newline(out_path)
        #     print_set(STORAGE_OF_END_USES_TYPES_DHN, 'STORAGE_OF_END_USES_TYPES ["HEAT_LOW_T_DHN"]', out_path)
        #     print_set(STORAGE_OF_END_USES_TYPES_DEC, 'STORAGE_OF_END_USES_TYPES ["HEAT_LOW_T_DECEN"]', out_path)
        #     print_set(STORAGE_OF_END_USES_TYPES_ELEC, 'STORAGE_OF_END_USES_TYPES ["ELECTRICITY"]', out_path)
        #     print_set(STORAGE_OF_END_USES_TYPES_HIGH_T, 'STORAGE_OF_END_USES_TYPES ["HEAT_HIGH_T"]', out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# Link between storages & specific technologies	'])
        #     # Hardcoded
        #     print_set(['TS_DEC_HP_ELEC'], 'TS_OF_DEC_TECH ["DEC_HP_ELEC"]', out_path)
        #     print_set(['TS_DEC_DIRECT_ELEC'], 'TS_OF_DEC_TECH ["DEC_DIRECT_ELEC"]', out_path)
        #     print_set(['TS_DEC_THHP_GAS'], 'TS_OF_DEC_TECH ["DEC_THHP_GAS"]', out_path)
        #     print_set(['TS_DEC_COGEN_GAS'], 'TS_OF_DEC_TECH ["DEC_COGEN_GAS"]', out_path)
        #     print_set(['TS_DEC_ADVCOGEN_GAS'], 'TS_OF_DEC_TECH ["DEC_ADVCOGEN_GAS"]', out_path)
        #     print_set(['TS_DEC_COGEN_OIL'], 'TS_OF_DEC_TECH ["DEC_COGEN_OIL"]', out_path)
        #     print_set(['TS_DEC_ADVCOGEN_H2'], 'TS_OF_DEC_TECH ["DEC_ADVCOGEN_H2"]', out_path)
        #     print_set(['TS_DEC_BOILER_GAS'], 'TS_OF_DEC_TECH ["DEC_BOILER_GAS"]', out_path)
        #     print_set(['TS_DEC_BOILER_WOOD'], 'TS_OF_DEC_TECH ["DEC_BOILER_WOOD"]', out_path)
        #     print_set(['TS_DEC_BOILER_OIL'], 'TS_OF_DEC_TECH ["DEC_BOILER_OIL"]', out_path)
        #     print_set(['PHEV_BATT'], 'EVs_BATT_OF_V2G ["CAR_PHEV"]', out_path)
        #     print_set(['BEV_BATT'], 'EVs_BATT_OF_V2G ["CAR_BEV"]', out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# Additional sets, just needed for printing results	'])
        #     print_set(COGEN, 'COGEN', out_path)
        #     print_set(BOILERS, 'BOILERS', out_path)
        #     newline(out_path)
        #
        #     # printing parameters
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# -----------------------------'])
        #         writer.writerow(['# PARAMETERS NOT DEPENDING ON THE NUMBER OF TYPICAL DAYS : '])
        #         writer.writerow(['# -----------------------------	'])
        #         writer.writerow([''])
        #         writer.writerow(['## PARAMETERS presented in Table 2.	'])
        #     # printing i_rate, re_share_primary,gwp_limit,solar_area
        #     print_param('i_rate', i_rate, 'part [2.7.4]', out_path)
        #     print_param('re_share_primary', re_share_primary, 'Minimum RE share in primary consumption', out_path)
        #     print_param('gwp_limit', gwp_limit, 'gwp_limit [ktCO2-eq./year]: maximum GWP emissions', out_path)
        #     print_param('solar_area', solar_area, '', out_path)
        #     print_param('power_density_pv', power_density_pv, 'PV : 1 kW/4.22m2   => 0.2367 kW/m2 => 0.2367 GW/km2',
        #                 out_path)
        #     print_param('power_density_solar_thermal', power_density_solar_thermal,
        #                 'Solar thermal : 1 kW/3.5m2 => 0.2857 kW/m2 => 0.2857 GW/km2', out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# Part [2.4]	'])
        #     print_df('param:', batt_per_car_df, out_path)
        #     newline(out_path)
        #     print_df('param:', vehicule_capacity_df, out_path)
        #     newline(out_path)
        #     print_df('param state_of_charge_ev :', state_of_charge_ev, out_path)
        #     newline(out_path)
        #
        #     # printing c_grid_extra and import_capacity
        #     print_param('c_grid_extra', c_grid_extra,
        #                 'cost to reinforce the grid due to intermittent renewable energy penetration. See 2.2.2',
        #                 out_path)
        #     print_param('import_capacity', import_capacity, '', out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# end_Uses_year see part [2.1]'])
        #     print_df('param end_uses_demand_year : ', eud_simple, out_path)
        #     newline(out_path)
        #     print_param('share_mobility_public_min', share_mobility_public_min, '', out_path)
        #     print_param('share_mobility_public_max', share_mobility_public_max, '', out_path)
        #     newline(out_path)
        #     print_param('share_freight_train_min', share_freight_train_min, '', out_path)
        #     print_param('share_freight_train_max', share_freight_train_max, '', out_path)
        #     newline(out_path)
        #     print_param('share_freight_road_min', share_freight_road_min, '', out_path)
        #     print_param('share_freight_road_max', share_freight_road_max, '', out_path)
        #     newline(out_path)
        #     print_param('share_freight_boat_min', share_freight_boat_min, '', out_path)
        #     print_param('share_freight_boat_max', share_freight_boat_max, '', out_path)
        #     newline(out_path)
        #     print_param('share_heat_dhn_min', share_heat_dhn_min, '', out_path)
        #     print_param('share_heat_dhn_max', share_heat_dhn_max, '', out_path)
        #     newline(out_path)
        #     print_df('param:', share_ned, out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# Link between layers  (data from Tables 19,21,22,23,25,29,30)'])
        #     print_df('param layers_in_out : ', layers_in_out, out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(
        #             ['# Technologies data from Tables (10,19,21,22,23,25,27,28,29,30) and part [2.2.1.1] for hydro'])
        #     print_df('param :', technologies_simple, out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# RESOURCES: part [2.5] (Table 26)'])
        #     print_df('param :', resources_simple, out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(
        #             ['# Storage inlet/outlet efficiency : part [2.6] (Table 28) and part [2.2.1.1] for hydro.	'])
        #     print_df('param storage_eff_in :', storage_eff_in, out_path)
        #     newline(out_path)
        #     print_df('param storage_eff_out :', storage_eff_out, out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# Storage characteristics : part [2.6] (Table 28) and part [2.2.1.1] for hydro.'])
        #     print_df('param :', storage_characteristics, out_path)
        #     newline(out_path)
        #     with open(out_path, mode='a', newline='') as file:
        #         writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
        #         writer.writerow(['# [A.6]'])
        #     print_df('param loss_network ', loss_network_df, out_path)

    def print_td_data(self, EUD_params=None, RES_params=None, RES_mult_params=None):
        """


        Returns
        -------

        """

        # PRELIMINARY COMPUTATIONS
        # From temporal aggregation results (td_of_days): generate t_h_td and td_count
        # and compute rescaled typical days ts and peak_sh_factor for each region
        self.ta.generate_t_h_td()
        peak_sh_factor = pd.DataFrame(0, index=self.regions_names, columns=['peak_sh_factor'])
        peak_sc_factor = pd.DataFrame(0, index=self.regions_names, columns=['peak_sc_factor'])
        for r in self.regions:
            self.regions[r].rescale_td_ts(self.ta.td_count)
            self.regions[r].compute_peak_sh_and_sc()
            peak_sh_factor.loc[r, 'peak_sh_factor'] = self.regions[r].peak_sh_factor
            peak_sc_factor.loc[r, 'peak_sc_factor'] = self.regions[r].peak_sc_factor

        t_h_td = self.ta.t_h_td.copy()
        t_h_td['par_l'] = '('
        t_h_td['par_r'] = ')'
        t_h_td['comma1'] = ','
        t_h_td['comma2'] = ','
        t_h_td = t_h_td[['par_l', 'H_of_Y', 'comma1', 'H_of_D', 'comma2', 'TD_number', 'par_r']]  # reordering columns

        # file to print to
        dat_file = self.dat_dir / ('ESMC_' + str(self.Nbr_TD) + 'TD.dat')

        # PRINTING
        # printing signature of data file
        dp.print_header(self.project_dir / 'esmc' / 'energy_model' / 'headers' / 'header_td_data.txt', dat_file)

        # printing set depending on TD

        # printing set TYPICAL_DAYS -> replaced by printing param nbr_tds
        # dp.print_set(my_set=[str(i) for i in np.arange(1, self.Nbr_TD + 1)],out_path=dat_file,name='TYPICAL_DAYS', comment='# typical days')
        # printing set T_H_TD
        dp.newline(dat_file, ['set T_H_TD := 		'])
        t_h_td.to_csv(dat_file, sep='\t', header=False, index=False, mode='a', quoting=csv.QUOTE_NONE)
        dp.end_table(dat_file)
        # printing parameters depending on TD
        # printing interlude
        dp.newline(dat_file, ['# -----------------------------', '# PARAMETERS DEPENDING ON NUMBER OF TYPICAL DAYS : ',
                              '# -----------------------------', ''])
        # printing nbr_tds
        dp.print_param(param=self.Nbr_TD, out_path=dat_file, name='nbr_tds')
        # printing peak_sh_factor and peak_sc_factor
        dp.print_df(df=dp.ampl_syntax(peak_sh_factor), out_path=dat_file, name='param ')
        dp.print_df(df=dp.ampl_syntax(peak_sc_factor), out_path=dat_file, name='param ')

        # Default name of timeseries in DATA.xlsx and corresponding name in ESTD data file
        if EUD_params is None:
            # for EUD timeseries
            EUD_params = {'Electricity (%_elec)': 'param electricity_time_series :=',
                          'Space Heating (%_sh)': 'param heating_time_series :=',
                          'Space Cooling (%_sc)': 'param cooling_time_series :=',
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

        # if only 1 country
        N_c = 2  # TODO check if need adaptation for 1 region
        if N_c == 1:
            logging.warning('Only one region defined')
            # # printing EUD timeseries param
            # for l in EUD_params.keys():
            #     with open(out_path, mode='a', newline='\n') as TD_file:
            #         TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
            #                                lineterminator="\n")
            #         TD_writer.writerow([EUD_params[l][0:-1]])
            #     for c in countries:
            #         name = l + '_' + c
            #         ts = all_TD_ts[name]
            #         ts.columns = np.arange(1, Nbr_TD + 1)
            #         ts = ts * norm[name] / norm_TD[name]
            #         ts.fillna(0, inplace=True)
            #         ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
            #         ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='', mode='a', quoting=csv.QUOTE_NONE)
            #     with open(out_path, mode='a', newline='\n') as TD_file:
            #         TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
            #                                lineterminator="\n")
            #         TD_writer.writerow(';')
            #         TD_writer.writerow([''])
            #
            # # printing c_p_t param #
            # with open(out_path, mode='a', newline='\n') as TD_file:
            #     TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
            #                            lineterminator="\n")
            #     TD_writer.writerow(['param c_p_t:='])
            #     # printing c_p_t part where 1 ts => 1 tech
            # for l in RES_params.keys():
            #     for c in countries:
            #         name = l + '_' + c
            #         ts = all_TD_ts[name]
            #         ts.columns = np.arange(1, Nbr_TD + 1)
            #         ts = ts * norm[name] / norm_TD[name]
            #         ts.fillna(0, inplace=True)
            #         ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
            #         ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='["' + RES_params[l] + '",*,*] :',
            #                   mode='a', quoting=csv.QUOTE_NONE)
            # # printing c_p_t part where 1 ts => more then 1 tech
            # for l in RES_mult_params.keys():
            #     for j in RES_mult_params[l]:
            #         for c in countries:
            #             name = l + '_' + c
            #             ts = all_TD_ts[name]
            #             ts.columns = np.arange(1, Nbr_TD + 1)
            #             ts = ts * norm[name] / norm_TD[name]
            #             ts.fillna(0, inplace=True)
            #             ts.rename(columns={ts.shape[1]: str(ts.shape[1]) + ' ' + ':='}, inplace=True)
            #             ts.to_csv(out_path, sep='\t', header=True, index=True, index_label='["' + j + '",*,*] :', mode='a',
            #                       quoting=csv.QUOTE_NONE)
            #
            # with open(out_path, mode='a', newline='\n') as TD_file:
            #     TD_writer = csv.writer(TD_file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
            #                            lineterminator="\n")
            #     TD_writer.writerow([';'])
        else:
            # printing EUD timeseries param
            for l in EUD_params.keys():
                dp.newline(out_path=dat_file, comment=[EUD_params[l]])
                for r in self.regions:
                    # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the name of the time series, put it into ampl syntax and print it
                    dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(l, slice(None)), :].droplevel(level=0)),
                                out_path=dat_file,
                                name='["' + r + '",*,*] : ', end_table=False)
                dp.end_table(out_path=dat_file)

            # printing c_p_t param #
            dp.newline(out_path=dat_file, comment=['param c_p_t:='])
            # printing c_p_t part where 1 ts => 1 tech
            for l in RES_params.keys():
                for r in self.regions:
                    # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the name of the time series, put it into ampl syntax and print it
                    dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(l, slice(None)), :].droplevel(level=0)),
                                out_path=dat_file,
                                name='["' + RES_params[l] + '","' + r + '",*,*] :', end_table=False)

            # printing c_p_t part where 1 ts => more then 1 tech
            for l in RES_mult_params.keys():
                for j in RES_mult_params[l]:
                    for r in self.regions:
                        # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the name of the time series, put it into ampl syntax and print it
                        dp.print_df(
                            df=dp.ampl_syntax(self.regions[r].ts_td.loc[(l, slice(None)), :].droplevel(level=0)),
                            out_path=dat_file, name='["' + j + '","' + r + '",*,*] :', end_table=False)

            dp.end_table(out_path=dat_file)
        return

    def set_esom(self, ref_dir=None, ampl_options=None, copy=True):
        """

        Set the energy system optimisation model (esom) with the mod and dat files from ref_dir that are copied into the

        """

        # path where to copy them for this case study
        mod_path =  self.cs_dir/'ESMC_model_AMPL.mod'
        data_path = [self.cs_dir/('ESMC_' + str(self.Nbr_TD) + 'TD.dat'),
                     self.cs_dir / 'ESMC_indep.dat',
                     self.cs_dir / 'ESMC_countries.dat']

        # TODO adapt for the case where we print countries.dat and indep.dat from data
        # if new case study, we copy ref files if not, we keep the ones that exist
        if copy:
            # path of the reference files for ampl
            if ref_dir is None:
                ref_dir = self.project_dir / 'case_studies' / 'dat_files'

            mod_ref = self.project_dir / 'esmc' / 'energy_model' / 'ESMC_model_AMPL.mod'
            data_ref = [ref_dir / self.space_id / ('ESMC_' + str(self.Nbr_TD) + 'TD.dat'),
                        ref_dir / 'ESMC_indep.dat',
                        ref_dir / self.space_id / 'ESMC_countries.dat']

            # copy the files from ref_dir to case_study directory
            shutil.copyfile(mod_ref, mod_path)
            shutil.copyfile(data_ref[0], data_path[0])
            shutil.copyfile(data_ref[1], data_path[1])
            shutil.copyfile(data_ref[2], data_path[2])

        # default ampl_options
        if ampl_options is None:
            cplex_options = ['baropt',
                             'predual=-1',
                             'barstart=4',
                             'crossover=0'
                             'timelimit 64800',
                             'bardisplay=1',
                             'prestats=0',
                             'display=0']
            cplex_options_str = ' '.join(cplex_options)
            ampl_options = {'show_stats': 3,
                            'log_file': str(self.cs_dir/'log.txt'),
                            'presolve': 0,
                            'times': 0,
                            'gentimes': 0,
                            'cplex_options': cplex_options_str}

        # set ampl for step_2
        self.esom = OptiProbl(mod_path=mod_path, data_path=data_path, options=ampl_options)
        return

    def solve_esom(self, run=True, outputs=True):
        """Solves the esom wih ampl

        Parameters
        ----------
        run
        outputs

        Returns
        -------

        """
        #TODO
        # Add possibility to choose options
        # Add possibility to print things into the log

        # update version tracking json file
        self.update_version()
        # print in log emission limit
        self.esom.ampl.eval('print "gwp_limit_overall [ktCO2eq/y]", gwp_limit_overall;')
        self.esom.ampl.eval('print "Number of TDs", last(TYPICAL_DAYS);	')

        if run:
            self.esom.run_ampl()
            self.esom.get_solve_time()
            # print in log main outputs
            self.esom.ampl.eval('print "TotalGWP_global", sum{c in COUNTRIES} (TotalGWP[c]);')
            self.esom.ampl.eval('print "GWP_op_global", sum{c in COUNTRIES, r in RESOURCES} (GWP_op[c,r]);')
            self.esom.ampl.eval('print "CO2_net_global", sum{c in COUNTRIES, r in RESOURCES} (CO2_net[c,r]);')
            self.esom.ampl.eval('print "TotalCost_global", sum{c in COUNTRIES} (TotalCost[c]);')


        if outputs:
            self.esom.get_outputs()
        return

    def prints_esom(self, inputs=True, outputs=True, solve_time=False):
        if inputs:
            self.esom.print_inputs()
        if outputs:
            self.esom.print_outputs(solve_time=solve_time)
        return





