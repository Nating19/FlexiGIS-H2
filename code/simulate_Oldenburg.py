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

city = 'Oldenburg'

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


# Germany


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
#df = gpd.read_file(os.path.join(input_destination_2, 'buildings/buildings.shp'))
#dfinst = gpd.read_file(os.path.join(input_destination_2, 'institutional/institutional.shp'))
#dfo = gpd.read_file(os.path.join(input_destination_2, 'other/other.shp'))

# get total rooftop area
area_a = dfa['area'].sum()
area_c = dfc['area'].sum()
area_e = dfe['area'].sum()
area_i = dfi['area'].sum()
area_r = dfr['area'].sum()
#area_inst = dfinst['area'].sum()
#area_o = dfo['area'].sum()
# calculate fraction of rooftop area that is suitable for pv deployment
area_a_pv = area_a*0.267
area_c_pv = area_c*0.267
area_e_pv = area_e*0.267
area_i_pv = area_i*0.267
area_r_pv = area_r*0.578
#area_inst_pv = area_i*0.267
#area_o_pv = area_i*0.267
# sum up total rooftop area that is suitable for pv depoyment
total_roof_to_area = area_a_pv+area_c_pv+area_e_pv+area_i_pv+area_r_pv
# calculate aggregate peak power at all rooftops
peak_power_agg = (peak_power*(total_roof_to_area/module_area)) / norm  # KW
print('Info: Maximum installed pv capacity = {} KW'.format(str(peak_power_agg)))
logging.info("Calculate maximum installed PV capacity at roof top.")

################################################################################################################

# SLP

################################################################################################################

Aggregated_load_MWh = pd.read_excel(input_destination_1+'170922_Aggregated-load.xlsx') # quarter hour values
# Get parameters to calculate demand (load) for relevant building classes
Load_categorised = pd.read_excel(input_destination_1+'171019_Categories_Aggregated-load.xlsx') # quarter hour values
# Drop the Unnamed: 0 column if it is not needed
Load_categorised = Load_categorised.drop(columns=['Unnamed: 0'])
# Assuming Load_categorised is your DataFrame
Load_categorised['datetime'] = pd.date_range(start='2022-01-01', end='2022-12-31 23:45:00', freq='15T')
# Set the new datetime column as the index
Load_categorised = Load_categorised.set_index('datetime')

# Resample the data to hourly frequency and sum the values
hourly_data = Load_categorised.resample('H').sum()
hourly_data.reset_index(drop=True, inplace=True)

# Get standard load profiles for different sectors
"""Read Standard Load Profiles."""
dfs = pd.read_csv(os.path.join(input_destination, 'SLP.csv'))
# get different scenario load profiles in kWh
#AL = dfs['L0'] / norm                                                  # TODO @ Alaa, why should this be devided by 1000 ?????
AL = hourly_data['Agricultural']
#CL = dfs['G0'] / norm
CL = hourly_data['Commercial']
#EL = dfs['G1'] / norm
EL = hourly_data['Educational']
#IL = dfs['G3'] / norm
IL = hourly_data['Industrial']
#RL = dfs['H0'] / norm
RL = hourly_data['Residential']
#SL = dfs['SB2'] / norm
SL = hourly_data['Street light']
# Get the electricity usage index for different sectors
"""Calculate Electricity Usage Index for different building type kWh/m2 per year."""
x_a = 120 / norm
x_c = 201 / norm
x_e = 142 / norm
x_i = 645 / norm
x_r = 146 / norm
x_sl = 4 / norm

# Simulate load and supply

##################################################################
# residential
##################################################################
"""Simulate Res. quarter hourly Energy Requirments REs."""
load_r = time_stamp
load_r['Load[kWh]'] = RL*1000
load_r['PV[kWh]'] = (pv_data*peak_power * (area_r_pv/module_area))/norm # kW, because input is in watt

