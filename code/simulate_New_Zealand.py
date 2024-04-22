"""
Created on 26/03/2024

@author: sns51

This script currently calculates the aggregated residential electricity demand and pv generation for residential rooftops based on NZ data.

"""

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging

city = 'Christchurch'

input_destination = "../data/01_raw_input_data/"
input_destination_1 = "../data/01_raw_input_data/"+city+"/"
input_destination_2 = "../data/02_urban_output_data/"+city+"/"
output_destination = "../data/03_urban_energy_requirements/"+city+"/"
output_destination2 = "../data/04_Visualisation/"+city+"/"
norm = 1000  # standard unit converter

# for chosen module
peak_power = 409.88699999999994 # Watt
module_area = 2.012016 # m^2

####################################################################################################


# New Zealand


#####################################################################################################

# Get parameters to calculate supply (pv)

# PV 

#####################################################################################################

# Import pv and wind power time series
pv_power = pd.read_csv(os.path.join(input_destination_1, 'pv_power.csv'))
pv_power['time'] = pd.to_datetime(pv_power['time'])

pv_data = pv_power["pv"]
time_stamp = pv_power[['time']]

# Calculate the rooftop capacity
# Import geospatial building data from shape files
dfa = gpd.read_file(os.path.join(input_destination_2, 'agricultural/agricultural.shp'))
dfc = gpd.read_file(os.path.join(input_destination_2, 'commercial/commercial.shp'))
dfe = gpd.read_file(os.path.join(input_destination_2, 'educational/educational.shp'))
dfi = gpd.read_file(os.path.join(input_destination_2, 'industrial/industrial.shp'))
dfr = gpd.read_file(os.path.join(input_destination_2, 'residential/residential.shp'))
dfinst = gpd.read_file(os.path.join(input_destination_2, 'institutional/institutional.shp'))
dfo = gpd.read_file(os.path.join(input_destination_2, 'other/other.shp'))

# get total rooftop area for each category
area_a = dfa['area'].sum()
area_c = dfc['area'].sum()
area_e = dfe['area'].sum()
area_i = dfi['area'].sum()
area_r = dfr['area'].sum()
area_inst = dfinst['area'].sum()
area_o = dfo['area'].sum()

# calculate fraction of rooftop area that is suitable for pv deployment
area_a_pv = area_a*0.267
area_c_pv = area_c*0.267
area_e_pv = area_e*0.267
area_i_pv = area_i*0.267
area_r_pv = area_r*0.578
area_inst_pv = area_inst*0.267
area_o_pv = area_o*0.267

# sum up total rooftop area that is suitable for pv deployment
total_roof_top_area = area_a_pv+area_c_pv+area_e_pv+area_i_pv+area_r_pv+area_inst_pv+area_o_pv

# calculate aggregate peak power at all rooftops
peak_power_agg = (peak_power*(total_roof_top_area/module_area)) / norm  # KW
print('Info: Maximum installed pv capacity = {} KW'.format(str(peak_power_agg)))
logging.info("Calculate maximum installed PV capacity at roof top.")

################################################################################################################

# SLP

################################################################################################################


# import electricity demand profiles for NZ
Electricity_Demand = pd.read_excel(input_destination_1+"Electricity_Demand_"+city+".xlsx")

##################################################################

# Simulate load and supply

##################################################################

# residential

##################################################################


"""Simulate Res. quarter hourly Energy Requirments REs."""
load_r = time_stamp
load_r['Load[MWh]'] = Electricity_Demand.GWh*1000
#load_r['PV[GWh]'] = (pv_data*peak_power * (area_r_pv/module_area))/1000000000 # convert in GWh, because input is in watt
load_r['PV[MWh]'] = (pv_data * (area_r_pv/module_area))/norm/norm # convert in MWh, because input is in watt
load_r['time'] = pd.to_datetime(load_r['time'],utc=True)
load_r['time']=load_r['time'].dt.tz_convert('Pacific/Auckland')
load_r.to_csv(os.path.join(output_destination, 'r_load.csv'))

summer_date = '2022-01-15' # for this part a random summer and random winter day has been selected
winter_date = '2022-06-15'

# Filter for the desired date
load_r_summer_day = load_r[load_r['time'].dt.date == pd.to_datetime(summer_date).date()]
load_r_winter_day = load_r[load_r['time'].dt.date == pd.to_datetime(winter_date).date()]
load_r_jan = load_r[load_r['time'].dt.month == 1]
load_r_jan_1_week = load_r[load_r['time'].dt.dayofyear.between(1, 7)]
load_r_jun_1_week = load_r[load_r['time'].dt.date.between(pd.to_datetime('2022-06-01'), pd.to_datetime('2022-06-07'))]

# plot summer day
fig_size = (16, 9)
load_r_summer_day['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r_summer_day['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['Simulated PV [MWh]', 'Simulated Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_day_summer", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_day_summer.svg', format='svg')
plt.show()

# plot winter day
fig_size = (16, 9)
load_r_winter_day['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r_winter_day['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['PV [MWh]', 'Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_day_winter", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_day_winter.svg', format='svg')
plt.show()

# plot Jan
fig_size = (16, 9)
load_r_jan['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r_jan['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['PV [MWh]', 'Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_jan", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_jan.svg', format='svg')
plt.show()

# plot first week of Jan
fig_size = (16, 9)
load_r_jan_1_week['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r_jan_1_week['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['PV [MWh]', 'Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_week_vs_summer", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_week_vs_summer.svg', format='svg')
plt.show()

# plot first week of June
fig_size = (16, 9)
load_r_jun_1_week['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r_jun_1_week['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['PV [MWh]', 'Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_week_winter", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_week_winter.svg', format='svg')
plt.show()

# plot winter and summer week comparison
fig_size = (16, 9)
load_r_jan_1_week['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True, linestyle='--')
load_r_jan_1_week['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True, linestyle='--')
load_r_jun_1_week['PV[MWh]'].reset_index(drop=True).plot(style='green',figsize=fig_size, grid=True)
load_r_jun_1_week['Load[MWh]'].reset_index(drop=True).plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['Summer PV [MWh]', 'Summer Load[MWh]', 'Winter PV [MWh]', 'Winter Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_week_winter_vs_summer", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_week_winter_vs_summer.svg', format='svg')
plt.show()


# plot winter and summer day comparison
fig_size = (16, 9)
load_r_summer_day['PV[MWh]'].reset_index(drop=True).plot(style='green',figsize=fig_size, grid=True, linestyle='--')
load_r_summer_day['Load[MWh]'].reset_index(drop=True).plot(style='red',figsize=fig_size, grid=True, linestyle='--')
load_r_winter_day['PV[MWh]'].reset_index(drop=True).plot(style='green',figsize=fig_size, grid=True)
load_r_winter_day['Load[MWh]'].reset_index(drop=True).plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
plt.title('Residential electricity requirements')
plt.legend(['Summer PV [MWh]', 'Summer Load[MWh]', 'Winter PV [MWh]', 'Winter Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_day_winter_vs_summer", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_day_winter_vs_summer.svg', format='svg')
plt.show()


# plot results
fig_size = (16, 9)
load_r['PV[MWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r['Load[MWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MWh')
#plt.ylim(0, (4371749807 + 5000))
plt.title('Residential electricity requirements')
plt.legend(['PV [MWh]', 'Load[MWh]'], loc='upper left')
plt.savefig(output_destination2+"r_pv_demand_all", dpi=300)
# Save the plot as SVG
plt.savefig(output_destination2+'r_pv_demand_all.svg', format='svg')
plt.show()