# -*- coding: utf-8 -*-
"""
This file defines a dictionary with global variables to be used in EnergyScope such as fuels, technologies, etc.
"""
import datetime

commons = {}

commons['logfile'] = str(datetime.datetime.now()).replace(':', '-').replace(' ', '_') + '.energyscope.log'

CSV_SEPARATOR = ';'
AMPL_SEPARATOR = '\t'

# defining 2 letter country codes and full country names
eu27_country_code = ['AT', 'BE', 'BG', 'CH', 'CZ',
                     'DE', 'DK', 'EE', 'ES', 'FI',
                     'FR', 'GB', 'GR', 'HR', 'HU',
                     'IE', 'IT', 'LT', 'LU', 'LV',
                     'NL', 'PL', 'PT', 'RO', 'SE',
                     'SI', 'SK']
eu27_full_names = ['Austria', 'Belgium', 'Bulgaria',  'Switzerland', 'Czech Republic',
                   'Germany', 'Denmark', 'Estonia', 'Spain', 'Finland',
                   'France', 'United Kingdom', 'Greece', 'Croatia', 'Hungary',
                   'Ireland', 'Italy', 'Lithuania', 'Luxembourg', 'Latvia',
                   'Netherlands', 'Poland', 'Portugal', 'Romania', 'Sweden',
                   'Slovenia', 'Slovakia']

full_2_code = dict(zip(eu27_full_names, eu27_country_code))
code_2_full = dict(zip(eu27_country_code, eu27_full_names))