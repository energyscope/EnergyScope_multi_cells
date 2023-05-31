import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd

sys.path.append('/home/pthiran/EnergyScope_multi_cells/')
from esmc import Esmc
from esmc.common import eu33_country_code_iso3166_alpha2, eu33_full_names

cases = ['fossil_free_ref', 'fossil_free_no_ned', 'fossil_free_no_h2_network',
         'fossil_free_tc_max_elec_2.5GW', 'fossil_free_recycling_for_NED']
no_imports = ['GASOLINE', 'DIESEL', 'LFO', 'GAS', 'COAL', 'H2', 'AMMONIA', 'METHANOL']
# # importing national emissions of 1990 (eurostat data)
# co2_1990 = pd.read_excel(Path(__file__).parents[1] / 'Data' / 'exogenous_data' / 'regions' / 'Total_energy_1990.xlsx',
#                          sheet_name='Total', header=[0], index_col=[0], nrows=33).loc[eu27_full_names, 'Total [ktCO2]']
# # imposed emission reduction
# reduction = 0.9
# number of typical days (check that tse<0.22)
tds = 14

print('Nbr_TDs', tds)

# specify ampl_path (set None if ampl is in Path environment variable or the path to ampl if not)
ampl_path = None

# info to switch off unused constraints
gwp_limit_overall = None
re_share_primary = None
f_perc = False

i = 0

for c in cases:

    print(c)

    # define configuration
    config = {'case_study': c,
              'comment': 'none',
              'regions_names': eu33_country_code_iso3166_alpha2,
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

    # update some data
    # force to be fossil free
    for r_code, region in my_model.regions.items():
        region.data['Resources'].loc[no_imports, 'avail_exterior'] = 0
        # case study specific changes
        if c == 'fossil_free_no_ned':
            region.data['Demands'].loc['NON_ENERGY', 'INDUSTRY'] = 0
        elif c == 'fossil_free_recycling_for_HVC':
            region.data['Demands'].loc['NON_ENERGY', 'INDUSTRY'] *= 0.7 # we assume 30% of the feedstock can come from recycling

    if c == 'fossil_free_no_h2_network':
        my_model.data_reg['Exch']['Network_exchnages'].loc[(slice(None), slice(None), 'H2'), 'tc_min'] = 0
        my_model.data_reg['Exch']['Network_exchnages'].loc[(slice(None), slice(None), 'H2'), 'tc_max'] = 0
    elif c == 'fossil_free_tc_max_elec_2.5GW' :
        my_model.data_reg['Exch']['Network_exchnages'].loc[(slice(None), slice(None), 'ELECTRICITY'), 'tc_min'] = 0
        my_model.data_reg['Exch']['Network_exchnages'].loc[(slice(None), slice(None), 'ELECTRICITY'), 'tc_max'] = 2.5

    #     region.data['Misc']['gwp_limit'] = (1-reduction) * co2_1990.loc[code_2_full[r_code]]

    # Initialize and solve the temporal aggregation algorithm:
    # if already run, set algo='read' to read the solution of the clustering
    # else, set algo='kmedoid' to run kmedoid clustering algorithm to choose typical days (TDs)
    if i==0:
        my_model.init_ta(algo='kmedoid', ampl_path=ampl_path)
    else:
        my_model.init_ta(algo='read', ampl_path=ampl_path)


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

    i+=1