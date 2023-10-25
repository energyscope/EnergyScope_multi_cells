# -*- coding: utf-8 -*-
"""
This module provides functions used to generate csv input data from exogenous data

@author: Paolo Thiran
"""
import pandas as pd
from pathlib import PurePath
import pvlib
from datetime import datetime
from esmc.common import CSV_SEPARATOR
import json

import os
from oemof.thermal.concentrating_solar_power import csp_precalc

# Module-wide variables
# path
project_dir = PurePath(__file__).parents[2]
ex_data_dir = project_dir / 'Data' / 'exogenous_data'


def compute_csp_ts(lat: float, long: float, year: int=2015,
                   additional_losses: float =0.2, eff_improvements: float = 0.1369,
                   land_use_csp_coll: float = 2.2353) -> pd.Series:
    """Computes the time series of heat production of the CSP [GW_th] per unit of collector installed [GW_p,th]
    Parameters
    ---------
    lat : float
        Latitude of the csp power plant
    lon : float
        Longitude of the csp power plant
    year : int, default: 2015
        Representative year for the meteorological data
    additional_losses : float, default: 0.2
        Additional losses after the collectors (e.g. in the pipes).
    eff_improvements : float, default: 0.1369
        Estimated overall efficiency improvement of the thermal part of the plant.
    land_use_csp_coll : float, default 2.2353
        Surface used for the entire plant per GW_th of collectors [km^2/GW_p,th]
    Returns
    -------
    csp_heat : Series
        Hourly time series (in UTC) of thermal production [kWh_th/kW]
        of the csp plant for the selected meteorological year
    meta : dict
        metadata of pvgis meteorological data
    """
    # getting the irradiance and tempurature data
    data, meta, inputs = pvlib.iotools.get_pvgis_hourly(latitude=lat, longitude=long, start=year, end=year,
                                                        raddatabase='PVGIS-SARAH2', trackingtype=2,
                                                        usehorizon=True, map_variables=False,
                                                        url='https://re.jrc.ec.europa.eu/api/v5_2/')


    # Parameters of the csp plant
    collector_tilt = 10
    collector_azimuth = 180
    cleanliness = 0.9
    a_1 = -0.00159
    a_2 = 0.0000977
    eta_0 = 0.816
    c_1 = 0.0622
    c_2 = 0.00023
    temp_collector_inlet = 435
    temp_collector_outlet = 500

    # computing the heat production of the csp plant [W/m^2]
    data_precalc = csp_precalc(lat, long,
                               collector_tilt, collector_azimuth, cleanliness,
                               eta_0, c_1, c_2,
                               temp_collector_inlet, temp_collector_outlet,
                               data['T2m'],
                               a_1, a_2,
                                irradiance_method='normal',
                               dni=data['Gb(i)'])

    # computing the final time series
    # additonal losses and efficiency improvement
    csp_heat = data_precalc['collector_heat'] * (1 - additional_losses) * (1 + eff_improvements)
    tot_irr = data['Gb(i)'].sum()
    tot_csp_heat = csp_heat.sum()
    eta_th = tot_csp_heat / tot_irr
    meta['eta_th'] = eta_th

    # converting [W/m^2] into [GW_th/GW_p,th]
    csp_heat = (csp_heat/1000)*land_use_csp_coll

    return csp_heat, meta

def generate_all_csp_ts(year: int=2015, land_use_csp: float=1/0.170, eta_pb: float=0.38,
                        additional_losses: float=0.2, eff_improvements: float=0.1369,
                        csp_file: PurePath=None, print_csv: bool=False):
    """

    Parameters
    ----------
    year : int, default: 2015
        Representative year considered
    land_use_csp : float, default: 1/0.170
        Land used for a typical csp power plant as a function of the capacity of power block installed [km^2/GW_p,e],
        (based on power plant with SM=1, if SM>1, then we assume increase in area used is proportional
        to the land used by the collectors)
    eta_pb : float, default: 0.38
        Efficiency of power block,
        used to compute the equivalent land used as a function of the capacity of collector installed [km^2/GW_p,th]
    additional_losses : float, default: 0.2
        Additional losses after the collectors (e.g. in the pipes).
    eff_improvements : float, default: 0.1369
        Estimated overall efficiency improvement of the thermal part of the plant.
    csp_file : PurePath; default: None
        Path to the json file defining the region for which to compute cst time series and their reference csp plant,
        It should follow this structure: 
        {"ES": {"repr_plant": "Extresol 1", "status": "Operational",
        "latitude": 38.65, "longitude": -6.733}}
    print_csv : bool, default=False
        Set to True to print computed data into "../../Data/exogenous_data/csp_oemof_thermal/ts_csp.csv "
    Returns
    -------
    ts : DataFrame
        Dataframe containing the hourly time series (in UTC) of thermal production [kWh_th/kW]
        of the different csp plants in the different regions for the selected meteorological year

    run_dict: dict
        Dictionary containing the configuration and metadata of the csp computation
    """
# TODO here finish and test

    # put default csp_file if not given
    if csp_file is None:
        csp_file = ex_data_dir / 'csp' / 'csp_to_compute.json'

    with open(csp_file, 'r') as fp:
        csp_to_compute = json.load(fp)

    # compute the surface used for the entire plant per GW_th of collectors [km^2/GW_p,th]
    land_use_csp_coll = land_use_csp * eta_pb

    # compute ts for each location
    leap_yr = ((year % 4) == 0)
    dt_index = pd.date_range(start=datetime(year,1,1), periods=8760, tz='UTC', freq='H')
    ts = pd.DataFrame(0, index=dt_index, columns=csp_to_compute.keys())
    all_meta = dict.fromkeys(csp_to_compute.keys())
    for k,v in csp_to_compute.items():
        print('Computing csp ts for ' + k + ' with following representative plant: ' + v['repr_plant'])
        ser, meta = compute_csp_ts(lat=v['latitude'], long=v['longitude'],
                            year=year, additional_losses=additional_losses,
                            eff_improvements=eff_improvements, land_use_csp_coll=land_use_csp_coll)

        if leap_yr:
            ser = ser.loc[~((ser.index.month == 2) & (ser.index.day == 29))]
        ts.loc[:, k] = ser.values
        all_meta[k] = meta

    run_dict = {'csp_to_compute': csp_to_compute, 'meta': all_meta}

    # save into a csv
    if print_csv:
        ts.to_csv(ex_data_dir / 'csp' / 'ts_csp.csv', sep=CSV_SEPARATOR)
        
    return ts, run_dict

