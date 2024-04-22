"""
Created on 30/01/2024

@author: sns51

This script converts excess electricity from residential pv generation into H2 for selected cities in New Zealand.
The conversion is currently based on given spreadsheet for a city size PEM electrolyser.

"""

# Spec sheet of H-TEC PEM Electrolyzer ME450
#
# H2 production nominal             450 kg/d | 210 Nm3/h
# Energy consumption                4.7 kWh/Nm3 H2 | 53 kWh/kg
# System efficiency                 75 %
# Performance class	                1 MW
# H2 production modulation range    42 – 210 Nm3/h | 20 – 100 %
# H2 purity                         5.0 (meets ISO 14687:2019 Table 2)
# Load change	                    30 s (Standby to nominal load)
# H2 output pressure 	            20 – 30 bar(g)
# Heat recovery	                    Heat output: 170 kW BoL | 350 kW EoL
#                                   57°C handover at customer system | >90% system efficiency 
# H2O required quality	            TrinkwV 2020  | EU Directive 2020/2184-EU
# H2O consumption nominal	        260 kg/h (at10°dH)
# Power supply electrolysis         3 x 480 V Y, 3 x 480 V ▲ /50 Hz (acc. ICE 600038)
#                                   Connecting power: 1.325 MVA
# Power supply periphery   	        3 x 400 V / 50 Hz (acc. ICE 600038)
#                                   Connecting value: 150 kW
# Dimensions LxWxH                  40' Container, incl. attachments ca. 13.2  x 4.0  x 5.7 m
# Weight	                        ca. 36 t (operational)
# Ambient temperature	            -20°C to +40°C


import pandas as pd
import matplotlib.pyplot as plt
import os

city = 'Christchurch'

input_destination = "../data/01_raw_input_data/"
input_destination_1 = "../data/01_raw_input_data/"+city+"/"
input_destination_2 = "../data/02_urban_output_data/"+city+"/"
output_destination = "../data/03_urban_energy_requirements/"+city+"/"
output_destination2 = "../data/04_Visualisation/"+city+"/"
norm = 1000  # standard unit converter

if city=='Auckland' or city=='Christchurch':
    print(city)
    res_df = pd.read_csv(os.path.join(output_destination, 'r_load.csv'))
    res_df['Load[kWh]'] = res_df['Load[MWh]']*norm
    res_df['PV[kWh]'] = res_df['PV[MWh]']*norm
    res_df['Surplus[kWh]']=res_df['PV[kWh]']-res_df['Load[kWh]']
    # set negative values to zero
    res_df['Surplus[kWh]'] = res_df['Surplus[kWh]'].clip(lower=0)
    res_df['plot_surplus'] = res_df['PV[kWh]'].where(res_df['PV[kWh]'] > res_df['Load[kWh]'], 0)
    res_df['plot_surplus_2'] = res_df['Load[kWh]'].where(res_df['PV[kWh]'] > res_df['Load[kWh]'], 0)

    fig_size = (16, 9)
    res_df['PV[kWh]'].plot(style='green', figsize=fig_size, grid=True)
    res_df['plot_surplus'].plot(style='black', figsize=fig_size, grid=True)
    res_df['plot_surplus_2'].plot(style='green', figsize=fig_size, grid=True)
    res_df['Load[kWh]'].plot(style='red', figsize=fig_size, grid=True)
    plt.xlabel('Time')
    plt.ylabel('kWh')
    #plt.ylim(0, 4371749807+100)
    plt.title(f'Residential Hydrogen Production for {city}')
    plt.legend(['Simulated PV','Surplus Electricity', '','Simulated load'], loc='upper left')
    #plt.savefig(output_destination2+"H2_res_production_ugly.png", dpi=300)
    plt.show()

    res_df['H2[kg]'] = res_df['Surplus[kWh]']/53

    Surplus_res_annual = res_df['Surplus[kWh]'].sum()
    H2_res_annual = res_df['H2[kg]'].sum()

    fig_size = (16, 9)
    res_df['H2[kg]'].plot(style='g', figsize=fig_size, grid=True)
    plt.xlabel('Time')
    plt.ylabel('kg')
    #plt.ylim(0, 44602375+10)
    plt.title(f'Hydrogen Production for {city}')
    plt.legend(['H2 produced'], loc='upper left')
    #plt.savefig(output_destination2+"H2_res_production.png", dpi=300)
    plt.show()