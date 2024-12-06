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
city='Karlsruhe'

# Supply own building shapefile
own_input = False    # True for New Zealand, false for Germany
shapefile_path = '../data/01_raw_input_data/buildings/'+city+'/nz-building-outlines.shp'

#######################################################################################################

pbf_file_path = "../data/01_raw_input_data/"+city+"/"+"02-UrbanInfrastructure.osm.pbf"
main_destination = "../data/02_urban_output_data/"+city+"/"

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
w = w[w['geometry'].geom_type == 'Polygon']
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




import osmium

import pandas as pd

from shapely.geometry import Polygon, LineString

import geopandas as gpd

from geopandas import GeoDataFrame

 

class UrbanHandler(osmium.SimpleHandler):

    def __init__(self):

        osmium.SimpleHandler.__init__(self)

        self.buildings = []

        self.landuse = []

        self.roads = []

 

    def area(self, a):

            if 'building' in a.tags or 'landuse' in a.tags:

                try:

                    outer_ring = list(a.outer_rings())[0]

                    polygon_coords = [(node.lon, node.lat) for node in outer_ring]

                    if 'building' in a.tags:

                        self.buildings.append([

                            a.id, a.tags.get('building'), Polygon(polygon_coords)

                        ])

                    elif 'landuse' in a.tags:

                        self.landuse.append([

                            a.id, a.tags.get('landuse'), Polygon(polygon_coords)

                        ])

                except Exception as e:

                    print(f"Error processing area with ID {a.id}: {e}")

    def way(self, w):

        if "highway" in w.tags:

            try:

                nodes = [(node.lon, node.lat) for node in w.nodes if node.location.valid()]

                if len(nodes) >= 2:

                    linestring = LineString(nodes)

                    self.roads.append({

                        'osm_id': w.id,

                        'highway': w.tags['highway'],

                        'length': linestring.length * 111139,  # Convert degrees to meters approximately

                        'geometry': linestring

                    })

            except Exception as e:

                print(f"Error processing road with ID {w.id}: {e}")

 

def load_data(pbf_path):

    handler = UrbanHandler()

    handler.apply_file(pbf_path)

    buildings_df = pd.DataFrame(handler.buildings, columns=['osm_id', 'building', 'geometry'])

    landuse_df = pd.DataFrame(handler.landuse, columns=['osm_id', 'landuse', 'geometry'])

    roads_df = pd.DataFrame(handler.roads)

    return buildings_df, landuse_df, roads_df

 

def create_geodataframes(buildings_df, landuse_df, roads_df):

    # Create GeoDataFrame for buildings, including only 'osm_id' and 'building'

    buildings_gdf = GeoDataFrame(buildings_df, columns=['osm_id', 'building', 'geometry'], geometry='geometry')

 

    # Create GeoDataFrame for land use, including only 'osm_id' and 'landuse'

    landuse_gdf = GeoDataFrame(landuse_df, columns=['osm_id', 'landuse', 'geometry'], geometry='geometry')

 

    # Create GeoDataFrame for roads, including 'osm_id', 'highway', 'length', and 'geometry'

    if not roads_df.empty:

        roads_gdf = GeoDataFrame(roads_df, geometry='geometry')

    else:

        roads_gdf = GeoDataFrame(columns=['osm_id', 'highway', 'length', 'geometry'])

 

    return buildings_gdf, landuse_gdf, roads_gdf

 

def classify_landuse_and_buildings(gdf, feature_type):

    # Mappings for classification

    mappings = {

        'landuse': {

            'farmland': 'agricultural',

            'farmyard': 'agricultural',

            'vineyard': 'agricultural',

            'education': 'educational',

            'retail': 'commercial',

            'industrial': 'industrial',

            'residential': 'residential'

        },

        'building': {

            'warehouse': 'industrial',

            'vineyard': 'agricultural',

            'community_center': 'institutional',

            'hospital': 'institutional',

            'government': 'institutional',

            'public': 'institutional',

            'fire_station': 'institutional',

            'apartments': 'residential',

            'house': 'residential',

            'cabin': 'residential',

            'semidetached_house': 'residential',

            'dormitory': 'residential',

            'retail': 'commercial',

            'office': 'commercial',

            'motel': 'commercial',

            'hotel': 'commercial',

            'hostel': 'commercial',

            'kindergarten': 'educational',

            'school': 'educational',

            'university': 'educational',

            'class_room': 'educational',

            'farm_auxiliary': 'agricultural',

            'garage': 'commercial',

            'detached': 'residential',

            'garages': 'commercial',

            'semidetached_house': 'residential',

            'carport': 'commercial',

            'terrace': 'residential',

            'outbuilding': 'residential',

            'shed': 'residential',

            'barn': 'agricultural',

            'container': 'commercial',

            'storage': 'commercial'

        }

    }

 

    default_classifications = ['residential', 'commercial', 'agricultural', 'educational', 'institutional', 'industrial', 'other']

 

    # Apply mappings

    if feature_type in mappings:

        gdf[feature_type] = gdf[feature_type].map(mappings[feature_type]).fillna('other')

 

    # Ensure default classifications for any unclassified types

    if feature_type == 'building':

        gdf.loc[~gdf['building'].isin(default_classifications), 'building'] = 'other'

    elif feature_type == 'landuse':

        gdf.loc[~gdf['landuse'].isin(default_classifications), 'landuse'] = 'other'


def save_data(gdf, feature_type, destination):

    if not gdf.empty:

        file_path = f"{destination}{feature_type}.shp"

        gdf.to_file(file_path)

        gdf.to_csv(f"{destination}{feature_type}.csv", encoding="utf8")

        print(f"{feature_type.capitalize()} shapefiles and CSV saved successfully at {file_path}")


if __name__ == "__main__":

    pbf_file_path = "../data/01_raw_input_data/02-UrbanInfrastructure.osm.pbf" # here you should mentioned your pbf file path

    main_destination = "../data/02_urban_output_data/Christchurch_new/" # Here is just the name of your folder where you want to let your results

   

    # Load data from PBF file

    buildings_df, landuse_df, roads_df = load_data(pbf_file_path)

   

    # Create separate GeoDataFrames for buildings, land use, and roads

    buildings_gdf, landuse_gdf, roads_gdf = create_geodataframes(buildings_df, landuse_df, roads_df)

   

    # Classify buildings and land use

    classify_landuse_and_buildings(buildings_gdf, 'building')

    classify_landuse_and_buildings(landuse_gdf, 'landuse')

   

    # Save GeoDataFrames to Shapefile

    save_data(buildings_gdf, 'buildings', main_destination)

    save_data(landuse_gdf, 'landuse', main_destination)

    save_data(roads_gdf, 'roads', main_destination)