import numpy as np
from pathlib import Path

# additional line for VS studio
import sys

import pandas as pd

sys.path.append('/home/pthiran/EnergyScope_multi_cells/')
from esmc import Esmc
from esmc.common import eu28_country_code

# defining cases
cases = ['100perc_re', '100perc_re_plus_waste', '100perc_re_no_plane_and_shipping',
         '100perc_re_no_ned', '100perc_re_no_plane_shipping_ned']
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

save_hourly = ['Resources', 'Exchanges', 'Assets', 'Storage', 'Curt']

i = 0

for c in cases:

    print(c)

    # define configuration
    config = {'case_study': c,
              'comment': 'none',
              'regions_names': eu28_country_code,
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

    # update some data
    # force to be 100% renewable
    for r_code, region in my_model.regions.items():
        # fossil-free
        region.data['Resources'].loc[no_imports, 'avail_exterior'] = 0
        # nuclear free
        region.data['Technologies'].loc['NUCLEAR', 'f_min'] = 0
        region.data['Technologies'].loc['NUCLEAR', 'f_max'] = 0
        # no waste incineration
        if c != '100perc_re_plus_waste':
            region.data['Resources'].loc['WASTE', 'avail_local'] = 0

    # according to case change some inputs
    if c == '100perc_re_no_plane_and_shipping':
        for r_code, region in my_model.regions.items():
            region.data['Demands'].loc['AVIATION_LONG_HAUL', 'TRANSPORTATION'] = 0
            region.data['Demands'].loc['SHIPPING', 'TRANSPORTATION'] = 0
            region.data['Misc']['share_short_haul_flights_min'] = 0
            region.data['Misc']['share_short_haul_flights_max'] = 0
    elif c == '100perc_re_no_ned':
        for r_code, region in my_model.regions.items():
            region.data['Demands'].loc['NON_ENERGY', 'INDUSTRY'] = 0
    elif c == '100perc_re_no_plane_shipping_ned':
        for r_code, region in my_model.regions.items():
            region.data['Demands'].loc['AVIATION_LONG_HAUL', 'TRANSPORTATION'] = 0
            region.data['Demands'].loc['SHIPPING', 'TRANSPORTATION'] = 0
            region.data['Misc']['share_short_haul_flights_min'] = 0
            region.data['Misc']['share_short_haul_flights_max'] = 0
            region.data['Demands'].loc['NON_ENERGY', 'INDUSTRY'] = 0

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
    my_model.get_year_results(save_hourly=save_hourly)
    my_model.prints_esom(inputs=True, outputs=True, solve_info=True, save_hourly=save_hourly)

    # delete ampl object to free resources
    my_model.esom.ampl.close()

    i+=1