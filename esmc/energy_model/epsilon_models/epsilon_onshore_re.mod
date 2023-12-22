# New sets
set ONSHORE_RE within TECHNOLOGIES;

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
minimize obj:  sum {c in REGIONS, i in ONSHORE_RE} (F [c,i])


