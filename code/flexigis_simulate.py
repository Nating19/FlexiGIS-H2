"""
Created on 7/01/2024

@author: sns51

"""
# TODO create option what slp categories are actually available, for instance onlry residential ect
# TODO when importing the time series of solar and wind, they need to be converted into the correct time zone: tmy.index = tmy.index.tz_localize('UTC').tz_convert(target_time_zone)   # TODO CORRECT DATA now the first hours are missing since we changed the time zone 
# tmy.index = pd.date_range(start='2023-01-01 00:00',end='2023-12-31 23:00',freq='h').tz_localize('UTC').tz_convert(target_time_zone)

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
import pickle
import logging
from pvlib.location import Location

input_destination_1 = "../data/01_raw_input_data/"
input_destination_2 = "../data/02_urban_output_data/"
output_destination = "../data/03_urban_energy_requirements/"
output_destination2 = "../data/04_Visualisation/"
norm = 1000  # standard unit converter
target_time_zone = 'Pacific/Auckland'

# Get parameters to calculate supply (pv)
# TODO the timeline for pv is in the wrong time zone!!!!
# import pv system parameters from previous skrip calcultions
"""Get wind and pv system data."""
# Get pv and wind parameters from pickle file
with open(os.path.join(input_destination_1, 'fp'), 'rb') as fp:
    feedin_parameter = pickle.load(fp)
peak_power = feedin_parameter[0]  # in watts
# TODO IDK why it says watts behind the peakpower, because the value imported should have the unit kW. maybe there is a mistake here and the imported value needs to be converted into watts.
# TODO check original peak power calculation in feedin. what unit is peakpower calculated in
module_area = feedin_parameter[1]
norminal_power_wind = feedin_parameter[2]  # in watts
# Import pv and wind power time series
pv_feedin = pd.read_csv(os.path.join(input_destination_1, 'pv_power.csv'))
pv_feedin['time'] = pd.to_datetime(pv_feedin['time'])
#pv_feedin = pv_feedin.set_index('time')                                         # TODO careful, made a column to an indexgggg
#pv_feedin['time'] = pv_feedin.index.tz_localize('UTC').tz_convert(target_time_zone)
wind_feedin = pd.read_csv(os.path.join(input_destination_1, 'wind_power.csv'))
pv_feedin = pv_feedin.reindex()
time_stamp = pv_feedin[['time']]
pv_data = pv_feedin["pv"]
wind_power_data = wind_feedin["wind"]
logging.info("Feedin data and powersystem parameter imported.")
print('*** Feedin data imported ***')

# Calculate the rooftop capacity
# Import geospatial building data from shape files
dfa = gpd.read_file(os.path.join(input_destination_2, 'agricultural/agricultural.shp'))
dfc = gpd.read_file(os.path.join(input_destination_2, 'commercial/commercial.shp'))
dfe = gpd.read_file(os.path.join(input_destination_2, 'educational/educational.shp'))
dfi = gpd.read_file(os.path.join(input_destination_2, 'industrial/industrial.shp'))
dfr = gpd.read_file(os.path.join(input_destination_2, 'residential/residential.shp'))
# get total rooftop area
area_a = dfa['area'].sum()
area_c = dfc['area'].sum()
area_e = dfe['area'].sum()
area_i = dfi['area'].sum()
area_r = dfr['area'].sum()
# calculate fraction of rooftop area that is suitable for pv deployment
area_a_pv = area_a*0.267
area_c_pv = area_c*0.267
area_e_pv = area_e*0.267
area_i_pv = area_i*0.267
area_r_pv = area_r*0.578
# sum up total rooftop area that is suitable for pv depoyment
total_roof_to_area = area_a_pv+area_c_pv+area_e_pv+area_i_pv+area_r_pv
# calculate aggregate peak power at all rooftops
peak_power_agg = (peak_power*(total_roof_to_area/module_area)) / norm  # KW
print('Info: Maximum installed pv capacity = {} KW'.format(str(peak_power_agg)))
logging.info("Calculate maximum installed PV capacity at roof top.")


# Get parameters to calculate demand (load) for relavant building classes

