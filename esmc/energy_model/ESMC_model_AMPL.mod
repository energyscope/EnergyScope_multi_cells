# -------------------------------------------------------------------------------------------------------------------------													
#	EnergyScope TD is an open-source energy model suitable for region scale analysis. It is a simplified representation of an urban or national energy system accounting for the energy flows												
#	within its boundaries. Based on a hourly resolution, it optimises the design and operation of the energy system while minimizing the cost of the system.												
#													
#	Copyright (C) <2018-2019> <Ecole Polytechnique Fédérale de Lausanne (EPFL), Switzerland and Université catholique de Louvain (UCLouvain), Belgium>
#													
#	Licensed under the Apache License, Version 2.0 (the "License");												
#	you may not use this file except in compliance with the License.												
#	You may obtain a copy of the License at												
#													
#		http://www.apache.org/licenses/LICENSE-2.0												
#													
#	Unless required by applicable law or agreed to in writing, software												
#	distributed under the License is distributed on an "AS IS" BASIS,												
#	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.												
#	See the License for the specific language governing permissions and												
#	limitations under the License.												
#													
#	Description and complete License: see LICENSE file.												
# -------------------------------------------------------------------------------------------------------------------------		


#########################
###  SETS [Figure 3]  ###
#########################

## MAIN SETS: Sets whose elements are input directly in the data file
set REGIONS; # regions
set RWITHOUTDAM within REGIONS; # regions that don't have hydro dams

set PERIODS := 1 .. 8760; # time periods (hours of the year)
set HOURS := 1 .. 24; # hours of the day
param nbr_tds > 0;  # number of typical days
set TYPICAL_DAYS := 1 .. nbr_tds ordered; # typical days
set T_H_TD within {PERIODS, HOURS, TYPICAL_DAYS}; # set linking periods, hours, days, typical days
set SECTORS; # sectors of the energy system
set END_USES_INPUT; # Types of demand (end-uses). Input to the model
set END_USES_CATEGORIES; # Categories of demand (end-uses): electricity, heat, mobility
set END_USES_TYPES_OF_CATEGORY {END_USES_CATEGORIES}; # Types of demand (end-uses).
set RESOURCES; # Resources: fuels (renewables and fossils) and electricity imports
set RE_FUELS within RESOURCES; # imported biofuels.
set EXPORT within RESOURCES; # exported resources
set NOT_LAYERS within RESOURCES; # resources which are not a layer
set END_USES_TYPES := setof {i in END_USES_CATEGORIES, j in END_USES_TYPES_OF_CATEGORY [i]} j; # secondary set
set TECHNOLOGIES_OF_END_USES_TYPE {END_USES_TYPES}; # set all energy conversion technologies (excluding storage technologies and infrastructure)
set STORAGE_TECH; #  set of storage technologies 
set STORAGE_OF_END_USES_TYPE {END_USES_TYPES} within STORAGE_TECH; # set all storage technologies related to an end-use types (used for thermal solar (TS))
set INFRASTRUCTURE; # Infrastructure: DHN, grid, and intermediate energy conversion technologies (i.e. not directly supplying end-use demand)
#set IMPORT within RESOURCES; # imported resources if positive, exported resources if negative

## SECONDARY SETS: a secondary set is defined by operations on MAIN SETS
set LAYERS := (RESOURCES diff NOT_LAYERS) union END_USES_TYPES; # Layers are used to balance resources/products in the system
set TECHNOLOGIES := (setof {i in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE [i]} j) union STORAGE_TECH union INFRASTRUCTURE; 
set TECHNOLOGIES_OF_END_USES_CATEGORY {i in END_USES_CATEGORIES} within TECHNOLOGIES := setof {j in END_USES_TYPES_OF_CATEGORY[i], k in TECHNOLOGIES_OF_END_USES_TYPE [j]} k;
set RE_RESOURCES within RESOURCES; # List of RE resources (including wind hydro solar), used to compute the RE share
set NOEXCHANGES within RESOURCES; # List of RE resources that can not physically be exchanged: wind, geo, hydro, solar
set V2G within TECHNOLOGIES;   # EVs which can be used for vehicle-to-grid (V2G).
set EVs_BATT   within STORAGE_TECH; # specific battery of EVs
set EVs_BATT_OF_V2G {V2G}; # Makes the link between batteries of EVs and the V2G technology
set STORAGE_DAILY within STORAGE_TECH;# Storages technologies for daily application 
set TS_OF_DEC_TECH {TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} ; # Makes the link between TS and the technology producing the heat

##Additional SETS added just to simplify equations.
set TYPICAL_DAY_OF_PERIOD {t in PERIODS} := setof {h in HOURS, td in TYPICAL_DAYS: (t,h,td) in T_H_TD} td; #TD_OF_PERIOD(T)
set HOUR_OF_PERIOD {t in PERIODS} := setof {h in HOURS, td in TYPICAL_DAYS: (t,h,td) in T_H_TD} h; #H_OF_PERIOD(T)

## Additional SETS: only needed for printing out results (not represented in Figure 3).
set COGEN within TECHNOLOGIES; # cogeneration tech
set BOILERS within TECHNOLOGIES; # boiler tech

set EXCHANGE_FREIGHT_R within RESOURCES; #exchanged resources which are transported by freight
set EXCHANGE_NETWORK_R within RESOURCES; # Resources that are exchanged through a network
set EXCHANGE_R := EXCHANGE_FREIGHT_R union EXCHANGE_NETWORK_R; # set of all exchanged resources
set NETWORK_TYPE {EXCHANGE_NETWORK_R} within TECHNOLOGIES; # different types of network inteconnecting the regions
#set GAS_NETWORK within NETWORK_TYPE; # gas network types that can be retrofitted to hydrogen network

#################################
### PARAMETERS [Tables 1-2]   ###
#################################
### Parameters independant from REGIONS set
## Parameters added to define scenarios and technologies [Table 2]
param i_rate > 0; # discount rate [-]: real discount rate
param gwp_limit_overall >=0; # [ktCO2-eq./year] maximum gwp emissions allowed for global system
param t_op {HOURS, TYPICAL_DAYS} default 1;# [h]: operating time 

# Attributes of TECHNOLOGIES and RESOURCES
param c_op_exterior {RESOURCES} >= 0; 
param layers_in_out {RESOURCES union TECHNOLOGIES diff STORAGE_TECH , LAYERS}; # f: input/output Resources/Technologies to Layers. Reference is one unit ([GW] or [Mpkm/h] or [Mtkm/h]) of (main) output of the resource/technology. input to layer (output of technology) > 0.
param gwp_op_exterior {RESOURCES} >= 0;
param co2_net {RESOURCES} >= 0;

# Attribute of electric vehicles
param batt_per_car {V2G} >= 0; # ev_Batt_size [GWh]: Battery size per EVs car technology
param state_of_charge_ev {V2G,HOURS} >= 0; # Minimum state of charge of the EV during the day.

