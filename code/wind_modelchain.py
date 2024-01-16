"""
Created on 16/01/2024

@author: sns51

"""
# TODO integrate windpowerlib and create and safe wind power time series with the following code windpower.to_csv(input_destination_1+f'wind_power_{city}_{district}.csv')!!!!!
# TODO check if the tmy generator delivers the necessary parameters to generate the windpower time series in windpowerlib. if not, we need to take the previously produced wind_data.csv file
# TODO create feedin parameter for wind, see norminal_power_wind = wind_turbine.nominal_power


import pandas as pd
import numpy as np
import logging
import pickle
import os
from pvlib.location import Location
import pvlib
from feedinlib import WindPowerPlant

# create a log file
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
                    filename="../code/log/wind_modelchain.log",
                    level=logging.DEBUG)

input_destination_1 = "../data/01_raw_input_data/"
input_destination_2 = "../data/02_urban_output_data/"
output_destination = "../data/04_Visualisation/"


########################################################################
#
# Define input parameters
#
########################################################################

# set location
latitude = -43.53
longitude = 172.63
altitude = 20
# set target time zone, check following page https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
target_time_zone = 'Pacific/Auckland'
time_zone = 'UTC'   # this is the time zone the data is in when downloaded
# set city and district name. If all of the city is modelled set district to 'all'
city = 'Christchurch'
district = 'all'

# set turbine specific data
turbine_name = 'E-101/3050'
hub_height = int(135)

#########################################################################
wind_data = 'wind_data.csv'

# set location to case study
location = Location(latitude=latitude, longitude=longitude, tz=target_time_zone, altitude=altitude, name=city)


# WEATHER / IRRADIANCE DATA - can be either calculated with the clear sky model from pvlib or a typical meteorological year can be downloaded or you can supply your own irradiance data
tmy, years, location_data, units = pvlib.iotools.get_pvgis_tmy(latitude=latitude, longitude=longitude, 
                                                               outputformat='csv', usehorizon=True, userhorizon=None,
                                                               startyear='2005', endyear='2020',                                    # TODO make this a variable
                                                               map_variables=True, url='https://re.jrc.ec.europa.eu/api/v5_2/', 
                                                               timeout=30)
# convert time series into correct time zone
tmy.index = tmy.index.tz_convert(target_time_zone)
# fix  mismatch of PVGIS TMY Time zone via timestep correction
tmy['hour'] = tmy.index.hour
tmy['day_of_year'] = tmy.index.dayofyear
tmy = tmy.sort_values(by=['day_of_year','hour']).drop(['hour', 'day_of_year'], axis=1)

# assign random year to time series to get rid of incontinues year stamps
tmy.index = pd.date_range(start='2023-01-01 00:00',end='2023-12-31 23:00',freq='h', tz=target_time_zone)
tmy.to_csv(input_destination_1+'tmy.csv')


# USE THE FOLLOWING LINE ONLY IF TMY GENERATOR DOES NOT PRODUCE REQUIRED WIND PARAMETERS
# read multi-index wind data
wind_data = pd.read_csv(input_destination_1+wind_data, index_col=[0], header=[0, 1],
                        date_parser=lambda idx: pd.to_datetime(idx, utc=True))




# feedin parameter
norminal_power_wind = wind_turbine.nominal_power

# Get pv parameters from pickle file
with open(os.path.join(input_destination_1, 'fp'), 'rb') as fp:
    feedin_parameter = pickle.load(fp)
pv_system_peak_power = feedin_parameter[0]
module_area = feedin_parameter[1]

pv_parameter = [pv_system_peak_power, module_area]
pv_parameter.append(norminal_power_wind)
feedin_parameter = pv_parameter

with open(os.path.join(input_destination_1, 'fp'), 'wb') as fp:
        pickle.dump(feedin_parameter, fp)
print('Info: Feedin time-series done!')
logging.info("feedin timeseries parameter successfully stored as pickle file.")

######################################################
#
# Previously used code with feedin lib THAT NEEDS TO BE REPLACED WITH WINDPOWERLIB
#
######################################################

"""Generate windpower feedin time-series."""
    # The available in turbine types and specification can found in the oemof database.
    # "https://github.com/wind-python/windpowerlib/blob/dev/windpowerlib/oedb/turbine_data.csv"

turbine_spec = {
    'turbine_type': turbine_name,
    'hub_height': hub_height
}
wind_turbine = WindPowerPlant(**turbine_spec)

# read multi-index wind data
wind_data = pd.read_csv(input_destination_1+wind_data, index_col=[0], header=[0, 1],
                        date_parser=lambda idx: pd.to_datetime(idx, utc=True))
# convert multi-index data frame columns levels to integer
wind_data.columns = wind_data.columns.set_levels(wind_data.columns.levels[1].astype(int), level=1)

feedin_wind = wind_turbine.feedin(weather=wind_data) # TODO or wind_turbine.feedin(weather=wind_data, scaling="nominal_power") ??????

windpower = feedin_wind.to_frame().rename(columns={"feedin_power_plant": "wind"})
windpower.to_csv(input_destination_1+"wind_power.csv")
logging.info("Wind feedin timeseries generated.")