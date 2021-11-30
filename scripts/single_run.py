import os
from pathlib import Path

import esmc.preprocessing.preprocessing as prp

path = Path(__file__).parents[1]
# setting configuration
# for step1_in and step2_in #
countries = ['ES-PT', 'FR', 'IE-UK']  # countries list
data = countries.copy()  # data path (in same order as data path)
i = 0
for c in countries:
    data[i] = os.path.join(path,'Data/DATA_' + c + '.xlsx')
    i += 1
N_ts = 7  # number of timeseries with a WEIGHT defined (per country)
Nbr_TD = 12  # number of typical day
# for step2_in #
# name of timeseries in DATA.xlsx and corresponding name in ESTD data file
# for EUD timeseries
EUD_params = {'Electricity (%_elec)': 'param electricity_time_series :=',
              'Space Heating (%_sh)': 'param heating_time_series :=', 'Space Cooling': 'param cooling_time_series :=',
              'Passanger mobility (%_pass)': 'param mob_pass_time_series :=',
              'Freight mobility (%_freight)': 'param mob_freight_time_series :='}
# for resources timeseries that have only 1 tech linked to it
RES_params = {'PV': 'PV', 'Wind_offshore': 'WIND_OFFSHORE', 'Wind_onshore': 'WIND_ONSHORE'}
# for resources timeseries that have several techs linked to it
RES_mult_params = {'Tidal': ['TIDAL_STREAM', 'TIDAL_RANGE'], 'Hydro_dam': ['HYDRO_DAM'], 'Hydro_river': ['HYDRO_RIVER'],
                   'Solar': ['DHN_SOLAR', 'DEC_SOLAR', 'PT_COLLECTOR', 'ST_COLLECTOR', 'STIRLING_DISH']}

# path step1
step1_path = os.path.join(path,'esmc/preprocessing/step1')
log_step1 = os.path.join(step1_path, 'log_' + str(Nbr_TD) + '.txt')
# path step2
step2_path = os.path.join(path,'esmc/energy_model')
step2_out = os.path.join(step2_path, 'output')
log_step2 = os.path.join(step2_out, 'log.txt')
cplex_options_step1 = ['mipdisplay=5',
                       'mipinterval=1000',
                       'mipgap=1e-6']
cplex_options_step1_str = ' '.join(cplex_options_step1)

options_step1 = {'show_stats': 3,
                 'log_file': log_step1,
                 'times': 1,
                 'gentimes': 1,
                 'cplex_options': cplex_options_step1_str}
# all_cplex_options =  'baropt predual=-1 display=2' + ' endsol ' + str(os.path.join(step2_path, 'output_'+str(Nbr_TD)+'TD/solution.sol'))
# all_options_ampl =  {'show_stats': 3,
#                 'log_file': os.path.join(step2_path,'output_'+str(Nbr_TD)+'TD/log.txt'),
#                 'presolve': 200, 'times': 1, 'gentimes': 1,
#                 'cplex_options_timelimit': 64800,
#                 'cplex_options': 'baropt predual=-1 bardisplay=1 display=2'}
cplex_options = ['baropt',
                 'predual=-1',
                 'barstart=4',
                 'crossover=0'
                 'timelimit 64800',
                 'bardisplay=1',
                 'prestats=1',
                 'display=2']
cplex_options_str = ' '.join(cplex_options)
ampl_options = {'show_stats': 3,
                'log_file': log_step2,
                'presolve': 0,
                'times': 0,
                'gentimes': 0,
                'cplex_options': cplex_options_str}
# config of each step
step1_config = {'running': False,
                'printing_out': False,
                'printing_step2_in': False,
                'step1_path': step1_path,  # path to Step 1 directory
                'EUD_params': EUD_params,
                'RES_params': RES_params,
                'RES_mult_params': RES_mult_params,
                'N_ts': N_ts,
                'ampl_options_step1': options_step1
                }
step2_config = {'step2_path': step2_path,  # path to Step 2 directory
                'printing_data': False,    #TODO printing the data in ESMC_countries.dat and ESMC_indep.dat file for the optimisation problem
                'printing_inputs': True,  # printing sets, params and vars into json files
                'running': True,  # running step 2
                'printing_outputs': True,  # printing outputs of step 2
                'ampl_options': ampl_options
                }
# general config
config = {'case_study': 'test2',
          # Name of the case study. The outputs will be printed into : config['ES_path']+'\output_'+config['case_study']
          # general inputs
          'Nbr_TD': Nbr_TD,  # Number of typical days
          'Working_directory': os.getcwd(),
          'AMPL_path': 'C:/My_programs/ampl_mswin64',  # PATH to AMPL licence (to adapt by the user)
          'GWP_limit': 1e+7,  # [ktCO2-eq./year]	# Minimum GWP reduction for all regions together
          'countries': countries,
          'data_folders': data,  # Folders containing the csv data files
          'all_data': dict(),
          # Dictionnary with the dataframes containing all the data in the form : {'Demand': eud, 'Resources': resources, 'Technologies': technologies, 'End_uses_categories': end_uses_categories, 'Layers_in_out': layers_in_out, 'Storage_characteristics': storage_characteristics, 'Storage_eff_in': storage_eff_in, 'Storage_eff_out': storage_eff_out, 'Time_series': time_series}
          # step specific inputs
          'step1_config': step1_config,  # Configuration of the step 1 (only useful if run step 1)
          'step2_config': step2_config  # configuration of step 2
          }
ampl_models = prp.run_esmc(config)
ampl = ampl_models['step2']['ampl']
t = ampl_models['step2']['time']
sets = ampl_models['step2']['inputs']['sets']
parameters = ampl_models['step2']['inputs']['parameters']
variables = ampl_models['step2']['inputs']['variables']
