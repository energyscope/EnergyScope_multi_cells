# -*- coding: utf-8 -*-
"""
Created on Mon May 22 12:38:09 2023

Used to generate extra-EU and intra-EU aviation passenger demand based on number of passenger
carried between countries avia_paexcc and avia_paincc from Eurostat and distance calculated via 
geopy. .csv file from eurostat should be modified to correspond to the format :
unit	tra_meas	partner	geo\time	<year analyzed (2019 for this case)>

@author: JulienJacquemin and Paolo Thiran
"""

import geopy.distance
from geopy.geocoders import Nominatim
import pandas as pd

# Countries of which we want to evaluate the aviation demand
country_code = ["AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "GR", "ES", "FI", "FR", 
 "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", 
 "SE", "SI", "SK", "UK"]

geolocator = Nominatim(user_agent="DistanceMatrix")

# functions to compute the aviation demand from estat data
def compute_pkm(row, lat_lon_dict):
    """ Compute the pkm of the row"""
    region = row['region']
    partner = row['partner']
    passengers = row['passengers']
    # compute distance of flight
    distance = geopy.distance.distance(lat_lon_dict[region], lat_lon_dict[partner]).km

    return distance * passengers

def compute_av_demand(estat_df):
    """ Computes the aviation demand in pkm for each region"""

    # computing pkm for each country
    pkm_df = estat_df.reset_index()

    # creating a dictionary of locations
    r_list = list(pkm_df['region'].unique())
    r_list.extend(pkm_df['partner'].unique())
    r_list = list(set(r_list))
    loc_dict = {r: geolocator.geocode({"country": r}) for r in r_list}
    lat_lon_dict = dict.fromkeys(r_list)
    for r, loc in loc_dict.items():
        if loc is None:
            print("Region is wrong : " + r)
            # Some partner country data code are not recognized so manual location is performed
        if r == "AN":
            lat_lon_dict[r] = (12.226079, -69.060087)
        elif r == "AW":
            lat_lon_dict[r] = (12.521110, -69.968338)
        elif r == "HK":
            lat_lon_dict[r] = (22.302711, 114.177216)
        elif r == "NC":
            lat_lon_dict[r] = (-21.123889, 165.846901)
        elif r == "PF":
            lat_lon_dict[r] = (-17.535000, -149.569595)
        elif r == "VI":
            lat_lon_dict[r] = (18.335765, -64.896335)
        elif r == "PS":
            lat_lon_dict[r] = (31.952162, 35.233154)
        else:
            lat_lon_dict[r] = (loc.latitude, loc.longitude)

    # computing distance and pkm for each row
    pkm_df['pkm'] = pkm_df.apply(compute_pkm, args=(lat_lon_dict,), axis=1)
    # summing over region
    pkm_df = pkm_df.set_index(['region', 'partner']).groupby('region').sum()
    # computing avg km of passengers
    pkm_df['avg_km'] = pkm_df['pkm'] / pkm_df['passengers']

    return pkm_df

"""
Intra-EU aviation
"""
# Open Eurostat data file, avia_paincc.tsv is for intra-EU aviation
# avia_paexcc.tsv is for extra-EU aviation.
# PAS_CRD_DEP is the data code related to departure of aircrafts.
estat_df = pd.read_csv("avia_paincc.tsv", keep_default_na=False,
                       index_col=[0, 2, 1], usecols=[1, 2, 3, 4], sep="\t").loc["PAS_CRD_DEP"]
# cleaning df
estat_df = estat_df.replace(to_replace=": ", value=0)
estat_df = estat_df.sort_index()
estat_df.index.names = ['region', 'partner']
estat_df.columns = ['passengers']
estat_df = estat_df.astype({'passengers': float})
estat_df = estat_df.drop(['EU27_2020', 'EU28', 'EU27_2007'], axis=0, level=1)\
    .drop(['EU27_2020', 'EU28', 'EU27_2007'], axis=0, level=0)

# comuting aviation demand
pkm_df_intra_eu = compute_av_demand(estat_df)


"""
Extra-EU aviation
"""
# Open Eurostat data file, avia_paincc.tsv is for intra-EU aviation
# avia_paexcc.tsv is for extra-EU aviation.
# PAS_CRD_DEP is the data code related to departure of aircrafts.
estat_df = pd.read_csv("avia_paexcc.tsv", keep_default_na=False,
                       index_col=[0, 2, 1], usecols=[1, 2, 3, 4], sep="\t").loc["PAS_CRD_DEP"]
# cleaning df
estat_df = estat_df.replace(to_replace=": ", value=0)
estat_df = estat_df.sort_index()
estat_df.index.names = ['region', 'partner']
estat_df.columns = ['passengers']
estat_df = estat_df.astype({'passengers': float})
# get rid of agg with more than 2 letters
estat_df = estat_df.loc[estat_df.index.get_level_values(level=0).str.len() == 2, :]
estat_df = estat_df.loc[estat_df.index.get_level_values(level=1).str.len() == 2, :]

# comuting aviation demand
pkm_df_extra_eu = compute_av_demand(estat_df)

"""
Grouping and saving
"""
gpkm_df_intra_eu = pkm_df_intra_eu.copy()
gpkm_df_intra_eu.loc[:, 'pkm'] *= 1e-9 # convert into Gpass and Gpkm
gpkm_df_intra_eu = gpkm_df_intra_eu.rename(columns={'passengers': 'Intra-EU aviation passengers [pass](Eurostat 2019)',
                                                    'pkm': 'Intra-EU aviation demand [Gpkm](Eurostat 2019)',
                                                    'avg_km': 'Intra-EU aviation average distance [km](Eurostat 2019)'})

gpkm_df_extra_eu = pkm_df_extra_eu.copy()
gpkm_df_extra_eu.loc[:, 'pkm'] *= 1e-9 # convert into Gpass and Gpkm
gpkm_df_extra_eu = gpkm_df_extra_eu.rename(columns={'passengers': 'Extra-EU aviation passengers [pass](Eurostat 2019)',
                                                    'pkm': 'Extra-EU aviation demand [Gpkm](Eurostat 2019)',
                                                    'avg_km': 'Extra-EU aviation average distance [km](Eurostat 2019)'})

av_dem_df = gpkm_df_intra_eu.merge(gpkm_df_extra_eu, left_index=True, right_index=True)
av_dem_df.to_csv('estat_aviation_2019.csv', sep=';')
