###################################################################################
#   FlexiGIS                                                                      #
#                                                                                 #
#   Copyright "2020" "DLR VE"                                                     #
#										  #
#   Licensed under the BSD-3-Clause, "New BSD License" or "Modified BSD License"  #
#                                                                                 #
#   Redistribution and use in source and binary forms, with or without            #
#   modification, are permitted provided that the following conditions are met:   #
#                                                                                 #
#   1. Redistributions of source code must retain the above copyright notice,     #
#      this list of conditions and the following disclaimer.                      #
#                                                                                 #
#   2. Redistributions in binary form must reproduce the above copyright notice,  #
#      this list of conditions and the following disclaimer in the documentation  #
#      and/or other materials provided with the distribution.                     #
#                                                                                 #
#   3. Neither the name of the copyright holder nor the names of its contributors #
#      may be used to endorse or promote products derived from this software      #
#      without specific prior written permission.                                 #
#                                                                                 #
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"   #
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE     #
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE#
#   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE  #
#   FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    #
#   DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR    #
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER    #
#   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, #
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE #
#   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.          #
#                                                                                 #
#        https://opensource.org/licenses/BSD-3-Clause                             #
###################################################################################


#=================================================================================#
#              Setting the config file                                            #
#=================================================================================#

config:=config.mk
include $(config)

#=================================================================================#
#              Output Files                                                       #
#=================================================================================#
ROAD_CSV:= $(output_folder)/highway/highway.shp
BUILDINGS_CSV:=$(output_folder)/buildings/buildings.shp
EXAMPLE_DATA:=$(input_folder)/example_OSM_data/OSM_road.csv
COMMODITIES:=$(urban_requirements_dir)/optimization-commodities.csv
#=================================================================================#
#              Definition of tasks                                                #
#=================================================================================#


.PHONY: all
.PHONY: example
.PHONY: shapefile
.PHONY: download
.PHONY: filter_data
.PHONY: export_data
.PHONY: abstract_data
.PHONY: feedin
.PHONY: demand_supply_simulation
.PHONY: optimization
.PHONY: drop_database

#=================================================================================#
#              Environment Variables                                              #
#=================================================================================#

all: drop_database download filter_data export_data abstract_data feedin demand_supply_simulation optimization

#=================================================================================#
#              DOWNLOAD OSM DATASETS                                              #
#=================================================================================#


# Step1: Download the OSM raw geo urban data.

download:
	@echo "\n STEP 1: \nDownload the OSM raw data from \n '$(OSM_raw_data_URL)' \n and saving it to \n '$(OSM_raw_data)':"
	@date >> log/download.log
	wget -nv -O $(OSM_raw_data) $(OSM_raw_data_URL) >> log/download.log 2>&1
	@echo "Done. Download OSM raw data" >> log/download.log
	#@date >> log/download.log
	@echo "--> Done. Download OSM raw data."
#=================================================================================#
#              BUILDING LANDUSE HIGHWAYS DATA EXTRACTION                          #
#=================================================================================#

# Step2: Filtering the OSM raw urban data.

