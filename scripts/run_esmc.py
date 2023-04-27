import numpy as np
from pathlib import Path

# additional line for VS studio
import sys
sys.path.append('/home/pthiran/EnergyScope_multi_cells/')
from esmc import Esmc
from esmc import writeSankeyFile
from esmc import drawSankey



tds = [14]  # np.concatenate((np.arange(2,62,2),np.arange(62,112,4),np.array([120,140,160,180,365])))

for t in tds:
    print('Nbr_TDs', t)

    # specify ampl_path (set None if ampl is in Path environment variable or the path to ampl if not)
    # ampl_path = Path(r'C:\Users\pathiran\ampl_mswin64')
    ampl_path = None

    # info to switch off unused constraints
    gwp_limit_overall = None
    re_share_primary = None
    f_perc = True

    # define configuration
    config = {'case_study': 'test',
              'comment': 'none',
              'regions_names': ['ES-PT', 'FR', 'IE-UK'],
              'ref_region': 'FR',
              'gwp_limit_overall': gwp_limit_overall,
              're_share_primary': re_share_primary,
              'f_perc': f_perc,
              'year': 2035}
    # initialize EnergyScope Multi-cells framework
    my_model = Esmc(config, nbr_td=t)

    # read the indep data
    my_model.read_data_indep()

    # initialize the different regions and reads their data
    my_model.init_regions()

    # Initialize and solve the temporal aggregation algorithm:
    # if already run, set algo='read' to read the solution of the clustering
    # else, set algo='kmedoid' to run kmedoid clustering algorithm to choose typical days (TDs)
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
    
    # Write the input2sankey... file
    writeSankeyFile(my_model.space_id, my_model.case_study)
    
    # Draw a sankey diagram via HTML from the input2sankey file previously written
    drawSankey(path=my_model.cs_dir / "outputs", outputfile='generated_sankey_Total.html')
    
    # delete ampl object to free resources
    my_model.esom.ampl.close()
