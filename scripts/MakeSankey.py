import SankeyDict as sd
import pandas as pd
import numpy as np



class Cell:
    
    def __init__(self, name, year_balance, storage):
        self.name = name
        self.year_balance = year_balance
        self.storage = storage
        
        self.year_balance = self.arrange_columns(self.year_balance.copy(), sd.RegroupLayers)
        self.year_balance = self.arrange_rows(self.year_balance.copy(), sd.RegroupElements)
        self.storage = self.arrange_columns(self.storage.copy(), sd.StorageField)
        self.storage = self.arrange_rows(self.storage.copy(), sd.EndUseStorage)
        
        self.update_year_balance()
        
    def arrange(self, dataframe, RegroupDict):
        
        for column_name, group_columns in RegroupDict.items():
            if len(group_columns) > 1:
                new_column = dataframe.pop(group_columns[0])
                for i in range(1, len(group_columns)):
                    new_column = new_column.add(dataframe.pop(group_columns[i]))
                new_column.name = column_name
                dataframe = pd.concat([dataframe, new_column], axis=1)
                
            else:
                dataframe = dataframe.rename(columns={group_columns[0]:column_name})
        for column in dataframe.columns:
            if column not in RegroupDict.keys():
                dataframe.pop(column)
        return dataframe
                
    def arrange_columns(self, data_frame, RegroupDict):
        return self.arrange(data_frame, RegroupDict)
    
    def arrange_rows(self, data_frame, RegroupDict):
        return self.arrange(data_frame.T, RegroupDict).T
    
    def update_year_balance(self):
        for sto in sd.StorageLayer:
            self.year_balance.loc[sto][sd.StorageLayer[sto]] = -self.storage.loc[sto]["Year energy flux"]
                
                
with open("Year_balance.csv", "r") as year_balance_file:

    # Get the name of all the macrocells
    year_balance_file.readline()
    first_column = [line.split(",")[0] for line in year_balance_file.readlines()]
    cells_name = []
    for index_name in first_column:
        if index_name not in cells_name:
            cells_name.append(index_name)
            
    year_balance_file.seek(0)
    
    # Get year_balance file under the form of a panda dataframe
    all_data_balance = pd.read_csv(year_balance_file, index_col=[0,1])
    all_data_balance = all_data_balance.replace(to_replace=np.nan, value=0)

with open("Sto_assets.csv", "r") as sto_assets_file:
    
    # Get Sto_assets file under the form of a panda dataframe
    all_data_sto = pd.read_csv(sto_assets_file, index_col=[0,1])
    all_data_sto = all_data_sto.replace(to_replace=np.nan, value=0)
    
cells = {}
for cell_name in cells_name:
    cells[cell_name] = Cell(cell_name, all_data_balance.loc[cell_name], all_data_sto.loc[cell_name])


total_data_balance = all_data_balance.loc[cells_name[0]]
total_data_sto = all_data_sto.loc[cells_name[0]]
for i in range(1, len(cells_name)):
    total_data_balance = total_data_balance.add(all_data_balance.loc[cells_name[i]])
    total_data_sto = total_data_sto.add(all_data_sto.loc[cells_name[i]])

cells["Total"] = Cell("Total", total_data_balance, total_data_sto)



for cell in cells.values():
    with open("input2sankey_"+cell.name+".csv", "w") as input2csv_file:
        print("source,target,realValue,layerID,layerColor,layerUnit", file=input2csv_file)
        
        for tech in cell.year_balance.index:
            tech_count = 0
            for layer in cell.year_balance.columns:
                value = cell.year_balance.loc[tech][layer]
                if value > 10 and tech != layer:
                    if tech == "End Use":
                        continue
                    else:
                        if tech not in sd.TechLayer.keys():
                            print("%s,%s,%f,%s,%s,%s" %(tech, layer, value/1000, layer, sd.LayerColor[layer], "TWh"), file=input2csv_file)
                        else:
                            print("%s,%s,%f,%s,%s,%s" %(tech, layer, value/1000, sd.TechLayer[tech], sd.LayerColor[sd.TechLayer[tech]], "TWh"), file=input2csv_file)
                
                if value > 0:
                    tech_count = tech_count + 1
                    
        for layer in cell.year_balance.T.index:
            for tech in cell.year_balance.T.columns:
                value = cell.year_balance.T.loc[layer][tech]
                if value < -10:
                    if layer in sd.EndUseLayer:
                        continue
                    elif tech != "End Use":
                        print("%s,%s,%f,%s,%s,%s" %(layer, tech, -value/1000, layer, sd.LayerColor[layer], "TWh"), file=input2csv_file)
                

        for layer in sd.EndUseName:
            value = cell.year_balance.loc["End Use"][layer]
            if value < -10:
                print("%s,%s,%f,%s,%s,%s" %(layer, sd.EndUseName[layer], -value/1000, layer, sd.LayerColor[layer], "TWh"), file=input2csv_file)
    
    
    
    
    