filter_data:
	@echo "\n STEP 2: \nFiltering OSM PBF File With Bounding POLY FILE:"
	@date >> log/osmosis.log
	osmosis \
	--read-pbf file=$(OSM_raw_data) \
	--tag-filter accept-ways building=* --used-node \
	--bounding-polygon file=$(polyfile) \
	--buffer outPipe.0=building \
	\
	--read-pbf file=$(OSM_raw_data) \
	--tag-filter accept-ways highway=* --used-node \
	--bounding-polygon file=$(polyfile) \
	--buffer outPipe.0=highway \
	\
	--read-pbf file=$(OSM_raw_data) \
	--tag-filter accept-ways landuse=* --used-node \
	--bounding-polygon file=$(polyfile) \
	--buffer outPipe.0=landuse_1 \
	\
	--read-pbf file=$(OSM_raw_data) \
	--tag-filter accept-relations landuse=* --used-node \
	--bounding-polygon file=$(polyfile) \
	--buffer outPipe.0=landuse_2 \
	\
	--read-pbf file=$(OSM_raw_data) \
	--tag-filter accept-ways power=* --used-node \
	--bounding-polygon file=$(polyfile) \
	--buffer outPipe.0=power_1 \
	\
	--read-pbf file=$(OSM_raw_data) \
	--tag-filter accept-nodes power=* --used-node \
	--bounding-polygon file=$(polyfile) \
	--buffer outPipe.0=power_2 \
	\
	--merge inPipe.0=power_1 inPipe.1=power_2 \
	--buffer outPipe.0=power_all \
	\
	--merge inPipe.0=landuse_1 inPipe.1=landuse_2 \
	--buffer outPipe.0=landuse_all \
	\
	--merge inPipe.0=landuse_all inPipe.1=building \
	--buffer outPipe.0=landuse_building \
	\
	--merge inPipe.0=landuse_building inPipe.1=highway \
	--buffer outPipe.0=landuse_building_highway \
	\
	--merge inPipe.0=landuse_building_highway inPipe.1=power_all \
	--write-pbf file=$(OSM_merged_data) >> log/osmosis.log 2>&1;
	@echo "osmosis data filtering done." >> log/osmosis.log
	@date >> log/osmosis.log
	@echo "Info: OSM Filtered Urban Energy Infrastructure"

#=================================================================================#
#              URBAN DATA EXPORT TO DATABASE                                      #
#=================================================================================#
# Step3: Export the Filtered OSM data to the Postgres Server.

export_data:
	@echo "\n STEP 3: \nExport the Filtered OSM data to Postgres Server:"
	@date >> log/database.log
	export PGPASSWORD=$(postgres_password); createdb -U $(postgres_user) -h $(postgres_host) $(postgres_database);
	export PGPASSWORD=$(postgres_password); $(osm2pgsql_bin) -r pbf --username=$(postgres_user) --database=$(postgres_database) --host=$(postgres_host) --port=$(postgres_port) -s \
	-C $(osm2pgsql_cache) --hstore --number-processes $(osm2pgsql_num_processes) $(OSM_merged_data);
	@echo "OSM data export to database done." >> log/database.log
	@date >> log/osm2pgsql.log
	@echo "Info: FlexiGIS OSM Data Export Complete."

#=================================================================================#
#              ABSTRACTION AND DATA PROCESSING                                    #
#=================================================================================#
# Step4: Execute the abstraction script flexigis_buildings.py & flexigis_road.py on the database created in Step3

abstract_data:
	@echo "\n STEP 4: \nRunning the Abstraction script on the database '$(postgres_database)':"
	@date >> log/abstract.log
	@if [ $(postgres_password) =  ]; \
	then \
	python flexigis_road.py -U $(postgres_user) -P $(postgres_port) -H $(postgres_host) -D $(postgres_database) ;\
	else \
	python flexigis_road.py -U $(postgres_user) -P $(postgres_port) -H $(postgres_host) -D $(postgres_database) -X $(postgres_password) ; \
	fi
	@echo "highway data abstraction done." >> log/abstract.log
	@echo "Info: FlexiGIS Highway Data Abstraction Complete."
	@date >> log/abstract.log
	@if [ $(postgres_password) =  ]; \
	then \
	python flexigis_buildings.py -U $(postgres_user) -P $(postgres_port) -H $(postgres_host) -D $(postgres_database) ;\
	else \
	python flexigis_buildings.py -U $(postgres_user) -P $(postgres_port) -H $(postgres_host) -D $(postgres_database) -X $(postgres_password) ; \
	fi
	@echo "Building and landuse data abstraction done." >> log/abstract.log
	@echo "Info: FlexiGIS Buildings Data Abstraction Complete."
	@echo "Info: Generating Plots of Geo-referenced Data."
	@if [ -e $(BUILDINGS_CSV) ]; then python plot_polygons.py ; fi
	@echo "Info: Plots Generated."

