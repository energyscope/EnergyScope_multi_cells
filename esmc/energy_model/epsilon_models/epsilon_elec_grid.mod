# New parameters
param total_cost_optimum >= 0 ; # Optimal cost computed in previous run
param epsilon >=0 default 0.1; # Deviation allowed from optimal cost

# new variable
var Max_tc_elec_incr >= 0;
	
# Additional epsilon constraints
#-------------------------------
subject to epsilon_space :
	sum{c in REGIONS} TotalCost[c] <= total_cost_optimum * (1 + epsilon);
	
subject to max_elec_line{c1 in REGIONS, c2 in REGIONS}:
	Max_tc_elec_incr >= sum{n in NETWORK_TYPE["ELECTRICITY"]} (Transfer_capacity [c1,c2,"ELECTRICITY",n] - tc_min[c1,c2,"ELECTRICITY",n]);


##########################
### OBJECTIVE FUNCTION ###
##########################

# Minimize the maximum electrical line capacity expansion
minimize obj:  Max_tc_elec_incr;


