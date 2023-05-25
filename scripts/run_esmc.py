import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd

sys.path.append('/home/pthiran/EnergyScope_multi_cells/')
from esmc import Esmc
from esmc.common import eu27_country_code, eu27_full_names, code_2_full

# importing national emissions of 1990 (eurostat data)
co2_1990 = pd.read_excel(Path(__file__).parents[1] / 'Data' / 'exogenous_data' / 'regions' / 'Total_energy_1990.xlsx',
                         sheet_name='Total', header=[0], index_col=[0], nrows=33).loc[eu27_full_names, 'Total [ktCO2]']
# imposed emission reduction
reduction = 0.9
# number of typical days (check that tse<0.22)
tds = 14

print('Nbr_TDs', tds)

# specify ampl_path (set None if ampl is in Path environment variable or the path to ampl if not)
ampl_path = None

# info to switch off unused constraints
gwp_limit_overall = None
re_share_primary = None
f_perc = False

# define configuration
config = {'case_study': 'test_new_elec_tc',
          'comment': 'none',
          'regions_names': ['DK-SE', 'BE-DE-LU-NL', 'IE-UK'], #eu27_country_code,
          'ref_region': 'FR',
          'gwp_limit_overall': gwp_limit_overall,
          're_share_primary': re_share_primary,
          'f_perc': f_perc,
          'year': 2035}

# initialize EnergyScope Multi-cells framework
my_model = Esmc(config, nbr_td=tds)

# read the indep data
my_model.read_data_indep()

# initialize the different regions and reads their data
my_model.init_regions()

# # update some data
# for r_code, region in my_model.regions.items():
#     region.data['Misc']['gwp_limit'] = (1-reduction) * co2_1990.loc[code_2_full[r_code]]

# Initialize and solve the temporal aggregation algorithm:
# if already run, set algo='read' to read the solution of the clustering
# else, set algo='kmedoid' to run kmedoid clustering algorithm to choose typical days (TDs)
my_model.init_ta(algo='kmedoid', ampl_path=ampl_path)

# Print the time related data of the energy system optimization model using the TDs to represent it
my_model.print_td_data()

# Print data
my_model.print_data(indep=True)

# Set the Energy System Optimization Model (ESOM) as an ampl formulated problem
my_model.set_esom(ampl_path=ampl_path)

# Solving the ESOM
my_model.solve_esom()

# Getting and printing year results
my_model.get_year_results()
my_model.prints_esom(inputs=True, outputs=True, solve_info=True)

# delete ampl object to free resources
my_model.esom.ampl.close()
