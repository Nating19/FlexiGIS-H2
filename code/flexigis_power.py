
"""
Created on 19/01/2024

@author: sns51

# minor lines are distribution lines
# lines are transmission lines

"""

import osmium
import pandas as pd
from shapely.geometry import LineString
from shapely import wkt
from geopandas import GeoDataFrame

#######################################################################################################
city='Karlsruhe'

#######################################################################################################

pbf_file_path = "../data/01_raw_input_data/"+city+"/"+"02-UrbanInfrastructure.osm.pbf"
main_destination = "../data/02_urban_output_data/"+city+"/"

class UrbanHandler(osmium.SimpleHandler):
    """Get landuse and building data from oms.pbf file."""
    def __init__(self):
        super(UrbanHandler, self).__init__()
        self.nodes_data =[]
        self.osm_id = []
        self.voltage = []
        self.power = []
        self.ways_power = 'power'
        self.location = []
        self.circuits = []
        self.line = []
        self.generator = []
        self.transformer =[]
        self.compensator = []
        self.geometry = []

    def way(self, w):
        if "power" in w.tags:
            print(f"Processing way {w.id} with nodes: {w.nodes} and tags:{w.tags}")
            try:
                nodes_data = [(node.lon, node.lat) for node in w.nodes]
                self.nodes_data.append(nodes_data)

                if len(nodes_data) >= 2:  # Changed to 2 as LineString requires at least 2 points
    # Create a Shapely LineString
                    linestring = LineString(nodes_data)
                    line = linestring.wkt

                    # Append the LineString to the data list
                    self.geometry.append(line)
                
                    osm_id = w.id
                    self.osm_id.append(osm_id)

                    power = w.tags.get(self.ways_power, None)
                    self.power.append(power)

                    voltage = w.tags.get('voltage', None)
                    self.voltage.append(voltage)

                    location = w.tags.get('location', None)
                    self.location.append(location)

                    circuits = w.tags.get('circuits', None)
                    self.circuits.append(circuits)

                    compensator = w.tags.get('compensator', None)
                    self.compensator.append(compensator)

                    generator = w.tags.get('generator', None)
                    self.generator.append(generator)

                    transformer = w.tags.get('transformer', None)
                    self.transformer.append(transformer)

                    line = w.tags.get('line', None)
                    self.line.append(line)
                
            except osmium.InvalidLocationError:
                print(f"Invalid location for way {w.id} with nodes: {w.nodes}")

u = UrbanHandler()
u.apply_file(pbf_file_path, locations=True)

osmrows = [u.osm_id, u.nodes_data, u.power, u.voltage, u.location, u.circuits, u.line, u.transformer, u.generator, u.compensator, u.geometry]
urban_df = pd.DataFrame(osmrows).T
urban_df.columns =["osm_id", "nodes", "power","voltage", "location", "circuits", "line", "transformer", "generator","compensator", "geometry"] 

urban_df = urban_df.dropna(subset=['geometry'])
urban_df['geometry'] = urban_df['geometry'].apply(wkt.loads)
urban_df = urban_df.drop(columns=['nodes'])
urban_df = GeoDataFrame(urban_df, geometry='geometry')
urban_df.crs = 'EPSG:4326'
urban_df = urban_df.to_crs('EPSG:3857')


urban_df.to_file(main_destination+"power", driver='ESRI Shapefile')


