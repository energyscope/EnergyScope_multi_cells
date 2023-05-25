# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 19:20:21 2023

@author: JulienJacquemin
"""


# Regroup the technologies that have similar characteristics. They will
# appear under the same group with name of their dictionary key on the Sankey
# diagram.
# Note that if the name of the group is the same as a layer to which it is 
# connected, the name between the group and the layer will not appear on the 
# diagram.
RegroupElements = {
    "Nuclear":          ["NUCLEAR"],
    "CCGT":             ["CCGT"],
    "CCGT_Ammonia":     ["CCGT_AMMONIA"],
    "Coal_US":          ["COAL_US"],
    "Coal_IGCC":        ["COAL_IGCC"],
    "Solar PV":         ["PV"],
    "CSP":              ["PT_POWER_BLOCK","ST_POWER_BLOCK"],
    "Stirling Dish":    ["STIRLING_DISH"],
    "Wind Onshore":     ["WIND_ONSHORE"],
    "Wind Offshore":    ["WIND_OFFSHORE"],
    "Hydro Dam":        ["HYDRO_DAM"],
    "Hydro River":      ["HYDRO_RIVER"],
    "Tidal Power":      ["NEW_TIDAL_STREAM","TIDAL_STREAM","TIDAL_RANGE"],
    "Wave":             ["WAVE"],
    "Geothermal":       ["GEOTHERMAL"],
    "Ind Cogen":        ["IND_COGEN_GAS","IND_COGEN_WOOD","IND_COGEN_WASTE"],
    "Ind Boiler":       ["IND_BOILER_GAS","IND_BOILER_WOOD","IND_BOILER_OIL",
                         "IND_BOILER_COAL","IND_BOILER_WASTE"],
    "Ind Direct Elec":  ["IND_DIRECT_ELEC"],
    "HPs":              ["DHN_HP_ELEC", "DEC_HP_ELEC"],
    "DHN Tech":              ["DHN_COGEN_GAS","DHN_COGEN_WOOD","DHN_COGEN_WASTE",
                         "DHN_COGEN_WET_BIOMASS","DHN_COGEN_BIO_HYDROLYSIS",
                         "DHN_BOILER_GAS","DHN_BOILER_WOOD","DHN_BOILER_OIL", 
                         "DHN_DEEP_GEO", "DHN_SOLAR"],
    "DEC Heat":         ["DEC_THHP_GAS", "DEC_COGEN_GAS","DEC_COGEN_OIL","DEC_ADVCOGEN_GAS",
                         "DEC_ADVCOGEN_H2", "DEC_BOILER_GAS","DEC_BOILER_WOOD","DEC_BOILER_OIL",
                         "DEC_SOLAR", "DEC_DIRECT_ELEC"],
    "Big Split":        ["BIG_SPLIT"],
    "Chiller":          ["CHILLER_WC"],
    "Public Mob": ["TRAMWAY_TROLLEY", "BUS_COACH_DIESEL", "BUS_COACH_HYDIESEL",
                         "BUS_COACH_CNG_STOICH", "BUS_COACH_FC_HYBRIDH2", "TRAIN_PUB"],
    "Private Mob": ["CAR_GASOLINE", "CAR_DIESEL", "CAR_NG", "CAR_METHANOL", 
                          "CAR_HEV", "CAR_PHEV", "CAR_BEV", "CAR_FUEL_CELL"],
    "Rail Freight":    ["TRAIN_FREIGHT"],
    "Boat Freight":     ["BOAT_FREIGHT_DIESEL", "BOAT_FREIGHT_NG", "BOAT_FREIGHT_METHANOL"],
    "Road Freight":     ["TRUCK_DIESEL", "TRUCK_METHANOL", "TRUCK_FUEL_CELL",
                         "TRUCK_ELEC", "TRUCK_NG"],
    "Solar" :           ["PT_COLLECTOR", "ST_COLLECTOR"],
    "H2.":               ["H2_ELECTROLYSIS", "SMR", "H2_BIOMASS", "AMMONIA_TO_H2"],
    "Gasifi SNG":       ["GASIFICATION_SNG"],
    "To Methane":       ["SYN_METHANATION", "BIOMETHANATION", "BIO_HYDROLYSIS"],
    "Pyrolise" :        ["PYROLYSIS_TO_LFO", "PYROLYSIS_TO_FUELS"],
    "To Methanol":      ["SYN_METHANOLATION", "METHANE_TO_METHANOL", "BIOMASS_TO_METHANOL"],
    "Haber Bosch":      ["HABER_BOSCH"],
    "To HVC":           ["OIL_TO_HVC", "GAS_TO_HVC", "BIOMASS_TO_HVC", "METHANOL_TO_HVC"],
    "Elec in/out":      ["ELECTRICITY"],
    "Oil imports":         ["GASOLINE"],
    "Diesel imports":           ["DIESEL"],
    "Bioethanol imports":       ["BIOETHANOL"],
    "Biodiesel imports":        ["BIODIESEL"],
    "LFO imports":              ["LFO"],
    "Gas imports":              ["GAS"],
    "Gas RE imports":           ["GAS_RE"],
    "Wood":                     ["WOOD"],
    "Biomass":                  ["WET_BIOMASS"],
    "Coal imports":             ["COAL"],
    "Waste imports":            ["WASTE"],
    "H2 imports":               ["H2"],
    "H2 RE imports":            ["H2_RE"],
    "Ammonia imports":          ["AMMONIA"],
    "Methanol imports":         ["METHANOL"],
    "Ammonia RE imports":       ["AMMONIA_RE"],
    "Methanol RE imports":      ["METHANOL_RE"],
    "DEC Sto":          ["TS_DEC_DIRECT_ELEC", "TS_DEC_HP_ELEC", "TS_DEC_THHP_GAS", 
                         "TS_DEC_COGEN_GAS", "TS_DEC_COGEN_OIL", "TS_DEC_ADVCOGEN_GAS", 
                         "TS_DEC_ADVCOGEN_H2", "TS_DEC_BOILER_GAS", "TS_DEC_BOILER_WOOD",
                         "TS_DEC_BOILER_OIL"],
    "DHN Sto":          ["TS_DHN_DAILY", "TS_DHN_SEASONAL"],
    "Cold Sto":         ["TS_COLD"],
    "End Use":          ["END_USES"]
}


# Names of the layers.
RegroupLayers ={
    "Elec": ["ELECTRICITY"],
    "Oil": ["GASOLINE"],
    "Diesel": ["DIESEL"],	
    "LFO": ["LFO"],
    "Gas": ["GAS"],	
    "Wood": ["WOOD"],
    "Biomass": ["WET_BIOMASS"],
    "Coal": ["COAL"],
    "Waste": ["WASTE"],	
    "H2.": ["H2"],
    "Ammonia": ["AMMONIA"],	
    "Methanol": ["METHANOL"],	
    "HVC": ["HVC"],	
    "Heat HT": ["HEAT_HIGH_T"],		
    "Heat LT DHN": ["HEAT_LOW_T_DHN"],	
    "Heat LT DEC": ["HEAT_LOW_T_DECEN"],	
    "Space Cool": ["SPACE_COOLING"],	
    "Process Cool": ["PROCESS_COOLING"],	
    "Public Mob": ["MOB_PUBLIC"],	
    "Private Mob": ["MOB_PRIVATE"],	
    "Rail Freight": ["MOB_FREIGHT_RAIL"],	
    "Road Freight": ["MOB_FREIGHT_ROAD"],	
    "Boat Freight": ["MOB_FREIGHT_BOAT"],	
    "Solar": ["PT_HEAT", "ST_HEAT"]
    }

# Link the tech with the layer name (as in LayerColor) of its output. If several
# output, they must listed in order of appearance of the layer in the "Layers_in_out.scv"
# file (from left to right).



TechLayer = {
    "Solar PV":         "RES Solar",
    "Wind Onshore":     "RES Wind",
    "Wind Offshore":    "RES Wind",
    "Hydro Dam":        "RES Hydro",
    "Hydro River":      "RES Hydro",
    "Tidal Power":      "RES Hydro",
    "Wave":             "RES Hydro",
    "Geothermal":       "Geothermal",
    "Nuclear":          "Uranium"
    }
# TechLayer = {
    
#     "Nuclear":          ["Uranium"],
#     "CCGT":             ["Elec"],
#     "CCGT_Ammonia":     ["Elec"],
#     "Coal_US":          ["Elec"],
#     "Coal_IGCC":        ["Elec"],
#     "Solar PV":         ["RES Solar"],
#     "CSP":              ["Elec"],
#     "Stirling Dish":    ["RES Solar"],
#     "Wind Onshore":     ["RES Wind"],
#     "Wind Offshore":    ["RES Wind"],
#     "Hydro Dam":        ["RES Hydro"],
#     "Hydro River":      ["RES Hydro"],
#     "Tidal Power":      ["RES Hydro"],
#     "Wave":             ["RES Hydro"],
#     "Geothermal":       ["Geothermal"],
#     "Ind Cogen":        ["Elec", "Heat HT"],
#     "Ind Boiler":       ["Heat HT"],
#     "Ind Direct Elec":  ["Heat HT"],
#     "HPs":              ["Heat LT DHN", "Heat LT DEC"],
#     "DHN Tech":         ["Elec", "Heat LT DHN"],
#     "DEC Heat":         ["Elec", "Heat LT DEC"],
#     "Big Split":        ["Space Cool"],
#     "Chiller":          ["Process Cool"],
#     "Solar Collector" : ["Solar"],
#     "H2.":              ["H2.", "Heat LT DHN"],
#     "Gasifi SNG":       ["Gas"],
#     "To Methane":       ["Elec", "Gas", "Heat LT DHN"],
#     "Pyrolise" :        ["Elec", "Gas", "LFO"],
#     "To Methanol":      ["Elec", "Methanol", "Heat LT DHN"],
#     "Haber Bosch":      ["Ammonia","Heat LT DHN"],
#     "Ammonia to H2":    ["H2."],
#     "To HVC":           ["HVC"],
#     "Elec in/out":      ["Elec"],
#     "Oil imports":         ["Oil"],
#     "Diesel imports":           ["Diesel"],
#     "Bioethanol imports":       ["Oil"],
#     "Biodiesel imports":        ["Diesel"],
#     "LFO imports":              ["LFO"],
#     "Gas imports":              ["Gas"],
#     "Gas RE imports":           ["Gas"],
#     "Wood imports":             ["Wood"],
#     "Biomass imports":          ["Biomass"],
#     "Coal imports":             ["Coal"],
#     "Uranium":                  ["Uranium"],
#     "Waste imports":            ["Waste"],
#     "H2 imports":               ["H2."],
#     "H2 RE imports":            ["H2."],
#     "Ammonia imports":          ["Ammonia"],
#     "Methanol imports":         ["Methanol"],
#     "Ammonia RE imports":       ["Ammonia"],
#     "Methanol RE imports":      ["Methanol"],
#     "RES Wind":         ["RES Wind"],
#     "RES Solar":        ["RES Solar"],
#     "RES Hydro":        ["RES Hydro"],
#     "RES Geo":          ["RES Geo"],
#     "DEC Sto":          ["Heat LT DEC"],
#     "DHN Sto":          ["Heat LT DHN"],
#     "Cold Sto":         ["Space Cool"],
    
#     }




# It is only relevant to show storage of layer linked to end use only.

EndUseStorage = {
    "DEC Sto":          ["TS_DEC_DIRECT_ELEC", "TS_DEC_HP_ELEC", "TS_DEC_THHP_GAS", 
                         "TS_DEC_COGEN_GAS", "TS_DEC_COGEN_OIL", "TS_DEC_ADVCOGEN_GAS", 
                         "TS_DEC_ADVCOGEN_H2", "TS_DEC_BOILER_GAS", "TS_DEC_BOILER_WOOD",
                         "TS_DEC_BOILER_OIL"],
    "DHN Sto":          ["TS_DHN_DAILY", "TS_DHN_SEASONAL"],
    "Cold Sto":         ["TS_COLD"]
    }

StorageField = {
    "Year energy flux": ["Year_energy_flux"]
    }

StorageLayer = {
    "DEC Sto":          ["Heat LT DEC"],
    "DHN Sto":          ["Heat LT DHN"],
    "Cold Sto":         ["Space Cool"]
    }




# Name of the end use of the end use layer. If the layer is end use only
# (There is no "-" is the layer column of "Layers_in_out" matrix), its
# name is the same as the name of the layer itself.

EndUseLayer = [
    "Heat LT DHN",
    "Heat LT DEC",
    "Space Cool",
    "Process Cool",
    "Public Mob",
    "Private Mob",
    "Road Freight",
    "Boat Freight",
    "Rail Freight"
]

EndUseName = {
    "Elec": "Elec Demand",
    "Ammonia": "Non-Energy Demand",
    "Methanol": "Non-Energy Demand",
    "HVC": "Non-Energy Demand",
    "Heat HT": "Ind Heat Demand",
}




LayerColor = {
    "Elec": "#00BFFF",
    "Oil": "#8B008B",
    "Diesel": "#D3D3D3",	
    "LFO": "#8B008B",
    "Gas": "#FFD700",	
    "Wood": "#CD853F",
    "Biomass": "#336600",
    "Coal": "#A0522D",
    "Uranium": "#FFC0CB",
    "Waste": "#808000",	
    "H2.": "#FF00FF",
    "Ammonia": "#000ECD",	
    "Methanol": "#CC0066",	
    "HVC": "#00FFFF",	
    "Heat HT": "#DC143C",		
    "Heat LT DHN": "#FA8072",	
    "Heat LT DEC": "#FA8072",	
    "Space Cool": "#00CED1",	
    "Process Cool": "#00CED1",		
    "RES Wind": "#27AE34",	
    "RES Solar": "#FFFF00",	
    "RES Hydro": "#00CED1",	
    "RES Geo": "#FF0000",	
    "Solar": "#FFFF00",
    "Geothermal": "#FF0000"
    }





