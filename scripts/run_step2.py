# additional line for VS studio
import os, sys
sys.path.append('C:\\Users\\pathiran\\Documents\\Energy_system_modelling\\EnergyScope_multi_cells')
from esmc import Esmc
from pathlib import Path
import numpy as np

t=10

print('Nbr_TDs',t)

# define configuration
config = {'case_study': 'GwpLimit=136884_'+str(t)+'TDs',
          'comment': 'no comment',
          'regions_names': ['ES-PT', 'FR', 'IE-UK']}
# initialize EnergyScope Multi-cells framework
my_model = Esmc(config, Nbr_TD=t)

# initialize the different regions and reads their data
my_model.init_regions()

# Initialize and solve the temporal aggregation algorithm:
# if already run, set algo='read' to read the solution of the clustering
# else, set algo='kmedoid' to run kmedoid clustring algorithm to choose typical days (TDs)
my_model.init_ta(algo='kmedoid')

# Print the time related data of the energy system optimization model using the TDs to represent it
my_model.print_td_data()

# Set the Energy Sytem Optimization Model (ESOM) as an ampl formulated problem
my_model.set_esom()

# # Read the outputs from previously solved proble
# my_model.esom.read_outputs(directory=directory)
# # Print as pickle
# my_model.esom.print_outputs(directory=directory, solve_time=True)

# Solving the ESOM
my_model.solve_esom()
# Printing the results
my_model.prints_esom(solve_time=True)

# delete ampl object to free resources
my_model.esom.ampl.close()