# Attributes of STORAGE_TECH
param storage_eff_in {STORAGE_TECH , LAYERS} >= 0, <= 1; # eta_sto_in [-]: efficiency of input to storage from layers.  If 0 storage_tech/layer are incompatible
param storage_eff_out {STORAGE_TECH , LAYERS} >= 0, <= 1; # eta_sto_out [-]: efficiency of output from storage to layers. If 0 storage_tech/layer are incompatible
param storage_losses {STORAGE_TECH} >= 0, <= 1; # %_sto_loss [-]: Self losses in storage (required for Li-ion batteries). Value = self discharge in 1 hour.
param storage_availability {STORAGE_TECH} >=0, default 1;# %_sto_avail [-]: Storage technology availability to charge/discharge. Used for EVs 

# Attributes of solar technologies
param power_density_pv >=0 default 0;# Maximum power irradiance for PV.
param power_density_solar_thermal >=0 default 0;# Maximum power irradiance for solar thermal.

# Networks attributes
param loss_network {END_USES_TYPES} >= 0 default 0; # %_net_loss: Losses coefficient [0; 1] in the networks (grid and DHN)
param c_grid_extra >=0, default 359; # Cost to reinforce the grid due to IRE penetration [M€2015/GW_intermittentRE].

# Attributes of exchanges
param exchange_losses {RESOURCES} >=0 default 0; #losses on network for exchanges [%]
param  lhv{EXCHANGE_FREIGHT_R}>=0; #lhv of fuels transported by freight

##Additional parameter (not presented in the paper)
param total_time := sum {t in PERIODS, h in HOUR_OF_PERIOD [t], td in TYPICAL_DAY_OF_PERIOD [t]} (t_op [h, td]); # [h]. added just to simplify equations

### Parameters depending on REGIONS set
## Parameters added to include time series in the model [Table 1]
param electricity_time_series {REGIONS, HOURS, TYPICAL_DAYS} >= 0, <= 1; # %_elec [-]: factor for sharing lighting across typical days (adding up to 1)
param heating_time_series {REGIONS, HOURS, TYPICAL_DAYS} >= 0, <= 1; # %_sh [-]: factor for sharing space heating across typical days (adding up to 1)
param cooling_time_series {REGIONS, HOURS, TYPICAL_DAYS} >= 0, <= 1;
param mob_pass_time_series {REGIONS, HOURS, TYPICAL_DAYS} >= 0, <= 1; # %_pass [-]: factor for sharing passenger transportation across Typical days (adding up to 1) based on https://www.fhwa.dot.gov/policy/2013cpr/chap1.cfm
param mob_freight_time_series {REGIONS, HOURS, TYPICAL_DAYS} >= 0, <= 1; # %_fr [-]: factor for sharing freight transportation across Typical days (adding up to 1)
param c_p_t {TECHNOLOGIES, REGIONS, HOURS, TYPICAL_DAYS} >= 0 default 1; #Hourly capacity factor [-]. If = 1 (default value) <=> no impact.

## Parameters added to define scenarios and technologies [Table 2]
param end_uses_demand_year {REGIONS, END_USES_INPUT, SECTORS} >= 0 default 0; # end_uses_year [GWh]: table end-uses demand vs sectors (input to the model). Yearly values. [Mpkm] or [Mtkm] for passenger or freight mobility.
param end_uses_input {c in REGIONS, i in END_USES_INPUT} := sum {s in SECTORS} (end_uses_demand_year [c,i,s]); # end_uses_input (Figure 1.4) [GWh]: total demand for each type of end-uses across sectors (yearly energy) as input from the demand-side model. [Mpkm] or [Mtkm] for passenger or freight mobility.
param re_share_primary {REGIONS} >= 0; # re_share [-]: minimum share of primary energy coming from RE
param gwp_limit {REGIONS} >= 0;    # [ktCO2-eq./year] maximum gwp emissions allowed.

# Share public vs private mobility
param share_mobility_public_min{REGIONS} >= 0, <= 1; # %_public,min [-]: min limit for penetration of public mobility over total mobility 
param share_mobility_public_max{REGIONS} >= 0, <= 1; # %_public,max [-]: max limit for penetration of public mobility over total mobility 

# Share train vs truck vs boat in freight transportation
param share_freight_train_min{REGIONS} >= 0, <= 1; # %_rail,min [-]: min limit for penetration of train in freight transportation
param share_freight_train_max{REGIONS} >= 0, <= 1; # %_rail,min [-]: max limit for penetration of train in freight transportation
param share_freight_boat_min{REGIONS}  >= 0, <= 1; # %_boat,min [-]: min limit for penetration of boat in freight transportation
param share_freight_boat_max{REGIONS}  >= 0, <= 1; # %_boat,min [-]: max limit for penetration of boat in freight transportation
param share_freight_road_min{REGIONS}  >= 0, <= 1; # %_road,min [-]: min limit for penetration of truck in freight transportation
param share_freight_road_max{REGIONS}  >= 0, <= 3; # %_road,min [-]: max limit for penetration of truck in freight transportation
param share_ned {REGIONS, END_USES_TYPES_OF_CATEGORY["NON_ENERGY"]} >= 0, <= 1; # %_ned [-] share of non-energy demand per type of feedstocks.


# Share dhn vs decentralized for low-T heating
param share_heat_dhn_min{REGIONS} >= 0, <= 1; # %_dhn,min [-]: min limit for penetration of dhn in low-T heating
param share_heat_dhn_max{REGIONS} >= 0, <= 1; # %_dhn,max [-]: max limit for penetration of dhn in low-T heating


