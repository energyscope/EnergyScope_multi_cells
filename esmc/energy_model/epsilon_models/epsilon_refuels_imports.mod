# New parameters
param total_cost_optimum >= 0 ; # Optimal cost computed in previous run
param epsilon >=0 default 0.01; # Deviation allowed from optimal cost
	
# Additional epsilon constraints
#-------------------------------
subject to epsilon_space :
	sum{c in REGIONS} TotalCost[c] <= total_cost_optimum * (1 + epsilon);


##########################
### OBJECTIVE FUNCTION ###
##########################

# Can choose between TotalGWP and TotalCost
minimize obj:  sum {c in REGIONS, i in RE_FUELS, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (R_t_exterior [c, i, h, td] * t_op [h, td]);


