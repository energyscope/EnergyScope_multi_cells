"""
Module with usefull functions for geographic analysis and plots

Author: Paolo Thiran
"""

from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from haversine import haversine


def make_bbox(long0, lat0, long1, lat1):
    """Make polygon from bbox coordinates https://stackoverflow.com/a/68741143/18253502
       /!\ all coordinates should be in the same projection

    Parameters
    ----------
    long0: float
        longitude of coordinate  0
    lat0: float
        latitude of coordinate 0
    long1: float
        longitude of coordinate 1
    lat1: float
        latitude of coordinate 1

    Returns
    -------
    A shapely.geometry.polygon from bbox coordinates

    """
    return Polygon([[long0, lat0],
                    [long1,lat0],
                    [long1,lat1],
                    [long0, lat1]])


def get_lat_lon(geo_ser: gpd.GeoSeries, centroid_id: str = 'centroid') -> tuple:
    """Get the latitude and longitude of the centroid of the GeoSeries

    Parameters
    ----------
    geo_ser: GeoSeries
        GeoSeries with centroid
    centroid_id: str, default='centroid'
        Name of the centroid index in the GeoSeries

    Returns
    -------
    (lat, lon): (float, float)
        The latitude and longitude of the cendroid
    """

    geo_ser = geo_ser.to_crs(4326)
    (lat, lon) = (geo_ser.centroid.y.values[0], geo_ser.centroid.x.values[0])
    return lat, lon


def dist_regions(gdf: gpd.GeoDataFrame, r1: str, r2: str,
                 id_col: str = 'id', centroid_col: str = 'centroid') -> float:
    """Computes the distance between the centroids of region r1 and region r2

    Parameters
    ----------
    gdf: GeoDataFrame
        GeoDataFrame containing the data of centroid location for regions r1 and r2
    r1: str
        ID of the region r1
    r2: str
        ID of the region r2
    id_col: str
        Name of the ID column in the gdf
    centroid_col: str
        Name of the centroid column in the gdf

    Returns
    -------
    dist: float
        Distance in kilometers from the centroid region r1 to the centroid of region r2

    """
    # checking crs and reprojecting if not the right one
    if gdf.loc[:, centroid_col].crs.srs != 'EPSG:3035':
        gdf.loc[:, centroid_col] = gdf.loc[:, centroid_col].to_crs(3035)

    coord1 = get_lat_lon(gdf.loc[gdf[id_col] == r1, centroid_col])
    coord2 = get_lat_lon(gdf.loc[gdf[id_col] == r2, centroid_col])
    dist = haversine(coord1, coord2)
    return dist

def create_gdf_eu(eu_country_code: list, overlay: bool = True) -> gpd.GeoDataFrame:
    """Creates a GeoDataFrame with the country code and geometry of the countries specified in eu_country_code list

    Parameters
    ----------
    eu_country_code:  list
        List of the 2 letter ISO-3166 Alpha-2 country code to select
    overlay: bool, default=True
        Whether to overlay the with a box to get rid of overseas territories

    Returns
    -------
    gdf : GeoDataFrame
        GeoDataFrame with the country code and geometry of the countries specified
    """
    # define path for data sources
    project_path = Path(__file__).parents[2]
    ex_data_path = project_path / 'Data' / 'exogenous_data'

    # convert to eurostat codes
    eu_country_code_eurostat = ['UK' if i=='GB' else 'EL' if i=='GR' else i for i in eu_country_code]

    # read geographical data
    eurostat_df = gpd.read_file(ex_data_path / 'gis' / 'NUTS_RG_20M_2021_3035.geojson')

    # select eu countries
    gdf = eurostat_df.loc[(eurostat_df['LEVL_CODE'] == 0)
                                   & (eurostat_df['id'].isin(eu_country_code_eurostat))].sort_values(by='id')
    gdf = gdf.loc[:, ['id', 'geometry']]


    # adding geographical data for BA and XK
    if ('BA' in eu_country_code) or ('XK' in eu_country_code):
        world_df = gpd.read_file(
            ex_data_path / 'gis' / 'ne_10m_admin_0_countries' / 'ne_10m_admin_0_countries.shp')
    if 'BA' in eu_country_code:
        geo_ba = world_df.loc[world_df['ADMIN'] == 'Bosnia and Herzegovina', ['geometry']]
        geo_ba['id'] = 'BA'
        geo_ba = geo_ba.to_crs(3035)
        gdf = pd.concat([gdf, geo_ba], axis=0).sort_values(by='id').reset_index(drop=True)
    if 'XK' in eu_country_code:
        geo_xk = world_df.loc[world_df['ADMIN'] == 'Kosovo', ['geometry']]
        geo_xk['id'] = 'XK'
        geo_xk = geo_xk.to_crs(3035)
        gdf = pd.concat([gdf, geo_xk], axis=0).sort_values(by='id').reset_index(drop=True)

    # renaming in ISO-3166 Alpha-2
    if 'UK' in eu_country_code_eurostat:
        gdf.loc[gdf['id'] == 'UK', 'id'] = 'GB'
    if 'EL' in eu_country_code_eurostat:
        gdf.loc[gdf['id'] == 'EL', 'id'] = 'GR'

    if overlay:
        # Coords covering Europe found at https://epsg.io/3035 (in EPSG 3035)
        bbox = make_bbox(1896628.62, 1095703.18, 7104179.2, 5582401.15)

        # Convert to gdf
        bbox_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:3035', geometry=[bbox])


        # Use bbox as clipping border for Europe
        gdf = gdf.overlay(bbox_gdf, how="intersection")

    return gdf