# Attributes of TECHNOLOGIES and RESOURCES
param f_max {REGIONS, TECHNOLOGIES} >= 0; # Maximum feasible installed capacity [GW], refers to main output. storage level [GWh] for STORAGE_TECH
param f_min {REGIONS, TECHNOLOGIES} >= 0; # Minimum feasible installed capacity [GW], refers to main output. storage level [GWh] for STORAGE_TECH
param fmax_perc {REGIONS, TECHNOLOGIES} >= 0, <= 1 default 1; # value in [0,1]: this is to fix that a technology can at max produce a certain % of the total output of its sector over the entire year
param fmin_perc {REGIONS, TECHNOLOGIES} >= 0, <= 1 default 0; # value in [0,1]: this is to fix that a technology can at min produce a certain % of the total output of its sector over the entire year
param avail_local {REGIONS, RESOURCES} >= 0; # Yearly availability of resources [GWh/y]
param avail_exterior {REGIONS, RESOURCES} >= 0;
param c_op_local {REGIONS, RESOURCES} >= 0; # cost of resources in the different periods [MCHF/GWh]
param vehicule_capacity {TECHNOLOGIES} >=0, default 0; #  veh_capa [capacity/vehicles] Average capacity (pass-km/h or t-km/h) per vehicle. It makes the link between F and the number of vehicles
param peak_sh_factor{REGIONS} >= 0;   # %_Peak_sh [-]: ratio between highest yearly demand and highest TDs demand
param peak_sc_factor{REGIONS} >= 0;   # %_Peak_sc [-]: ratio between highest yearly demand and highest TDs deman
param c_inv {REGIONS, TECHNOLOGIES} >= 0; # Specific investment cost [MCHF/GW].[MCHF/GWh] for STORAGE_TECH
param c_maint {REGIONS, TECHNOLOGIES} >= 0; # O&M cost [MCHF/GW/year]: O&M cost does not include resource (fuel) cost. [MCHF/GWh/year] for STORAGE_TECH
param lifetime {REGIONS, TECHNOLOGIES} >= 0; # n: lifetime [years]
param tau {c in REGIONS, i in TECHNOLOGIES} := i_rate * (1 + i_rate)^lifetime [c,i] / (((1 + i_rate)^lifetime [c,i]) - 1); # Annualisation factor ([-]) for each different technology [Eq. 2]
param gwp_constr {REGIONS, TECHNOLOGIES} >= 0; # GWP emissions associated to the construction of technologies [ktCO2-eq./GW]. Refers to [GW] of main output
param gwp_op_local {REGIONS, RESOURCES} >= 0; # GWP emissions associated to the use of resources [ktCO2-eq./GWh]. Includes extraction/production/transportation and combustion
param c_p {REGIONS, TECHNOLOGIES} >= 0, <= 1 default 1; # yearly capacity factor of each technology [-], defined on annual basis. Different than 1 if sum {t in PERIODS} F_t (t) <= c_p * F
param tc_min {REGIONS, REGIONS, i in EXCHANGE_NETWORK_R, NETWORK_TYPE[i]} >=0, default 0; #minimal transfer capacity of each resource between regions [GW]
param tc_max {REGIONS, REGIONS, i in EXCHANGE_NETWORK_R, NETWORK_TYPE[i]} >=0, default 0; #maximal transfer capacity of each resource between regions [GW]
param retro_gas_to_h2 >=0; # conversion ratio of gas pipelines to hydrogen pipelines in term of GW transported

# Attributes of STORAGE_TECH
param storage_charge_time    {REGIONS, STORAGE_TECH} >= 0; # t_sto_in [h]: Time to charge storage (Energy to Power ratio). If value =  5 <=>  5h for a full charge.
param storage_discharge_time {REGIONS, STORAGE_TECH} >= 0; # t_sto_out [h]: Time to discharge storage (Energy to Power ratio). If value =  5 <=>  5h for a full discharge.

# Other attributes
param import_capacity{REGIONS} >= 0; # Maximum electricity import capacity [GW]
param solar_area_rooftop{REGIONS} >= 0; # Maximum land available for solar deployement on rooftops [km2]
param solar_area_ground{REGIONS} >= 0; # Maximum land available for solar deployement on the ground [km2]
param solar_area_ground_high_irr{REGIONS} >= 0; # Maximum land available for solar deployement on the ground in locations with high irradiance [km2]
param sm_max >= 0 default 4; # Maximum solar multiple for csp plants


# Parameters for additional freight due to exchanges calcultations
param  dist{REGIONS, REGIONS} >=0 default 1E+09; #travelled distance by fuels exchanged in each region


#################################
###   VARIABLES [Tables 3-4]  ###
#################################


##Independent variables [Table 3] :
var Share_mobility_public{c in REGIONS} >= share_mobility_public_min[c], <= share_mobility_public_max[c]; # %_Public: Ratio [0; 1] public mobility over total passenger mobility
var Share_freight_train{c in REGIONS}, >= share_freight_train_min[c], <= share_freight_train_max[c]; # %_Rail: Ratio [0; 1] rail transport over total freight transport
var Share_freight_road{c in REGIONS}, >= share_freight_road_min[c], <= share_freight_road_max[c]; # %_Road: Ratio [0; 1] Road transport over total freight transport
var Share_freight_boat{c in REGIONS}, >= share_freight_boat_min[c], <= share_freight_boat_max[c]; # %_Boat: Ratio [0; 1] boat transport over total freight transport
var Share_heat_dhn{c in REGIONS}, >= share_heat_dhn_min[c], <= share_heat_dhn_max[c]; # %_DHN: Ratio [0; 1] centralized over total low-temperature heat
var F {REGIONS, TECHNOLOGIES} >= 0; # F: Installed capacity ([GW]) with respect to main output (see layers_in_out). [GWh] for STORAGE_TECH.
var F_t {REGIONS, TECHNOLOGIES, HOURS, TYPICAL_DAYS} >= 0; # F_t: Operation in each period [GW] or, for STORAGE_TECH, storage level [GWh]. multiplication factor with respect to the values in layers_in_out table. Takes into account c_p
var Curt {REGIONS, TECHNOLOGIES, HOURS, TYPICAL_DAYS} >=0; # Curtailement [GW]
var R_t_local {REGIONS, RESOURCES , HOURS, TYPICAL_DAYS} >= 0; # Use of resource from local feedstock
var R_t_exterior {REGIONS, RESOURCES , HOURS, TYPICAL_DAYS} >= 0; # Import of resource from the exterior of the overall system
var R_t_import{REGIONS, RESOURCES, HOURS, TYPICAL_DAYS} >= 0; # Import of resources from neighbouring regions modelled in the overall system
var R_t_export{REGIONS, RESOURCES, HOURS, TYPICAL_DAYS} >= 0; # Export of resources to neighbouring region modelled in the overall system

