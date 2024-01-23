"""
Created on 19/01/2024

@author: sns51

"""

import osmium
import pandas as pd
from shapely.geometry import Polygon
from shapely import wkt
import geopandas as gpd
from geopandas import GeoDataFrame

#######################################################################################################

# Supply own building shapefile
own_input = True
shapefile_path = '../data/01_raw_input_data/buildings/Christchurch/nz-building-outlines.shp'

#######################################################################################################

pbf_file_path = "../data/01_raw_input_data/02-UrbanInfrastructure.osm.pbf"
main_destination = "../data/02_urban_output_data/"

class UrbanHandler(osmium.SimpleHandler):
    """Get landuse and building data from oms.pbf file."""
    def __init__(self):
        super(UrbanHandler, self).__init__()
        self.landuse =[]
        self.building =[]  
        self.osm_id =[] 
        self.geometry =[] 
        self.ways_building = 'building'
        self.ways_landuse = 'landuse'

    def way(self, w):
        if "building" in w.tags or "landuse" in w.tags:
            try:
                nodes_data = [(node.lon, node.lat) for node in w.nodes]

                # Check if there are enough nodes to form a polygon
                if len(nodes_data) >= 3:
                    # Ensure that the first and last coordinates are the same to close the polygon
                    if nodes_data[0] != nodes_data[-1]:
                        nodes_data.append(nodes_data[0])
                    
                    print(f"Processing way {w.id}")

                    # Create a Shapely Polygon
                    polygon = Polygon(nodes_data)
                    poly = polygon.wkt
                    # Append the polygon to the data list
                    self.geometry.append(poly)

                    # Extract building and landuse tags
                    building = w.tags.get(self.ways_building, None)
                    landuse = w.tags.get(self.ways_landuse, None)

                    self.building.append(building)
                    self.landuse.append(landuse)

                    osm_id = w.id
                    self.osm_id.append(osm_id)

            except osmium.InvalidLocationError:
                print(f"Invalid location for way {w.id} with nodes: {w.nodes}")

u = UrbanHandler()
u.apply_file(pbf_file_path, locations=True)

osmrows = [u.osm_id, u.building, u.landuse, u.geometry]
urban_df = pd.DataFrame(osmrows).T
urban_df.columns =["osm_id", "building", "landuse", "geometry"] 
urban_df['geometry'] = urban_df['geometry'].apply(wkt.loads) # converts str into shapely geometry object
urban_df = GeoDataFrame(urban_df, geometry='geometry')
urban_df.crs = 'EPSG:4326'
urban_df = urban_df.to_crs('EPSG:3857')
urban_df['area'] = urban_df.geometry.area 

# Building data correction
"""Get building data."""
data_building = urban_df.drop(columns=["landuse"])
data_building = data_building.dropna().sort_values(by="building")

"""Get landuse data."""
# Landuse data correction
df_landuse = urban_df.drop(columns=["building"])
data_landuse = df_landuse.dropna().sort_values(by="landuse")

if own_input:

    # Read the shapefile and converts it into a GeoDataFrame
    gpd_buildings = gpd.read_file(shapefile_path)
    gpd_buildings = gpd_buildings[['building_i', 'suburb_loc', 'name', 'use', 'town_city', 'geometry']]
    gpd_buildings = gpd_buildings.rename(columns={'suburb_loc': 'suburb'})
    gpd_buildings = gpd_buildings.to_crs('EPSG:3857')

    res_intersects = gpd.overlay(gpd_buildings, data_landuse, how="intersection")
    rew = gpd.overlay(res_intersects, data_building, how="intersection", keep_geom_type=False)
    rew = rew.drop(columns=['name','town_city','suburb','area_1', 'area_2'])
    rew.loc[rew['building'] == 'yes', 'building'] = rew.loc[rew['building'] == 'yes','landuse']
    w=res_intersects.merge(rew, how="left", on='building_i')

    w.loc[w.building.isna(),'building']=w.loc[w.building.isna(),'landuse_x']
    w.loc[w['use_x'] == 'School','building'] = 'educational'
    w.loc[w['use_x'] == 'Hospital','building'] = 'institutional'
    w.loc[w['use_x'] == 'Supermarket','building'] = 'commercial'
    
    w = w.rename(columns={'geometry_x': 'geometry','building_i':'building_id'})
    w = w.drop(columns=["name", "use_x", "town_city", "use_y", "osm_id_1", "osm_id_2", "landuse_y","geometry_y", 'osm_id','landuse_x','area'])
    w['area'] = gpd.GeoSeries(w.geometry).area
        
else:
    w = gpd.overlay(data_building, data_landuse, how="intersection", keep_geom_type=False)
    w.loc[w['building'] == 'yes', 'building'] = w.loc[w['building'] == 'yes','landuse']
    w = w.drop(columns=["osm_id_2", "area_2",'landuse',])
    w = w.rename(columns={'osm_id_1': 'osm_1','area_1':'area'})

data_landuse.loc[data_landuse['landuse'].isin(['farmland', 'farmyard']),'landuse'] = 'agricultural'  
data_landuse.loc[data_landuse['landuse'] == 'education','landuse'] = 'educational'
data_landuse.loc[data_landuse['landuse'] == 'retail','landuse'] = 'commercial'
data_landuse.loc[data_landuse['landuse'] == 'vineyard','landuse'] = 'industrial'

data_landuse.to_file(main_destination+"landuse", driver='ESRI Shapefile')
data_landuse.to_csv(main_destination+"landuse.csv", encoding="utf8")

w.loc[w['building'].isin(['warehouse', 'vineyard']),'building'] = 'industrial'
w.loc[w['building'].isin(['community_center', 'hospital','government','public','fire_station']),'building'] = 'institutional'
w.loc[w['building'].isin(['apartments', 'house','cabin', 'semidetached_house','dormitory']),'building'] = 'residential'
w.loc[w['building'].isin(['retail', 'office', 'cabin', 'motel', 'hotel', 'hostel']),'building'] = 'commercial'
w.loc[w['building'].isin(['kindergarten', 'school', 'university', 'class_room']),'building'] = 'educational'
w.loc[w['building'].isin(['farmland', 'farmyard', 'farm_auxiliary']),'building'] = 'agricultural'
w.loc[~w['building'].isin(['residential', 'commercial', 'agricultural', 'educational', 'institutional', 'industrial']),'building'] = 'other'

w = gpd.GeoDataFrame(w, geometry='geometry')
w.to_file(main_destination+"buildings", driver='ESRI Shapefile')
w.to_csv(main_destination+"buildings.csv", encoding="utf8")

# residential
b_r = w.loc[w['building'] == 'residential']
b_r.to_file(main_destination+"residential", driver='ESRI Shapefile')

# industrial
b_i = w.loc[w['building'] == 'industrial']
b_r.to_file(main_destination+"industrial", driver='ESRI Shapefile')

# commercial
b_c = w.loc[w['building'] == 'commercial']
b_c.to_file(main_destination+"commercial", driver='ESRI Shapefile')

# agricultural
b_a = w.loc[w['building'] == 'agricultural']
b_a.to_file(main_destination+"agricultural", driver='ESRI Shapefile')

# educational
b_e = w.loc[w['building'] == 'educational']
b_e.to_file(main_destination+"educational", driver='ESRI Shapefile')

# institutional
b_inst = w.loc[w['building'] == 'institutional']
b_inst.to_file(main_destination+"institutional", driver='ESRI Shapefile')

# other
b_r = w.loc[w['building'] == 'other']
b_r.to_file(main_destination+"other", driver='ESRI Shapefile')