# Get standard load profiles for different sectors
"""Read Standard Load Profiles."""
dfs = pd.read_csv(os.path.join(input_destination_1, 'SLP.csv'))
# get different scenario load profiles in kWh
AL = dfs['L0'] / norm,
CL = dfs['G0'] / norm
EL = dfs['G1'] / norm
IL = dfs['G3'] / norm
RL = dfs['H0'] / norm
SL = dfs['SB2'] / norm
logging.info("Get load profile for different scenarios.")
print('Info: Load profile data imported')

# Get the electricity usage index for different sectors
"""Calculate Electricity Usage Index for different building type kWh/m2 per year."""
x_a = 120 / norm
x_c = 201 / norm
x_e = 142 / norm
x_i = 645 / norm
x_r = 146 / norm
x_sl = 4 / norm
logging.info("Calculate electricty usage index for urban infrastructure.")
print('Info: Electricity usage index calculated')

# Simulate load and supply

# residential
"""Simulate Res. quarter hourly Energy Requirments REs."""
load_r = time_stamp
load_r['Load[kWh]'] = (RL*area_r*x_r)#*norm  # I added *1000 to make it match with PV, but how does this make sense? now this should be in W
load_r['PV[kWh]'] = (pv_data*peak_power * (area_r_pv/module_area))/norm # this assumes the input is Watt

