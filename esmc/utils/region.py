import logging

import pandas as pd
import numpy as np
from pathlib import Path

import esmc.postprocessing.amplpy2pd as a2p
from esmc.utils.df_utils import clean_indices
from esmc.common import CSV_SEPARATOR


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

    def __init__(self, nuts, data_dir, ref_region=False):
        # instantiate different attributes
        self.nuts = nuts
        self.ref_region = ref_region # whether it is the reference region or not
        #TODO add geographical management
        # self.name =
        # self.geo =
        self.data_path = data_dir/nuts
        #('DATA_'+nuts+'.xlsx')
        if ref_region:
            self.data = dict()
        self.read_data()

        self.n_daily_ts = pd.DataFrame() # normalized (sum over the year=1) daily time series (shape=(365x(24*n_ts))
        self.ts_td = None # rescaled daily time series of the typical days
        self.peak_sh_factor = np.nan # ...

        self.results = dict()

        return

    def read_ts(self):
        """
        Reads the time series defining the hourly data of the region and stores it in the data attribute as a dataframe
        (demands and intermittent renewable energies production)

        """
        # The time series are redefined fully without considering the data of the ref_region
        # read the csv
        self.data['Time_series'] = pd.read_csv(self.data_path/'Time_series.csv', sep=CSV_SEPARATOR, header=[0], index_col=0)
        self.data['Time_series'] = clean_indices(self.data['Time_series'])
        self.data['Time_series'].set_index(np.arange(1, 8761), inplace=True) # setting index from 1 to 8760 hours
        return

    def read_weights(self):
        """Read the weights of the time series of this region and stores it in the data attribute as a dataframe

        Returns
        -------

        """
        # the Weights are redefined fully without considering the ref_region
        self.data['Weights'] = pd.read_csv(self.data_path/'Weights.csv', sep=CSV_SEPARATOR, header=[0], index_col=[0])\
            .dropna(axis=0, how='any')
        self.data['Weights'].index.rename('Category', inplace=True)
        self.data['Weights'] = clean_indices(self.data['Weights'])

        # The time series without weight into data have NaN as Weight
        self.data['Weights'] = self.data['Weights'].reindex(self.data['Time_series'].columns,
                                                            method=None, fill_value=np.nan)
        return

    def read_eud(self):
        """Read the End-uses demands of the region and stores it in the data attribute as a dataframe

        Returns
        -------

        """
        # the Demands is redefined fully without considering the ref_region
        self.data['Demands'] = pd.read_csv(self.data_path/'Demands.csv', sep=CSV_SEPARATOR, header=[0], index_col=[2])
        self.data['Demands'] = clean_indices(self.data['Demands'])
        return

    def read_resources(self):
        """Reads the resources data of the region and stores it in the data attribute as a dataframe

        Returns
        -------

        """
        r_path = self.data_path / 'Resources.csv'
        # if the file exist, update the data
        if r_path.is_file():
            if self.ref_region:
                # read csv and clean df
                df = pd.read_csv(r_path, sep=CSV_SEPARATOR, header=[2], index_col=[2]).dropna(axis=1, how='all')
                df = clean_indices(df)
                # put df into attribute data
                self.data['Resources'] = df
            else:
                # read csv and clean df
                df = pd.read_csv(r_path, sep=CSV_SEPARATOR, header=[0], index_col=[0]).dropna(axis=1, how='all')
                df = clean_indices(df)
                # using update method to replace only the data redefined in the csv of the region
                self.data['Resources'].update(df)

        return

    def read_tech(self):
        """
        Reads the technologies data of the region and stores it in the data attribute as a dataframe
        """
        r_path = self.data_path / 'Technologies.csv'
        # if the file exist, update the data
        if r_path.is_file():
            if self.ref_region:
                # read csv and clean df
                df = pd.read_csv(r_path, sep=CSV_SEPARATOR, header=[0], index_col=[3], skiprows=[1],
                                 dtype={'fmin_perc': np.float64, 'f_min': np.float64}).drop(
                    columns=['Comment']
                    , errors='ignore')
                df = clean_indices(df)
                # put df into attribute data
                self.data['Technologies'] = df
            else:
                df = pd.read_csv(r_path, sep=CSV_SEPARATOR, header=[0], index_col=[0]).dropna(how='all', axis=1)
                df = clean_indices(df)
                # using update method to replace only the data redefined in the csv of the region
                self.data['Technologies'].update(df)
        return

    def read_storage_power_to_energy(self):
        """
        Reads the storage power to energy ratio of the region and stores it in the data attribute as a dataframe
        """
        r_path = self.data_path / 'Storage_power_to_energy.csv'
        # if the file exist, update the data
        if r_path.is_file():
            # read csv and clean df
            df = pd.read_csv(r_path, sep=CSV_SEPARATOR, header=[0], index_col=[0])
            df = clean_indices(df)

            # put df into attribute data
            if self.ref_region:
                self.data['Storage_power_to_energy'] = df
            else:
                # using update method to replace only the data redefined in the csv of the region
                self.data['Storage_power_to_energy'].update(df)
        return

    def read_misc(self):
        """
        Reads the miscellaneous data of the region and store it in the data attribute as a dictionary
        """
        r_path = (self.data_path/'Misc.json')
        # if the file exist, update the data
        if r_path.is_file():
             d = a2p.read_json(r_path)
             if self.ref_region:
                 self.data['Misc'] = d
             else:
                 # if not ref_region replace edited values
                for key, value in d.items():
                    self.data['Misc'][key] = value

        return


    def read_data(self, all=True, ):
        """
        Reads the data related to this region
        """
        logging.info('Read data from '+str(self.data_path))

        self.read_eud()
        self.read_resources()
        self.read_tech()
        self.read_storage_power_to_energy()
        self.read_ts()
        self.read_weights()
        self.read_misc()
        return

    def compute_cell_w(self, time_series_mapping:dict):
        """Compute the weight of each time series in the region (Cell_w)
            
        Parameters
        ----------
        demand_ts: list
            List of demand time series. It should use the same nomenclature as time series data.
        prod_ts : list
            List of production time series. It should use the same nomenclature as time series data.
        """
        # Instantiate tot_ts and tot_yr
        tot_ts = self.data['Time_series'].sum(axis=0)

        # TODO automatise this
        demand_ts = list(time_series_mapping['eud_params'].keys())
        prod_ts = list(time_series_mapping['res_params'].keys()) \
                       + list(time_series_mapping['res_mult_params'].keys())
        # # default name of demand and prod ts if not given
        # if demand_ts is None:
        #     demand_ts = ['ELECTRICITY', 'HEAT_LOW_T_SH', 'SPACE_COOLING']
        # if prod_ts is None:
        #     prod_ts = ['PV', 'WIND_ONSHORE', 'WIND_OFFSHORE', 'HYDRO_DAM', 'HYDRO_RIVER', 'TIDAL', 'SOLAR']

        # dictionnary for time series linking with multiple entries
        # demand_map = {'ELECTRICITY':['LIGHTING']}
        res_mult_params = time_series_mapping['res_mult_params']
            # TODO improve integration of solar_area and limits and adapt

        # select only simple demand and prod ts
        # demand_simple = [t for t in demand_ts if t not in demand_map.keys()]
        prod_simple = [t for t in prod_ts if t not in res_mult_params.keys()]

        # multiply demand time series sum by the year consumption
        tot_ts[demand_ts] = tot_ts[demand_ts]*self.data['Demands'].loc[demand_ts, :]\
            .sum(axis=1,numeric_only=True)
        # for t,l in demand_map.items():
        #     tot_ts[t] = tot_ts[t]*self.data['Demands'].loc[l,:].sum(axis=1, numeric_only=True).sum(axis=0)
        # multiply the sum of the production time series
        # by the maximum potential (f_max in GW) of the corresponding technologies
        tot_ts[prod_simple] = tot_ts[prod_simple] * self.data['Technologies'].loc[prod_simple,'f_max']
        for t,l in res_mult_params.items():
            tot_ts[t] = tot_ts[t] * self.data['Technologies'].loc[l,'f_max'].sum()

        # Add Cell_w to the Weights data
        self.data['Weights'].loc[:,'Cell_w'] = tot_ts*self.data['Weights'].loc[:,'Weights']

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
        tot_td = ts_td.groupby(level=0).sum().mul(td_count.set_index('TD_of_days').loc[:,'#days'],axis=1).sum(axis=1)
        ts_td = ts_td.mul(tot_yr/tot_td,axis=0, level=0).fillna(value=1e-4) # rescaling the ts of the TDs to have the same total over the year
        ts_td.columns = td_count['TD_number'] # set index to TD_number
        self.ts_td = ts_td
        return

    def compute_peak_sh_and_sc(self):
        """Computes the peak_sh_factor
        Computes the ratio between the peak space heating demand over the year and over the typical days (peak_sh_factor)
        and stores it into the attribute
        """
        if self.ts_td is None:
            logging.error('Call first rescale_td_ts to compute td_ts')
        # TODO this should be linked with the inputs for the names of the ts
        max_sh_td = self.ts_td.loc[('HEAT_LOW_T_SH', slice(None)),:].max().max()
        max_sh_yr = self.data['Time_series'].loc[:,'HEAT_LOW_T_SH'].max()
        self.peak_sh_factor = max_sh_yr/max_sh_td

        max_sc_td = self.ts_td.loc[('SPACE_COOLING', slice(None)), :].max().max()
        max_sc_yr = self.data['Time_series'].loc[:, 'SPACE_COOLING'].max()
        self.peak_sc_factor = max_sc_yr / max_sc_td
        return

    def compute_tau(self, i_rate=0.015):
        """Compute the annualisation factor for each technology

        Parameters
        ---------
        i_rate : float
        Discount rate
        """
        # create a series i_rate with technologies names as index
        tech = self.data['Technologies']
        i_rate_s = pd.Series(i_rate, index=tech.index)
        tau = i_rate_s * (1 + i_rate_s) ** tech['lifetime'] / (((1 + i_rate_s) ** tech['lifetime']) - 1)
        self.data['tau'] = tau
        return

#TODO generate synthetic time series
