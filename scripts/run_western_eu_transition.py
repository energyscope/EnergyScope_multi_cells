import numpy as np

# additional line for VS studio
import sys
sys.path.append('C:\\Users\\pathiran\\Documents\\Energy_system_modelling\\EnergyScope_multi_cells')
from esmc import Esmc

co2_1990 = {'AT-CH-IT': 559200, 'BE-DE-LU-NL': 1420200, 'DK-SE': 111770, 'ES-PT': 280037, 'FR': 410026, 'IE-UK': 678771} # net emissions in 1990 [ktCO2_eq/y]
gwp_limit = dict()
reduction =[0, 0.5, 0.8, 0.9, 1.0]

tds = 14  # np.concatenate((np.arange(2,62,2),np.arange(62,112,4),np.array([120,140,160,180,365])))

for red in reduction:
    print('Reduction', red)

    gwp_limit_overall = None
    re_share_primary = None
    f_perc = False

    # define configuration
    config = {'case_study': 'gwp_red_'+str(red),
              'comment': 'change gwp_limit',
              'regions_names': ['AT-CH-IT', 'BE-DE-LU-NL', 'DK-SE', 'ES-PT', 'FR', 'IE-UK'],
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

    # Initialize and solve the temporal aggregation algorithm:
    # if already run, set algo='read' to read the solution of the clustering
    # else, set algo='kmedoid' to run kmedoid clustering algorithm to choose typical days (TDs)
    my_model.init_ta(algo='read')

    # Print the time related data of the energy system optimization model using the TDs to represent it
    my_model.print_td_data()

    # Set the Energy System Optimization Model (ESOM) as an ampl formulated problem
    my_model.set_esom()

    # update gwp_limit
    gwp_limit_param = my_model.esom.ampl.get_parameter('gwp_limit')

    for r,g in co2_1990.items():
        gwp_limit[r] = g*(1-red)
    gwp_limit_param.setValues(gwp_limit)

    # Solving the ESOM
    my_model.solve_esom()

    # Getting and printing year results
    my_model.get_year_results()
    my_model.prints_esom(inputs=True, outputs=True, solve_info=True)

    # delete ampl object to free resources
    my_model.esom.ampl.close()
