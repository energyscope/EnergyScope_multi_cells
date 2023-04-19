# -*- coding: utf-8 -*-
"""
This script reads data from external sources,
computes the hourly time series from it,
and puts them into csv Data

@author: Paolo Thiran
"""

# TODO
# choose another location for csp FR because this one is too low
# print time series
# make a function out of it
# learn geopandas for centroid and distances (+plots)
# solar thermal ts from opsd data + centroid + oemof.thermal
# write doc solar
# update distances and exchanges modelling
# get RES potentials from ENSPRESO
# test run
# put onto gitkraken

import pandas as pd

from esmc import generate_all_csp_ts
from pathlib import PurePath
from esmc import CSV_SEPARATOR

# path
project_dir = PurePath(__file__).parents[1]
data_dir = project_dir / 'Data'
ex_data_dir = data_dir / 'exogenous_data'



# computing csp ts
# fixed parameters
ref_year = 2015
# general parameters to convert into ESMC inputs (time series of [GW_th/GW_p,th]
land_use_csp = 1/0.170  # [km^2/GW_p,e] (If SM=1, surface used for the entire plant per GW electrical installed)
eta_pb = 0.38  # efficiency of power block
additional_losses = 0.2 # additional losses (e.g. in the pipes)
eff_improvements = 0.1369 # overall efficiency improvement of the thermal part of the plant

csp_ts, run_dict = generate_all_csp_ts(year=ref_year, land_use_csp=land_use_csp, eta_pb=eta_pb, additional_losses=additional_losses,
                         eff_improvements=eff_improvements,
                         csp_file=ex_data_dir / 'csp' / 'csp_to_compute.json',
                         print_csv=True)

# proj_year = 2035
# region = 'FR'
# file = 'Time_series.csv'
# ser = csp_ts.loc[:,region]
# ser.name = 'SOLAR'
# ser = ser.reset_index(drop=True)
# ser.index = ser.index + 1
#
# file_path = data_dir / str(proj_year) / region / file
# my_df = pd.read_csv(file_path, sep=CSV_SEPARATOR)
# my_df.update(ser)
