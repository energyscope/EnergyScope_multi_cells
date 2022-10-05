import numpy as np

from esmc import Esmc
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

config = {'case_study': 'test',
          'comment': 'this a test of json version printing',
          'regions_names': ['AT', 'BE', 'CH', 'DE', 'DK', 'ES', 'FR', 'IE', 'IT', 'LU', 'NL', 'PT', 'SE', 'UK']}
# create model and import regions data
my_model = Esmc(config, nbr_td=10)

# path to data
project_dir = my_model.project_dir
data_dir = project_dir / 'Data'


# # import population data
# pop = pd.read_csv(data_dir/'pop_projection_eu.tsv',sep='\t', index_col=0).rename(columns=lambda x : int(x))
#
# # create and fill demand and demand per person (demands_pp) recap table for all regions
regions_names = config['regions_names']
regions = my_model.regions
# demands = pd.DataFrame(0, index=regions[regions_names[0]].data['Demand'].index,
#                        columns=regions_names)
# demands_pp = demands.copy()
# for r in regions:
#     regions[r].data['Population'] = pop.loc[r,2030]
#     demands.loc[:,r] = regions[r].data['Demand'].sum(axis=1)/1000 # total demand in [TWh] or [Gpkm] or [Gtkm]
# demands_pp = demands.div(pop.loc[regions_names,2030])*1e6 # demand per person in [MWh/pers], [kpkm/pers] or [ktkm/pers]
#
# # conversion of mobility into [TWh] or [MWh/pers] using average EU forecast 2035
# ratio_pass = 0.32 #[TWh/Gpkm]
# ratio_freight = 0.24 #[TWh/Gtkm]
# demands_e = demands.copy() # total demand in [TWh]
# demands_e.loc['MOBILITY_PASSENGER',:] = demands.loc['MOBILITY_PASSENGER',:]*ratio_pass
# demands_e.loc['MOBILITY_FREIGHT',:] = demands.loc['MOBILITY_FREIGHT',:]*ratio_freight
# demands_e.loc['TOTAL',:] = demands_e.sum(axis=0)
# demands_e_pp = demands_e.div(pop.loc[regions_names,2030])*1e6 # demand per person in [MWh/pers]
#
# # add units for printing
# demands.rename(index=lambda x : x+' [TWh]', inplace=True)
# demands.rename(index={'MOBILITY_PASSENGER [TWh]': 'MOBILITY_PASSENGER [Gpkm]',
#                       'MOBILITY_FREIGHT [TWh]': 'MOBILITY_FREIGHT [Gtkm]'},
#                inplace=True)
# demands_pp.rename(index=lambda x : x+' [MWh/pers]', inplace=True)
# demands_pp.rename(index={'MOBILITY_PASSENGER [MWh/pers]': 'MOBILITY_PASSENGER [kpkm/pers]',
#                       'MOBILITY_FREIGHT [MWh/pers]': 'MOBILITY_FREIGHT [ktkm/pers]'},
#                inplace=True)
# demands_e.rename(index=lambda x : x+' [TWh]', inplace=True)
# demands_e_pp.rename(index=lambda x : x+' [MWh/pers]', inplace=True)
#
# # printing demands into excel file
# writer = pd.ExcelWriter(my_model.cs_dir/'demand_data.xlsx', engine='xlsxwriter')
# demands.to_excel(writer, sheet_name='Demand', float_format='%.3f')
# demands_e.to_excel(writer, sheet_name='Demand_energy', float_format='%.3f')
# demands_pp.to_excel(writer, sheet_name='Demand_pp', float_format='%.3f')
# demands_e_pp.to_excel(writer, sheet_name='Demand_pp_energy', float_format='%.3f')
# writer.save()
#
# # computing c_p of renewables for each country
# res_names = ['PV', 'Wind_onshore', 'Wind_offshore', 'Hydro_dam', 'Hydro_river', 'Tidal', 'Solar']
# c_p = pd.DataFrame(0, index=res_names, columns=regions_names)
#
# for r in regions:
#     c_p.loc[:,r] = regions[r].data['Time_series'].sum(axis=0)/8760
#
# # printing c_p
# c_p.to_csv(my_model.cs_dir/'c_p.csv', float_format='%.3f')
p = Path(__file__).parents[1]/'case_studies'/'graphs'
ts_names = list(regions[regions_names[0]].data['Time_series'].columns)
dc = dict()
for t in ts_names:
    dc[t] = pd.DataFrame(0,index=np.arange(1,8761), columns=regions_names)
    for r in regions:
        dc[t].loc[:,r] = regions[r].data['Time_series'].loc[:,t].sort_values(ascending=False).reset_index(drop=True)
    dc[t].plot(title=('Duration curve '+str(t)), xlabel='Hours')
    plt.savefig(p/('dc_'+str(t)+'_westernEU.svg'), format='svg')


# # printing demands into excel file
# writer = pd.ExcelWriter(my_model.cs_dir/'demand_data.xlsx', engine='xlsxwriter')
# demands.to_excel(writer, sheet_name='Demand', float_format='%.3f')
# demands_e.to_excel(writer, sheet_name='Demand_energy', float_format='%.3f')
# demands_pp.to_excel(writer, sheet_name='Demand_pp', float_format='%.3f')
# demands_e_pp.to_excel(writer, sheet_name='Demand_pp_energy', float_format='%.3f')
# writer.save()