var Storage_in {REGIONS, i in STORAGE_TECH, LAYERS, HOURS, TYPICAL_DAYS} >= 0; # Sto_in [GW]: Power input to the storage in a certain period
var Storage_out {REGIONS, i in STORAGE_TECH, LAYERS, HOURS, TYPICAL_DAYS} >= 0; # Sto_out [GW]: Power output from the storage in a certain period
var Power_nuclear{REGIONS}  >=0; # [GW] P_Nuc: Constant load of nuclear
var Shares_mobility_passenger {REGIONS, TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_PASSENGER"]} >=0; # %_MobPass [-]: Constant share of passenger mobility
var Shares_mobility_freight {REGIONS, TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_FREIGHT"]} >=0; # %_Freight [-]: Constant share of passenger mobility
var Shares_lowT_dec {REGIONS, TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}}>=0 ; # %_HeatDec [-]: Constant share of heat Low T decentralised + its specific thermal solar
var F_solar         {REGIONS, TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} >=0; # F_sol [GW]: Solar thermal installed capacity per heat decentralised technologies
var F_t_solar       {REGIONS, TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, h in HOURS, td in TYPICAL_DAYS} >= 0; # F_t_sol [GW]: Solar thermal operating per heat decentralised technologies

##Dependent variables [Table 4] :
var End_uses {REGIONS, LAYERS, HOURS, TYPICAL_DAYS} >= 0; #EndUses [GW]: total demand for each type of end-uses (hourly power). Defined for all layers (0 if not demand). [Mpkm] or [Mtkm] for passenger or freight mobility.
var TotalCost{REGIONS} >= 0; # C_tot [ktCO2-eq./year]: Total GWP emissions in the system.
var C_inv {REGIONS, TECHNOLOGIES} >= 0; #C_inv [MCHF]: Total investment cost of each technology
var C_maint {REGIONS, TECHNOLOGIES} >= 0; #C_maint [MCHF/year]: Total O&M cost of each technology (excluding resource cost)
var C_op {REGIONS, RESOURCES} >= 0; #C_op [MCHF/year]: Total O&M cost of each resource
var TotalGWP{REGIONS} >= 0; # GWP_tot [ktCO2-eq./year]: Total global warming potential (GWP) emissions in the system
var GWP_constr {REGIONS, TECHNOLOGIES} >= 0; # GWP_constr [ktCO2-eq.]: Total emissions of the technologies
var GWP_op {REGIONS, RESOURCES} >= 0; #  GWP_op [ktCO2-eq.]: Total yearly emissions of the resources [ktCO2-eq./y]
var CO2_net {REGIONS, RESOURCES} >=0;
var Network_losses {REGIONS, END_USES_TYPES, HOURS, TYPICAL_DAYS} >= 0; # Net_loss [GW]: Losses in the networks (normally electricity grid and DHN)
var Storage_level {REGIONS, STORAGE_TECH, PERIODS} >= 0; # Sto_level [GWh]: Energy stored at each period
var Exch_imp{REGIONS,REGIONS, EXCHANGE_R, HOURS, TYPICAL_DAYS} >= 0; # (Import of c1 from c2) Positive part (import) of the exchanges of ressource between regions during a certain period t [GW]
var Exch_exp{REGIONS,REGIONS, EXCHANGE_R, HOURS, TYPICAL_DAYS} >= 0; # (Export of c1 to c2) Negative part (export) of the exchanges of ressource between regions during a certain period t [GW]
var Exch_freight_border{REGIONS, REGIONS}>=0; # yearly additional freight due to exchanges accross each border
var Exch_freight{REGIONS}>=0; # yearly additional freight due to exchanges for each region
var Transfer_capacity{c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_NETWORK_R, n in NETWORK_TYPE[i]} >= 0; # Optimal transer capacity from c2 to c1
var TC_gas_build{c1 in REGIONS, c2 in REGIONS, g in NETWORK_TYPE["GAS"]} >= 0; # gas pipeline build (include already existing ones and new ones)
var TC_gas_retrofit{c1 in REGIONS, c2 in REGIONS, g in NETWORK_TYPE["GAS"]} >= 0; # gas pipeline retrofitted to hydrogen pipelines
#var Curt{REGIONS} >=0;

#########################################
###      CONSTRAINTS Eqs [1-42]       ###
#########################################

## End-uses demand calculation constraints 
#-----------------------------------------

# [Figure 4] From annual energy demand to hourly power demand. End_Uses is non-zero only for demand layers.
subject to end_uses_t {c in REGIONS, l in LAYERS, h in HOURS, td in TYPICAL_DAYS}:
	End_uses [c, l, h, td] = (if l == "ELECTRICITY" 
		then
			(end_uses_input[c,l] * electricity_time_series [c, h, td] / t_op [h, td] ) + Network_losses [c,l,h,td]
		else (if l == "HEAT_LOW_T_DHN" then
			(end_uses_input[c,"HEAT_LOW_T_HW"] / total_time + end_uses_input[c,"HEAT_LOW_T_SH"] * heating_time_series [c, h, td] / t_op [h, td] ) * Share_heat_dhn[c] + Network_losses [c,l,h,td]
		else (if l == "HEAT_LOW_T_DECEN" then
			(end_uses_input[c,"HEAT_LOW_T_HW"] / total_time + end_uses_input[c,"HEAT_LOW_T_SH"] * heating_time_series [c, h, td] / t_op [h, td] ) * (1 - Share_heat_dhn[c])
		else (if l == "MOB_PUBLIC" then
			(end_uses_input[c,"MOBILITY_PASSENGER"] * mob_pass_time_series [c, h, td] / t_op [h, td]  ) * Share_mobility_public[c]
		else (if l == "MOB_PRIVATE" then
			(end_uses_input[c,"MOBILITY_PASSENGER"] * mob_pass_time_series [c, h, td] / t_op [h, td]  ) * (1 - Share_mobility_public[c])
		else (if l == "MOB_FREIGHT_RAIL" then
			(end_uses_input[c,"MOBILITY_FREIGHT"]   * mob_freight_time_series [c, h, td] / t_op [h, td] ) *  Share_freight_train[c]
		else (if l == "MOB_FREIGHT_ROAD" then
			(end_uses_input[c,"MOBILITY_FREIGHT"]   * mob_freight_time_series [c, h, td] / t_op [h, td] ) *  Share_freight_road[c]
		else (if l == "MOB_FREIGHT_BOAT" then
			(end_uses_input[c,"MOBILITY_FREIGHT"]   * mob_freight_time_series [c, h, td] / t_op [h, td] ) *  Share_freight_boat[c]
		else (if l == "HEAT_HIGH_T" then
			end_uses_input[c,l] / total_time
		else (if l == "SPACE_COOLING" then
			end_uses_input[c,l] * cooling_time_series [c, h, td] / t_op [h, td]
		else (if l == "PROCESS_COOLING" then
			end_uses_input[c,l] / total_time
		else (if l == "HVC" then
			end_uses_input[c,"NON_ENERGY"] * share_ned [c, "HVC"] / total_time
		else (if l == "AMMONIA" then
			end_uses_input[c, "NON_ENERGY"] * share_ned [c, "AMMONIA"] / total_time
		else (if l == "METHANOL" then
			end_uses_input[c, "NON_ENERGY"] * share_ned [c, "METHANOL"] / total_time
		else 
			0 )))))))))))))); # For all layers which don't have an end-use demand


## Cost
#------

# [Eq. 1]	
subject to totalcost_cal{c in REGIONS}:
	TotalCost[c] = sum {j in TECHNOLOGIES} (tau [c,j]  * C_inv [c,j] + C_maint [c,j]) + sum {i in RESOURCES} C_op [c,i];
	
# [Eq. 3] Investment cost of each technology
subject to investment_cost_calc {c in REGIONS, j in TECHNOLOGIES}: 
	C_inv [c,j] = c_inv [c,j] * F [c,j];
		
# [Eq. 4] O&M cost of each technology
subject to main_cost_calc {c in REGIONS, j in TECHNOLOGIES}: 
	C_maint [c,j] = c_maint [c,j] * F [c,j];		

# [Eq. 5] Total cost of each resource
subject to op_cost_calc {c in REGIONS, i in RESOURCES}:
	C_op [c,i] = sum {t in PERIODS, h in HOUR_OF_PERIOD [t], td in TYPICAL_DAY_OF_PERIOD [t]} (c_op_local [c, i] * R_t_local [c, i, h, td] * t_op [h, td] + c_op_exterior [i] * R_t_exterior [c, i, h, td] * t_op [h, td] ) ;

## Emissions
#-----------

# [Eq. 6]
subject to totalGWP_calc {c in REGIONS}:
	TotalGWP[c] = sum {j in TECHNOLOGIES} (GWP_constr [c,j] / lifetime [c,j]) + sum {i in RESOURCES} GWP_op [c,i];
	
# [Eq. 7]
subject to gwp_constr_calc {c in REGIONS, j in TECHNOLOGIES}:
	GWP_constr [c,j] = gwp_constr [c,j] * F [c,j];

# [Eq. 8]
subject to gwp_op_calc {c in REGIONS, i in RESOURCES}:
	GWP_op [c,i] = sum {t in PERIODS, h in HOUR_OF_PERIOD [t], td in TYPICAL_DAY_OF_PERIOD [t]} (R_t_local [c, i, h, td] * gwp_op_local [c, i] * t_op [h, td] + R_t_exterior [c, i, h, td] * gwp_op_exterior [i] * t_op [h, td] );	

# Direct emissions of the fuels, to match GWP historical data
subject to co2_net_calc {c in REGIONS, i in RESOURCES}:
	CO2_net [c,i] = sum {t in PERIODS, h in HOUR_OF_PERIOD [t], td in TYPICAL_DAY_OF_PERIOD [t]} (R_t_local [c, i, h, td] * co2_net [i] * t_op [h, td] + R_t_exterior [c, i, h, td] * co2_net [i] * t_op [h, td] );	

	
## Multiplication factor
#-----------------------
	
# [Eq. 9] min & max limit to the size of each technology
subject to size_limit {c in REGIONS, j in TECHNOLOGIES}:
	f_min [c,j] <= F [c,j] <= f_max [c,j];
	
# [Eq. 10] relation between power and capacity via period capacity factor. This forces max hourly output (e.g. renewables)
subject to capacity_factor_t {c in REGIONS, j in TECHNOLOGIES, h in HOURS, td in TYPICAL_DAYS}:
	F_t [c,j, h, td] + Curt[c, j, h, td] = F [c,j] * c_p_t [j, c, h, td];
	
# [Eq. 11] relation between mult_t and mult via yearly capacity factor. This one forces total annual output
subject to capacity_factor {c in REGIONS, j in TECHNOLOGIES}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD [t], td in TYPICAL_DAY_OF_PERIOD [t]} (F_t [c, j, h, td] * t_op [h, td]) <= F [c, j] * c_p [c, j] * total_time;	
		
