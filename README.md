# Acknowledging authorship #
In the academic spirit of collaboration, the source code should be appropriately acknowledged in the resulting scientific disseminations.  
You may cite it as follows: 
- [1], for general reference to the EnergyScope project and the EnergyScope modeling framework  	
- [2], for reference to the origins of the EnergyScope project or to the first online version of the calculator energyscope.ch 	
- [3], for reference to the energyscope MILP modeling framework 	
- [4], for reference to the Belgian version
- [5], for reference to the extension to a Multi-Cell version
- [6], for reference to the energyscope Multi-Cell for Western EU energy system (v1)
- [7], for the current code

You are welcome to report any bugs related to the code to the following:    
 paolo.thiran@gmail.com
 
# Content #
This folder contains EnergyScope MultiCell, the multi-regional extension of the whole energy system model EnergyScope.
Other releases are available @ the EnergyScope project repository: https://github.com/energyscope/EnergyScope   
This version of the model corresponds to the one in [6].  
The data used in this version of the model are fully documented in [6].

Description of the repository:
- ./Data/ : COntains the data by country and for the exchanges in specific excel files.
- ./Documentation/ : Contains the documentation of this version of the model and previous versions.
- ./STEP_1_TD_Selection/ : Contains the optimisation model to cluster the days of the year into typical days (TD).
- ./STEP_2_Energy_Model/ : Contains the multi-regional whole energy system model, EnergyScope Multi-Cell (MC)
- ./LICENSE : license file
- ./NOTICE : authors acknolodgment and references
- ./README : this file
- ./UI_step1.ipynb : Jupyter Notebook to run the step 1, that is the selection of the TDs.

# License:  # 
Copyright (C) <2018-2019> <Ecole Polytechnique Fédérale de Lausanne (EPFL), Switzerland and Université catholique de Louvain (UCLouvain), Belgium>

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License


# How to run the model #
The model is coded in AMPL and uses CPLEX solver.

1. Install AMPL (If you don't have an AMPL license, it is possible to run it with GLPK. Refer to the other realeses on the EnergyScope project repository.
)
2. Clone/download the content of this folder
3. Navigate to the folder 'STEP_2_Energy_Model' folder via terminal/cmd prompt and execute:
	a) ampl ESMC_main_solve_writesol.run
	To solve the optimisation problem and write the solution in the solution.sol file.
	
	b) ampl ESMC_main_print_all_readsol.run
	To read the solution.sol file and print outputs into .csv files

4. Check the output files: 
Most of the outputs are printed for each region and for all regions together with the corresponding code at the end of the name of the files (ex: Assets_NO.csv is assets for North).

Descriptions of outputs files and folders: 
- ./Assets_##.csv : Installed capacity of each technology and its specific cost, gwp... 
- ./cost_breakdown_##.csv : Cost of resources and technologies.
- ./Curt.csv : total curtailement by region.
- ./exch_##.csv : yearly exchanges.
- ./exch_losses.csv : exchanges losses by region.
- ./gwp_breakdown_##.csv : GWP of resources and technologies. 
- ./losses_##.csv : Losses in the networks.
- ./resources_##.csv : resources summary over the year.
- ./Share.csv : shares of different technologies or categories of thecnologies in each region.
- ./YearBalance_##.csv : year balance of resources and technologies.
- ./hourly_data_TD/ : Folder containing the hourly data by TD for each layer and for each storage technology. 
- ./hourly_data_year/ : Folder containing the hourly data for the entire year for each layer and for each storage technology. 
- ./sankey/ : Folder containing the SANKEY diagram. 


# Previous versions and Authors: #  
- first release (v1, monthly MILP) of the EnergyScope (ES) model: https://github.com/energyscope/EnergyScope/tree/v1.0 .
- second release (v2, hourly LP) of the EnergyScope (ES) model: https://github.com/energyscope/EnergyScope/tree/v2.0 .
- first MultiCell release on a 3-cell ficitve case: https://github.com/pathiran22/EnergyScope/tree/Hernandez_Thiran_Multi_cell_2020
- EnergyScope MC for Western EU energy system (v1): https://github.com/16NoCo/EnergyScope/tree/Multi_cell_West-Eu_2021

Authors: 
- Stefano Moret, Ecole Polytechnique Fédérale de Lausanne (Switzerland), <moret.stefano@gmail.com> 
- Gauthier Limpens, Université catholique de Louvain (Belgium), <gauthierLimpens@gmail.com> 
- Paolo Thiran, Université catholique de Louvain (Belgium), <paolo.thiran@gmail.com>
- Aurélia Hernandez, Université catholique de Louvain (Belgium).
- Noé Cornet, Université catholique de Louvain (Belgium).
- Pauline Eloy, Université catholique de Louvain (Belgium).

# References:  #  
[1] G. Limpens, S . Moret, H. Jeanmart, F. Maréchal (2019). EnergyScope TD: a novel open-source model for regional energy systems and its application to the case of Switzerland. https://doi.org/10.1016/j.apenergy.2019.113729	

[2] V. Codina Gironès, S. Moret, F. Maréchal, D. Favrat (2015). Strategic energy planning for large-scale energy systems: A modelling framework to aid decision-making. Energy, 90(PA1), 173–186. https://doi.org/10.1016/j.energy.2015.06.008   	

[3] S. Moret, M. Bierlaire, F. Maréchal (2016). Strategic Energy Planning under Uncertainty: a Mixed-Integer Linear Programming Modeling Framework for Large-Scale Energy Systems. https://doi.org/10.1016/B978-0-444-63428-3.50321-0  	

[4] Limpens, G. (2021). Generating energy transition pathways : application to Belgium.

[5] Hernandez, A., Thiran, P., Jeanmart, H., & Limpens, G. (2020). EnergyScope Multi-Cell : A novel open-source model for multi-regional energy systems and application to a 3-cell , low-carbon energy [UCLouvain]. http://hdl.handle.net/2078.1/thesis:25229

[6] Cornet, N., Eloy, P., Jeanmart, H., & Limpens, G. (2021). Energy Exchanges between Countries for a Future Low-Carbon Western Europe By merging cells in EnergyScope MC to handle wider regions.

[7] Thiran, P., Hernandez, A., Limpens, G., Prina, M. G., Jeanmart, H., & Contino, F. (2021). Flexibility options in a multi-regional whole-energy system : the role of energy carriers in the Italian energy transition. Proceedings of ECOS 2021 - The 34th International Conference on Efficiency, Cost, Optimization, Simulation and Environmental Impact of Energy Systems, Mc, 1–12.
