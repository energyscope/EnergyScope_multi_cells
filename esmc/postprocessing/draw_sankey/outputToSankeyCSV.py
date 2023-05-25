import pandas as pd
import numpy as np
from pathlib import Path



class Cell:
    
    def __init__(self, name, year_balance, storage, limit):
        self.name = name
        self.year_balance = year_balance
        self.storage = storage
        self.limit = limit
        
        self.year_balance = self.arrange_columns(self.year_balance.copy(), RegroupLayers)
        self.year_balance = self.arrange_rows(self.year_balance.copy(), RegroupElements)
        self.storage = self.arrange_columns(self.storage.copy(), StorageField)
        self.storage = self.arrange_rows(self.storage.copy(), EndUseStorage)
        
        self.update_year_balance()
        
    def arrange(self, dataframe, RegroupDict, arrange_rows = False):
        
        for column_name, group_columns in RegroupDict.items():
            if len(group_columns) > 1:
                new_column = dataframe.pop(group_columns[0])
                for i in range(1, len(group_columns)):
                    new_column = new_column.add(dataframe.pop(group_columns[i]))
                new_column.name = column_name
                dataframe = pd.concat([dataframe, new_column], axis=1)
                
            else:
                dataframe = dataframe.rename(columns={group_columns[0]:column_name})
            if arrange_rows and not self.check_relevance(dataframe, column_name):
                dataframe.pop(column_name)
                
        for column in dataframe.columns:
            if column not in RegroupDict.keys():
                dataframe.pop(column)
        return dataframe
                
    def arrange_columns(self, data_frame, RegroupDict):
        return self.arrange(data_frame, RegroupDict)
    
    def arrange_rows(self, data_frame, RegroupDict):
        return self.arrange(data_frame.T, RegroupDict, arrange_rows=True).T
    
    def update_year_balance(self):
        for sto in StorageLayer:
            self.year_balance.loc[sto][StorageLayer[sto]] = -self.storage.loc[sto]["Year energy flux"]
    
    def check_relevance(self, dataframe, column_name):
        minus_presence = False
        plus_presence = False
        minus_under_limit = True
        plus_under_limit = True
        
        relevance = True
        
        for index in dataframe.index:
            value = dataframe.loc[index][column_name]
            if value < 0:
                minus_presence = True
            if value > 0:
                plus_presence = True
            if value < 0 and abs(value) > self.limit :
                minus_under_limit = False
            if value > 0 and value > self.limit :
                plus_under_limit = False
                
        if minus_presence and plus_presence and (minus_under_limit or plus_under_limit):
            relevance = False
        
        if self.name == "Total" and (column_name in Resources) and minus_presence :
            relevance = False
        
        return relevance
        
                
def writeSankeyFile(space_id, case_study, limit=50):
    
    proj_dir = Path(__file__).parents[3]
    output_dir = proj_dir / "case_studies" / space_id / case_study / "outputs"
                    
    with open(output_dir / "Year_balance.csv", "r") as year_balance_file:
    
        # Get the name of all the macrocells
        year_balance_file.readline()
        first_column = [line.split(";")[0] for line in year_balance_file.readlines()]
        cells_name = []
        for index_name in first_column:
            if index_name not in cells_name:
                cells_name.append(index_name)
                
        year_balance_file.seek(0)
        
        # Get year_balance file under the form of a panda dataframe
        all_data_balance = pd.read_csv(year_balance_file, index_col=[0,1], sep=";")
        all_data_balance = all_data_balance.replace(to_replace=np.nan, value=0)
    
    with open(output_dir / "Sto_assets.csv", "r") as sto_assets_file:
        
        # Get Sto_assets file under the form of a panda dataframe
        all_data_sto = pd.read_csv(sto_assets_file, index_col=[0,1], sep=";")
        all_data_sto = all_data_sto.replace(to_replace=np.nan, value=0)
        
    cells = {}
    for cell_name in cells_name:
        cells[cell_name] = Cell(cell_name, all_data_balance.loc[cell_name], all_data_sto.loc[cell_name], limit)
    
    
    total_data_balance = all_data_balance.loc[cells_name[0]]
    total_data_sto = all_data_sto.loc[cells_name[0]]
    for i in range(1, len(cells_name)):
        total_data_balance = total_data_balance.add(all_data_balance.loc[cells_name[i]])
        total_data_sto = total_data_sto.add(all_data_sto.loc[cells_name[i]])
    
    cells["Total"] = Cell("Total", total_data_balance, total_data_sto, limit)
    print(cells["Total"].year_balance)
    print(cells["ES-PT"].year_balance)
    
    
    for cell in cells.values():
        file_name = "input2sankey_"+cell.name+".csv"
        with open(output_dir / file_name, "w") as input2csv_file:
            print("source,target,realValue,layerID,layerColor,layerUnit", file=input2csv_file)
            
            for tech in cell.year_balance.index:
                tech_count = 0
                for layer in cell.year_balance.columns:
                    value = cell.year_balance.loc[tech][layer]
                    if value > cell.limit and tech != layer:
                        if tech == "End Use":
                            continue
                        else:
                            if tech not in TechLayer.keys():
                                print("%s,%s,%f,%s,%s,%s" %(tech, layer, value/1000, layer, LayerColor[layer], "TWh"), file=input2csv_file)
                            else:
                                print("%s,%s,%f,%s,%s,%s" %(tech, layer, value/1000, TechLayer[tech], LayerColor[TechLayer[tech]], "TWh"), file=input2csv_file)
                    
                    if value > 0:
                        tech_count = tech_count + 1
                        
            for layer in cell.year_balance.T.index:
                for tech in cell.year_balance.T.columns:
                    value = cell.year_balance.T.loc[layer][tech]
                    if value < -10:
                        if layer in EndUseLayer:
                            continue
                        elif tech != "End Use":
                            print("%s,%s,%f,%s,%s,%s" %(layer, tech, -value/1000, layer, LayerColor[layer], "TWh"), file=input2csv_file)
                    
    
            for layer in EndUseName:
                value = cell.year_balance.loc["End Use"][layer]
                if value < -10:
                    print("%s,%s,%f,%s,%s,%s" %(layer, EndUseName[layer], -value/1000, layer, LayerColor[layer], "TWh"), file=input2csv_file)
        
        