## Resources
#-----------

# [Eq. 12] Resources availability equation
subject to resource_availability_local {c in REGIONS, i in RESOURCES}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (R_t_local [c, i, h, td] * t_op [h, td]) <= avail_local [c, i];
	
subject to resource_availability_exterior {c in REGIONS, i in RESOURCES}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (R_t_exterior [c, i, h, td] * t_op [h, td]) <= avail_exterior [c, i];

## Layers
#--------

# [Eq. 13] Layer balance equation with storage. Layers: input > 0, output < 0. Demand > 0. Storage: in > 0, out > 0;
# output from technologies/resources/storage - input to technologies/storage = demand. Demand has default value of 0 for layers which are not end_uses
subject to layer_balance {c in REGIONS, l in LAYERS, h in HOURS, td in TYPICAL_DAYS}:
		sum {i in RESOURCES} (layers_in_out[i, l] * (R_t_local [c, i, h, td] + R_t_exterior [c, i, h, td] - R_t_export[c, i, h, td] + R_t_import[c, i, h, td])) 
		+ sum {k in TECHNOLOGIES diff STORAGE_TECH} (layers_in_out[k, l] * F_t [c, k, h, td]) 
		+ sum {j in STORAGE_TECH} ( Storage_out [c, j, l, h, td] - Storage_in [c, j, l, h, td] )
		- End_uses [c, l, h, td]
		= 0;
		
	
## Storage	
#---------
	
# [Eq. 14] The level of the storage represents the amount of energy stored at a certain time.
subject to storage_level {c in REGIONS, j in STORAGE_TECH, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}:
	Storage_level [c, j, t] = (if t == 1 then
	 			Storage_level [c, j, card(PERIODS)] * (1.0 -  storage_losses[j])
				+ t_op [h, td] * (   (sum {l in LAYERS: storage_eff_in [j,l] > 0}  (Storage_in [c, j, l, h, td]  * storage_eff_in  [j, l])) 
				                   - (sum {l in LAYERS: storage_eff_out [j,l] > 0} (Storage_out [c, j, l, h, td] / storage_eff_out [j, l])))
	else
	 			Storage_level [c, j, t-1] * (1.0 -  storage_losses[j])
				+ t_op [h, td] * (   (sum {l in LAYERS: storage_eff_in [j,l] > 0}  (Storage_in [c, j, l, h, td]  * storage_eff_in  [j, l])) 
				                   - (sum {l in LAYERS: storage_eff_out [j,l] > 0} (Storage_out [c, j, l, h, td] / storage_eff_out [j, l])))
				);

# [Eq. 15] Bounding daily storage
subject to impose_daily_storage {c in REGIONS, j in STORAGE_DAILY, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}:
	Storage_level [c, j, t] = F_t [c, j, h, td];
	
# [Eq. 16] Bounding seasonal storage
subject to limit_energy_stored_to_maximum {c in REGIONS, j in STORAGE_TECH diff STORAGE_DAILY , t in PERIODS}:
	Storage_level [c, j, t] <= F [c, j];# Never exceed the size of the storage unit
	
# [Eqs. 17-18] Each storage technology can have input/output only to certain layers. If incompatible then the variable is set to 0
subject to storage_layer_in {c in REGIONS, j in STORAGE_TECH, l in LAYERS, h in HOURS, td in TYPICAL_DAYS}:
	Storage_in [c, j, l, h, td] * (ceil (storage_eff_in [j, l]) - 1) = 0;
subject to storage_layer_out {c in REGIONS, j in STORAGE_TECH, l in LAYERS, h in HOURS, td in TYPICAL_DAYS}:
	Storage_out [c, j, l, h, td] * (ceil (storage_eff_out [j, l]) - 1) = 0;

# [Eq. 19] limit the Energy to power ratio. 
subject to limit_energy_to_power_ratio {c in REGIONS, j in STORAGE_TECH diff {"BEV_BATT","PHEV_BATT"}, l in LAYERS, h in HOURS, td in TYPICAL_DAYS}:
	Storage_in [c, j, l, h, td] * storage_charge_time[c,j] + Storage_out [c, j, l, h, td] * storage_discharge_time[c,j] <=  F [c, j] * storage_availability[j];