# plot results
fig_size = (16, 9)
load_r['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_r['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Residential energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
#plt.savefig(output_destination2+"r_load_PV", dpi=300)
plt.show()

# save results
load_r.to_csv(os.path.join(output_destination, 'r_load.csv'))

##################################################################
# aggricultural
##################################################################
"""Simulate Agricultural building type electricity demand and PV feedin supply."""
load_a = time_stamp
load_a['Load[kWh]'] = AL#*1000
load_a['PV[kWh]'] = (pv_data*peak_power *(area_a_pv/module_area)) / norm  # kWh
# plot results
fig_size = (16, 9)
load_a['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_a['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Agricultural energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
plt.savefig(output_destination2+"a_load_PV", dpi=300)
plt.show()

# save results
load_a.to_csv(os.path.join(output_destination, 'a_load.csv'))

##################################################################
# commercial
##################################################################
"""Simulate Com.  building type electricity demand and PV feedin supply."""
load_c = time_stamp
load_c['Load[kWh]'] = CL#*1000
load_c['PV[kWh]'] = (pv_data*peak_power * (area_c_pv/module_area))/norm
# plot results
fig_size = (16, 9)
load_c['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_c['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Commercial energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
plt.savefig(output_destination2+"c_load_PV", dpi=300)
plt.show()

# save results
load_c.to_csv(os.path.join(output_destination, 'c_load.csv'))

##################################################################
# educational
##################################################################
"""Simulate edu. quarter hourly Energy Requirments REs."""
load_e = time_stamp
load_e['Load[kWh]'] = EL#*1000
load_e['PV[kWh]'] = (pv_data*peak_power * (area_e_pv/module_area))/norm
# plot results
fig_size = (16, 9)
load_e['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_e['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Educational energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
plt.savefig(output_destination2+"e_load_PV", dpi=300)
plt.show()

# save results
load_e.to_csv(os.path.join(output_destination, 'e_load.csv'))

##################################################################
# industrial
##################################################################
"""Simulate Ind. quarter hourly Energy Requirments REs."""
load_i = time_stamp
load_i['Load[kWh]'] = IL#*1000
load_i['PV[kWh]'] = (pv_data*peak_power *(area_i_pv/module_area))/norm
# plot results
fig_size = (16, 9)
load_i['PV[kWh]'].plot(style='green',figsize=fig_size, grid=True)
load_i['Load[kWh]'].plot(style='red',figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('kW')
plt.title('Industrial energy requirements')
plt.legend(['Simulated PV [kWh]', 'Simulated Load[kWh]'], loc='upper left')
plt.savefig(output_destination2+"i_load_PV", dpi=300)
plt.show()

# save results
load_i.to_csv(os.path.join(output_destination, 'i_load.csv'))

##################################################################
# Streetlight
##################################################################
"""Simulate Urban Streetlightning. quarter hourly."""
street_data = gpd.read_file(os.path.join(input_destination_2, 'highway/highway.shp'))
area_sl = street_data['area'].sum()
no_building = len(street_data)
load_sl = time_stamp
load_sl['Load[kWh]'] = SL*area_sl*x_sl
load_sl.to_csv(os.path.join(output_destination, 'sl_load.csv'))



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
            demand_supply_resi['Load[kWh]'] + demand_street_light['Load[kWh]']
            ) 

# prepare demand and supply data for optimization
agg_load = np.array(agg_load)
agg_load = pd.DataFrame(agg_load, columns=["Load[MWh]"])
agg_load['PV[MWh]'] = agg_pv["PV[MWh]"]
agg_load['demand_el'] = agg_load["Load[MWh]"].values #* \
1000  # Kilo-watts hour
#agg_load['wind'] = wind_power_data  # normalized wind feedin data TODO NEEDS FIXING, prev steps for wind need to be included
agg_load['pv'] = pv_data  # normalized pv feedin data
agg_load['time'] = time_stamp['time']
agg_load = agg_load.set_index('time')

agg_load.loc[:, ["Load[MWh]", 'PV[MWh]']].to_csv(os.path.join(output_destination, 'aggregated-demand-supply.csv'))
#agg_load.loc[:, ["demand_el", 'wind', 'pv']].to_csv(os.path.join(output_destination, 'optimization-commodities.csv'))
logging.info("Calculate aggregated electricty demand and supplies")

Aggregated_load_MWh = pd.read_excel(input_destination_1+'170922_Aggregated-load.xlsx')
Aggregated_load_MWh['datetime'] = pd.date_range(start='2022-01-01', end='2022-12-31 23:45:00', freq='15T')
# Set the new datetime column as the index
Aggregated_load_MWh = Aggregated_load_MWh.set_index('datetime')

# Resample the data to hourly frequency and sum the values
hourly_data = Aggregated_load_MWh.resample('H').sum()
hourly_data.reset_index(drop=True, inplace=True)


"""Simulate quarter load and plot Urban Energy Requirments REs."""
print('Info: Plot Urban Energy Requirments.')
fig_size = (16, 9)
sim_df = pd.read_csv(os.path.join(output_destination, 'aggregated-demand-supply.csv'))
sim_df['Load[MWh]'] = hourly_data.MWh
(sim_df['PV[MWh]']).plot(style='g', figsize=fig_size, grid=True)
(sim_df['Load[MWh]']).plot(style='r', figsize=fig_size, grid=True)
plt.xlabel('Time')
plt.ylabel('MW')
plt.title('Aggregated Energy Requirments in Oldenburg')
plt.legend(['Simulated PV', 'Simulated load'], loc='upper left')
plt.savefig(output_destination2+"Energy_Requirments.png", dpi=300)
plt.show()



"""Aggrgate all simulated PV power generation."""
Aggregated_load_MWh = pd.read_excel(input_destination_1+'170922_Aggregated-load.xlsx') # quarter hour values