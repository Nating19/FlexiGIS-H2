"""
Created on 5/01/2024

@author: sns51

"""

import pandas as pd
import numpy as np
import pvlib
from pvlib.pvsystem import PVSystem
from pvlib.location import Location
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS
import matplotlib.pyplot as plt
import pickle
import logging

# create a log file
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
                    filename="../code/log/pv_modelchain.log",
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

# set pv panel specific data
pv_panel = 'Advent_Solar_Ventura_210___2008_'
inverter_type = 'ABB__MICRO_0_25_I_OUTD_US_208__208V_'

#########################################################################


# set location to case study
location = Location(latitude=latitude, longitude=longitude, tz=target_time_zone, altitude=altitude, name=city)

# load module and inverter parameters from database
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

sandia_module = sandia_modules[pv_panel]
cec_inverter = cec_inverters[inverter_type]

# set temperature model
temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'] 

# set up system parameters
system = PVSystem(surface_tilt=20, surface_azimuth=200, #TODO adjust surface tilt and surface azamuth
                  module_parameters=sandia_module,
                  inverter_parameters=cec_inverter,
                  temperature_model_parameters=temperature_model_parameters)

# get feedin parameters
module_area = system.arrays[0].module_parameters.Area

# peak power in kW for ac
pv_system_peak_power = min(system.arrays[0].module_parameters.Impo
    *system.arrays[0].module_parameters.Vmpo
    *system.arrays[0].strings
    *system.arrays[0].modules_per_string,
    system.inverter_parameters.Paco)

pv_parameter = [pv_system_peak_power, module_area]

# run model
mc = ModelChain(system, location)

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

# create hourly average of irradiance data
tmy_daily_mean=tmy.groupby(tmy.index.hour).mean()

# create plot
fig_size = (16, 9)
tmy_daily_mean['dhi'].plot(style='blue', figsize=fig_size, grid=True) # TODO decide on what day to show
tmy_daily_mean['ghi'].plot(style='grey', figsize=fig_size, grid=True)
tmy_daily_mean['dni'].plot(style='green', figsize=fig_size, grid=True)
plt.xlabel('Time (hr)')
plt.ylabel('Hourly irradiance (W/m^2)')
plt.title(f'Hourly average DNI, DHI, and GHI of solar irradiance for {city} (W/m^2)' if district == 'all' else f'Hourly average DNI, DHI, and GHI of solar irradiance for {city}, {district} (W/m^2)')
plt.legend(['dhi', 'ghi', 'dni'], loc='upper left')
plt.savefig(output_destination+f"tmy_hourly_irradiance_{city}_{district}.png", dpi=300)
plt.show()
logging.info("Generate tmy irradiance plot")

# combine irradiance data with our model chain
weather = tmy
mc.run_model(weather)

# produce ac output (energy yield in Watts behind the inverter) of our pv system
pv_output = mc.results.ac
where_nan = np.isnan(pv_output)
pv_output[where_nan] = 0
pv_output[pv_output < 0] = 0

# plot the ac power output of one day
fig_size = (16, 9)
pv_output[pv_output.index.day_of_year==1].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('Power Output (W)')
plt.title(f'Ac power output of pv system for {city}' if district == 'all' else f'Ac power output of pv system for {city}, {district}')
plt.savefig(output_destination+f"ac_day_{city}_{district}.png", dpi=300)
plt.show()
logging.info("Generate day ac plot")

# create plot of hourly average ac power output
fig_size = (16, 9)
pv_output.groupby(pv_output.index.hour).mean().plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('Power Output (W)')
plt.title(f'Daily average ac power output of pv system for {city}' if district == 'all' else f'Daily average ac power output of pv system for {city}, {district}')
plt.savefig(output_destination+f"ac_daily_mean_{city}_{district}.png", dpi=300)
plt.show()
logging.info("Generate daily average ac plot")

# resample data for a monthly sum of energy yield in W
monthly_ac = pv_output.resample('M').sum()

# Plot the monthly sum of ac power output (energy yield in kW)
fig_size = (16, 9)
(pv_output.resample('M').sum()/1000).plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time (months)')
plt.ylabel('Power Output (kW)')
plt.title(f'Monthly sum of ac power output of pv system for {city}' if district == 'all' else f'Monthly sum of ac power output of pv system for {city}, {district}')
plt.savefig(output_destination+f"ac_monthly_sum_{city}_{district}.png", dpi=300)
plt.show()
logging.info("Generate monthly ac plot")

pvpower = pv_output.to_frame().rename(columns={0: "pv"})
pvpower = pvpower.rename_axis('time')
pvpower.to_csv(input_destination_1+f'pv_power_{city}_{district}.csv')

# feedin parameter
feedin_parameter = pv_parameter

with open(input_destination_1+'fp', 'wb') as fp:
        pickle.dump(feedin_parameter, fp)
print('Info: Feedin pv time-series done!')
logging.info("feedin pv timeseries parameters successfully stored as pickle file.")