# [Eq. 2.19-bis] limit the Energy to power ratio. 
subject to limit_energy_to_power_ratio_bis {c in REGIONS, i in V2G, j in EVs_BATT_OF_V2G[i], l in LAYERS, h in HOURS, td in TYPICAL_DAYS}:
    Storage_in [c, j, l, h, td] * storage_charge_time[c,j] + (Storage_out [c, j, l, h, td] + layers_in_out[i,"ELECTRICITY"]* F_t [c, i, h, td]) * storage_discharge_time[c,j]  <= ( F [c, j] - F_t [c,i,h,td] / vehicule_capacity [i] * batt_per_car[i] ) * storage_availability[j];



## Infrastructure
#----------------

# [Eq. 20] Calculation of losses for each end-use demand type (normally for electricity and DHN)
subject to network_losses {c in REGIONS, eut in END_USES_TYPES, h in HOURS, td in TYPICAL_DAYS}:
	Network_losses [c,eut,h,td] = (sum {j in TECHNOLOGIES diff STORAGE_TECH: layers_in_out [j, eut] > 0} ((layers_in_out[j, eut]) * F_t [c, j, h, td])) * loss_network [eut] + (sum {i in RESOURCES: layers_in_out [i, eut] > 0} ((layers_in_out[i, eut]) * R_t_import [c, i, h, td])) * loss_network [eut];

# [Eq. 21] 9.4 M€ is the extra investment needed if there is a big deployment of stochastic renewables
subject to extra_grid{c in REGIONS}:
    F [c,"GRID"] = 1 + (c_grid_extra / c_inv[c,"GRID"]) *( (F [c,"WIND_ONSHORE"]     + F [c,"WIND_OFFSHORE"]     + F [c,"PV_ROOFTOP"]   + F [c,"PV_UTILITY"]   )
					                                     - (f_min [c,"WIND_ONSHORE"] + f_min [c,"WIND_OFFSHORE"]  + f_min [c,"PV_ROOFTOP"] + f_min [c,"PV_UTILITY"]) );


# [Eq. 22] DHN: assigning a cost to the network
subject to extra_dhn{c in REGIONS}:
	F [c,"DHN"] = sum {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DHN"]} (F [c,j]);

	
## Additional constraints
#------------------------
	
# [Eq. 24] Fix nuclear production constant : 
subject to constantNuc {c in REGIONS, h in HOURS, td in TYPICAL_DAYS}:
	F_t [c,"NUCLEAR", h, td] = Power_nuclear[c];

# [Eq. 25] Operating strategy in mobility passenger (to make model more realistic)
# Each passenger mobility technology (j) has to supply a constant share  (Shares_mobility_passenger[j]) of the passenger mobility demand
subject to operating_strategy_mob_passenger{c in REGIONS, j in TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_PASSENGER"], h in HOURS, td in TYPICAL_DAYS}:
	F_t [c, j, h, td]   = Shares_mobility_passenger [c,j] * (end_uses_input[c,"MOBILITY_PASSENGER"] * mob_pass_time_series [c, h, td] / t_op [h, td] );

# [Eq. 25] Operating strategy in mobility freight (to make model more realistic)
# Each freight mobility technology (j) has to supply a constant share  (Shares_mobility_freight[j]) of the passenger mobility demand
subject to operating_strategy_mobility_freight{c in REGIONS, j in TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_FREIGHT"], h in HOURS, td in TYPICAL_DAYS}:
	F_t [c, j, h, td]   = Shares_mobility_freight [c,j] * (end_uses_input[c,"MOBILITY_FREIGHT"] * mob_freight_time_series [c, h, td] / t_op [h, td] );

# [Eq. 26] To impose a constant share in the mobility
subject to Freight_shares {c in REGIONS} :
	Share_freight_train[c] + Share_freight_road[c] + Share_freight_boat[c] = sum{j in TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_FREIGHT"]} (Shares_mobility_freight [c,j]); # =1 should work... But don't know why it doesn't

	
## Thermal solar & thermal storage:

# [Eq. 26] relation between decentralised thermal solar power and capacity via period capacity factor.
subject to thermal_solar_capacity_factor {c in REGIONS, j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, h in HOURS, td in TYPICAL_DAYS}:
	F_t_solar [c, j, h, td] <= F_solar[c,j] * c_p_t["DEC_SOLAR", c, h, td];
	
# [Eq. 27] Overall thermal solar is the sum of specific thermal solar 	
subject to thermal_solar_total_capacity {c in REGIONS} :
	F [c,"DEC_SOLAR"] = sum {j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}} F_solar[c,j];

# [Eq. 28]: Decentralised thermal technology must supply a constant share of heat demand.
subject to decentralised_heating_balance  {c in REGIONS, j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, i in TS_OF_DEC_TECH[j], h in HOURS, td in TYPICAL_DAYS}:
	F_t [c, j, h, td] + F_t_solar [c, j, h, td] + sum {l in LAYERS } ( Storage_out [c, i, l, h, td] - Storage_in [c, i, l, h, td])  
		= Shares_lowT_dec[c,j] * (end_uses_input[c,"HEAT_LOW_T_HW"] / total_time + end_uses_input[c,"HEAT_LOW_T_SH"] * heating_time_series [c, h, td] / t_op [h, td]);

## EV storage :

# [Eq. 32] Compute the equivalent size of V2G batteries based on the share of V2G, the amount of cars and the battery capacity per EVs technology
subject to EV_storage_size {c in REGIONS, j in V2G, i in EVs_BATT_OF_V2G[j]}:
	F [c,i] = F[c,j] / vehicule_capacity [j] * batt_per_car[j];# Battery size proportional to the amount of cars
	
# [Eq. 33]  Impose EVs to be supplied by their battery.
subject to EV_storage_for_V2G_demand {c in REGIONS, j in V2G, i in EVs_BATT_OF_V2G[j], h in HOURS, td in TYPICAL_DAYS}:
	Storage_out [c,i,"ELECTRICITY",h,td] >=  - layers_in_out[j,"ELECTRICITY"]* F_t [c, j, h, td];
	
# [Eq. 33 bis] Impose a minimum state of charge of EV batteries at some hours of the day
subject to EV_storage_min_SOC {c in REGIONS, j in V2G, i in EVs_BATT_OF_V2G[j], t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}:
	Storage_level [c, i, t] >= F [c,i] * state_of_charge_ev[j,h];
		
## Peak demand :

# [Eq. 34] Peak in decentralized heating
subject to peak_lowT_dec {c in REGIONS, j in TECHNOLOGIES_OF_END_USES_TYPE["HEAT_LOW_T_DECEN"] diff {"DEC_SOLAR"}, h in HOURS, td in TYPICAL_DAYS}:
	F [c,j] >= peak_sh_factor[c] * F_t [c, j, h, td] ;

# [Eq. 35] Calculation of max heat demand in DHN (1st constrain required to linearised the max function)
var Max_Heat_Demand{REGIONS} >= 0;
subject to max_dhn_heat_demand {c in REGIONS, h in HOURS, td in TYPICAL_DAYS}:
	Max_Heat_Demand[c] >= End_uses [c,"HEAT_LOW_T_DHN", h, td];
# Peak in DHN
subject to peak_lowT_dhn {c in REGIONS}:
	sum {j in TECHNOLOGIES_OF_END_USES_TYPE ["HEAT_LOW_T_DHN"], i in STORAGE_OF_END_USES_TYPE["HEAT_LOW_T_DHN"]} (F [c,j] + F[c,i]/storage_discharge_time[c,i]) >= peak_sh_factor[c] * Max_Heat_Demand[c];
	
# [Eq. 34] Peak in space cooling
subject to peak_space_cooling {c in REGIONS, j in TECHNOLOGIES_OF_END_USES_TYPE["SPACE_COOLING"], h in HOURS, td in TYPICAL_DAYS}:
	F [c,j] >= peak_sc_factor[c] * F_t [c, j, h, td] ;

## Adaptation for the case study: Constraints needed for the application to Switzerland (not needed in standard LP formulation)
#-----------------------------------------------------------------------------------------------------------------------

# [Eq. 36]  constraint to reduce the GWP subject to Minimum_gwp_reduction :
subject to Minimum_GWP_reduction {c in REGIONS}:
	sum{r in RESOURCES} (CO2_net [c,r]) <= gwp_limit[c];
	
# [Eq. 36]  constraint to reduce the GWP subject to Minimum_gwp_reduction :
# Macro-cells: modified to account for direct emissions only
subject to Minimum_GWP_reduction_global :
	sum{c in REGIONS, r in RESOURCES} (CO2_net [c,r]) <= gwp_limit_overall;
	#sum{c in REGIONS} TotalGWP[c] <= gwp_limit_overall;

# [Eq. 37] Minimum share of RE in primary energy supply
subject to Minimum_RE_share {c in REGIONS} :
	sum {j in RE_RESOURCES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (R_t_local [c, j, h, td]+ R_t_exterior [c, j, h, td] + R_t_import [c, j, h, td]) * t_op [h, td] 
	>=	re_share_primary[c] *
	sum {j in RESOURCES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (R_t_local [c, j, h, td]+ R_t_exterior [c, j, h, td] + R_t_import [c, j, h, td]) * t_op [h, td]	;


## Those 2 equations or the 2 after must be activated but not both	
# [Eq. 38] Definition of min/max output of each technology as % of total output in a given layer.
subject to f_max_perc_train_pub {c in REGIONS}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c,"TRAIN_PUB",h,td] * t_op[h,td]) 
	<= fmax_perc [c,"TRAIN_PUB"] * sum {j in TECHNOLOGIES_OF_END_USES_TYPE["MOB_PUBLIC"], t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c, j, h, td] * t_op[h,td]);
	
# [Eq. 38] Definition of min/max output of each technology as % of total output in a given layer.
subject to f_max_perc_tramway {c in REGIONS}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c,"TRAMWAY_TROLLEY",h,td] * t_op[h,td]) 
	<= fmax_perc [c,"TRAMWAY_TROLLEY"] * sum {j in TECHNOLOGIES_OF_END_USES_TYPE["MOB_PUBLIC"], t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c, j, h, td] * t_op[h,td]);

