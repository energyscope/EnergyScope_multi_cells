import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd


# Add parent directory to path to import esmc package
sys.path.insert(0, str(Path(__file__).parent.parent))
from esmc import Esmc
from esmc.common import eu34_country_code_iso3166_alpha2, CSV_SEPARATOR

# cwd = Path.cwd()
# print('Current working directory:', cwd)

# regions_names = ['BE'] #eu34_country_code_iso3166_alpha2

# exch_path = cwd / 'Data' / '2050' /'01_EXCH'
# import esmc.postprocessing.amplpy2pd as a2p

# r_path = (exch_path / 'Misc_exch.json')
# misc_exch = {}
# if r_path.is_file(): # if the file exist, update the data
#     misc_exch = a2p.read_json(r_path)
# net_exch = pd.read_csv(exch_path / 'Network_exchanges.csv', sep=CSV_SEPARATOR,
#                                                       header=[0], index_col=[0, 1, 2, 3])

# res_net = misc_exch['add_sets']['NETWORK_TYPE']
# pair_index = pd.MultiIndex.from_tuples(
#     [(r, r, res, n) for r in regions_names for res, net in res_net.items() for n in net],
#     names=net_exch.index.names,
# )
# net_exch = net_exch.reindex(net_exch.index.union(pair_index), fill_value=0).sort_index().loc[(regions_names, regions_names, misc_exch['add_sets']['EXCHANGE_NETWORK_R'], slice(None)), :]


#  self.data_reg['Exch']['Network_exchanges'] = pd.read_csv(data_path / 'Network_exchanges.csv', sep=CSV_SEPARATOR,
#                                                       header=[0], index_col=[0, 1, 2, 3]).loc[
#                                           (self.regions_names, self.regions_names,
#                                            self.data_reg['Exch']['Misc_exch']['add_sets']['EXCHANGE_NETWORK_R'],
#                                            slice(None)), :]


# defining cases
c = 'test_3c'

# blocking all import of fossil fuels to reach a fossil-free energy system
no_imports = ['GASOLINE', 'DIESEL', 'LFO', 'JET_FUEL', 'GAS', 'COAL', 'H2', 'AMMONIA', 'METHANOL']

# number of typical days (check that tse<0.22)
tds = 14

print('Nbr_TDs', tds)

# specify ampl_path (set None if ampl is in Path environment variable or the path to ampl if not)
ampl_path = None

# info to switch off unused constraints
gwp_limit_overall = None
re_share_primary = None
f_perc = False

# results to save with an hourly time step
save_hourly = ['Resources', 'Exchanges', 'Assets', 'Storage', 'Curt']

# printing name of case
print(c)

# define configuration
config = {'case_study': c,
          'comment': 'none',
          'regions_names': ['BE'], #eu34_country_code_iso3166_alpha2,
          'gwp_limit_overall': gwp_limit_overall,
          're_share_primary': re_share_primary,
          'f_perc': f_perc,
          'year': 2050}

# initialize EnergyScope Multi-cells framework
my_model = Esmc(config, nbr_td=tds)

# read the indep data
my_model.read_data_indep()

# initialize the different regions and reads their data
my_model.init_regions()

# force to be 100% renewable
for r_code, region in my_model.regions.items():
    # fossil-free
    region.data['Resources'].loc[no_imports, 'avail_exterior'] = 0
    # nuclear free
    region.data['Technologies'].loc['NUCLEAR', 'f_min'] = 0
    region.data['Technologies'].loc['NUCLEAR', 'f_max'] = 0

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
my_model.get_year_results(save_hourly=save_hourly)
my_model.prints_esom(inputs=True, outputs=True, solve_info=True, save_hourly=save_hourly)

# delete ampl object to free resources
my_model.esom.ampl.close()