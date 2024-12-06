"""**Helper functions for FlexiGIS data abstraction**."""
import psycopg2
import optparse
import sys
import os
import pandas as pd
import geopandas as gpd
import glob
import numpy as np
from natsort import natsorted
from shapely import wkt
from geopandas import GeoDataFrame


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Helper functions flexigis_road
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def dbconn_from_args():
    """Parse database credentials as environmental variables.

    Get database connection from command-line arguments or
    environment ariables. Reuse environment variables from libpq/psql
    (see http://www.postgresql.org/docs/9.1/static/libpq-envars.html)
    """
    argv = sys.argv[1:]
    environ = os.environ
    parser = optparse.OptionParser()
    parser.add_option("-D", "--dbname", action="store", dest="dbname",
                      help="database name of the topology network")
    parser.add_option("-H", "--dbhost", action="store", dest="dbhost",
                      help="database host address of the topology network")
    parser.add_option("-P", "--dbport", action="store", dest="dbport",
                      help="database port of the topology network")
    parser.add_option("-U", "--dbuser", action="store", dest="dbuser",
                      help="database user name of the topology network")
    parser.add_option("-X", "--dbpwrd", action="store", dest="dbpwrd",
                      help="database user password of the topology network")

    (options, args) = parser.parse_args(argv)
    # Options have precedence over environment variables, which have
    # precedence over defaults.

    # NB: None (or null) host and port values are completely reasonable and
    # mean a local (unix domain socket) connection. This way postgresql can
    # be configured without network support, which is convenient and secure.
    dbhost = options.dbhost or environ.get('PGHOST')
    dbport = options.dbport or environ.get('PGPORT')
    # postgres is the default database role, and why not use it?
    dbuser = options.dbuser or environ.get('PGUSER', 'postgres')
    # A None password is also valid but it
    # implies the server must be configured to support either
    # 'trust' or 'ident' identification. For a local server this is convenient,
    # but it isn't secure for network installations. Review
    # man pg_hba.conf for the details.
    dbpwrd = options.dbpwrd
    dbname = options.dbname

    try:
        return psycopg2.connect(host=dbhost, port=dbport, user=dbuser,
                                password=dbpwrd, database=dbname)
    except psycopg2.Error as e:

        if len(argv) == 0 or len(args) == len(argv):
            parser.print_help()
        raise e


def compute_area(dataset, width):
    """Compute area for each line feature and return a dataframe object.

    :param DataFrame dataset: OSM planet data
    :param dict width: unique highway category as `key` and the width in meters
     as the `value`
    :return: dataframe containing an "area" attribute
    :rtype: DataFrame
    """
    #Area = []
    dataset['area'] = np.nan
    for key, value in width.items():
        dataset.loc[key,'area'] = dataset.loc[key]["length"]*value
        #Area.append(area)

    #if isinstance(Area[0], pd.Series) is True:
    #    Area = pd.concat(Area)
    #    dataset["area"] = Area.values
    #else:
    #    dataset["area"] = Area

    dataset_new = dataset.reset_index()
    return dataset_new


def data_to_file(dataset, name="name"):
    """Write a dataframe to a csv/shape file.

    :param DataFrame dataset: OSM planet data
    :param str name: file name of the output csv file (eg. `table_name`)
    """
    dataset_new = dataset["geometry"].str.split(";", n=1, expand=True)
    dataset["polygon"] = dataset_new[1]
    dataset = dataset.drop(columns=["geometry"])
    dataset = dataset.rename(columns={"polygon": "geometry"})
    dataset['geometry'] = dataset['geometry'].apply(wkt.loads)
    dataset = GeoDataFrame(dataset, geometry='geometry')
    # dataset.to_csv(name, encoding="utf-8")
    dataset.to_file(name, driver='ESRI Shapefile')

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# helper functions flexigis_optimize
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

def shape_legend(node, ax, handles, labels, reverse=False, **kwargs):
    """Plot legend manipulation. This code is copied from the oemof example script
    see link here: https://github.com/oemof/oemof-examples/tree/master/oemof_examples/oemof.solph/v0.3.x/plotting_examples
    """
    handels = handles
    labels = labels
    axes = ax
    parameter = {}

    new_labels = []
    for label in labels:
        label = label.replace('(', '')
        label = label.replace('), flow)', '')
        label = label.replace(node, '')
        label = label.replace(',', '')
        label = label.replace(' ', '')
        new_labels.append(label)
    labels = new_labels

    parameter['bbox_to_anchor'] = kwargs.get('bbox_to_anchor', (1, 0.5))
    parameter['loc'] = kwargs.get('loc', 'center left')
    parameter['ncol'] = kwargs.get('ncol', 1)
    plotshare = kwargs.get('plotshare', 0.9)

    if reverse:
        handels = handels.reverse()
        labels = labels.reverse()

    box = axes.get_position()
    axes.set_position([box.x0, box.y0, box.width * plotshare, box.height])

    parameter['handles'] = handels
    parameter['labels'] = labels
    axes.legend(**parameter)
    return axes





if __name__ == "__main__":
    print("This module provides helper functions only.")
