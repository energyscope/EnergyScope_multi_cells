"""
This file contains a class to define an energy system

"""
import logging

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

        # path definition
        self.project_dir = Path(__file__).parents[2]
        self.dat_dir = self.project_dir/'case_studies'/'dat_files'/self.space_id
        self.cs_dir = self.project_dir/'case_studies'/self.space_id/self.case_study
        # create directories
        self.dat_dir.mkdir(parents=True, exist_ok=True)
        self.cs_dir.mkdir(parents=True, exist_ok=True)

        # create and initialize regions
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
        data_dir = self.project_dir/'Data'
        for r in self.regions_names:
            self.regions[r] = Region(nuts=r, data_dir=data_dir)
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

    def set_esom(self, ref_dir=None, ampl_options=None, copy=True):
        """

        Set the energy system optimisation model (esom) with the mod and dat files from ref_dir that are copied into the

        """

        # path where to copy them for this case study
        mod_path =  self.cs_dir/'ESMC_model_AMPL.mod'
        data_path = [self.cs_dir/('ESMC_' + str(self.Nbr_TD) + 'TD.dat'),
                     self.cs_dir / 'ESMC_indep.dat',
                     self.cs_dir / 'ESMC_countries.dat']

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
        self.esom.ampl.eval('print "gwp_limit_global [ktCO2eq/y]", gwp_limit_global;')
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
        for r in self.regions:
            self.regions[r].rescale_td_ts(self.ta.td_count)
            self.regions[r].compute_peak_sh()
            peak_sh_factor.loc[r, 'peak_sh_factor'] = self.regions[r].peak_sh_factor

        t_h_td = self.ta.t_h_td.copy()
        t_h_td['par_l'] = '('
        t_h_td['par_r'] = ')'
        t_h_td['comma1'] = ','
        t_h_td['comma2'] = ','
        t_h_td = t_h_td[['par_l', 'H_of_Y', 'comma1', 'H_of_D', 'comma2', 'TD_number', 'par_r']]  # reordering columns

        # file to print to
        dat_file = self.dat_dir/('ESMC_'+str(self.Nbr_TD)+'TD.dat')

        # PRINTING
        # printing signature of data file
        dp.print_header(self.project_dir/'esmc'/'energy_model'/'header_td_data.txt', dat_file)

        # printing set depending on TD

        # printing set TYPICAL_DAYS -> replaced by printing param nbr_tds
        #dp.print_set(my_set=[str(i) for i in np.arange(1, self.Nbr_TD + 1)],out_path=dat_file,name='TYPICAL_DAYS', comment='# typical days')
        # printing set T_H_TD
        dp.newline(dat_file,['set T_H_TD := 		'])
        t_h_td.to_csv(dat_file, sep='\t', header=False, index=False, mode='a', quoting=csv.QUOTE_NONE)
        dp.end_table(dat_file)
        # printing parameters depending on TD
        # printing interlude
        dp.newline(dat_file,['# -----------------------------','# PARAMETERS DEPENDING ON NUMBER OF TYPICAL DAYS : ','# -----------------------------',''])
        # printing nbr_tds
        dp.print_param(param=self.Nbr_TD, out_path=dat_file, name='nbr_tds')
        # printing peak_sh_factor
        dp.print_df(df=dp.ampl_syntax(peak_sh_factor),out_path=dat_file,name='param ')

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
                dp.newline(out_path=dat_file,comment=[EUD_params[l]])
                for r in self.regions:
                    # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the name of the time series, put it into ampl syntax and print it
                    dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(l, slice(None)),:].droplevel(level=0)), out_path=dat_file,
                                name='["'+r+'",*,*] : ', end_table=False)
                dp.end_table(out_path=dat_file)

            # printing c_p_t param #
            dp.newline(out_path=dat_file, comment=['param c_p_t:='])
            # printing c_p_t part where 1 ts => 1 tech
            for l in RES_params.keys():
                for r in self.regions:
                    # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the name of the time series, put it into ampl syntax and print it
                    dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(l, slice(None)),:].droplevel(level=0)), out_path=dat_file,
                                name='["' + RES_params[l] + '","' + r + '",*,*] :', end_table=False)

            # printing c_p_t part where 1 ts => more then 1 tech
            for l in RES_mult_params.keys():
                for j in RES_mult_params[l]:
                    for r in self.regions:
                        # select the (24xNbr_TD) dataframe of region r and time series l, drop the level of index with the name of the time series, put it into ampl syntax and print it
                        dp.print_df(df=dp.ampl_syntax(self.regions[r].ts_td.loc[(l, slice(None)), :].droplevel(level=0)),
                                    out_path=dat_file, name='["' + j + '","' + r + '",*,*] :', end_table=False)

            dp.end_table(out_path=dat_file)
        return