subject to f_max_perc {c in REGIONS, eut in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE[eut]}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c,j,h,td] * t_op[h,td])
	<= fmax_perc [c,j] *(sum {j2 in TECHNOLOGIES_OF_END_USES_TYPE[eut], t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c, j2, h, td] * t_op[h,td])
	+ sum {r in RESOURCES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (layers_in_out [r, eut] * (R_t_local [c, r, h, td] + R_t_exterior [c, r, h, td] + R_t_import [c, r, h, td] - R_t_export [c, r, h, td])));
subject to f_min_perc {c in REGIONS, eut in END_USES_TYPES, j in TECHNOLOGIES_OF_END_USES_TYPE[eut]}:
	sum {t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c,j,h,td] * t_op[h,td]) >= fmin_perc [c,j] * 
	(sum {j2 in TECHNOLOGIES_OF_END_USES_TYPE[eut], t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (F_t [c, j2, h, td] * t_op[h,td])
	+ sum {r in RESOURCES, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]} (layers_in_out [r, eut] * (R_t_local [c, r, h, td] + R_t_exterior [c, r, h, td] + R_t_import [c, r, h, td] - R_t_export [c, r, h, td])));

# [Eq. 39] Energy efficiency is a fixed cost
subject to extra_efficiency{c in REGIONS}:
	F [c,"EFFICIENCY"] = 1 / (1 + i_rate);
	
# [Eq. ..] Limit electricity import capacity
subject to max_elec_import {c in REGIONS, h in HOURS, td in TYPICAL_DAYS}:
	R_t_exterior [c,"ELECTRICITY", h, td] * t_op [h, td] <= import_capacity[c]; 

## Variant equations for hydro dams	
# [Eq. 40] Seasonal storage in hydro dams.
# When installed power of new dams 0 -> 0.44, maximum storage capacity changes linearly 0 -> 2400 GWh/y
subject to storage_level_hydro_dams {c in REGIONS diff RWITHOUTDAM}: 
	F [c,"DAM_STORAGE"] <= f_min [c,"DAM_STORAGE"] + (f_max [c,"DAM_STORAGE"]-f_min [c,"DAM_STORAGE"]) * (F [c,"HYDRO_DAM"] - f_min [c,"HYDRO_DAM"])/(f_max [c,"HYDRO_DAM"] - f_min [c,"HYDRO_DAM"]);

# [Eq. 41] Hydro dams can stored the input energy and restore it whenever. Hence, inlet is the input river and outlet is bounded by max capacity
subject to impose_hydro_dams_inflow {c in REGIONS, h in HOURS, td in TYPICAL_DAYS}: 
	Storage_in [c, "DAM_STORAGE", "ELECTRICITY", h, td] = F_t [c, "HYDRO_DAM", h, td];

# [Eq. 42] Hydro dams production is lower than installed F_t capacity:
subject to limit_hydro_dams_output {c in REGIONS, h in HOURS, td in TYPICAL_DAYS}: 
	Storage_out [c, "DAM_STORAGE", "ELECTRICITY", h, td] <= F [c,"HYDRO_DAM"];


# [Eq. 39] Limit surface area for solar
subject to solar_area_rooftop_limited {c in REGIONS} :
	(F[c,"PV_ROOFTOP"])/power_density_pv +(F[c,"DEC_SOLAR"]+F[c,"DHN_SOLAR"])/power_density_solar_thermal <= solar_area_rooftop [c];

