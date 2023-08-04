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
from esmc.utils.df_utils import clean_indices
from esmc.common import CSV_SEPARATOR, AMPL_SEPARATOR
import shutil
import git
import pandas as pd
import csv
from pathlib import Path
from datetime import datetime


# TODO
# adapt exchanges modelling by using this syntax (Borasio's wmodels): var ship
# {LAYERS, HOURS, TYPICAL_DAYS, r in REGIONS, r2 in REGIONS:r <> r2}; # resources transfer from one region (r)
# to another (r2)
# add logging and time different steps
# dat_files not on github -> extern person cannot use them...
# add error when no ampl license
# check error DHN into sankey
# to compute yearly exchanges -> sum over the year positive and negative part of each link
# try approach of exchanges more on the link point of view
# add into .mod some variables to have general results (ex: total prod over year:
# Tech_wnd [y,l,tech] = sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}
# layers_in_out [y,tech,l] * F_t [y,tech, h, td];))
# /!\ data into xlsx not the same as in indep.dat and regions.dat (at least for layers_in_out)
# * get rid of csp in countries where it is weird
# * get rid of add_var?
# * put something that detects if problem in run


# TODO check 18TDs


class Esmc:
    """

    TODO Update documentation

    Parameters
    ----------


    """

    def __init__(self, config, nbr_td=14):
        # identification of case study
        self.case_study = config['case_study']
        self.comment = config['comment']
        self.regions_names = config['regions_names']
        self.regions_names.sort()
        self.space_id = '_'.join(self.regions_names)  # identification of the spatial case study in one string
        self.nbr_td = nbr_td
        # TODO integrate in print .dat
        self.gwp_limit_overall = config['gwp_limit_overall']  # None or number
        self.re_share_primary = config['re_share_primary']  # None or dict giving the re_share_primary in each region
        self.f_perc = config['f_perc']  # True or False
        self.year = config['year']

        # path definition
        self.project_dir = Path(__file__).parents[2]
        self.dat_dir = self.project_dir / 'case_studies' / self.space_id / '00_td_dat'
        self.cs_dir = self.project_dir / 'case_studies' / self.space_id / self.case_study
        # create directories
        self.dat_dir.mkdir(parents=True, exist_ok=True)
        self.cs_dir.mkdir(parents=True, exist_ok=True)

        # create and initialize regions
        self.ref_region_name = config['ref_region']
        self.ref_region = None
        self.regions = dict.fromkeys(self.regions_names, None)
        # create and initialize data dictionnaries
        self.sets = dict()
        self.data_indep = dict.fromkeys(['Misc_indep', 'Layers_in_out', 'Resources_indep',
                                         'Storage_characteristics', 'Storage_eff_in', 'Storage_eff_out'
                                         ])  # data independent from regions considered
        self.data_reg = dict.fromkeys(['Exch', 'Demands', 'Technologies',
                                       'Storage_power_to_energy', 'Misc'])  # data specific to regions considered

        # initialize TemporalAggregation object
        self.ta = None
        # TODO self.spatial_aggreg = object spatial_aggreg
        #

        # create energy system optimization problem (esom)
        self.esom = None

        # create empty dictionary to be filled with main results
        self.results = dict.fromkeys(['TotalCost', 'Cost_breakdown', 'Gwp_breakdown', 'Transfer_capacity',
                                      'Exchanges_year', 'Resources',
                                      'Assets', 'Sto_assets', 'Year_balance', 'Curt'])
        self.hourly_results = dict()

        return

    # TODO add an automated initialization for specific pipeline

    def init_regions(self):
        logging.info('Initialising regions: ' + ', '.join(self.regions_names))
        data_dir = self.project_dir / 'Data' / str(self.year)
        self.ref_region = Region(nuts=self.ref_region_name, data_dir=data_dir, ref_region=True)
        for r in self.regions_names:
            if r != self.ref_region_name:
                self.regions[r] = copy.deepcopy(self.ref_region)
                self.regions[r].__init__(nuts=r, data_dir=data_dir, ref_region=False)
            else:
                self.regions[r] = self.ref_region

        self.read_data_exch()
        return

    def init_ta(self, algo='kmedoid', ampl_path=None):
        """Initialize the temporal aggregator

        """
        logging.info('Initializing TemporalAggregation with ' + algo + ' algorithm')
        self.ta = TemporalAggregation(self.regions, self.dat_dir, Nbr_TD=self.nbr_td, algo=algo,
                                      ampl_path=ampl_path,
                                      time_series_mapping=self.data_indep['Misc_indep']['time_series_mapping'])
        return

    def update_version(self):
        """Updating version file

        Updating the version.json file into case_studies directory to add the description of this run

        """
        # path of case_studies dir
        cs_versions = self.cs_dir.parent / 'versions.json'

        # logging info
        logging.info('Updating ' + str(cs_versions))

        # get git commit used
        repo = git.Repo(search_parent_directories=True)
        commit_name = repo.head.commit.summary

        # get current datetime
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # read versions dict
        try:
            versions = a2p.read_json(cs_versions)
        except FileNotFoundError:
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

    def read_data_exch(self):
        """Read the data related to exchanges and sores it into the dict attribute data_reg['Exch']

        """
        data_path = self.project_dir / 'Data' / str(self.year) / '01_EXCH'
        # logging info
        logging.info('Read exchanges data from ' + str(data_path))
        # read data
        self.data_reg['Exch'] = dict()
        # self.data_reg['Exch']['Dist'] = pd.read_csv(data_path / 'Dist.csv', sep=CSV_SEPARATOR,
        #                                             header=[0], index_col=[0]).loc[self.regions_names, :]
        self.data_reg['Exch']['Dist'] = pd.read_csv(data_path / 'Dist.csv', sep=CSV_SEPARATOR,
                                                    header=[0], index_col=[0,1]).loc[
                                        (self.regions_names, self.regions_names), :]
        self.data_reg['Exch']['Exchange_losses'] = pd.read_csv(data_path / 'Exchange_losses.csv', sep=CSV_SEPARATOR,
                                                    header=[0], index_col=[0])
        r_path = (data_path / 'Misc_exch.json')
        if r_path.is_file(): # if the file exist, update the data
            self.data_reg['Exch']['Misc_exch'] = a2p.read_json(r_path)

        self.data_reg['Exch']['Lhv'] = pd.read_csv(data_path / 'Lhv.csv', sep=CSV_SEPARATOR, header=[0], index_col=[0])\
                                           .loc[self.data_reg['Exch']['Misc_exch']['add_sets']['EXCHANGE_FREIGHT_R'], :]

        self.data_reg['Exch']['Network_exchanges'] = pd.read_csv(data_path / 'Network_exchanges.csv', sep=CSV_SEPARATOR,
                                                      header=[0], index_col=[0, 1, 2, 3]).loc[
                                          (self.regions_names, self.regions_names,
                                           self.data_reg['Exch']['Misc_exch']['add_sets']['EXCHANGE_NETWORK_R'],
                                           slice(None)), :]

    def read_data_indep(self):
        """Read data independent of the region dimension of the problem

        """
        data_path = self.project_dir / 'Data' / str(self.year) / '00_INDEP'
        # logging info
        logging.info('Read indep data from ' + str(data_path))
        # reading misc_indep
        r_path = (data_path / 'Misc_indep.json')
        if r_path.is_file():  # if the file exist, update the data
            self.data_indep['Misc_indep'] = a2p.read_json(r_path)
        # reading layers_in_out
        self.data_indep['Layers_in_out'] = pd.read_csv(data_path / 'Layers_in_out.csv', sep=CSV_SEPARATOR, header=[0],
                                                       index_col=[0])
        self.data_indep['Layers_in_out'] = clean_indices(self.data_indep['Layers_in_out'])
        # reading resources_indep
        self.data_indep['Resources_indep'] = clean_indices(pd.read_csv(data_path / 'Resources_indep.csv',
                                                                       sep=CSV_SEPARATOR, header=[2], index_col=[2]))\
            .drop(columns=['Comment'])
        # reading storage_characteristics
        self.data_indep['Storage_characteristics'] = clean_indices(pd.read_csv(data_path / 'Storage_characteristics.csv'
                                                                   ,sep=CSV_SEPARATOR, header=[0], index_col=[0]))
        # reading storage_eff_in
        self.data_indep['Storage_eff_in'] = clean_indices(pd.read_csv(data_path / 'Storage_eff_in.csv',
                                                                      sep=CSV_SEPARATOR, header=[0], index_col=[0]))\
            .dropna(axis=0, how='all')
        # reading storage_eff_out
        self.data_indep['Storage_eff_out'] = clean_indices(pd.read_csv(data_path / 'Storage_eff_out.csv', sep=CSV_SEPARATOR,
                                                                      header=[0], index_col=[0])) \
            .dropna(axis=0, how='all')
        return

    def concat_reg_data(self, to_concat: []):
        """ Concatenates across regions the input data corresponding to to_concat

        Parameters
        ----------
        to_concat: list
        List of the names of the dataframes to concatenate
        (acceptable values: ['Demands', 'Resources', 'Technologies', 'Storage_power_to_energy',
                            'Time_series', 'Weights', 'Misc']

        Returns
        -------
        out: tuple
        Tuple containing the concatenated data for all except Misc, it give multiindex pandas dataframes.
        For Misc, it provides a dict with a dataframe for share_ned and a dataframe for the other data

        """

        # Create frames for concatenation
        frames = dict.fromkeys(to_concat)
        # Misc need a special procedure because it contains less homogenous data
        if 'Misc' in to_concat:
            frames['Misc'] = dict.fromkeys(['misc', 'share_ned'])

        for c in to_concat:
            if c == 'Misc':
                frames[c]['misc'] = list()
                frames[c]['share_ned'] = list()
            else:
                frames[c] = list()

            for n, r in self.regions.items():
                if c == 'Misc':
                    d = r.data[c].copy()
                    share_ned = d.pop('share_ned')
                    frames[c]['misc'].append(pd.Series(d))
                    frames[c]['share_ned'].append(pd.Series(share_ned))
                else:
                    frames[c].append(r.data[c].copy())

        # Concatenate and store into a tuple
        out = tuple()
        for c in to_concat:
            if c == 'Misc':
                misc_dict = dict.fromkeys(['misc', 'share_ned'])
                misc_dict['misc'] = pd.concat(frames[c]['misc'], axis=1, keys=self.regions_names, join='inner').T
                misc_dict['share_ned'] = pd.concat(frames[c]['share_ned'], axis=1,
                                                   keys=self.regions_names, join='inner').T
                out = out + (misc_dict,)
            else:
                out = out + (pd.concat(frames[c], axis=0, keys=self.regions_names, join='inner'),)

        return out

    def print_data(self, indep=False):
        """
        TODO add doc
        """
        # Logging
        logging.info('Printing regional data into ' + str(self.cs_dir))

        # Concatenate data across regions
        self.data_reg['Demands'], self.data_reg['Resources'], \
            self.data_reg['Technologies'], self.data_reg['Storage_power_to_energy'], self.data_reg['Misc'] = \
            self.concat_reg_data(to_concat=['Demands', 'Resources', 'Technologies', 'Storage_power_to_energy', 'Misc'])

        # Print demands, resources, technologies and storage power to energy
        for n in ['Demands', 'Resources', 'Technologies', 'Storage_power_to_energy']:
            df = self.data_reg[n].drop(columns=['Category', 'Subcategory', 'Technologies name', 'Units', 'Comment']
                                       , errors='ignore')
            df = df.mask(df > 1e14, 'Infinity')

            if n == 'Demands':
                name = 'param end_uses_demand_year : '
            else:
                name = 'param : '

            dp.print_df(df=dp.ampl_syntax(df),
                        out_path=self.cs_dir / ('reg_' + n.lower() + '.dat'),
                        name=name,
                        mode='w')

        # Process and print misc data

        # Get set of regions without dam
        df = self.data_reg['Technologies'].loc[(slice(None), 'HYDRO_DAM'), 'f_max']
        rwithoutdam = list(df.loc[df < 1e-2].index.get_level_values(level=0))

        # Print reg_misc.dat
        misc_file = self.cs_dir / 'reg_misc.dat'

        dp.print_header(dat_file=misc_file, header_txt='File containing miscellaneous sets and parameters')

        dp.print_set(my_set=self.regions_names, out_path=misc_file, name='REGIONS')
        dp.newline(out_path=misc_file)
        dp.print_set(my_set=rwithoutdam, out_path=misc_file, name='RWITHOUTDAM', comment='# Regions without hydro dam')
        dp.newline(out_path=misc_file)

        dp.print_df(dp.ampl_syntax(self.data_reg['Misc']['share_ned']), out_path=misc_file, name='param share_ned :')

        step = 4
        for i in np.arange(0, self.data_reg['Misc']['misc'].shape[1], step):
            df = self.data_reg['Misc']['misc'].iloc[:, i:i + step]  # select a subset of df
            df = df.mask(df > 1e14, 'Infinity')  # replace high numbers by Infinity
            dp.print_df(dp.ampl_syntax(df), out_path=misc_file, name='param :')

        # Print reg_exch.dat
        exch_file = self.cs_dir / 'reg_exch.dat'

        dp.print_header(dat_file=exch_file, header_txt='File containing data related to exchanges between regions')

        for n, d in self.data_reg['Exch'].items():
            if n != 'Misc_exch':
                dp.print_df(dp.ampl_syntax(d), out_path=exch_file, name='param : ')
            else:
                for n2, d2 in d.items():
                    if type(d2) is dict:
                        if n2 != 'add_sets':
                            df = pd.DataFrame.from_dict(d2, orient='index', columns=[n2])
                            name = 'param : '
                            df = df.mask(df > 1e14, 'Infinity')
                            dp.print_df(df=dp.ampl_syntax(df),
                                        out_path=exch_file,
                                        name=name,
                                        mode='a')
                            dp.newline(out_path=exch_file)
                        else:
                            pass
                    else:
                        if d2 > 1e14:
                            d2 = 'Infinity'
                        dp.print_param(param=d2, out_path=exch_file, name=n2)
                        dp.newline(out_path=exch_file)

        if indep:
            # Building SETS from data #
            # demand related sets
            self.sets['SECTORS'] = list(self.ref_region.data['Demands']
                                        .drop(columns=['Category', 'Subcategory', 'Units']).columns)
            self.sets['END_USES_INPUT'] = list(self.ref_region.data['Demands'].index)
            self.sets['END_USES_CATEGORIES'] = list(self.data_indep['Misc_indep']['add_sets']['END_USES_CATEGORIES'].keys())
            self.sets['END_USES_TYPES_OF_CATEGORY'] = self.data_indep['Misc_indep']['add_sets']['END_USES_CATEGORIES']
            eut = list(self.sets['END_USES_TYPES_OF_CATEGORY'].values())
            eut = [item for sublist in eut for item in sublist] # flatten list
            # resources related sets
            self.sets['RESOURCES'] = list(self.data_indep['Resources_indep'].index)
            self.sets['RE_FUELS'] = list(self.data_indep['Resources_indep'][self.data_indep['Resources_indep']
                                         .loc[:, 'Subcategory'] == 'Renewable fuel'].index)
            self.sets['RE_RESOURCES'] = list(self.data_indep['Resources_indep'][self.data_indep['Resources_indep']
                                         .loc[:, 'Category'] == 'Renewable'].index)
            self.sets['EXPORT'] = list(self.data_indep['Resources_indep'][self.data_indep['Resources_indep']
                                       .loc[:,'Category'] == 'Export'].index)
            self.sets['NOT_LAYERS'] = self.data_indep['Misc_indep']['add_sets']['NOT_LAYERS']
            # exchanges related sets
            self.sets['EXCHANGE_FREIGHT_R'] = self.data_reg['Exch']['Misc_exch']['add_sets']['EXCHANGE_FREIGHT_R']
            self.sets['EXCHANGE_NETWORK_R'] = self.data_reg['Exch']['Misc_exch']['add_sets']['EXCHANGE_NETWORK_R']
            self.sets['NETWORK_TYPE'] = self.data_reg['Exch']['Misc_exch']['add_sets']['NETWORK_TYPE']

            self.sets['NOEXCHANGES'] = list(set(self.sets['RESOURCES']) - set(self.sets['EXCHANGE_FREIGHT_R'])
                                                                             - set(self.sets['EXCHANGE_NETWORK_R']))
            # technologies related sets
            all_techs = list(self.ref_region.data['Technologies'].index)
            layers_in_out_tech = self.data_indep['Layers_in_out'].loc[~self.data_indep['Layers_in_out'].index.isin(self.sets['RESOURCES']), :]
            self.sets['TECHNOLOGIES_OF_END_USES_TYPE'] = dict.fromkeys(eut)
            for i in eut:
                li = list(layers_in_out_tech.loc[layers_in_out_tech.loc[:, i] == 1, :].index)
                self.sets['TECHNOLOGIES_OF_END_USES_TYPE'][i] = li

            all_tech_of_eut = [item for sublist in list(self.sets['TECHNOLOGIES_OF_END_USES_TYPE'].values()) for item in sublist]

            self.sets['STORAGE_TECH'] = list(self.data_indep['Storage_eff_in'].index)
            self.sets['INFRASTRUCTURE'] = [item for item in all_techs
                                           if item not in self.sets['STORAGE_TECH']
                                           and item not in all_tech_of_eut]
            self.sets['EVs_BATT'] = self.data_indep['Misc_indep']['add_sets']['EVs_BATT']
            self.sets['V2G'] = self.data_indep['Misc_indep']['add_sets']['V2G']

            self.sets['STORAGE_DAILY'] = self.data_indep['Misc_indep']['add_sets']['STORAGE_DAILY']
            self.sets['STORAGE_OF_END_USES_TYPE'] = dict.fromkeys(eut)
            for i in eut:
                li = list(self.data_indep['Storage_eff_in'].loc[self.data_indep['Storage_eff_in'].loc[:, i] > 0, :].index)
                self.sets['STORAGE_OF_END_USES_TYPE'][i] = li
            self.sets['STORAGE_OF_END_USES_TYPE']\
                = {k: v for k, v in self.sets['STORAGE_OF_END_USES_TYPE'].items() if v}  # Get rid of empty keys
            dec_tech = self.sets['TECHNOLOGIES_OF_END_USES_TYPE']['HEAT_LOW_T_DECEN'].copy()
            # TODO autmatise the thing about DEC_SOLAR?
            dec_tech.remove('DEC_SOLAR')
            ts_of_dec_tech = [['TS_' + item] for item in dec_tech]
            self.sets['TS_OF_DEC_TECH'] = dict(zip(dec_tech, ts_of_dec_tech))
            self.sets['EVs_BATT_OF_V2G'] = dict(zip(self.sets['V2G'], [[item] for item in self.sets['EVs_BATT']]))
            self.sets['BOILERS'] = []
            self.sets['COGEN'] = []
            for i in all_tech_of_eut:
                if 'BOILER' in i:
                    self.sets['BOILERS'].append(i)
                if 'COGEN' in i:
                    self.sets['COGEN'].append(i)

            # Printing indep.dat #
            indep_file = self.cs_dir / 'indep.dat'
            # Header
            dp.print_header(dat_file=indep_file,
                            header_txt='File containing data independent of the modelled regions')
            # Sets
            dp.newline(out_path=indep_file, comment=['#----------------------------------------',
                                                     '# SETS not depending on TD, nor on REGIONS',
                                                     '#----------------------------------------'])
            for n,s in self.sets.items():
                if type(s) is list:
                    dp.print_set(my_set=s, out_path=indep_file, name=n)
                else:
                    for n2,s2 in s.items():
                        dp.print_set(my_set=s2, out_path=indep_file, name=(n + '["' + n2 + '"]'))
            # Parameters
            dp.newline(out_path=indep_file, comment=['',
                                                     '#----------------------------------------',
                                                     '# PARAMETERS NOT DEPENDING ON THE NUMBER OF TYPICAL DAYS, '
                                                     'NOR ON THE REGIONS :',
                                                     '#----------------------------------------'])
            # TODO is it possible to bettter automatise this?
            for n,d in self.data_indep.items():
                if n != 'Misc_indep':
                    df = d.drop(
                        columns=['Category', 'Subcategory', 'Technologies name', 'Units', 'Comment']
                        , errors='ignore')
                    df = df.mask(df > 1e14, 'Infinity')

                    if n == 'Layers_in_out':
                        name = 'param layers_in_out : '
                    elif n == 'Storage_eff_in':
                        name = 'param storage_eff_in : '
                    elif n == 'Storage_eff_out':
                        name = 'param storage_eff_out : '
                    else:
                        name = 'param : '

                    dp.print_df(df=dp.ampl_syntax(df),
                                out_path=indep_file,
                                name=name,
                                mode='a')
                    dp.newline(out_path=indep_file)
                else:
                    for n2,d2 in d.items():
                        if type(d2) is dict:
                            if n2 != 'add_sets' and n2 != 'time_series_mapping':
                                if n2 == 'state_of_charge_ev':
                                    df = pd.DataFrame.from_dict(d2, orient='index', columns=np.arange(1,25))
                                    name = 'param state_of_charge_ev : '
                                else:
                                    df = pd.DataFrame.from_dict(d2,orient='index', columns=[n2])
                                    name = 'param : '

                                df = df.mask(df > 1e14, 'Infinity')
                                dp.print_df(df=dp.ampl_syntax(df),
                                            out_path=indep_file,
                                            name=name,
                                            mode='a')
                                dp.newline(out_path=indep_file)
                            else:
                                pass

                        else:
                            if d2 > 1e14:
                                d2 = 'Infinity'
                            dp.print_param(param=d2, out_path=indep_file, name=n2)
                            dp.newline(out_path=indep_file)
        return

    def print_td_data(self, eud_params=None, res_params=None, res_mult_params=None):
        """


        Returns
        -------

        """

        # file to print to
        dat_file = self.cs_dir / ('reg_' + str(self.nbr_td) + 'TD.dat')

        # logging info
        logging.info('Printing TD data into ' + str(dat_file))

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

        # PRINTING
        # printing signature of data file
        dp.print_header(dat_file=dat_file
                        , header_file=self.project_dir / 'esmc' / 'energy_model' / 'headers' / 'header_td_data.txt'
                        )

        # printing set depending on TD

        # printing set TYPICAL_DAYS -> replaced by printing param nbr_tds
        # dp.print_set(my_set=[str(i) for i in np.arange(1, self.Nbr_TD + 1)],out_path=dat_file,name='TYPICAL_DAYS',
        # comment='# typical days')
        # printing set T_H_TD
        dp.newline(dat_file, ['set T_H_TD := 		'])
        t_h_td.to_csv(dat_file, sep=AMPL_SEPARATOR, header=False, index=False, mode='a', quoting=csv.QUOTE_NONE)
        dp.end_table(dat_file)
        # printing parameters depending on TD
        # printing interlude
        dp.newline(dat_file, ['# -----------------------------', '# PARAMETERS DEPENDING ON NUMBER OF TYPICAL DAYS : ',
                              '# -----------------------------', ''])
        # printing nbr_tds
        dp.print_param(param=self.nbr_td, out_path=dat_file, name='nbr_tds')
        # printing peak_sh_factor and peak_sc_factor
        dp.print_df(df=dp.ampl_syntax(peak_sh_factor), out_path=dat_file, name='param ')
        dp.print_df(df=dp.ampl_syntax(peak_sc_factor), out_path=dat_file, name='param ')

        # TODO automise this

        # Default name of timeseries in DATA.xlsx and corresponding name in ESTD data file
        if eud_params is None:
            # # for EUD timeseries
            # eud_params = {'ELECTRICITY': 'param electricity_time_series :=',
            #               'HEAT_LOW_T_SH': 'param heating_time_series :=',
            #               'SPACE_COOLING': 'param cooling_time_series :=',
            #               'MOBILITY_PASSENGER': 'param mob_pass_time_series :=',
            #               'MOBILITY_FREIGHT': 'param mob_freight_time_series :='}
            eud_params = self.data_indep['Misc_indep']['time_series_mapping']['eud_params']
        if res_params is None:
            res_params = self.data_indep['Misc_indep']['time_series_mapping']['res_params']

            # # for resources timeseries that have only 1 tech linked to it
            # res_params = {'PV': 'PV', 'WIND_OFFSHORE': 'WIND_OFFSHORE', 'WIND_ONSHORE': 'WIND_ONSHORE',
            #               'HYDRO_DAM': 'HYDRO_DAM', 'HYDRO_RIVER': 'HYDRO_RIVER'}
        if res_mult_params is None:
            res_mult_params = self.data_indep['Misc_indep']['time_series_mapping']['res_mult_params']

            # # for resources timeseries that have several techs linked to it
            # res_mult_params = {'TIDAL': ['TIDAL_STREAM', 'TIDAL_RANGE'],
            #                    'SOLAR': ['DHN_SOLAR', 'DEC_SOLAR', 'PT_COLLECTOR', 'ST_COLLECTOR', 'STIRLING_DISH']}

        # printing EUD timeseries param
        for i in eud_params.keys():
            dp.newline(out_path=dat_file, comment=['param ' + eud_params[i] + ' :='])
            for r in self.regions:
                # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the
                # name of the time series, put it into ampl syntax and print it
                dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(i, slice(None)), :].droplevel(level=0)),
                            out_path=dat_file,
                            name='["' + r + '",*,*] : ', end_table=False)
            dp.end_table(out_path=dat_file)

        # printing c_p_t param #
        dp.newline(out_path=dat_file, comment=['param c_p_t:='])
        # printing c_p_t part where 1 ts => 1 tech
        for i in res_params.keys():
            for r in self.regions:
                # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the
                # name of the time series, put it into ampl syntax and print it
                dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(i, slice(None)), :].droplevel(level=0)),
                            out_path=dat_file,
                            name='["' + res_params[i] + '","' + r + '",*,*] :', end_table=False)

        # printing c_p_t part where 1 ts => more than 1 tech
        for i in res_mult_params.keys():
            for j in res_mult_params[i]:
                for r in self.regions:
                    # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index
                    # with the name of the time series, put it into ampl syntax and print it
                    dp.print_df(
                        df=dp.ampl_syntax(self.regions[r].ts_td.loc[(i, slice(None)), :].droplevel(level=0)),
                        out_path=dat_file, name='["' + j + '","' + r + '",*,*] :', end_table=False)

        dp.end_table(out_path=dat_file)
        return

    def set_esom(self, ref_dir=None, ampl_options=None, copy_from_ref=True, solver='cplex', ampl_path=None):
        """

        Set the energy system optimisation model (esom) with the mod and dat files from ref_dir that are copied into the

        """

        # path where to copy them for this case study
        mod_path = self.cs_dir / 'ESMC_model_AMPL.mod'
        data_path = [self.cs_dir / 'indep.dat',
                     self.cs_dir / ('reg_' + str(self.nbr_td) + 'TD.dat'),
                     self.cs_dir / 'reg_demands.dat',
                     self.cs_dir / 'reg_exch.dat',
                     self.cs_dir / 'reg_misc.dat',
                     self.cs_dir / 'reg_resources.dat',
                     self.cs_dir / 'reg_storage_power_to_energy.dat',
                     self.cs_dir / 'reg_technologies.dat',
                     ]

        # TODO adapt for the case where we print regions.dat and indep.dat from data
        # if new case study, we copy ref files if not, we keep the ones that exist
        if copy_from_ref:
            # path of the reference files for ampl
            if ref_dir is None:
                ref_dir = self.project_dir / 'esmc' / 'energy_model'
            # TODO get rid of this if it work without it
            # logging
            logging.info('Copying mod file from ' + str(ref_dir) + ' to ' + str(self.cs_dir))

            # TODO automatise the names of the .dat
            # mod and data files ref path
            mod_ref = self.project_dir / 'esmc' / 'energy_model' / 'ESMC_model_AMPL.mod'

            # copy the files from ref_dir to case_study directory
            shutil.copyfile(mod_ref, mod_path)


        # default ampl_options
        if ampl_options is None:
            logging.info('Using default ampl_options')
            cplex_options = ['baropt',
                             'predual=-1',
                             'barstart=4',
                             'comptol=1e-5',
                             'crossover=0',
                             'timelimit 64800',
                             'bardisplay=1',
                             'prestats=1',
                             'display=2']
            cplex_options_str = ' '.join(cplex_options)
            ampl_options = {'show_stats': 3,
                            'log_file': str(self.cs_dir / 'log.txt'),
                            'presolve': 200,
                            'times': 1,
                            'gentimes': 1,
                            'cplex_options': cplex_options_str}

        # set ampl for step_2
        logging.info('Setting esom into ' + str(self.cs_dir))
        self.esom = OptiProbl(mod_path=mod_path, data_path=data_path, options=ampl_options, solver=solver,
                              ampl_path=ampl_path)

        # deactivate some unused constraints
        if self.gwp_limit_overall is None:
            self.esom.ampl.get_constraint('Minimum_GWP_reduction_global').drop()
        if self.re_share_primary is None:
            self.esom.ampl.get_constraint('Minimum_RE_share').drop()
        if self.f_perc:
            # drop specific f_perc for train pub and tramway if all f_perc are considered
            self.esom.ampl.get_constraint('f_max_perc_train_pub').drop()
            self.esom.ampl.get_constraint('f_max_perc_tramway').drop()
        else:
            # drop general f_perc constraints
            self.esom.ampl.get_constraint('f_max_perc').drop()
            self.esom.ampl.get_constraint('f_min_perc').drop()

        return

    def solve_esom(self, run=True):
        """Solves the esom wih ampl

        Parameters
        ----------
        run

        Returns
        -------

        """
        # TODO
        # Add possibility to choose options
        # Add possibility to print things into the log

        # update version tracking json file
        self.update_version()
        # print in log emission limit
        self.esom.ampl.eval('print "gwp_limit_overall [ktCO2eq/y]", gwp_limit_overall;')
        self.esom.ampl.eval('print "Number of TDs", last(TYPICAL_DAYS);	')

        if run:
            # logging info
            logging.info('Solving optimisation problem')
            # running esom
            self.esom.run_ampl()
            # logging info
            logging.info('Finished run')
            # print in log main outputs
            self.esom.ampl.eval('print "TotalGWP_global", sum{c in REGIONS} (TotalGWP[c]);')
            self.esom.ampl.eval('print "GWP_op_global", sum{c in REGIONS, r in RESOURCES} (GWP_op[c,r]);')
            self.esom.ampl.eval('print "CO2_net_global", sum{c in REGIONS, r in RESOURCES} (CO2_net[c,r]);')
            self.esom.ampl.eval('print "TotalCost_global", sum{c in REGIONS} (TotalCost[c]);')
        return

    def prints_esom(self, inputs=True, outputs=True, solve_info=False, save_hourly:list=[]):
        # TODO Update
        # if inputs:


            # # Printing input sets and parameters variables names
            # logging.info('Printing inputs')
            # self.esom.print_inputs()

        directory = self.cs_dir / 'outputs'
        if outputs:
            # Printing self.results into outputs
            logging.info('Printing results into outputs')
            directory.mkdir(parents=True, exist_ok=True)

            for key, df in self.results.items():
                df.to_csv(directory / (key + '.csv'), sep=CSV_SEPARATOR)

            if len(save_hourly) > 0:
                (directory/'hourly_results').mkdir(parents=True, exist_ok=True)
                for key, df in self.hourly_results.items():
                    df.to_csv(directory/ 'hourly_results' / (key + '.csv'), sep=CSV_SEPARATOR)

        if solve_info:
            # Getting and printing solve time
            if self.esom.t is None:
                self.esom.get_solve_info()
            with open(directory / 'Solve_info.csv', mode='w', newline='\n') as file:
                writer = csv.writer(file, delimiter=AMPL_SEPARATOR, quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                    lineterminator="\n")
                writer.writerow(['ampl_elapsed_time', CSV_SEPARATOR, self.esom.t[0]])
                writer.writerow(['solve_elapsed_time', CSV_SEPARATOR, self.esom.t[1]])
                writer.writerow(['solve_result_num', CSV_SEPARATOR, self.esom.t[2]])
        return

    # TODO add a if none into results that need other results

    def get_year_results(self, save_hourly: list=[]):
        """Wrapper function to get the year summary results"""
        logging.info('Getting year summary')
        self.get_total_cost()
        self.get_cost_breakdown()
        self.get_gwp_breakdown()
        self.get_resources_and_exchanges(save_hourly=save_hourly)
        self.get_assets(save_hourly=save_hourly)
        self.get_year_balance()
        self.get_curt(save_hourly=save_hourly)
        return

    def get_total_cost(self):
        """Get the total annualized cost of the energy system of the different regions
            It is stored into self.esom.outputs['TotalCost'] and into self.results['TotalCost']
        """
        logging.info('Getting TotalCost')
        total_cost = self.esom.get_var('TotalCost').reset_index()  # .rename(columns={'index0':'Region'})
        # TotalCost.index = pd.CategoricalIndex(TotalCost.index, categories=self.regions_names, ordered=True)
        total_cost['Regions'] = pd.Categorical(total_cost['Regions'], self.regions_names)
        total_cost = total_cost.set_index(['Regions'])
        total_cost.sort_index(inplace=True)
        self.results['TotalCost'] = total_cost

    def get_cost_breakdown(self):
        """Gets the cost breakdown and stores it into the results"""
        logging.info('Getting Cost_breakdown')

        # Get the different costs variables
        c_inv = self.esom.get_var('C_inv')
        c_maint = self.esom.get_var('C_maint')
        c_op = self.esom.get_var('C_op')

        # set index names (for later merging)
        index_names = ['Regions', 'Elements']
        c_inv.index.names = index_names
        c_maint.index.names = index_names
        c_op.index.names = index_names

        # Annualize the investiments
        # create frames for concatenation (list of df to concat)
        frames = list()
        for n, r in self.regions.items():
            r.compute_tau()
            frames.append(r.data['tau'].copy())

        all_tau = pd.concat(frames, axis=0, keys=self.regions_names)
        all_tau.index.names = index_names
        c_inv_ann = c_inv.mul(all_tau, axis=0)

        # Merge costs into cost breakdown
        cost_breakdown = c_inv_ann.merge(c_maint, left_index=True, right_index=True, how='outer') \
            .merge(c_op, left_index=True, right_index=True, how='outer')
        # Set regions and technologies/resources as categorical data for sorting
        cost_breakdown = cost_breakdown.reset_index()
        cost_breakdown['Regions'] = pd.Categorical(cost_breakdown['Regions'], self.regions_names)
        self.categorical_esmc(df=cost_breakdown, col_name='Elements', el_name='Elements')
        cost_breakdown.sort_values(by=['Regions', 'Elements'], axis=0, ignore_index=True, inplace=True)
        cost_breakdown.set_index(['Regions', 'Elements'], inplace=True)

        # put very small values as nan
        treshold = 1e-2
        cost_breakdown = cost_breakdown.mask((cost_breakdown > -treshold) & (cost_breakdown < treshold), np.nan)

        # Store into results
        self.results['Cost_breakdown'] = cost_breakdown
        return

    def get_gwp_breakdown(self):
        """Get the gwp breakdown [ktCO2e/y] of the technologies and resources"""
        logging.info('Getting Gwp_breakdown')

        # Get GWP_constr and GWP_op
        gwp_constr = self.esom.get_var('GWP_constr')  # .rename(columns={'index0':'Region', 'index1':'Element'})
        gwp_op = self.esom.get_var('GWP_op')  # .rename(columns={'index0':'Region', 'index1':'Element'})
        co2_net = self.esom.get_var('CO2_net')  # .rename(columns={'index0':'Region', 'index1':'Element'})

        # set index names (for later merging)
        index_names = ['Regions', 'Elements']
        gwp_constr.index.names = index_names
        gwp_op.index.names = index_names
        co2_net.index.names = index_names

        # Get lifetime of technologies from input data
        # create frames for concatenation (list of df to concat)
        frames = list()
        for n, r in self.regions.items():
            frames.append(r.data['Technologies'].loc[:, 'lifetime'].copy())
        lifetime = pd.concat(frames, axis=0, keys=self.regions_names)

        # annualize GWP_constr by dividing by lifetime
        lifetime.index.names = index_names
        gwp_constr_ann = pd.DataFrame(gwp_constr['GWP_constr'] / lifetime,
                                      columns=['GWP_constr'])  # .reset_index()

        # merging emissions into gwp_breakdown
        gwp_breakdown = gwp_constr_ann.merge(gwp_op
                                             .merge(co2_net, left_index=True, right_index=True),
                                             left_index=True, right_index=True, how='outer').reset_index()

        # Set regions and technologies/resources as categorical data for sorting
        gwp_breakdown['Regions'] = pd.Categorical(gwp_breakdown['Regions'], self.regions_names)
        self.categorical_esmc(df=gwp_breakdown, col_name='Elements', el_name='Elements')
        gwp_breakdown.sort_values(by=['Regions', 'Elements'], axis=0, ignore_index=True, inplace=True)
        gwp_breakdown.set_index(['Regions', 'Elements'], inplace=True)

        # put very small values as nan
        treshold = 1e-2
        gwp_breakdown = gwp_breakdown.mask((gwp_breakdown > -treshold) & (gwp_breakdown < treshold), np.nan)

        # store into results
        self.results['Gwp_breakdown'] = gwp_breakdown
        return

    def get_resources_and_exchanges(self, save_hourly: list=[]):
        """Get the Resources yearly local and exterior production, and import and exports as well as exchanges"""
        logging.info('Getting Yearly resources and exchanges')

        # EXTRACTING DATA FROM OPTIMISATION MODEL
        # Get list of resources exchanged
        network_exch_r = self.esom.ampl.get_set('EXCHANGE_NETWORK_R').getValues().toList()
        freight_exch_r = self.esom.ampl.get_set('EXCHANGE_FREIGHT_R').getValues().toList()
        r_exch = network_exch_r.copy()  # all resources exchanged
        r_exch.extend(freight_exch_r)
        r_list = list(self.ref_region.data['Resources'].index)  # all resources

        # Get hourly data
        r_t_local = self.esom.get_var('R_t_local')
        r_t_exterior = self.esom.get_var('R_t_exterior')

        # Get results related to Resources and Exchanges and sum over all layers
        # year local production and import from exterior
        r_year_local = self.ta.from_td_to_year(ts_td=r_t_local.reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Resources']).sum().rename(columns={'R_t_local': 'R_year_local'})
        r_year_exterior = self.ta.from_td_to_year(ts_td=r_t_exterior
                                                  .reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Resources']).sum().rename(columns={'R_t_exterior': 'R_year_exterior'})

        # get exchanges over the year for r_exch
        exch_imp = self.esom.get_var('Exch_imp').loc[(slice(None), slice(None), r_exch, slice(None), slice(None)), :]
        exch_exp = self.esom.get_var('Exch_exp').loc[(slice(None), slice(None), r_exch, slice(None), slice(None)), :]
        # # adding exchange_losses
        # exchange_losses = self.esom.ampl.get_parameter('exchange_losses').getValues().toPandas()['exchange_losses']
        # dist = self.esom.ampl.get_parameter('dist').getValues().toPandas()['dist']
        # exch_exp = exch_exp.mul((dist/1000), axis=0, level=['From', 'To'])\
        #     .mul((1 + exchange_losses), axis=0, level='Resources')
        # rename indices to have
        ind = ['From', 'To', 'Resources', 'Hours', 'Typical_days']
        exch_imp.index.rename(ind, inplace=True)
        exch_exp.index.rename(ind, inplace=True)
        # Get the transfer capacity
        transfer_capacity = self.esom.get_var('Transfer_capacity')
        transfer_capacity.index.names = ['From', 'To', 'Resources', 'Network_type']  # set names of indices
        all_tc = transfer_capacity.copy()
        transfer_capacity = transfer_capacity.groupby(['From', 'To', 'Resources']).sum()

        # save all transfer capacity
        # put very small values as nan
        treshold = 1e-3
        all_tc = all_tc.mask((all_tc > -treshold) & (all_tc < treshold), np.nan)


        # EXCHANGES RELATED COMPUTATIONS
        # Clean exchanges from double fictive fluxes due to LP formulation
        # group into 1 df, compute the difference
        exch = exch_exp.merge(-exch_imp, right_index=True, left_index=True)
        exch['Balance'] = exch['Exch_imp'] + exch['Exch_exp']
        # replace Exch_imp and Exch_exp by values deduced from Balance
        # such that at each hour the flow goes only in 1 direction
        threshold = 1e-6
        exch['Exch_imp'] = exch['Balance'].mask((exch['Balance'] > -threshold), np.nan)
        exch['Exch_exp'] = exch['Balance'].mask((exch['Balance'] < threshold), np.nan)
        # compute total over the year
        exchanges_year = self.ta.from_td_to_year(ts_td=exch.reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['From', 'To', 'Resources']).sum().drop(columns=['Balance'])
        r_exch_region = exchanges_year.groupby(['From', 'Resources']).sum().abs()

        # keep only one direction per link
        exchanges_year = exchanges_year.drop(columns='Exch_imp').rename(columns={'Exch_exp': 'Exchanges_year'})

        # compute utilization factor of lines
        exchanges_year = exchanges_year.merge(transfer_capacity, how='outer', left_index=True, right_index=True)
        exchanges_year['Utilization_factor'] = \
            exchanges_year['Exchanges_year'] / (transfer_capacity['Transfer_capacity'] * 8760)

        # Set regions and resources as categorical data for sorting
        exchanges_year = exchanges_year.reset_index()
        exchanges_year['From'] = pd.Categorical(exchanges_year['From'], self.regions_names)
        exchanges_year['To'] = pd.Categorical(exchanges_year['To'], self.regions_names)
        self.categorical_esmc(df=exchanges_year, col_name='Resources', el_name='Resources')
        exchanges_year.sort_values(by=['From', 'To', 'Resources'], axis=0, ignore_index=True, inplace=True)
        exchanges_year.set_index(['From', 'To', 'Resources'], inplace=True)

        # put very small values as nan
        treshold = 1e-3
        exchanges_year = exchanges_year.mask((exchanges_year > -treshold) & (exchanges_year < treshold), np.nan)
        # exchanges_year.dropna(axis=0, how='all', inplace=True)

        # RESOURCES RELATED COMPUTATIONS
        # # add to r_exch_region the losses due to fictive exchanges
        # exp_year = self.ta.from_td_to_year(ts_td=exch_exp.reset_index().set_index(['Typical_days', 'Hours'])) \
        #     .groupby(['From', 'To', 'Resources']).sum()
        # diff_exp = (exp_year['Exch_exp'] - exchanges_year['Exchanges_year']).groupby(['From', 'Resources']).sum()

        # compute R_year_import and R_year_export from the exchanges_year computed
        r_year_export = pd.DataFrame(r_exch_region['Exch_exp']).rename(columns={'Exch_exp': 'R_year_export'})
        r_year_export.index.set_names(r_year_local.index.names, inplace=True)  # set proper name to index
        r_year_import = pd.DataFrame(r_exch_region['Exch_imp']).rename(columns={'Exch_imp': 'R_year_import'})
        r_year_import.index.set_names(r_year_local.index.names, inplace=True)  # set proper name to index
        # Get availabilities from input data
        # create frames for concatenation (list of df to concat)
        frames = list()
        for n, r in self.regions.items():
            frames.append(r.data['Resources'].loc[:, ['avail_local', 'avail_exterior']].copy())
        resources = pd.concat(frames, axis=0, keys=self.regions_names)
        resources.index.set_names(r_year_local.index.names, inplace=True)  # set proper name to index
        # merge availabilities with uses of Resources
        resources = resources.merge(r_year_local, left_index=True, right_index=True, how='outer') \
            .merge(r_year_exterior, left_index=True, right_index=True, how='outer') \
            .merge(r_year_import, left_index=True, right_index=True, how='outer') \
            .merge(r_year_export, left_index=True, right_index=True, how='outer').reset_index()

        # Set regions and resources as categorical data for sorting
        resources['Regions'] = pd.Categorical(resources['Regions'], self.regions_names)
        self.categorical_esmc(df=resources, col_name='Resources', el_name='Resources')
        resources.sort_values(by=['Regions', 'Resources'], axis=0, ignore_index=True, inplace=True)
        resources.set_index(['Regions', 'Resources'], inplace=True)

        # put very small values as nan
        treshold = 1e-2
        resources = resources.mask((resources > -treshold) & (resources < treshold), np.nan)
        # resources.dropna(axis=0, how='all', inplace=True)

        # store into results
        self.results['Transfer_capacity'] = all_tc['Transfer_capacity'] = all_tc
        self.results['Exchanges_year'] = exchanges_year
        self.results['Resources'] = resources

        if 'Exchanges' in save_hourly:
            self.hourly_results['Exchanges'] = exch.reset_index()\
                .set_index(['Resources', 'From', 'To', 'Typical_days', 'Hours']).sort_index()
        if 'Resources' in save_hourly:
            self.hourly_results['R_t_local'] = r_t_local.reset_index()\
                .set_index(['Regions', 'Resources', 'Typical_days', 'Hours']).sort_index()
            self.hourly_results['R_t_exterior'] = r_t_exterior.reset_index()\
                .set_index(['Regions', 'Resources', 'Typical_days', 'Hours']).sort_index()
            # TODO ? add R_t_import et R_t_export?

        return

    def get_assets(self, save_hourly:list=[]):
        """Gets the assets and stores it into the results,
        for storage assets, and additional data set is created (Sto_assets)

        self.results['Assets']: Each asset is defined by its installed capacity (F) [GW],
                                the bound on it (f_min,f_max) [GW]
                                and its production on its main output layer (F_year) [GWh]
                                It has the following columns:
                                ['Regions', 'Technologies', 'F', 'f_min', 'f_max', 'F_year']
                                containing the following information:
                                [region name,
                                technology name,
                                installed capacity [GW] (or [GWh] for storage technologies),
                                lower bound on the installed capacity [GW] (or [GWh] for storage technologies),
                                upper bound on the installed capacity [GW] (or [GWh] for storage technologies),
                                year production [GWh] (or losses for storage technologies)
                                ]

        self.results['Sto_assets']: It has the following columns:
                                    ['Regions', 'Technologies', 'F', 'f_min', 'f_max', 'Losses', 'Year_energy_flux',
                                    'Storage_in_max', 'Storage_out_max']
                                    containing the following information:
                                    [region name,
                                    technology name,
                                    installed capacity [GWh],
                                    lower bound on the instaled capacity [GWh],
                                    upper bound on the installed capacity [GWh],
                                    year losses [GWh],
                                    year energy flux going out of the storage technology [GWh],
                                    maximum input power [GW],
                                    maximum output power [GW]
                                    ]

        """
        logging.info('Getting Assets and Storage assets')

        # EXTRACTING OPTIMISATION MODEL RESULTS
        # installed capacity
        f = self.esom.get_var('F')
        # energy produced by the technology
        f_t = self.esom.get_var('F_t')
        f_year = self.ta.from_td_to_year(ts_td=f_t.reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Technologies']).sum() \
            .rename(columns={'F_t': 'F_year'})
        # Get Storage_power (power balance at each hour)
        storage_in = self.esom.get_var('Storage_in') \
            .groupby(['Regions', 'I in storage_tech', 'Hours', 'Typical_days']).sum()
        storage_out = self.esom.get_var('Storage_out') \
            .groupby(['Regions', 'I in storage_tech', 'Hours', 'Typical_days']).sum()

        # ASSETS COMPUTATIONS
        # Get the bounds on F (f_min,f_max)
        # create frames for concatenation (list of df to concat)
        frames = list()
        for n, r in self.regions.items():
            frames.append(r.data['Technologies'].loc[:, ['f_min', 'f_max']].copy())
        assets = f.merge(pd.concat(frames, axis=0, keys=self.regions_names)
                         , left_on=['Regions', 'Technologies'], right_index=True) \
            .merge(f_year, left_on=['Regions', 'Technologies'], right_on=['Regions', 'Technologies']).reset_index()
        # set Regions and Technologies as categorical data and sort it
        assets['Regions'] = pd.Categorical(assets['Regions'], self.regions_names)
        self.categorical_esmc(df=assets, col_name='Technologies', el_name='Technologies')
        assets.sort_values(by=['Regions', 'Technologies'], axis=0, ignore_index=True, inplace=True)
        assets.set_index(['Regions', 'Technologies'], inplace=True)
        # put very small values as nan
        treshold = 1e-2
        assets = assets.mask((assets > -treshold) & (assets < treshold), np.nan)
        treshold = 1e-1
        assets['F_year'] = assets['F_year'].mask((assets['F_year'] > -treshold) & (assets['F_year'] < treshold), np.nan)

        # STORAGE ASSETS COMPUTATIONS
        # compute the balance
        storage_power = storage_out.merge(-storage_in, left_index=True, right_index=True)
        storage_power['Storage_power'] = storage_power['Storage_out'] + storage_power['Storage_in']
        storage_power.index.rename(['Regions', 'Storage_tech', 'Hours', 'Typical_days'], inplace=True)
        # losses are the sum of the balance over the year
        sto_losses = self.ta.from_td_to_year(ts_td=storage_power['Storage_power']
                                             .reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Storage_tech']).sum()
        # Update F_year in assets df for STORAGE_TECH
        assets.loc[sto_losses.index, 'F_year'] = sto_losses['Storage_power']
        # replace Storage_in and Storage_out by values deduced from Storage_power
        # such that at each hour the flow goes only in 1 direction
        threshold = 1e-2
        storage_power['Storage_in'] = storage_power['Storage_power'].mask((storage_power['Storage_power'] > -threshold),
                                                                          np.nan)
        storage_power['Storage_out'] = storage_power['Storage_power'].mask((storage_power['Storage_power'] < threshold),
                                                                           np.nan)
        # Compute total over the year by mapping TD
        sto_flux_year = self.ta.from_td_to_year(ts_td=storage_power.reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Storage_tech']).sum() \
            .rename(columns={'Storage_out': 'Year_energy_flux'}).drop(columns=['Storage_in', 'Storage_power'])
        # create sto_assets from copy() of assets
        sto_assets = assets.copy()
        sto_assets.rename(columns={'F_year': 'Losses'}, inplace=True)
        # merge it with sto_flux_year
        sto_flux_year.index.set_names(sto_assets.index.names, inplace=True)  # set proper name to index
        sto_assets = sto_assets.merge(sto_flux_year, left_index=True, right_on=['Regions', 'Technologies'],
                                      how='right')
        # Get storage_charge_time and storage_discharge_time from input data
        # and compute maximum input and output power of the storage technology
        frames = list()
        for n, r in self.regions.items():
            frames.append(r.data['Storage_power_to_energy'].copy())
        sto_assets = sto_assets.merge(pd.concat(frames, axis=0, keys=self.regions_names)
                                      , left_on=['Regions', 'Technologies'], right_index=True)
        sto_assets['Storage_in_max'] = sto_assets['F'] / sto_assets['storage_charge_time']
        sto_assets['Storage_out_max'] = sto_assets['F'] / sto_assets['storage_discharge_time']
        sto_assets.drop(columns=['storage_charge_time', 'storage_discharge_time'], inplace=True)
        # set Region and Technology as categorical data and sort it
        sto_assets.reset_index(inplace=True)
        sto_assets['Regions'] = pd.Categorical(sto_assets['Regions'], self.regions_names)
        self.categorical_esmc(df=sto_assets, col_name='Technologies', el_name='Technologies')
        sto_assets.sort_values(by=['Regions', 'Technologies'], axis=0, ignore_index=True, inplace=True)
        sto_assets.set_index(['Regions', 'Technologies'], inplace=True)
        # put very small values as nan
        treshold = 1
        sto_assets = sto_assets.mask((sto_assets > -treshold) & (sto_assets < treshold), np.nan)

        # Store into results
        self.results['Assets'] = assets
        self.results['Sto_assets'] = sto_assets

        if 'Assets' in save_hourly:
            self.hourly_results['F_t'] = f_t.reset_index()\
                .set_index(['Regions', 'Technologies', 'Typical_days', 'Hours']).sort_index()
        if 'Storage' in save_hourly:
            self.hourly_results['Storage_level'] = self.esom.get_var('Storage_level')
            self.hourly_results['Storage_power'] = storage_power.reset_index()\
                .set_index(['Regions', 'Storage_tech', 'Typical_days', 'Hours']).sort_index()

        return

    def get_year_balance(self):
        """Get the year energy balance of each layer"""
        logging.info('Getting Year_balance')

        # EXTRACT RESULTS FROM OPTIMISATION MODEL
        end_uses = -self.ta.from_td_to_year(ts_td=self.esom.get_var('End_uses')
                                            .reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Layers']).sum()

        end_uses = end_uses.reset_index()
        end_uses['Elements'] = 'END_USES'
        end_uses = end_uses.reset_index().pivot(index=['Regions', 'Elements'], columns=['Layers'], values=['End_uses'])
        end_uses.columns = end_uses.columns.droplevel(level=0)

        # If not computed yet compute assets and resources
        if self.results['Assets'] is None:
            self.get_assets()
        if self.results['Resources'] is None:
            self.get_resources_and_exchanges()

        # get previously computed results, year fluxes of resources and technologies
        f_year = self.results['Assets']['F_year'].reset_index() \
            .rename(columns={'Technologies': 'Elements'}).astype({'Elements': str})
        r_year = (self.results['Resources']['R_year_local'].fillna(0)
                  + self.results['Resources']['R_year_exterior'].fillna(0)
                  + self.results['Resources']['R_year_import'].fillna(0)
                  - self.results['Resources']['R_year_export'].fillna(0)) \
            .reset_index().rename(columns={'Resources': 'Elements', 0: 'R_year'}).astype({'Elements': str})

        year_fluxes = pd.concat([r_year.set_index(['Regions', 'Elements'])['R_year'],
                                 f_year.set_index(['Regions', 'Elements'])['F_year']
                                 ], axis=0)

        # Get storage_charge_time and storage_discharge_time from input data
        # and compute maximum input and output power of the storage technology
        # create frames for concatenation (list of df to concat)
        frames = list()
        lio = self.data_indep['Layers_in_out'].copy()
        sto_eff = self.data_indep['Storage_eff_in'].copy()
        sto_eff = sto_eff.mask(sto_eff > 0.001, 1)  # storage eff only used to know on which layer it has an impact
        all_eff = pd.concat([lio, sto_eff], axis=0)
        for n, r in self.regions.items():
            frames.append(all_eff.copy())
        layers_in_out_all = pd.concat(frames, axis=0, keys=self.regions_names)
        layers_in_out_all.index.set_names(year_fluxes.index.names, inplace=True)
        year_balance = layers_in_out_all.mul(year_fluxes, axis=0)
        # add eud
        year_balance = pd.concat([year_balance, end_uses], axis=0)

        # Set regions, elements and layers as categorical data for sorting
        year_balance = year_balance.reset_index()
        year_balance['Regions'] = pd.Categorical(year_balance['Regions'], self.regions_names)
        ordered_tech = list(self.ref_region.data['Technologies'].index)
        ordered_res = list(self.ref_region.data['Resources'].index)
        ordered_list = ordered_tech.copy()
        ordered_list.extend(ordered_res)
        ordered_list.append('END_USES')
        year_balance['Elements'] = pd.Categorical(year_balance['Elements'], ordered_list)
        year_balance.sort_values(by=['Regions', 'Elements'], axis=0, ignore_index=True, inplace=True)
        year_balance.set_index(['Regions', 'Elements'], inplace=True)

        # put very small values as nan
        treshold = 1e-1
        year_balance = year_balance.mask((year_balance.min(axis=1) > -treshold) & (year_balance.max(axis=1) < treshold),
                                         np.nan)

        # Store into results
        self.results['Year_balance'] = year_balance
        return

    def get_curt(self, save_hourly:list=[]):
        """Gets the yearly curtailment of renewables"""
        logging.info('Getting Curt')

        # Get curtailment
        curt_t = self.esom.get_var('Curt')
        curt = self.ta.from_td_to_year(ts_td=curt_t.reset_index().set_index(['Typical_days', 'Hours'])) \
            .groupby(['Regions', 'Technologies']).sum()
        # Get tech with a c_p_t defined (by addding list of res_params and flatten list of res_mult_param)
        tech_cpt = list(self.data_indep['Misc_indep']['time_series_mapping']['res_params'].values()) \
                   + [element for sublist in
                      self.data_indep['Misc_indep']['time_series_mapping']['res_mult_params'].values()
                      for element in sublist]
        # Keep only curt for tech_cpt
        curt = curt.loc[(slice(None), tech_cpt),:].copy()
        # Set regions as categorical data
        curt.reset_index(inplace=True)
        curt['Regions'] = pd.Categorical(curt['Regions'], self.regions_names)
        curt = curt.set_index(['Regions'])
        curt.sort_index(inplace=True)
        # Store Curt into results
        self.results['Curt'] = curt

        if 'Curt' in save_hourly:
            self.hourly_results['Curt'] = curt_t.reset_index()\
                .set_index(['Regions', 'Technologies', 'Typical_days', 'Hours']).sort_index()

        return

    def read_results(self):
        """ Reads the results printed into csv and store them into results dictionnary

        """
        # Reading the main results into csv
        self.results['TotalCost'] = pd.read_csv(self.cs_dir / 'outputs' / 'TotalCost.csv',
                                                header=[0], index_col=[0], sep=CSV_SEPARATOR)
        self.results['Cost_breakdown'] = pd.read_csv(self.cs_dir / 'outputs' / 'Cost_breakdown.csv',
                                                header=[0], index_col=[0, 1], sep=CSV_SEPARATOR)
        self.results['Gwp_breakdown'] = pd.read_csv(self.cs_dir / 'outputs' / 'Gwp_breakdown.csv',
                                                header=[0], index_col=[0, 1], sep=CSV_SEPARATOR)
        self.results['Exchanges_year'] = pd.read_csv(self.cs_dir / 'outputs' / 'Exchanges_year.csv',
                                                header=[0], index_col=[0, 1, 2], sep=CSV_SEPARATOR)
        self.results['Resources'] = pd.read_csv(self.cs_dir / 'outputs' / 'Resources.csv',
                                                header=[0], index_col=[0,1], sep=CSV_SEPARATOR)
        self.results['Assets'] = pd.read_csv(self.cs_dir / 'outputs' / 'Assets.csv',
                                                header=[0], index_col=[0,1], sep=CSV_SEPARATOR)
        self.results['Sto_assets'] = pd.read_csv(self.cs_dir / 'outputs' / 'Sto_assets.csv',
                                                header=[0], index_col=[0,1], sep=CSV_SEPARATOR)
        self.results['Year_balance'] = pd.read_csv(self.cs_dir / 'outputs' / 'Year_balance.csv',
                                                header=[0], index_col=[0,1], sep=CSV_SEPARATOR)
        self.results['Curt'] = pd.read_csv(self.cs_dir / 'outputs' / 'Curt.csv',
                                                header=[0], index_col=[0,1], sep=CSV_SEPARATOR)

        # reading the solving information and storing them
        if self.esom is None:
            # initialize empty OptiProbl if doesn't exist
            self.esom = OptiProbl(set_ampl=False)

        self.esom.t = list(pd.read_csv(self.cs_dir / 'outputs' / 'Solve_info.csv',
                                  header=None, index_col=[0], sep=CSV_SEPARATOR).values)

        return

    def categorical_esmc(self, df: pd.DataFrame, col_name: str, el_name: str):
        """Transform the column (col_name) of the dataframe (df) into categorical data of the type el_name
        df is modified by the function.

        Parameters
        __________
        df: pd.DataFrame()
        DataFrame to modify

        col_name: str
        Name of the column to transform into categorical data

        el_name: {'Layers', 'Elements', 'Technologies', 'Resources'}
        Type of element to consider. The order of the categorical data is taken from the input data.
        Layers are taken as the column names of Layers_in_out
        Elements are taken as the concatenation of the index of the Technologies and Resources dataframes
        of the ref_region
        Technologies are taken as the index of the Technologies dataframe of the ref_region
        Resources are taken as the index of the Resources dataframe of the ref_region
        """
        if el_name == 'Layers':
            ordered_list = list(self.data_indep['Layers_in_out'].columns)
        elif el_name == 'Elements':
            ordered_tech = list(self.ref_region.data['Technologies'].index)
            ordered_res = list(self.ref_region.data['Resources'].index)
            ordered_list = ordered_tech.copy()
            ordered_list.extend(ordered_res)
        else:
            # if el_name is Technologies or Resources
            ordered_list = list(self.ref_region.data[el_name].index)

        df[col_name] = pd.Categorical(df[col_name], ordered_list)
        return

    # TODO here test
    #  Add a function to get hourly data of layer balance and SOC of storages
    #
