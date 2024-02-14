"""
Created on 7/01/2024

@author: sns51

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

# get total rooftop area
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
# sum up total rooftop area that is suitable for pv depoyment
total_roof_top_area = area_a_pv+area_c_pv+area_e_pv+area_i_pv+area_r_pv+area_inst_pv+area_o_pv
# calculate aggregate peak power at all rooftops
peak_power_agg = (peak_power*(total_roof_top_area/module_area)) / norm  # KW
print('Info: Maximum installed pv capacity = {} KW'.format(str(peak_power_agg)))
logging.info("Calculate maximum installed PV capacity at roof top.")

################################################################################################################

# SLP

################################################################################################################

sheet_names = ['christchurch_res', 'christchurch_com_ind']
slp_data = {}

for s in sheet_names:
    # import electricity demand profiles for NZ
    SLP_NZ_table = pd.read_excel("../data/01_raw_input_data/SLP_NZ_calculated.xlsx", sheet_name=s)
    # Reshape imported dataframe
    SLP_NZ = pd.melt(SLP_NZ_table, id_vars=["Unnamed: 0"], var_name="Time", value_name="Values")
    # Rename the columns
    SLP_NZ.columns = ["day", "time", "kWh"]
    SLP_NZ['year'] = '2022'

    # Merge "Day" and "Time" into a single datetime column
    SLP_NZ["time"] = pd.to_datetime(SLP_NZ["year"] + "-" + SLP_NZ["day"] + " " + SLP_NZ["time"], format="%Y-%d-%b %I %p")

    # Drop the original "day" and "year" columns and sort the time
    SLP_NZ = SLP_NZ.drop(["day", "year"], axis=1).sort_values(by="time")
    # Store the DataFrame in a variable with a dynamic name
    slp_data[f'SLP_{s}'] = SLP_NZ

# Access the DataFrames using dynamic variable names
res = slp_data[f'SLP_{city}_res']
com_ind = slp_data[f'SLP_{city}_com_ind']

# Get standard load profiles for different sectors
"""Read Standard Load Profiles."""
# get different scenario load profiles in kWh
                                                         
RL = res['kWh']
IL = com_ind['Commercial']

SLP = pd.read_excel(f"../data/01_raw_input_data/{city}/SLP_NZ.xlsx")
SLP_res = SLP['res']
SLP_com = SLP['com']


SLP['datetime'] = pd.date_range(start='2022-01-01', end='2022-12-31 23:45:00', freq='30T')
# Set the new datetime column as the index
SLP = SLP.set_index('datetime')

# Resample the data to hourly frequency and sum the values
hourly_data = SLP.resample('H').sum()
hourly_data.reset_index(drop=True, inplace=True)

RL = hourly_data.res
IL = hourly_data.com

# Get the electricity usage index for different sectors
"""Calculate Electricity Usage Index for different building type kWh/m2 per year."""
x_c = 201 #/ norm
x_r = 146# / norm
x_a = 120 #/ norm
x_e = 142 #/ norm
x_i = 645 #/ norm


# Simulate load and supply

##################################################################
# residential
##################################################################
"""Simulate Res. quarter hourly Energy Requirments REs."""
load_r = time_stamp
load_r['Load[kWh]'] = (RL*area_r*x_r)
load_r['PV[kWh]'] = (pv_data*peak_power * (area_r_pv/module_area))/norm # kW, because input is in watt

# plot results
fig_size = (16, 9)
load_r['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.ylim(0, (4371749807 + 5000))
plt.title('Residential energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
plt.savefig(output_destination2+"r_load_PV", dpi=300)
plt.show()
# auckland max 4371749807 kWh
# save results
load_r.to_csv(os.path.join(output_destination, 'r_load.csv'))

##################################################################
# commercial and industrial
##################################################################
"""Simulate Com.  building type electricity demand and PV feedin supply."""
load_c = time_stamp
load_c['Load[kWh]'] = IL*(area_c+area_a+area_e+area_i)*x_i
load_c['PV[kWh]'] = (pv_data*peak_power * ((total_roof_top_area-area_r_pv)/module_area))/norm
# plot results
fig_size = (16, 9)
load_c['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_c['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.ylim(0, (21643521226.92853 + 5000))
plt.title('Commercial and industrial energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
plt.savefig(output_destination2+"c_load_PV", dpi=300)
plt.show()
# 21643521226.92853 kWh max for Auckland

# save results
load_c.to_csv(os.path.join(output_destination, 'c_load.csv'))


"""Aggrgate all simulated PV power generation."""
demand_supply_comm = pd.read_csv(os.path.join(output_destination, 'c_load.csv'))
demand_supply_resi = pd.read_csv(os.path.join(output_destination, 'r_load.csv'))

# aggregate all pv supply for the different building types
agg_pv = (demand_supply_comm['PV[kWh]'] + demand_supply_resi['PV[kWh]'])/norm  # to MWh
agg_pv = np.array(agg_pv)
agg_pv = pd.DataFrame(agg_pv, columns=["PV[MWh]"])

# aggregate all electricity demand for the different building types (MWh)
agg_load = (demand_supply_comm['Load[kWh]']+ demand_supply_resi['Load[kWh]']) /norm # to MWh

# prepare demand and supply data for optimization
agg_load = np.array(agg_load)
agg_load = pd.DataFrame(agg_load, columns=["Load[MWh]"])
agg_load['PV[MWh]'] = agg_pv["PV[MWh]"]
agg_load['demand_el_kWh'] = agg_load["Load[MWh]"].values *1000  # Kilo-watts hour
#agg_load['wind'] = wind_power_data  # normalized wind feedin data TODO NEEDS FIXING, prev steps for wind need to be included
agg_load['pv'] = pv_data  # normalized pv feedin data
agg_load['time'] = time_stamp['time']
agg_load = agg_load.set_index('time')
# Auckland max 23644535.56990612 MWh
agg_load.loc[:, ["Load[MWh]", 'PV[MWh]']].to_csv(os.path.join(output_destination, 'aggregated-demand-supply.csv'))
#agg_load.loc[:, ["demand_el", 'wind', 'pv']].to_csv(os.path.join(output_destination, 'optimization-commodities.csv'))
logging.info("Calculate aggregated electricty demand and supplies")


"""Simulate quarter load and plot Urban Energy Requirments REs."""
print('Info: Plot Urban Energy Requirments.')
fig_size = (16, 9)
sim_df = pd.read_csv(os.path.join(output_destination, 'aggregated-demand-supply.csv'))
sim_df['PV[MWh]'].plot(style='g', figsize=fig_size, grid=True)
sim_df['Load[MWh]'].plot(style='r', figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MW')
plt.ylim(0, (23644535+5000))
plt.title(f'Aggregated Energy Requirments in {city}')
plt.legend(['Simulated PV', 'Simulated load'], loc='upper left')
plt.savefig(output_destination2+"Energy_Requirments.png", dpi=300)
plt.show()