RegroupElements = {
    "Nuclear":          ["NUCLEAR"],
    "CCGT":             ["CCGT"],
    "CCGT_Ammonia":     ["CCGT_AMMONIA"],
    "Coal_US":          ["COAL_US"],
    "Coal_IGCC":        ["COAL_IGCC"],
    "Solar PV":         ["PV_ROOFTOP", "PV_UTILITY"],
    "CSP":              ["PT_POWER_BLOCK","ST_POWER_BLOCK"],
    "Wind Onshore":     ["WIND_ONSHORE"],
    "Wind Offshore":    ["WIND_OFFSHORE"],
    "Hydro":            ["HYDRO_DAM", "HYDRO_RIVER"],
    #"Hydro Dam":        ["HYDRO_DAM"],
    #"Hydro River":      ["HYDRO_RIVER"],
    "Tidal Power":      ["NEW_TIDAL_STREAM","TIDAL_STREAM","TIDAL_RANGE"],
    "Wave":             ["WAVE"],
    "Geothermal":       ["GEOTHERMAL"],
    "Ind Cogen":        ["IND_COGEN_GAS","IND_COGEN_WOOD","IND_COGEN_WASTE"],
    "Ind Boiler":       ["IND_BOILER_GAS","IND_BOILER_WOOD","IND_BOILER_OIL",
                         "IND_BOILER_COAL","IND_BOILER_WASTE", "IND_BOILER_BIOWASTE"],
    "Ind Direct Elec":  ["IND_DIRECT_ELEC"],
    "HPs":              ["DHN_HP_ELEC", "DEC_HP_ELEC"],
    "DHN Tech":              ["DHN_COGEN_GAS","DHN_COGEN_WOOD","DHN_COGEN_WASTE",
                         "DHN_COGEN_WET_BIOMASS","DHN_COGEN_BIO_HYDROLYSIS",
                         "DHN_BOILER_GAS","DHN_BOILER_WOOD","DHN_BOILER_OIL", 
                         "DHN_DEEP_GEO", "DHN_SOLAR"],
    "DEC Heat":         ["DEC_THHP_GAS", "DEC_COGEN_GAS","DEC_COGEN_OIL","DEC_ADVCOGEN_GAS",
                         "DEC_ADVCOGEN_H2", "DEC_BOILER_GAS","DEC_BOILER_WOOD","DEC_BOILER_OIL",
                         "DEC_SOLAR", "DEC_DIRECT_ELEC"],
    "Cooling tech.":     ["BIG_SPLIT", "CHILLER_WC"],
    #"Big Split":        ["BIG_SPLIT"],
    #"Chiller":          ["CHILLER_WC"],
    
    "Mobility": ["TRAMWAY_TROLLEY", "BUS_COACH_DIESEL", "BUS_COACH_HYDIESEL",
                 "BUS_COACH_CNG_STOICH", "BUS_COACH_FC_HYBRIDH2", "TRAIN_PUB", 
                 "PLANE_DIESEL_INTRA_EU", "PLANE_DIESEL_EXTRA_EU", "CAR_GASOLINE", 
                 "CAR_DIESEL", "CAR_NG", 
                 "CAR_METHANOL", "CAR_HEV", "CAR_PHEV", "CAR_BEV", "CAR_FUEL_CELL"],
    #"Public Mob": ["TRAMWAY_TROLLEY", "BUS_COACH_DIESEL", "BUS_COACH_HYDIESEL",
     #            "BUS_COACH_CNG_STOICH", "BUS_COACH_FC_HYBRIDH2", "TRAIN_PUB", 
      #           "PLANE_JETFUEL"],
    #"Private Mob": ["CAR_GASOLINE", "CAR_DIESEL", "CAR_NG", "CAR_METHANOL", 
     #                     "CAR_HEV", "CAR_PHEV", "CAR_BEV", "CAR_FUEL_CELL"],
    
    "Freight": ["TRAIN_FREIGHT", "BOAT_FREIGHT_DIESEL", "BOAT_FREIGHT_NG", 
                "BOAT_FREIGHT_METHANOL", "TRUCK_DIESEL", "TRUCK_METHANOL", 
                "TRUCK_FUEL_CELL", "TRUCK_ELEC", "TRUCK_NG"],
    #"Rail Freight":    ["TRAIN_FREIGHT"],
    #"Boat Freight":     ["BOAT_FREIGHT_DIESEL", "BOAT_FREIGHT_NG", "BOAT_FREIGHT_METHANOL"],
    #"Road Freight":     ["TRUCK_DIESEL", "TRUCK_METHANOL", "TRUCK_FUEL_CELL",
    #                     "TRUCK_ELEC", "TRUCK_NG"],
    "Int. Freight":     ["CONTAINER_CARGO_DIESEL", "CONTAINER_CARGO_LNG", 
                         "CONTAINER_CARGO_METHANOL", "CONTAINER_CARGO_AMMONIA", 
                         "CONTAINER_CARGO_FUELCELL_AMMONIA","CONTAINER_CARGO_RETRO_METHANOL",
                         "CONTAINER_CARGO_RETRO_AMMONIA", "CONTAINER_CARGO_FUELCELL_LH2"],
    "Solar" :           ["PT_COLLECTOR", "ST_COLLECTOR"],
    "H2.":               ["H2_ELECTROLYSIS", "SMR", "H2_BIOMASS", "AMMONIA_TO_H2"],
    "To Methane":       ["GASIFICATION_LIGNO_TO_SNG", "GASIFICATION_BIOWASTE_TO_SNG", 
                         "SYN_METHANATION", "BIOMETHANATION_WET_BIOMASS", "BIOMETHANATION_BIOWASTE", "BIO_HYDROLYSIS"],
    "Pyrolise" :        ["PYROLYSIS_LIGNO_TO_LFO", "PYROLYSIS_LIGNO_TO_FUELS", "PYROLYSIS_BIOWASTE_TO_LFO", 
                         "PYROLYSIS_BIOWASTE_TO_FUELS"],
    "To Methanol":      ["SYN_METHANOLATION", "METHANE_TO_METHANOL", "BIOMASS_TO_METHANOL"],
    "Haber Bosch":      ["HABER_BOSCH"],
    "Fischer-Tropsch":  ["FISCHER_TROPSCH_DIESEL", "FISCHER_TROPSCH_GASOLINE", "FISCHER_TROPSCH_LFO"],
    "Bio Fischer-Tropsch" : ["FT_LIGNO_GASOLINE", "FT_LIGNO_LFO", "FT_LIGNO_DIESEL",
                             "FT_BIOWASTE_GASOLINE", "FT_BIOWASTE_LFO", "FT_BIOWASTE_DIESEL"],
    "Biomass to fuel" : ["BIOMASS_TO_FUEL"],
    "HVC":           ["OIL_TO_HVC", "GAS_TO_HVC", "BIOMASS_TO_HVC", "METHANOL_TO_HVC"],
    "Elec in/out":      ["ELECTRICITY"],
    "Oil imports":         ["GASOLINE"],
    "Oil RE imports":      ["GASOLINE_RE"],
    "Diesel imports":           ["DIESEL"],
    "Bioethanol imports":       ["BIOETHANOL"],
    "Biodiesel imports":        ["BIODIESEL"],
    "LFO imports":              ["LFO"],
    "Gas imports":              ["GAS"],
    "Gas RE imports":           ["GAS_RE"],
    "Wood/Ligno":               ["WOOD", "OTHER_LIGNO"],
    "Wet Biomass":              ["WET_BIOMASS"],
    "Biowaste":                 ["BIOWASTE", "BIOMASS_RESIDUES"],
    "Coal imports":             ["COAL"],
    "Waste":            ["WASTE"],
    "H2 imports/export":               ["H2"],
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
    "End Use":          ["END_USES"],
    "Steel":            ["STEEL_DRI_C_EAF", "STEEL_DRI_H_EAF", "STEEL_BF_BOF",
                         "STEEL_EAF_SCRAP"]
}

