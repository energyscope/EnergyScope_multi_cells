""" Temporal aggregation class

This class defines the object TemporalAggregation and its methods
to perform temporal aggregation on time series of multi-regional energy systems
"""
import logging

import numpy as np
import pandas as pd
import csv
from pathlib import Path
import esmc.preprocessing.dat_print as dp
from esmc.utils.opti_probl import OptiProbl

class TemporalAggregation:
    """
    A class used to perform temporal aggregation on time series of multi-regional energy systems.
    It also contains convenient functions to manipulate time series

    ...

    Attributes
    ----------
    regions_names : list
        ordered list of nuts abbreviation of the regions
    regions : dict
        dictionnary containing the different regions defined as Region objects
    weights : pd.DataFrame()
        weights of all the region concatenated and normalized
    n_daily_ts : pd.DataFrame()
        normalized daily time series of all regions concatenated
    n_data : pd.DataFrame()
        normalized and weighted daily time series of all regions concatenated, used in the clustering algorithm

    Methods
    -------
    says(sound=None)
        Prints the animals name and what sound it makes
    """

    def __init__(self, regions, dat_dir:Path,  time_series_mapping: dict, Nbr_TD=10, algo='kmedoid', ampl_path=None):

        self.regions_names = list(regions.keys())
        self.time_series_mapping = time_series_mapping
        self.demand_ts = list(time_series_mapping['eud_params'].keys())
        self.prod_ts = list(time_series_mapping['res_params'].keys()) \
                  + list(time_series_mapping['res_mult_params'].keys())
        self.Nbr_TD = Nbr_TD
        self.regions = regions
        self.dat_dir = dat_dir
        self.dat_dir.mkdir(parents=True, exist_ok=True)
        # pivot ts in each region to have (365x(24*N_ts))
        self.pivot_ts()

        self.weights = pd.DataFrame()
        self.n_daily_ts = pd.DataFrame()
        # group and weight the time series of all the regions
        self.group()
        self.n_data = pd.DataFrame()
        self.weight()

        self.td_of_days = pd.DataFrame()
        self.e_ts = np.nan
        # run clustering algorithm
        if algo=='kmedoid':
            self.td_of_days = self.kmedoid_clustering(ampl_path=ampl_path)
        elif algo=='read':
            self.td_of_days = self.read_td_of_days()
            self.e_ts = pd.read_csv(dat_dir / ('e_ts' + str(self.Nbr_TD) + '.txt'),
                                    header=None, index_col=None, sep='\t').values[0,0]

        logging.info('The typical days clustering has an time series error of ' + str(self.e_ts))
        self.t_h_td = pd.DataFrame()
        self.generate_t_h_td()
        return

    def read_td_of_days(self, td_file=None):
        """Reads the file containing the TD_of_days
        By default, reads the following path : self.dat_dir / ('TD_of_days_' + str(self.Nbr_TD) + '.out')
        Stores the data into the attribute td_of_days as a pd.DataFrame()
        """
        # default value of td_file
        if td_file is None:
            td_file = self.dat_dir / ('TD_of_days_' + str(self.Nbr_TD) + '.out')
        # logging info
        logging.info('Reading typical days from ' + str(td_file))
        # reading td_of_days
        td_of_days = pd.read_csv(td_file, header=None)
        td_of_days.columns = ['TD_of_days']
        td_of_days.index = np.arange(1,366)
        return td_of_days



    def pivot_ts(self):
        """Pivot the time series of each region in the daily format"""
        for r in self.regions.values():
            r.n_pivot_ts()

        return

    def group(self):
        """Groups the regions

         Groups time series and weights of the different regions
         and store them into the attributes n_daily_ts and weights
         The weights are normalized across regions according to the Cell_w
        """
        # compute Cell_w in each region
        for r in self.regions_names:
            self.regions[r].compute_cell_w(time_series_mapping=self.time_series_mapping)

        # create frames for concatenation (list of df to concat)
        frames = list()
        frames_w = list()
        for r in self.regions_names:
            frames.append(self.regions[r].n_daily_ts.copy())
            frames_w.append(self.regions[r].data['Weights'].copy())

        # concatenating and storing results into attributes
        self.n_daily_ts = pd.concat(frames, axis=1, keys=self.regions_names)
        self.weights = pd.concat(frames_w, keys=self.regions_names)

        # normalizing the weights accross regions
        self.normalize_weights()
        return

    def normalize_weights(self):
        """Normalize weights across regions

        The weights of each region are normalized taking into account the importance of each region (Cell_w)
        This importance is defined as the yearly demand for energy demands and as potential yearly production
        at full scale deployment for renewable energies.
        The results are stored in a new column of the weights attribute called 'Weights_n'

        """
        # TODO automatise this
        # demand and production time series names
        prod_ts_with_weight = [item for item in self.prod_ts if item in self.weights.index.unique(level=1)]
        demand_ts_with_weight = [item for item in self.demand_ts if item in self.weights.index.unique(level=1)]
        # prod_ts = ['PV', 'WIND_ONSHORE', 'WIND_OFFSHORE', 'HYDRO_DAM', 'HYDRO_RIVER', 'TIDAL', 'SOLAR']
        # demand_ts = ['ELECTRICITY','HEAT_LOW_T_SH','SPACE_COOLING']

        self.weights.loc[:,'Weights_n'] = 0.0 # initialize normalized weights column
        # NORMALIZING WEIGHTS ACCROSS COUNTRIES #
        regions_total = pd.Series(0.0,index=self.weights.index.levels[1])
        regions_total[demand_ts_with_weight] = self.weights.loc[(slice(None),demand_ts_with_weight), 'Cell_w'].sum(axis=0) # total of demand ts weights
        regions_total[prod_ts_with_weight] = self.weights.loc[(slice(None),prod_ts_with_weight), 'Cell_w'].sum(axis=0) # total of production ts weights

        # TODO automatize this (everything should happen in python code, prod and demand ts classification should be an input, set a treshold on cell_w and/or weight_n to neglect a ts, names should coincide with model's names)
        # replacing regions_total by the sum of demands for demands and the sum of potential productions for productions

        # first normalization
        self.weights.loc[:,'Weights_n'] = (self.weights.loc[:,'Cell_w']).div(regions_total, axis=0, level=1)
        # sort out the ts with Weights_n < 0.001 and renormalize the Weights_n
        self.weights.loc[self.weights['Weights_n']<0.001,'Weights_n'] = np.nan
        regions_total[demand_ts_with_weight] = self.weights.loc[(slice(None), demand_ts_with_weight), 'Weights_n'].sum(axis=0)  # total of demand ts weights
        regions_total[prod_ts_with_weight] = self.weights.loc[(slice(None), prod_ts_with_weight), 'Weights_n'].sum(axis=0)  # total of production ts weights
        # second normalization to have sum=1
        self.weights.loc[:,'Weights_n'] = (self.weights.loc[:,'Weights_n']).div(regions_total, axis=0, level=1)/2
        return


    def weight(self):
        """Weighting the normalized daily time series

        The normalized daily concatenated time series (n_daily_ts) are weighted by the normalized weights (weights['Weights_n']).
        The time series with no weight or a null weight are dropped.
        The result (n_data) is ready to be used in a clustering algorithm and is of shape (365x(len(non_null_weights)*24))

        """
        # use numpy broadcasting to multiply each time series by its weight
        self.n_data = self.numpy_broadcasting(self.weights.loc[:,'Weights_n'],self.n_daily_ts.transpose())
        # drop ts without weight
        self.n_data.dropna(axis=0, how='any', inplace=True)
        self.n_data = self.n_data.transpose() # transpose to the form (365x(n_ts*n_regions*24))

        return

    def print_dat(self, dat_file=None):
        """

        Parameters
        ----------
        dat_file

        Returns
        -------

        """
        if dat_file is None:
            # path to the .dat file
            dat_file = self.dat_dir / ('data_' + str(self.Nbr_TD) + '.dat')

        # set n_data columns index to numerical index
        n_data = self.n_data.copy()
        n_data.columns = np.arange(1, self.n_data.shape[1] + 1)

        # printing signature of data file
        dp.print_header(dat_file=dat_file, header_file=Path(__file__).parent/'kmedoid_clustering'/'header.txt')
        # printing SET DIMENSIONS
        dp.print_set(my_set=[str(i) for i in n_data.columns], out_path=dat_file, name='DIMENSIONS')

        # printing Nbr_TD
        dp.print_param(self.Nbr_TD, dat_file, name='Nbr_TD')
        dp.newline(dat_file)
        # printing weights as a comment
        weights = self.weights.copy()
        weights = weights.reset_index().rename(columns={'level_0':'Regions', 'level_1':'Time series'})
        weights['#'] = '#'
        weights = weights[['#', 'Regions', 'Time series', 'Weights', 'Cell_w', 'Weights_n']]
        weights.to_csv(dat_file, sep='\t', header=True, index=False, mode='a')
        dp.newline(dat_file)
        # printing param n_data in ampl syntax
        dp.print_df(df=dp.ampl_syntax(n_data), out_path=dat_file, name='param Ndata :')
        return

    def kmedoid_clustering(self, ampl_path=None):
        """

        Returns
        -------

        """

        # define path
        mod_path = Path(__file__).parent/'kmedoid_clustering'/'TD_main.mod'
        data_path = self.dat_dir/('data_'+str(self.Nbr_TD)+'.dat')
        log_file = self.dat_dir/('log_'+str(self.Nbr_TD)+'.txt')

        # logging info
        logging.info('Starting kmedoid clustering of typical days based on '+ str(data_path))


        # print .dat file
        self.print_dat(dat_file=data_path)

        # define options
        cplex_options = ['mipdisplay=5',
                               'mipinterval=1000',
                               'mipgap=1e-6']
        cplex_options_str = ' '.join(cplex_options)
        options= {'show_stats': 3,
                         'log_file': str(log_file),
                         'times': 1,
                         'gentimes': 1,
                         'cplex_options': cplex_options_str}

        # create and run optimization problem
        my_optimizer = OptiProbl(mod_path=[mod_path], data_path=[data_path], options=options, ampl_path=ampl_path)
        my_optimizer.run_ampl()
        # get cluster_matrix, compute td_of_days and print it
        cm = my_optimizer.ampl.getVariable('Cluster_matrix').get_values().to_pandas()
        ind = cm.index.names[0]
        col = cm.index.names[1]
        cm = cm.reset_index().pivot(index=ind, columns=col, values='Cluster_matrix.val')
        # cm = my_optimizer.outputs['Cluster_matrix'].pivot(index='index0', columns='index1', values='Cluster_matrix.val')
        cm.index.name = None
        td_of_days = pd.DataFrame(cm.mul(np.arange(1, 366), axis=0).sum(axis=0), index=np.arange(1,366),
                                  columns=['TD_of_days']).astype(int)
        td_of_days.to_csv(self.dat_dir/('TD_of_days_'+str(self.Nbr_TD)+'.out'), header=False, index=False, sep='\t')

        # get the clustering error and printong it
        self.e_ts = my_optimizer.ampl.get_objective('Euclidean_distance').value()
        with open(self.dat_dir/('e_ts'+str(self.Nbr_TD)+'.txt'), mode='w', newline='') as file:
            writer = csv.writer(file, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)
            writer.writerow([str(self.e_ts)])

        # closing ampl object
        my_optimizer.ampl.close()


        # logging info
        logging.info('End of typical days clustering')
        return td_of_days

    def generate_t_h_td(self):
        """Generate t_h_td and td_count dataframes and assign it to each region
        t_h_td is a pd.DataFrame containing 4 columns:
        hour of the year (H_of_Y), hour of the day (H_of_D), typical day representing this day (TD_of_days)
        and the number assigned to this typical day (TD_number)

        td_count is a pd.DataFrame containing 2 columns:
        List of typical days (TD_of_days) and number of days they represent (#days)
        """
        # GETTING td_of_days FROM TEMPORAL AGGREGATION
        td_of_days = self.td_of_days.copy()
        td_of_days['day'] = np.arange(1, 366, 1)

        # COMPUTING NUMBER OF DAYS REPRESENTED BY EACH TD AND ASSIGNING A TD NUMBER TO EACH REPRESENTATIVE DAY
        td_count = td_of_days.groupby('TD_of_days').count()
        td_count = td_count.reset_index().rename(columns={'index': 'TD_of_days', 'day': '#days'})
        td_count['TD_number'] = np.arange(1, self.Nbr_TD + 1)

        # BUILDING T_H_TD MATRICE
        t_h_td = pd.DataFrame(np.repeat(td_of_days['TD_of_days'].values, 24, axis=0),
                              columns=['TD_of_days'])  # column TD_of_days is each TD repeated 24 times
        map_td = dict(zip(td_count['TD_of_days'],
                          np.arange(1, self.Nbr_TD + 1)))  # mapping dictionnary from TD_of_Days to TD number
        t_h_td['TD_number'] = t_h_td['TD_of_days'].map(map_td)
        t_h_td['H_of_D'] = np.resize(np.arange(1, 25), t_h_td.shape[0])  # 365 times hours from 1 to 24
        t_h_td['H_of_Y'] = np.arange(1, 8761)
        # save into TemporalAggregation object
        self.t_h_td = t_h_td
        self.td_count = td_count

        #logging info
        logging.info('t_h_td and td_count generated')
        return

    def from_td_to_year(self, ts_td):
        """Converts time series on TDs to yearly time series

        Parameters
        ----------
        ts_td: pandas.DataFrame
        Multiindex dataframe of hourly data for each hour of each TD.
        The index should be of the form (TD_number, hour_of_the_day).

        t_h_td: pandas.DataFrame


        """
        if self.t_h_td is None:
            self.generate_t_h_td()

        td_h = self.t_h_td.loc[:, ['TD_number', 'H_of_D']]
        ts_yr = td_h.merge(ts_td, left_on=['TD_number', 'H_of_D'], right_index=True).sort_index()
        return ts_yr.drop(columns=['TD_number', 'H_of_D'])



    @staticmethod
    def numpy_broadcasting(df0, df1):
        """
        Multiplies 2 multiindexed pandas dataframes of different dimensions using numpy broadcasting
        Used to multiply each hour of each day for each time series of each region by its respective weight

        Parameters
        ----------
        df0: pd.Series()
            Multiindexed dataframe containing the normalized weights of the time series of each region
            (df0.index.levshape = (n_regions, n_ts))
        df1: pd.DataFrame()
            Multiindexed dataframe containing the times series of each region under the form:
            df1.index.levshape = (n_regions, n_ts, 24), df1.shape[1] = 365

        Returns
        -------
        df_out: pd.DataFrame()
            Multiindexed dataframe (same shape as df1), product of df1 by df0.
            For each region and each time series, all the hours of all the days are multiplied by the normalized weight (df0)

        """
        m, n, r = map(len, df1.index.levels)
        a0 = df0.values.reshape(m, n, -1)
        a1 = df1.values.reshape(m, n, r, -1)
        out = (a1 * a0[..., None, :]).reshape(-1, a1.shape[-1])
        df_out = pd.DataFrame(out, index=df1.index, columns=df1.columns)
        return df_out



    #TODO
    # add reading of TD_of_days.out if not running ta_algo