#=================================================================================#
#              DOWNLOAD ERA5 WEATHER DATA                                         #
#=================================================================================#
weather_data:
	@echo "\n *** Getting ERA5 weather data from Climate Data Store (CDS) ***"
	@ echo "weather data region checker: $(region)"
	@if [ "$(region)" -eq 1 ];\
	then python weather_data.py $(lon_region) $(lat_region) $(target_file) $(start_date) $(end_date) $(region); \
	else \
	python weather_data.py $(lon_single_location) $(lat_single_location) $(target_file) $(start_date) $(end_date) $(region); \
	fi
	@echo "INFO: see ../data/01_raw_input_data, for output netcdf"

#=================================================================================#
#              GENERATE WIND AND SOLAR POWER PARAMETER IN FEEDINLIB FORMAT        #
#=================================================================================#
feedin_data_format:
	@echo "\n Weather data in Feedinlib format"
	@if [ -e $(target_file) ]; then python data_format_updated.py $(lon_single_location) $(lat_single_location) $(target_file); fi
	@echo "INFO: see ../data/01_raw_input_data, for csv files of weather data"

#=================================================================================#
#              GENERATE WIND AND SOLAR FEEDIN TIMESERIES                          #
#=================================================================================#
feedin:
	@echo "\n Feedin generation from wind and solar"
	@if [ "$(input_folder)" = "../data/01_raw_input_data/" ]; then python feedin.py $(lon_single_location) $(lat_single_location) $(solar_data) $(wind_data) $(turbine_name) $(pv_panel) $(inverter_type) $(hub_height) ; fi
	@echo "INFO: see ../data/01_raw_input_data, for csv files of power data"
#=================================================================================#
#              MODELLING URBAN ENERGY REQUIREMENT                                 #
#=================================================================================#

demand_supply_simulation:
	@echo "\n Urban Electricity Demand and Supply"
	@date >> log/urban_energy.log
	@if [ -e $(ROAD_CSV) ]; then python flexigis_simulate.py ; fi
	@echo "Done. Modelling urban energy requirements." >> log/urban_energy.log
	@echo "Info: Output Files IN Folder '$(load_folder)'"

#=================================================================================#
#              OPTIMIZATION OF STORAGE AND FEEDIN SUPPLY                          #
#=================================================================================#

optimization:
	@echo "\n Optimization of Storage and Supply"
	@if [ -e $(COMMODITIES) ]; then python flexigis_optimize.py ; fi
	@echo "Info: Done!"

#=================================================================================#
#              FLEXIGIS-EXAMPLE                                 				  #
#=================================================================================#
example:
	@echo "\n TEST: \nExample Based on Filtered OSM CSV Data"
	@if [ -e $(EXAMPLE_DATA) ]; then python example.py ; fi
	@if [ -e $(BUILDINGS_CSV) ]; then python plot_polygons.py ; fi
	@if [ "$(input_folder)" = "../data/01_raw_input_data/" ]; then python feedin.py $(lon_single_location) $(lat_single_location) $(solar_data) $(wind_data) $(turbine_name) $(pv_panel) $(inverter_type) $(hub_height) ; fi
	@if [ -e $(ROAD_CSV) ]; then python flexigis_simulate.py ; fi
	@if [ -e $(COMMODITIES) ]; then python flexigis_optimize.py ; fi
	@echo "Info: Example Data Abstraction & Simulation Complete. see ../data/04_Visualisation folder for sample plot"


#=================================================================================#
#              DROPPING                                                           #
#=================================================================================#
# If you wish to drop your database
drop_database:
	$(eval answer := $(shell read -r -p "Do you really want to delete the FlexiGIS database '$(postgres_database)'? Type 'yes' or 'y' if you are sure you wish to continue: " ANSWER; echo $$ANSWER))
	@if [ "$(answer)" = "yes" ] || [ "$(answer)" = "y" ]; then if(dropdb --username=$(postgres_user) --port=$(postgres_port) --host=$(postgres_host) $(postgres_database)); then echo "The FlexiGIS database '$(postgres_database)' has been dropped."; fi else echo "\nDid not drop the FlexiGIS database '$(postgres_database)'."; fi
