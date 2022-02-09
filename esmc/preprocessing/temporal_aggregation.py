""" Temporal aggregation class

This class defines the object TemporalAggregation and its methods
to perform temporal aggregation on time series of multi-regional energy systems
"""
import numpy as np
import pandas as pd
import csv
from pathlib import Path
import esmc.preprocessing.dat_print as dp

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

    def __init__(self, regions, dat_dir, Nbr_TD=10):
        """TODO
        Parameters
        ----------
        name : str
            The name of the animal
        sound : str
            The sound the animal makes
        num_legs : int, optional
            The number of legs the animal (default is 4)
        """
        self.regions_names = list(regions.keys())
        self.Nbr_TD = Nbr_TD
        self.regions = regions
        self.dat_dir = dat_dir
        self.pivot_ts()

        self.weights = pd.DataFrame()
        self.n_daily_ts = pd.DataFrame()

        self.group()

        self.n_data = pd.DataFrame()

        self.weight()

        self.print_dat()

        return

    def pivot_ts(self):
        """Pivot the time series of each region in the daily format"""
        for r in self.regions.values():
            r.pivot_ts()

        return

    def group(self):
        """Groups the regions

         Groups time series and weights of the different regions
         and store them into the attributes n_daily_ts and weights
         The weights are normalized across regions according to the Cell_w
        """

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

        self.weights.loc[:,'Weights_n'] = 0 # initialize normalized weights column
        # NORMALIZING WEIGHTS ACCROSS COUNTRIES #
        regions_total = self.weights.loc[:, 'Cell_w'].sum(axis=0, level=1)
        self.weights.loc[:,'Weights_n'] = (self.weights.loc[:,'Weights']*self.weights.loc[:,'Cell_w']).div(regions_total, axis=0, level=1)
        return

    def weight(self):
        """Weighting the normalized daily time series

        The normalized daily concatenated time series (n_daily_ts) are weighted by the normalized weights (weights['Weights_n']).
        The time series with no weight or a null weight are dropped.
        The result (n_data) is ready to be used in a clustering algorithm and is of shape (365x(len(non_null_weights)*24))

        """
        # use numpy broadcasting to multiply each time series by its weight
        self.n_data = self.numpy_broadcasting(self.weights.loc[:,'Weights_n'],self.n_daily_ts.transpose())
        self.n_data.dropna(axis=0, how='any', inplace=True) # drop ts without weight
        self.n_data = self.n_data.transpose() # transpose to the form (365x(n_ts*n_regions*24))


        return

    def print_dat(self):
        """

        Returns
        -------

        """

        # set n_data columns index to numerical index
        n_data = self.n_data.copy()
        n_data.columns = np.arange(1, self.n_data.shape[1] + 1)

        # path to the .dat file
        dat_file = self.dat_dir / ('data'+str(self.Nbr_TD)+'.dat')

        # printing signature of data file
        dp.print_header(Path(__file__).parent/'kmedoid_clustering'/'header.txt', dat_file)
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
    # test the whole chain to create n_data
    # add the print of .dat
    # add clustering model attribute -> first step do it with ampl model but think that it could be replaced by another one
    # add solving of model and ouptut
    # add print of ESTD_##TD.dat