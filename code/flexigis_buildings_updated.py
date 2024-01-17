import osmium
from shapely.geometry import Polygon
from pyproj import Transformer 

pbf_file_path = "/home/stella/FlexiGIS-H2/data/01_raw_input_data/02-UrbanInfrastructure.osm.pbf"

class UrbanHandler(osmium.SimpleHandler):
    def __init__(self):
        super(UrbanHandler, self).__init__()
        self.data = []  # set an empty list where content can be appended to
        self.nodes = []
    def way(self, w):
        try:
            nodes_data = [(node.lon, node.lat) for node in w.nodes]
            #print(f"works for way {w.id} with nodes: {w.nodes}")
            # Check if there are enough nodes to form a polygon
            if len(nodes_data) >= 3:
                # Ensure that the first and last coordinates are the same to close the polygon
                if nodes_data[0] != nodes_data[-1]:
                    nodes_data.append(nodes_data[0])

                # Create a Shapely Polygon                                  # TODO not sure if this is in the correct CRS to calculate the area
                polygon = Polygon(nodes_data)
                area = polygon.area
                # Append the polygon to the data list
                self.data.append(area)
                self.nodes.append(nodes_data)
            #if w.id == 1170428557:
            #    print(f"Works for way {w.id} with nodes: {w.nodes}")
            #    print(f"Processing way {w.id}:")
            #    for tag in w.tags:
            #        print(f"  {tag.k}: {tag.v}")
            #    for node in w.nodes:
            #        print(f"    Node ID: {node}")
                    #print(f"    Node ID: {node.ref}, Latitude: {node.lat}, Longitude: {node.lon}")
        except osmium.InvalidLocationError:
            print(f"Invalid location for way {w.id} with nodes: {w.nodes}")
            #print(f"Processing way {w.id}:")
            #for tag in w.tags:
            #    print(f"  {tag.k}: {tag.v}")
            #for node in w.nodes:
            #    print(f"    Node ID: {node}")
                #print(f"    Node ID: {node.ref}, Latitude: {node.lat}, Longitude: {node.lon}")
            #print(f"Node IDs and coordinates: {[(node.lon, node.lat) for node in w.nodes]}")
            #print(f"Tags: {w.tags}")
            #if w.id == 1170428559:
            #    print(f"Processing way {w.id}:")
            #    for tag in w.tags:
            #        print(f"  {tag.k}: {tag.v}")
            #    for node in w.nodes:
            #        print(f"    Node ID: {node}")
                    #print(f"    Node ID: {node.ref}, Latitude: {node.lat}, Longitude: {node.lon}")


h = UrbanHandler()
h.apply_file(pbf_file_path, locations=True)

print(h.data)


class UrbanHandler(osmium.SimpleHandler):
    def __init__(self):
        super(UrbanHandler, self).__init__()
        self.data = [] # set empty list, where content can be append to

    def way(self, w):
#        if w.tags.get('landuse') == 'residential' and 'name' in w.tags:
        nodes_data = [(node.lon, node.lat) for node in w.nodes]
        #if len(nodes_data) >= 3:
                # Ensure that the first and last coordinates are the same to close the polygon
            #if nodes_data[0] != nodes_data[-1]:
                #nodes_data.append(nodes_data[0])
                    #polygon = Polygon(nodes_data).exterior.xy
                    #polygon = Polygon(nodes_data[0])
                    #self.data2.append(polygon)
        self.data.append(nodes_data)
        # Create a Shapely Polygon
        
        
#            self.data.append(w.tags['name'])
        
h = UrbanHandler()
h.apply_file(pbf_file_path, locations=True)

print(sorted(h.data))



        def way(self, w):
        # Check if the way has building or landuse tags
        if "building" in w.tags or "landuse" in w.tags:
            result = self.area_and_polygon(w)
            if result:
                self.data.append(result)



class CounterHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.num_nodes = 0

    def node(self, n):
        self.num_nodes += 1
h = CounterHandler()
h.apply_file(pbf_file_path)
print("Number of nodes: %d" % h.num_nodes)

import osmium
import shapely.wkb as wkblib

pbf_file_path = "/home/stella/FlexiGIS-H2/data/01_raw_input_data/02-UrbanInfrastructure.osm.pbf"

# A global factory that creates WKB from a osmium geometry
wkbfab = osmium.geom.WKBFactory()

class WayLenHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.total = 0

    def way(self, w):
        wkb = wkbfab.create_linestring(w)
        line = wkblib.loads(wkb, hex=True)
        # Length is computed in WGS84 projection, which is practically meaningless.
        # Lets pretend we didn't notice, it is an example after all.
        self.total += line.length

h = WayLenHandler()
h.apply_file(pbf_file_path, locations=True)
print("Total length: %f" % h.total)








import osmium
import pandas as pd
from shapely.geometry import Polygon
from pyproj import Transformer                                         #NEW

transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")

class OSMHandler(osmium.SimpleHandler):
    def __init__(self):
        super(OSMHandler, self).__init__()
        self.data = []
        self.ways_building = "building"
        self.ways_landuse = "landuse"

    def area_and_polygon(self, way):
        try:

            # Convert the way's geometry to a list of coordinate tuples
            nodes_data = [(node.lon, node.lat) for node in way.nodes]

            # Check if there are enough nodes to form a polygon
            if len(nodes_data) >= 3:
                # Ensure that the first and last coordinates are the same to close the polygon
                if nodes_data[0] != nodes_data[-1]:
                    nodes_data.append(nodes_data[0])
                
                

                transformed_coordinates = []
                for pt in transformer.itransform(nodes_data):
                    transformed = '{:.3f} {:.3f}'.format(*pt)
                    transformed_coordinates.append(transformed)

                # Create a Shapely Polygon
#                polygon = Polygon(nodes_data).exterior.xy

#                transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")
#                transformed_polygon = transformer.transform(polygon)

                # Create a Shapely Polygon
                polygon = Polygon(transformed_coordinates)

                # Calculate the area of the polygon
                area = polygon.area

                # Extract building and landuse tags
                building = way.tags.get(self.ways_building, None)
                landuse = way.tags.get(self.ways_landuse, None)

                # Return the OSM ID, area, and polygon as a tuple
                return way.id, building, landuse, area, polygon.wkt

            else:
                print(f"Error processing way {way.id}: Not enough nodes to form a polygon")
                return None

        except Exception as e:
            print(f"Error processing way {way.id}: {e}")
            return None

    def way(self, w):
        # Check if the way has building or landuse tags
        if "building" in w.tags or "landuse" in w.tags:
            result = self.area_and_polygon(w)
            if result:
                self.data.append(result)

def process_osm_pbf(pbf_file):
    handler = OSMHandler()
    handler.apply_file(pbf_file, locations=True)

    # Create a DataFrame from the collected data
    df = pd.DataFrame(handler.data, columns=["osm_id", "building", "landuse", "area", "polygon"])

    return df

# Example usage:
pbf_file_path = "/home/stella/FlexiGIS-H2/data/01_raw_input_data/02-UrbanInfrastructure.osm.pbf"
osm3_df = process_osm_pbf(pbf_file_path)