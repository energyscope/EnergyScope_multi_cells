# New sets
set ONSHORE_RE within TECHNOLOGIES;

# New parameters
param total_cost_optimum >= 0; # Optimal cost computed in previous run
param epsilon >= 0 default 0.1; # Deviation allowed from optimal cost
param power_density_won >= 0 default 0.0088; # Power density of wind onshore in GW/km2

# New variables
var New_area_onshore_re >= 0; # land use of onshore renewables
	
# Additional epsilon constraints
#-------------------------------
subject to epsilon_space :
	sum{c in REGIONS} TotalCost[c] <= total_cost_optimum * (1 + epsilon);
	
subject to new_area_onshore_re_comp :
	New_area_onshore_re = sum{c in REGIONS}
	((F[c,"PV_UTILITY"] - f_min[c,"PV_UTILITY"])/power_density_pv 
	+ ((-(F[c,"PT_COLLECTOR"])/layers_in_out ["PT_POWER_BLOCK", "PT_HEAT"]) - f_min[c,"PT_POWER_BLOCK"])/power_density_pv
	+ ((-(F[c,"ST_COLLECTOR"])/layers_in_out ["ST_POWER_BLOCK", "ST_HEAT"]) - f_min[c,"ST_POWER_BLOCK"])/power_density_pv
	+ (F[c,"WIND_ONSHORE"] - f_min[c,"WIND_ONSHORE"])/power_density_won); 


##########################
### OBJECTIVE FUNCTION ###
##########################

# Minimize the installed capacity of ONSHORE_RE
minimize obj:  New_area_onshore_re;


