import logging

import pandas as pd
import numpy as np
from pathlib import Path


class Region:
    """TODO update doc

    The Region class defines a region with its nuts abbreviation and allows to read the data corresponding to that region

    Parameters
    ----------
    nuts : str
        nuts abbreviation of the region. If several regions merged together, '-' is used between the regions names
    data_dir : pathlib.Path
       path to the directory containing all the data

    """

    def __init__(self, nuts, data_dir):
        # instantiate different attributes
        self.nuts = nuts
        #TODO add geographical management
        # self.name =
        # self.geo =
        self.data_path = data_dir/('DATA_'+nuts+'.xlsx')
        self.data = dict()
        self.read_data()

        self.n_daily_ts = pd.DataFrame() # normalized (sum over the year=1) daily time series (shape=(365x(24*n_ts))
        self.ts_td = None # rescaled daily time series of the typical days
        self.peak_sh_factor = np.nan # ...

        self.results = dict()

        return

    def read_ts(self):
        """
        Reads the time series defining the hourly data of the region
        (demands and intermittent renewable energies production)

        """
        self.data['Time_series'] = pd.read_excel(self.data_path, sheet_name='1.1 Time Series', header=[1], index_col=0,
                                                 nrows=8760, engine='openpyxl')
        self.data['Time_series'].drop(labels='period_duration [h]', axis=1, inplace=True)
        self.data['Time_series'].dropna(axis=1, how='all', inplace=True)
        return

    def read_eud(self):
        self.data['Demand'] = pd.read_excel(self.data_path, sheet_name='2.3 EUD', header=[1], index_col=0,
                                             nrows=10,usecols=[0, 1, 2, 3, 4], engine='openpyxl')
        self.data['Demand'].index.rename('EUD', inplace=True)
        return

    def read_weights(self, N_ts=8):
        self.data['Weights'] = pd.read_excel(self.data_path, sheet_name='2.2 User defined', header=[4], index_col=0,
                                             nrows=N_ts,usecols=[0, 1, 2],
                                             engine='openpyxl').rename(columns={'Unnamed: 1': 'Weights',
                                                                                'Cell importance': 'Cell_w'})\
            .dropna(axis=0, how='any')
        self.data['Weights'].index.rename('Category', inplace=True)
        # The time series without weight into data have NaN as Weight and Cell_w
        self.data['Weights'] = self.data['Weights'].reindex(self.data['Time_series'].columns, method=None, fill_value=np.nan)
        return

    def read_data(self):
        """

        Reads the weights of the different time series for the typical days selection step

        """
        self.read_ts()
        self.read_eud()
        self.read_weights()
        return

    def norm_ts(self, ts=None):
        """Compute the normalized time series
        Parameters
        ----------
        ts : pd.DataFrame()
            Time series to normalize under the form (365xN_ts).
            If no time series is given, then self.data['Time_series'] is taken as a default

        Returns
        -------
        Normalized time series dataframe

        """
        # NORMALIZING TIMESERIES
        if ts is None:
            ts = self.data['Time_series'].copy()
        return (ts/ts.sum()).fillna(0)

    def pivot_ts(self, ts=None):
        """Pivot time series in daily format

        Transforms the time series in the data to have normalized daily time series of shape (365x(N_ts*24))
        and stores it in the attribute n_daily_ts

        Parameters
        ----------
        ts : pd.DataFrame()
            Time series to pivot under the form (365xN_ts).
            If no time series is given, then self.data['Time_series'] is taken as a default

        Returns
        -------
        Pivoted time series in the daily format (365x(N_ts*24))

        """
        if ts is None:
            ts = self.data['Time_series'].copy()

        ts_names = ts.columns
        # adding columns for pivoting
        ts['Days'] = np.repeat(np.arange(1,366), 24, axis=0)
        ts['H_of_D'] = np.resize(np.arange(1,25), ts.shape[0])
        # pivoting normalized time series (norm_ts) to get daily normalized time series (Ndaily_ts)
        return ts.pivot(index='Days', columns='H_of_D', values=ts_names)

    def n_pivot_ts(self, ts=None):
        """Normalize and pivot time series

        Normalized and pivoted time series in the daily format (365x(N_ts*24)) is stored into n_daily_ts attribute

        Parameters
        ----------
        ts : pd.DataFrame()
            Time series (365xN_ts) to normalize and pivot under the form.
            If no time series is given, then self.data['Time_series'] is taken as a default

        """
        if ts is None:
            ts = self.data['Time_series'].copy()

        self.n_daily_ts = self.pivot_ts(ts=self.norm_ts(ts=ts))

        return

    def rescale_td_ts(self, td_count: pd.DataFrame):
        """Select and rescale the time series of the typical days (TDs)
        The time series of the typical days are rescaled such that
        the sum over the year of the synthetic time series produced from the TDs
        is equal to the sum over the year of the original time series

        """
        ts = self.data['Time_series'].copy()
        tot_yr = ts.sum() # compute the total of each ts over the year
        ts = self.pivot_ts(ts).transpose() # pivotting the ts in a daily format
        ts_td = ts.loc[:,td_count['TD_of_days']] # selecting only the ts of TDs
        # computing the total over the year by multiplying the total of each TD by the number of days it represents
        tot_td = ts_td.sum(axis=0,level=0).mul(td_count.set_index('TD_of_days').loc[:,'#days'],axis=1).sum(axis=1)
        ts_td = ts_td.mul(tot_yr/tot_td,axis=0, level=0).fillna(value=1e-4) # rescaling the ts of the TDs to have the same total over the year
        ts_td.columns = td_count['TD_number'] # set index to TD_number
        self.ts_td = ts_td
        return

    def compute_peak_sh(self):
        """Computes the peak_sh_factor
        Computes the ratio between the peak space heating demand over the year and over the typical days (peak_sh_factor)
        and stores it into the attribute
        """
        if self.ts_td is None:
            logging.error('Call first rescale_td_ts to compute td_ts')

        max_sh_td = self.ts_td.loc[('Space Heating (%_sh)', slice(None)),:].max().max()
        max_sh_yr = self.data['Time_series'].loc[:,'Space Heating (%_sh)'].max()
        self.peak_sh_factor = max_sh_yr/max_sh_td
        return

#TODO generate synthetic time series
