import pandas as pd
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
        return
    def read_weights(self, N_ts=7):
        self.data['Weights'] = pd.read_excel(self.data_path, sheet_name='2.2 User defined', header=[4], index_col=0,
                                             nrows=N_ts,usecols=[0, 1, 2],
                                             engine='openpyxl').rename(columns={'Unnamed: 1': 'Weights',
                                                                                'Cell importance': 'Cell_w'})
        self.data['Weights'].index.rename('Category', inplace=True)
        return

    def read_data(self):
        """

        Reads the weights of the different time seriess for the typical days selection step

        """
        self.read_ts()
        self.read_weights()
        return
