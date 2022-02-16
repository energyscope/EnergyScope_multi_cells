"""
This file contains a class to define an energy system

"""
import numpy as np

from esmc.utils.region import Region
from esmc.utils.opti_probl import OptiProbl
from esmc.preprocessing.temporal_aggregation import TemporalAggregation
import esmc.preprocessing.dat_print as dp
import esmc.postprocessing.amplpy2pd as a2p
import shutil
import git
import pandas as pd
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

        # update version tracking json file
        self.update_version()

        # create and initialize regions
        self.regions = dict()
        self.init_regions()
        self.data_exch = dict()

        # initialize TemporalAggregation object
        # TODO self.spatial_aggreg = object spatial_aggreg
        #

        # create energy system optimization problem (esom)
        self.esom = None

        return

    def init_regions(self):
        data_dir = self.project_dir/'Data'
        for r in self.regions_names:
            self.regions[r] = Region(nuts=r, data_dir=data_dir)
        return

    def init_ta(self):
        """Initialize the temporal aggregator

        """
        self.ta = TemporalAggregation(self.regions, self.dat_dir)
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

    def set_esom(self, ref_dir=None, ampl_options=None):
        """

        Set the energy system optimisation model (esom) with the mod and dat files from ref_dir that are copied into the

        """

        # path of the reference files for ampl
        if ref_dir is None:
            ref_dir = self.project_dir/'case_studies'/'dat_files'

        mod_ref = self.project_dir/'esmc'/'energy_model'/'ESMC_model_AMPL.mod'
        data_ref = [ref_dir/self.space_id/('ESMC_' + str(self.Nbr_TD) + 'TD.dat'),
                  ref_dir/'ESMC_indep.dat',
                  ref_dir/self.space_id/'ESMC_countries.dat']
        # path where to copy them for this case study
        mod_path =  self.cs_dir/'ESMC_model_AMPL.mod'
        data_path = [self.cs_dir/('ESMC_' + str(self.Nbr_TD) + 'TD.dat'),
                     self.cs_dir / 'ESMC_indep.dat',
                     self.cs_dir / 'ESMC_countries.dat']

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
        if run:
            self.esom.run_ampl()
            self.esom.get_solve_time()
        if outputs:
            self.esom.get_outputs()
        return

    def prints_esom(self, inputs=True, outputs=True):
        if inputs:
            self.esom.print_inputs()
        if outputs:
            self.esom.print_outputs()
        return

    def print_td_data(self, EUD_params=None, RES_params=None, RES_mult_params=None):
        """


        Returns
        -------

        """
        # Default name of timeseries in DATA.xlsx and corresponding name in ESTD data file
        if EUD_params is None:
            # for EUD timeseries
            EUD_params = {'Electricity (%_elec)': 'param electricity_time_series :=',
                          'Space Heating (%_sh)': 'param heating_time_series :=',
                          'Space Cooling': 'param cooling_time_series :=',
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
        #TODO call self.generate_t_h_td
        t_h_td = self.ta.t_h_td.copy()
        # adding ampl syntax for printing
        t_h_td['par_l'] = '('
        t_h_td['par_r'] = ')'
        t_h_td['comma1'] = ','
        t_h_td['comma2'] = ','
        t_h_td = t_h_td[['par_g', 'H_of_Y', 'comma1', 'H_of_D', 'comma2', 'TD_of_days', 'par_d']] # reordering columns





        return

    def generate_t_h_td(self):
        """Generate t_h_td and td_count dataframes and assign it to each region
        t_h_td is a pd.DataFrame containing 4 columns:
        hour of the year (H_of_Y), hour of the day (H_of_D), typical day representing this day (TD_of_days)
        and the number assigned to this typical day (TD_number)

        td_count is a pd.DataFrame of 2 columns



        """
        # GETTING td_of_days FROM TEMPORAL AGGREGATION
        td_of_days = self.ta.td_of_days.copy()
        td_of_days['day'] = np.arange(1, 366, 1)

        # COMPUTING NUMBER OF DAYS REPRESENTED BY EACH TD AND ASSIGNING A TD NUMBER TO EACH REPRESENTATIVE DAY
        td_count = td_of_days.groupby('TD_of_days').count()
        td_count = td_count.reset_index().rename(columns={'index': 'TD_of_days', 'day': '#days'})
        td_count['TD'] = np.arange(1, self.Nbr_TD + 1)
        self.ta.td_count = td_count.copy()  # save into TemporalAggregation object

        # BUILDING T_H_TD MATRICE
        t_h_td = pd.DataFrame(np.repeat(td_of_days['TD_of_days'].values, 24, axis=0),
                              columns=['TD_of_days'])  # column TD_of_days is each TD repeated 24 times
        map_td = dict(zip(td_count['TD_of_days'],
                          np.arange(1, self.Nbr_TD + 1)))  # mapping dictionnary from TD_of_Days to TD number
        t_h_td['TD_number'] = t_h_td['TD_of_days'].map(map_td)
        t_h_td['H_of_D'] = np.resize(np.arange(1, 25), t_h_td.shape[0])  # 365 times hours from 1 to 24
        t_h_td['H_of_Y'] = np.arange(1, 8761)
        # save into TemporalAggregation object
        self.ta.t_h_td = t_h_td
        self.ta.td_count= td_count

        for r in self.regions:
            self.regions[r].t_h_td = t_h_td
            self.regions[r].td_count = td_count

        return