# plot results
fig_size = (16, 9)
load_r['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Residential energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
#plt.savefig(output_destination2+"r_load_PV", dpi=300)
#plt.show()
logging.info("Generate residential energy requirements plot")

# save results
load_r.to_csv(os.path.join(output_destination, 'r_load.csv'))
logging.info(
"Calculate electricty demand and supply for residential buildings")
print('Info: Residential building load and pv supply siml.')

# aggricultural
"""Simulate Agricultural building type electricity demand and PV feedin supply."""
load_a = time_stamp
load_a['Load[kWh]'] = AL*area_a*x_a
load_a['PV[kWh]'] = (pv_data*peak_power *(area_a_pv/module_area)) / norm  # kWh
# plot results
fig_size = (16, 9)
load_a['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_a['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Agricultural energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
#plt.savefig(output_destination2+"a_load_PV", dpi=300)
#plt.show()
logging.info("Generate agricultural energy requirements plot")

# save results
load_a.to_csv(os.path.join(output_destination, 'a_load.csv'))
logging.info(
"Calculate electricty demand and supply for agricultural buildings")
print('Info: Agricultural building load and pv supply simulation.')

# commercial
"""Simulate Com.  building type electricity demand and PV feedin supply."""
load_c = time_stamp
load_c['Load[kWh]'] = CL*area_c*x_c
load_c['PV[kWh]'] = (pv_data*peak_power * (area_c_pv/module_area))/norm
# plot results
fig_size = (16, 9)
load_c['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_c['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Commercial energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
#plt.savefig(output_destination2+"c_load_PV", dpi=300)
#plt.show()
logging.info("Generate commercial energy requirements plot")

# save results
load_c.to_csv(os.path.join(output_destination, 'c_load.csv'))
logging.info("Calculate electricty demand and supply for commercial buildings")
print('Info: Commercial building load and pv supply siml.')

# educational
"""Simulate edu. quarter hourly Energy Requirments REs."""
load_e = time_stamp
load_e['Load[kWh]'] = EL*area_e*x_e
load_e['PV[kWh]'] = (pv_data*peak_power * (area_e_pv/module_area))/norm
# plot results
fig_size = (16, 9)
load_e['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_e['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Educational energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
#plt.savefig(output_destination2+"e_load_PV", dpi=300)
#plt.show()
logging.info("Generate educational energy requirements plot")

# save results
load_e.to_csv(os.path.join(output_destination, 'e_load.csv'))
logging.info(
"Calculate electricty demand and supply for educational buildings")
print('Info: Eductaional building load and pv supply siml.')

# industrial
"""Simulate Ind. quarter hourly Energy Requirments REs."""
load_i = time_stamp
load_i['Load[kWh]'] = IL*area_i*x_i
load_i['PV[kWh]'] = (pv_data*peak_power *(area_i_pv/module_area))/norm
# plot results
fig_size = (16, 9)
load_i['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_i['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Industrial energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
#plt.savefig(output_destination2+"i_load_PV", dpi=300)
#plt.show()
logging.info("Generate industrial energy requirements plot")

# save results
load_i.to_csv(os.path.join(output_destination, 'i_load.csv'))
logging.info("Calculate electricty demand and supply for industrial buildings")
print('Info: Industrial building load and pv supply siml.')

"""Simulate Urban Streetlightning. quarter hourly."""
street_data = gpd.read_file(os.path.join(input_destination_2, 'highway/highway.shp'))
area_sl = street_data['area'].sum()
no_building = len(street_data)
load_sl = time_stamp
load_sl['Load[kWh]'] = SL*area_sl*x_sl
load_sl.to_csv(os.path.join(output_destination, 'sl_load.csv'))
logging.info("Calculate electricty demand for street lights")
print('Info: Streetlightning load siml.')


"""Aggrgate all simulated PV power generation."""
print('Info: Aggregate simulated PV power generation and electricity demand.')

demand_supply_agri = pd.read_csv(os.path.join(output_destination, 'a_load.csv'))
demand_supply_comm = pd.read_csv(os.path.join(output_destination, 'c_load.csv'))
demand_supply_educ = pd.read_csv(os.path.join(output_destination, 'e_load.csv'))
demand_supply_indu = pd.read_csv(os.path.join(output_destination, 'i_load.csv'))
demand_supply_resi = pd.read_csv(os.path.join(output_destination, 'r_load.csv'))
demand_street_light = pd.read_csv(os.path.join(output_destination, 'sl_load.csv'))

# aggregate all pv supply for the different building types
agg_pv = (demand_supply_agri['PV[kWh]'] + demand_supply_comm['PV[kWh]'] +
          demand_supply_educ['PV[kWh]'] + demand_supply_indu['PV[kWh]'] +
          demand_supply_resi['PV[kWh]'])/norm  # to MWh
agg_pv = np.array(agg_pv)
agg_pv = pd.DataFrame(agg_pv, columns=["PV[MWh]"])

# aggregate all electricity demand for the different building types (MWh)
agg_load = (demand_supply_agri['Load[kWh]'] + demand_supply_comm['Load[kWh]'] +
            demand_supply_educ['Load[kWh]'] + demand_supply_indu['Load[kWh]'] +
            demand_supply_resi['Load[kWh]'] + demand_street_light['Load[kWh]'])/norm

        # prepare demand and supply data for optimization
agg_load = np.array(agg_load)
agg_load = pd.DataFrame(agg_load, columns=["Load[MWh]"])
agg_load['PV[MWh]'] = agg_pv["PV[MWh]"]
agg_load['demand_el'] = agg_load["Load[MWh]"].values * \
1000  # Kilo-watts hour
#agg_load['wind'] = wind_power_data  # normalized wind feedin data TODO NEEDS FIXING, prev steps for wind need to be included
agg_load['pv'] = pv_data  # normalized pv feedin data
agg_load['time'] = time_stamp['time']
agg_load = agg_load.set_index('time')

agg_load.loc[:, ["Load[MWh]", 'PV[MWh]']].to_csv(os.path.join(output_destination, 'aggregated-demand-supply.csv'))
#agg_load.loc[:, ["demand_el", 'wind', 'pv']].to_csv(os.path.join(output_destination, 'optimization-commodities.csv'))
logging.info("Calculate aggregated electricty demand and supplies")


"""Simulate quarter load and plot Urban Energy Requirments REs."""
print('Info: Plot Urban Energy Requirments.')
fig_size = (16, 9)
sim_df = pd.read_csv(os.path.join(output_destination, 'aggregated-demand-supply.csv'))
sim_df['PV[MWh]'].plot(style='r', figsize=fig_size, grid=True)
(sim_df['Load[MWh]']).plot(style='g', figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MW')
plt.title('Aggregated Energy Requirments in Oldenburg')
plt.legend(['Simulated PV', 'Simulated load'], loc='upper left')
#plt.savefig(self.output_destination2+"Energy_Requirments.png", dpi=300)
plt.show()
logging.info("Generate demand and supply plot")

