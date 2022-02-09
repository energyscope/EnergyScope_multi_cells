"""
This file contains a class to define an energy system

"""
from esmc.utils.region import Region
from esmc.utils.opti_probl import OptiProbl
from esmc.preprocessing.temporal_aggregation import TemporalAggregation
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
        self.ta = TemporalAggregation(self.regions, self.dat_dir)

        # create energy system optimization problem (esom)
        self.esom = None

        return

    def init_regions(self):
        data_dir = self.project_dir/'Data'
        for r in self.regions_names:
            self.regions[r] = Region(nuts=r, data_dir=data_dir)
        return



    def update_version(self):
        """

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
        if outputs:
            self.esom.get_outputs()
        return

    def prints_esom(self, inputs=True, outputs=True):
        if inputs:
            self.esom.print_inputs()
        if outputs:
            self.esom.print_outputs()
        return