Resources = [
    "Elec in/out",
    "Oil imports",
    "Oil RE imports",
    "Diesel imports",
    "Bioethanol imports",
    "Biodiesel imports",
    "LFO imports",
    "Gas imports",
    "Gas RE imports",
    "Wood/Ligno",
    "Wet Biomass",
    "Biowaste",
    "Coal imports",
    "Waste",
    "H2 imports/export",
    "H2 RE imports",
    "Ammonia imports",
    "Methanol imports",
    "Ammonia RE imports",
    "Methanol RE imports"]

# Names of the layers.
RegroupLayers ={
    "Elec": ["ELECTRICITY"],
    "Oil": ["GASOLINE"],
    "Jet Fuel": ["JET_FUEL"],
    "Diesel": ["DIESEL"],	
    "LFO": ["LFO"],
    "Gas": ["GAS"],	
    "Wood/Ligno": ["WOOD"],
    "Wet Biomass": ["WET_BIOMASS"],
    "Biowaste": ["BIOWASTE"],
    "Coal": ["COAL"],
    "Waste": ["WASTE"],	
    "H2.": ["H2"],
    "Ammonia": ["AMMONIA"],	
    "Methanol": ["METHANOL"],	
    "HVC": ["HVC"],	
    "Heat HT": ["HEAT_HIGH_T"],		
    "Heat LT DHN": ["HEAT_LOW_T_DHN"],	
    "Heat LT DEC": ["HEAT_LOW_T_DECEN"],	
    "Cooling": ["SPACE_COOLING", "PROCESS_COOLING"],
    #"Space Cool": ["SPACE_COOLING"],	
    #"Process Cool": ["PROCESS_COOLING"],
    "Mobility": 	["MOB_PUBLIC", "MOB_PRIVATE", "INTRA_EU_AVIATION", "EXTRA_EU_AVIATION"],
    #"Public Mob": ["MOB_PUBLIC"],	
    #"Private Mob": ["MOB_PRIVATE"],	
    "Freight": ["MOB_FREIGHT_RAIL","MOB_FREIGHT_ROAD", "MOB_FREIGHT_BOAT"],
    #"Rail Freight": ["MOB_FREIGHT_RAIL"],	
    #"Road Freight": ["MOB_FREIGHT_ROAD"],	
    #"Boat Freight": ["MOB_FREIGHT_BOAT"],	
    "Int. Freight": ["CONTAINER_FREIGHT"],
    "Solar": ["PT_HEAT", "ST_HEAT"],
    "Steel": ["STEEL"]
    }