subject to solar_area_ground_limited {c in REGIONS} :
	(F[c,"PV_UTILITY"])/power_density_pv
		+ (layers_in_out ["PT_POWER_BLOCK", "PT_HEAT"]*F[c,"PT_COLLECTOR"]+layers_in_out ["ST_POWER_BLOCK", "ST_HEAT"]*F[c,"ST_COLLECTOR"])/power_density_pv
<= solar_area_ground [c];

subject to solar_area_ground_high_irr_limited {c in REGIONS} :
	(layers_in_out ["PT_POWER_BLOCK", "PT_HEAT"]*F[c,"PT_COLLECTOR"]
		+layers_in_out ["ST_POWER_BLOCK", "ST_HEAT"]*F[c,"ST_COLLECTOR"])/power_density_pv
<= solar_area_ground_high_irr [c];

# Limit on solar multiple of csp plants (by definition, sm = (F_coll*eta_pb)/F_pb
subject to sm_limit_solar_tower {c in REGIONS}:
	layers_in_out ["ST_POWER_BLOCK", "ST_HEAT"] * F[c,"ST_COLLECTOR"] <= sm_max * F[c,"ST_POWER_BLOCK"];

subject to sm_limit_parabolic_trough {c in REGIONS}:
	layers_in_out ["PT_POWER_BLOCK", "ST_HEAT"] * F[c,"PT_COLLECTOR"] <= sm_max * F[c,"PT_POWER_BLOCK"];



# EQUATIONS Multi-Cells
#-----------------------

# equations common to all types of exchanges
subject to reciprocity_of_Exchanges {c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_R, h in HOURS, td in TYPICAL_DAYS} :
	Exch_imp[c1,c2,i,h,td] * (1 + exchange_losses[i]* dist[c1, c2]/1000) - Exch_exp[c1,c2,i,h,td] = - Exch_imp[c2,c1,i,h,td] * (1 + exchange_losses[i] * dist[c2, c1]/1000) + Exch_exp[c2,c1,i,h,td];
subject to importation {c1 in REGIONS, i in EXCHANGE_R, h in HOURS, td in TYPICAL_DAYS}:
	R_t_import[c1, i, h, td]  = sum{c2 in REGIONS} Exch_imp[c1,c2,i,h,td];
subject to exportation {c1 in REGIONS, i in EXCHANGE_R, h in HOURS, td in TYPICAL_DAYS}:
	R_t_export[c1, i, h, td]  = sum{c2 in REGIONS} Exch_exp[c1,c2,i,h,td];

# resources without exchanges
subject to resources_no_exchanges {c1 in REGIONS, n in NOEXCHANGES, h in HOURS, td in TYPICAL_DAYS} :
	R_t_import [c1, n, h, td] = 0;
subject to resources_no_exchanges2 {c1 in REGIONS, n in NOEXCHANGES, h in HOURS, td in TYPICAL_DAYS} :
	R_t_export [c1, n, h, td] = 0;

# network exchanges
subject to capacity_limit_imp {c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_NETWORK_R, h in HOURS, td in TYPICAL_DAYS} :
	Exch_imp[c1,c2,i,h,td] <= sum{n in NETWORK_TYPE[i]} Transfer_capacity [c2,c1,i,n];
subject to capacity_limit_exp {c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_NETWORK_R, h in HOURS, td in TYPICAL_DAYS} :
	Exch_exp[c1,c2,i,h,td] <= sum{n in NETWORK_TYPE[i]} Transfer_capacity [c1,c2,i,n];
subject to transfer_capacity_bounds {c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_NETWORK_R diff {"GAS"}, n in NETWORK_TYPE[i]}:
	tc_min[c1, c2, i, n] <= Transfer_capacity[c1, c2, i, n] <= tc_max[c1, c2, i, n];

subject to bidirectonal_exchanges {c1 in REGIONS, c2 in REGIONS, i in EXCHANGE_NETWORK_R, n in NETWORK_TYPE[i]}:
	Transfer_capacity [c1,c2,i,n] = Transfer_capacity [c2,c1,i,n];
	
# special equations for gas network being retrofitted into hydrogen network
subject to transfer_capacity_bounds_gas_pipeline {c1 in REGIONS, c2 in REGIONS}:
	tc_min[c1, c2, "GAS", "GAS_PIPELINE"] <=
	Transfer_capacity[c1, c2, "GAS", "GAS_PIPELINE"] + Transfer_capacity[c1, c2, "H2", "H2_RETROFITTED"] / retro_gas_to_h2
	<= tc_max[c1, c2, "GAS", "GAS_PIPELINE"];
subject to transfer_capacity_bounds_gas_subsea {c1 in REGIONS, c2 in REGIONS}:
	tc_min[c1, c2, "GAS", "GAS_SUBSEA"] <=
	Transfer_capacity[c1, c2, "GAS", "GAS_SUBSEA"] + Transfer_capacity[c1, c2, "H2", "H2_SUBSEA_RETRO"] / retro_gas_to_h2
	<= tc_max[c1, c2, "GAS", "GAS_SUBSEA"];
	
# equation to link Transfer_capapcity to equivalent technology
subject to networks_infra {c1 in REGIONS, i in EXCHANGE_NETWORK_R, n in NETWORK_TYPE[i]}:
	F[c1, n] >= sum{c2 in REGIONS} (dist[c1, c2] * Transfer_capacity [c1,c2,i,n]/2);

# freight exchanges (+ eq 25 and 26), computing and adding addtional freight due to exchanges
subject to freight_of_exchanges_border{c1 in REGIONS, c2 in REGIONS} :
	Exch_freight_border[c1,c2] = dist[c1,c2] * sum{r in EXCHANGE_FREIGHT_R, t in PERIODS, h in HOUR_OF_PERIOD[t], td in TYPICAL_DAY_OF_PERIOD[t]}((Exch_imp[c1,c2,r,h,td] + Exch_exp[c1,c2,r,h,td])/lhv[r]);
subject to freight_of_exchanges{c1 in REGIONS} :
	Exch_freight[c1] = sum{c2 in REGIONS} Exch_freight_border[c1,c2]/2;
subject to additional_freight{c in REGIONS} :
	sum{j in TECHNOLOGIES_OF_END_USES_CATEGORY["MOBILITY_FREIGHT"]} (Shares_mobility_freight [c,j]) = (Exch_freight[c] + end_uses_input[c,"MOBILITY_FREIGHT"])/(end_uses_input[c,"MOBILITY_FREIGHT"]);


##########################
### OBJECTIVE FUNCTION ###
##########################

# Can choose between TotalGWP and TotalCost
minimize obj:  sum{c in REGIONS} TotalCost[c];

## formula for GWP_op optimization
# sum{c in REGIONS, r in RESOURCES} (GWP_op [c,r]);
# 
