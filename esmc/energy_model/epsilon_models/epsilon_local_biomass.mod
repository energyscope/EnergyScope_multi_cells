# New sets
set BIOMASS within RESOURCES;

# New parameters
param total_cost_optimum >= 0 ; # Optimal cost computed in previous run
param epsilon >=0 default 0.1; # Deviation allowed from optimal cost
	
# Additional epsilon constraints
#-------------------------------
subject to epsilon_space :
	sum{c in REGIONS} TotalCost[c] <= total_cost_optimum * (1 + epsilon);


##########################
### OBJECTIVE FUNCTION ###
##########################

# Minimize the use of local BIOMASS
minimize obj:  sum {c in REGIONS, i in BIOMASS, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (R_t_local [c, i, h, td] * t_op [h, td]);