# Link the tech with the layer name (as in LayerColor) of its output. If several
# output, they must listed in order of appearance of the layer in the "Layers_in_out.scv"
# file (from left to right).


TechLayer = {
    "Solar PV":         "RES Solar",
    "Wind Onshore":     "RES Wind",
    "Wind Offshore":    "RES Wind",
    "Hydro":            "RES Hydro",
    #"Hydro Dam":        "RES Hydro",
    #"Hydro River":      "RES Hydro",
    "Tidal Power":      "RES Hydro",
    "Wave":             "RES Hydro",
    "Geothermal":       "Geothermal",
    "Nuclear":          "Uranium"
    }


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
    #"Cold Sto":         ["Space Cool"]
    }


# Name of the end use of the end use layer. If the layer is end use only
# (There is no "-" is the layer column of "Layers_in_out" matrix), its
# name is the same as the name of the layer itself.

EndUseLayer = [
    "Heat LT DHN",
    "Heat LT DEC",
    "Cooling",
    #"Space Cool",
    #"Process Cool",
    "Mobility",
    "Freight",
    #"Public Mob",
    #"Private Mob",
    #"Road Freight",
    #"Boat Freight",
    #"Rail Freight",
    "Int. Freight",
    "Steel"
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
    "Wood/Ligno": "#CD853F",
    "Wet Biomass": "#336600",
    "Biowaste": "#336600",
    "Coal": "#A0522D",
    "Uranium": "#FFC0CB",
    "Waste": "#808000",	
    "H2.": "#FF00FF",
    "Ammonia": "#000ECD",	
    "Methanol": "#CC0066",
    "Steel": "#B0C4DE",	
    "HVC": "#00FFFF",	
    "Heat HT": "#DC143C",		
    "Heat LT DHN": "#FA8072",	
    "Heat LT DEC": "#FA8072",	
    "Cooling": "#00CED1",
    #"Space Cool": "#00CED1",	
    #"Process Cool": "#00CED1",		
    "RES Wind": "#27AE34",	
    "RES Solar": "#FFFF00",	
    "RES Hydro": "#00CED1",	
    "RES Geo": "#FF0000",	
    "Solar": "#FFFF00",
    "Geothermal": "#FF0000"
    }






        
        