import pandas as pd
import numpy as np
from pathlib import Path


class Region:
    """

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

        self.n_daily_ts = pd.DataFrame()

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

    def pivot_ts(self):
        """

        Transforms the time series in the data to have normalized daily time series of shape (365x(N_ts*24))
        and stores it in the attribute n_daily_ts

        """
        # TODO make normlisation asside

        # NORMALIZING TIMESERIES #
        # compute norm = sum(ts)
        timeseries = self.data['Time_series']
        norm = timeseries.sum(axis=0)
        norm.name = 'Norm'
        # normalise ts to have sum(norm_ts)=1
        norm_ts = timeseries / norm
        # fill NaN with 0
        norm_ts.fillna(0, inplace=True)

        # CREATING DAY AND HOUR COLUMNS (for later pivoting) #
        # creating df with 2 columns : day of the year | hour in the day
        # TODO make it a global variable ?
        day_and_hour_array = np.ones((24 * 365, 2))
        for i in range(365):
            day_and_hour_array[i * 24:(i + 1) * 24, 0] = day_and_hour_array[i * 24:(i + 1) * 24, 0] * (i + 1)
            day_and_hour_array[i * 24:(i + 1) * 24, 1] = np.arange(1, 25, 1)
        day_and_hour = pd.DataFrame(day_and_hour_array, index=np.arange(1, 8761, 1), columns=['Days', 'H_of_D'])
        day_and_hour = day_and_hour.astype('int64')
        # merge day_and_hour with weight_ts for later pivot
        norm_ts = norm_ts.merge(day_and_hour, left_index=True, right_index=True)

        # pivoting normalized time series (norm_ts) to get daily normalized time series (Ndaily_ts)
        self.n_daily_ts = norm_ts.pivot(index='Days', columns='H_of_D', values=timeseries.columns)


        return