import numpy as np
import os
import logging
import pandas as pd
import csv
from pathlib import Path
import pickle
from amplpy import AMPL, DataFrame
from esmc.postprocessing import amplpy2pd as a2p

# todo add possibility to choose solver with options aswell
class OptiProbl:
    """

    The OptiProbl class allows to set an optimization problem in ampl, solve it,
     and interface with it trough the amplpy API and some additionnal functions

    Parameters
    ----------
    mod_path : pathlib.Path
        Specifies the path of the .mod file defining the LP problem in ampl syntax
    data_path : list(pathlib.Path)
        List specifying the path of the different .dat files with the data of the LP problem
        in ampl syntax
    options : dict
        Dictionary of the different options for ampl and the cplex solver

    """

    def __init__(self, mod_path, data_path, options):
        # instantiate different attributes
        self.dir = Path()
        self.dir = mod_path.parent
        self.mod_path = mod_path
        self.data_path = data_path
        self.options = options
        self.ampl = self.set_ampl(mod_path, data_path)
        self.vars = list()
        self.params = list()
        self.sets = dict()
        self.t = None
        self.outputs = dict()

        return

    def run_ampl(self):
        """

               Run the LP optimization with AMPL and saves the running time in self.t

               """
        try:
            # set options
            for o in self.options:
                self.ampl.setOption(o, self.options[o])

            self.ampl.solve()
            # reinitialize log printing options to have no log prints after solving
            self.ampl.setOption('show_stats',0)
            self.ampl.setOption('times',0)
            self.ampl.setOption('gentimes',0)

            # display general info on the optimization
            self.get_solve_info()

            # stop printing into the log
            self.ampl.setOption('log_file', "")
        except Exception as e:
            print(e)
            raise
        return

    def get_solve_info(self):
        """

       Get the solving info (time and result) and stores it into t attribute

        """
        logging.info('Getting solve_info')
        self.t = list()
        self.t.append(self.ampl.getData('_ampl_elapsed_time;').toList()[0])
        self.t.append(self.ampl.getData('_solve_elapsed_time;').toList()[0])
        self.t.append(self.ampl.getData('solve_result_num;').toList()[0])
        # TODO understand why doesn't work with kmedoid_clustering
        return

    def get_inputs(self):
        """

        Get the name of variables and parameters and the sets

        """
        # get values of attributes
        self.get_vars()
        self.get_params()
        self.get_sets()

    def get_vars(self):
        """

        Get the name of the LP optimization problem's variables

        """
        self.vars = list()
        for name, values in self.ampl.getVariables():
            self.vars.append(name)

    def get_params(self):
        """

        Get the name of the LP optimization problem's parameters

               """
        self.params = list()
        for n, p in self.ampl.getParameters():
            self.params.append(n)

    def get_sets(self):
        #TODO update to a more robust version
        """

               Function to sets of the LP optimization problem

        """
        self.sets = dict()
        for name, obj in self.ampl.getSets():
            if len(obj.instances()) <= 1:
                try:
                    self.sets[name] = obj.getValues().toList()
                except Exception as e:
                    logging.warning(str(name) + ' set not working, replacing it by a empty list')
                    self.sets [name] = list()
            else:
                self.sets[name] = self.get_subset(obj)

    def print_inputs(self, directory=None):
        """

        Prints the sets, parameters' names and variables' names of the LP optimization problem

        Parameters
        ----------
        directory : pathlib.Path
        Path of the directory where to save the inputs

        """
        # default directory
        if directory is None:
            directory = self.dir / 'inputs'
        # creating inputs dir
        directory.mkdir(parents=True, exist_ok=True)

        # if params is empty get all inputs
        if not self.params:
            self.get_inputs()
        # printing inputs
        a2p.print_json(self.sets, directory / 'sets.json')
        a2p.print_json(self.params, directory / 'parameters.json')
        a2p.print_json(self.vars, directory / 'variables.json')

        return

    def get_outputs(self):
        """

               Function to extract the values of each variable after running the optimization problem

                      """
        # function to get the outputs of ampl under the form of a dict filled with one df for each variable
        amplpy_sol = self.ampl.getVariables()
        self.outputs = dict()
        for name, var in amplpy_sol:
            self.outputs[name] = self.to_pd(var.getValues())

    def get_var(self, var_name:str):
        """Function to extract the mentioned variable and store it into self.outputs

        Parameters
        ----------
        var_name: str
        Name of the variable to extract from the optimisation problem results. Should be written as in the .mod file

        Returns
        -------
        var: pd.DataFrame()
        DataFrame containing the values of the different elements of the variable.
        The n first columns give the n sets on which it is indexed
        and the last column give the value obtained from the optimization.

        """
        ampl_var = self.ampl.getVariable(var_name)
        # Getting the names of the sets
        indexing_sets = [s.capitalize() for s in ampl_var.getIndexingSets()]
        # Getting the data of the variable into a pandas dataframe
        amplpy_df = ampl_var.getValues()
        var = amplpy_df.toPandas()
        # getting the number of indices. If var has more then 1 index, we set it as a MultiIndex
        n_indices = amplpy_df.getNumIndices()
        if n_indices>1:
            var.index = pd.MultiIndex.from_tuples(var.index, names=indexing_sets)
        else:
            var.index = pd.Index(var.index, name=indexing_sets[0])
        # getting rid of '.val' (4 trailing characters of the string) into columns names such that the name of the columns correspond to the variable
        var.rename(columns=lambda x: x[:-4], inplace=True)
        #self.to_pd(ampl_var.getValues()).rename(columns={(var_name+'.val'):var_name})
        self.outputs[var_name] = var
        return var


    def print_outputs(self, directory=None, solve_time=False):
        """

        Prints the outputs (dictionary of pd.DataFrame()) into a pickle file

        Parameters
        ----------
        directory : pathlib.Path
        Path of the directory where to save the dataframes

        """
        # default directory
        if directory is None:
            directory = self.dir / 'outputs'
        # creating outputs dir
        directory.mkdir(parents=True, exist_ok=True)
        # printing outputs
        with open(directory/'outputs.p', 'wb') as handle:
            pickle.dump(self.outputs, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # for ix, (key, val) in enumerate(self.outputs.items()):
        #     val.to_csv(directory / (str(key) + '.csv'))

        if solve_time:
            if self.t is None:
                self.get_solve_info()
            with open(directory / 'Solve_time.csv', mode='w', newline='\n') as file:
                writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL,
                                       lineterminator="\n")
                writer.writerow(['ampl_elapsed_time', self.t[0]])
                writer.writerow(['solve_elapsed_time', self.t[1]])
        return

    def read_outputs(self, directory=None):
        """

        Reads the outputs previously printed into csv files to recover a case study without running it again

        Parameters
        ----------
        directory : pathlib.Path
        Path of the directory where the outputs are saved

        """
        # default directory
        if directory is None:
            directory = self.dir / 'outputs'

        with open(directory/'outputs.p', 'rb') as handle:
            self.outputs = pickle.load(handle)

        # # To save as csv

        # #if vars is an empty list, get vars
        # if not self.vars:
        #     self.get_vars()
        # # read outputs
        # self.outputs = dict()
        # for v in self.vars:
        #     self.outputs[v] = pd.read_csv(directory / (v + '.csv'), index_col=0)


    # def remove_outputs(self, directory):
    #     for v in self.vars:
    #         filename = directory / (v + '.csv')
    #         try:
    #             os.remove(filename)
    #         except OSError:
    #             print('Could not erase previous log file ' + filename)

    #############################
    #       STATIC METHODS      #
    #############################

    @staticmethod
    def set_ampl(mod_path, data_path, solver='cplex'):
        """

        Initialize the AMPL() object containing the LP problem

        Parameters
        ----------
         mod_path : pathlib.Path
        Specifies the path of the .mod file defining the LP problem in ampl syntax

        data_path : list(pathlib.Path)
        List specifying the path of the different .dat files with the data of the LP problem
        in ampl syntax

        options : dict
        Dictionary of the different options for ampl and the cplex solver

        Returns
        -------
        ampl object created

        """
        try:
            # Create an AMPL instance
            ampl = AMPL()
            # define solver
            ampl.setOption('solver', 'cplex')

            # Read the model and data files.
            ampl.read(mod_path)
            for d in data_path:
                ampl.readData(d)
        except Exception as e:
            print(e)
            raise

        return ampl

    @staticmethod
    def get_subset(my_set):
        """

        Function to extract the subsets of set containing sets from the AMPL() object

               Parameters
               ----------
            my_set : amplpy.set.Set
            2-dimensional set to extract


               Returns
               -------
               d : dict()
               dictionary containing the subsets as lists

               """
        d = dict()
        for n, o in my_set.instances():
            try:
                d[n] = o.getValues().toList()
            except Exception as e:
                logging.warning(str(n) + ' subset not working, , replacing it by a empty list')
                d[n] = list()
        return d

    @staticmethod
    def to_pd(amplpy_df):
        # TODO check if name of indexes can be nasme of corresponding sets
        """

               Function to transform an amplpy.DataFrame into pandas.DataFrame for easier manipulation

                      Parameters
                      ----------
                   amplpy_df : amplpy.DataFrame
                   amplpy dataframe to transform


                      Returns
                      -------
                      df : pandas.DataFrame
                      DataFrame transformed as 'long' dataframe (can be easily pivoted later)
                      """
        headers = amplpy_df.getHeaders()
        columns = {header: list(amplpy_df.getColumn(header)) for header in headers}
        df = pd.DataFrame(columns)
        return df