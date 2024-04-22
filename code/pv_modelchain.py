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

# set city and district name. If all of the city is modelled set district to 'all'
city = 'Christchurch'
district = 'all'

cities = pd.DataFrame(columns=['city',"latitude",'longitude','altitude','time_zone'])
cities = cities.append(pd.DataFrame([['Auckland',-36.848461,174.763336,float(196),'Pacific/Auckland']], columns=['city',"latitude",'longitude','altitude','time_zone']))
cities = cities.append(pd.DataFrame([['Christchurch', -43.53,172.63,float(20),'Pacific/Auckland']], columns=['city',"latitude",'longitude','altitude','time_zone']))
cities = cities.append(pd.DataFrame([['Oldenburg', 53.099,8.217,float(3),'Europe/Berlin']], columns=['city',"latitude",'longitude','altitude','time_zone']))
cities = cities.append(pd.DataFrame([['Karlsruhe', 49.006889,8.403653,float(115),'Europe/Berlin']], columns=['city',"latitude",'longitude','altitude','time_zone']))

# set location
latitude = cities.loc[cities['city'] == city, 'latitude'].values[0] # according to your folder order Christchurch: -43.53, Auckland: -36.848461, Oldenburg: 53.099, Karlsruhe: 49.006889
longitude = cities.loc[cities['city'] == city, 'longitude'].values[0] # according to your folder order Christchurch: 172.63, Auckland: 174.763336, Oldenburg: 8.217, Karlsruhe: 8.403653
altitude = cities.loc[cities['city'] == city, 'altitude'].values[0] # Adjust accordingly Christchurch: 20, Auckland: 196, Oldenburg: 3, Karlsruhe: 115
# set target time zone, check following page https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
target_time_zone = cities.loc[cities['city'] == city, 'time_zone'].values[0] # Germany: 'Europe/Berlin' / New Zealand: 'Pacific/Auckland'
time_zone = 'UTC'   # this is the time zone the data is in when downloaded


district = 'all'

# set pv panel specific data
#pv_panel = 'Advent_Solar_Ventura_210___2008_'
#inverter_type = 'ABB__MICRO_0_25_I_OUTD_US_208__208V_'
pv_panel = 'Jinko_Solar_Co___Ltd_JKM410M_72HL_V'
inverter_type = 'Altenergy_Power_System_Inc___YC500A__208V_' # Necessary in order to generate even in days with small irradiance. Efficiency of 94%. Could be better! 


#########################################################################


# set location to case study
location = Location(latitude=latitude, longitude=longitude, tz=target_time_zone, altitude=altitude, name=city)

# load module and inverter parameters from database
#sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sandia_modules = pvlib.pvsystem.retrieve_sam('CECMod')
cec_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')

sandia_module = sandia_modules[pv_panel]
cec_inverter = cec_inverters[inverter_type]

# set temperature model
temperature_model_parameters = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'] 

##################################
# In the southern hemisphere, the best direction for typical roof-mounted solar panels to face is north. The sun rises in the east 
# and sets in the west, so a north-facing solar panel will receive the maximum amount of sunlight it can, no matter what time of day it is.
# from: https://www.zenenergy.co.nz/blog/what-is-the-best-direction-for-solar-panels

# Zs: surface azimuth angle, the angle between the normal to the surface from true south, westward is designated as positive
# For a south-facing tilted surface in the Northern Hemisphere, Zs 0. Applies for cities in Germany.
# For a north-facing tilted surface in the Southern Hemisphere, Zs 180.  Applies for cities in New Zeland.
# from alogirou_Chapter2 page 63.

# Optimal Slope (surface tilt) for Chritschurch seems to be 41 (using PVGIS Tool), however the best behaviour obtained was for 20.


# set up system parameters
#system = PVSystem(surface_tilt=20, surface_azimuth=200, #TODO adjust surface tilt and surface azimuth
#                  module_parameters=sandia_module,
#                  inverter_parameters=cec_inverter,
#                  temperature_model_parameters=temperature_model_parameters)

system = PVSystem(surface_tilt=42, surface_azimuth=180, #  for realistic results use the optimized surface tilt suggested in PVGIS. As surface:azimuth 180° for Germany and New Zeland
                 module_parameters=sandia_module,
                 inverter_parameters=cec_inverter,
                 temperature_model_parameters=temperature_model_parameters,
                 albedo=0.25, surface_type=None, module=None,  #TODO albedo of 0.25 according to Bredemeier for Urban PV Systems
                 module_type='glass_polymer', 
                 inverter=None, 
                 racking_model='open_rack', 
                 losses_parameters=None)


# manually define Area parameters
panel_width = 1.002
panel_length = 2.008
module_area = panel_width*panel_length


# get feedin parameters
#module_area = system.arrays[0].module_parameters.Area

#manually define the I_mp and V_mp parameters parameters
Impo = 9.69 # data from the datasheet of the panel we want to implement-- previously system.arrays[0].module_parameters.Impo
Vmpo = 42.3 # data from the datasheet of the panel we want to implement-- previously system.arrays[0].module_parameters.Vmpo

# peak power in kW for ac
#pv_system_peak_power = min(system.arrays[0].module_parameters.Impo
#    *system.arrays[0].module_parameters.Vmpo
#    *system.arrays[0].strings
#    *system.arrays[0].modules_per_string,
#    system.inverter_parameters.Paco)

# peak power in kW for ac
pv_system_peak_power = min(Impo # previously called system.arrays[0].module_parameters.Impo
    *Vmpo# previously called system.arrays[0].module_parameters.Vmpo
    *system.arrays[0].strings
    *system.arrays[0].modules_per_string,
    system.inverter_parameters.Paco)

pv_parameter = [pv_system_peak_power, module_area]

# run model
mc = ModelChain(system, location, aoi_model="no_loss")

# WEATHER / IRRADIANCE DATA - can be either calculated with the clear sky model from pvlib or a typical meteorological year can be downloaded or you can supply your own irradiance data
tmy, years, location_data, units = pvlib.iotools.get_pvgis_tmy(latitude=latitude, longitude=longitude, 
                                                               outputformat='csv', usehorizon=True, userhorizon=None,
                                                               startyear='2005', endyear='2020',                                    # TODO make this a variable
                                                               map_variables=True, url='https://re.jrc.ec.europa.eu/api/v5_2/', 
                                                               timeout=30)

# print years of months comprised in tmy
for m in range(1, 13):
    unique_years = tmy[tmy.index.month == m].index.year.unique().values
    print(f"Month {m}: {unique_years}")

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

# Add to weather dataframe the column "precipitable_water" which will be requested by the mc 
# documentation https://pvlib-python.readthedocs.io/en/v0.10.3/reference/generated/pvlib.atmosphere.gueymard94_pw.html
weather["precipitable_water"] =  pvlib.atmosphere.gueymard94_pw(weather["temp_air"], weather["relative_humidity"]) 

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