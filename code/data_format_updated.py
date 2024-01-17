"""Store Downloaded data as csv file in feedinlib format.

This script is used to write the downloaded weather data to csv file in the format
that Feedinlib understands.
"""
from feedinlib import era5
import sys
import logging
"""new next line"""
import pvlib
from pvlib import irradiance
from pvlib.solarposition import get_solarposition
import pandas as pd
# create a log file
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s',
                    filename="../code/log/weather_data.log",
                    level=logging.DEBUG)


def feedin_solarFormat(lon, lat, target_file, weather_dir, to_csv=False):
    """Get weather data in pvlib format."""
    pv_data = era5.weather_df_from_era5(era5_netcdf_filename=target_file,
                                        lib="pvlib",
                                        area=[lon, lat])
    """"Get wind data to extract pressure parameter for dni calculation"""
    wind_data = era5.weather_df_from_era5(era5_netcdf_filename=target_file,
                                          lib="windpowerlib",
                                          area=[lon, lat])
    p = wind_data.pressure.squeeze()*100
    """Calculate solar position"""
    altitude = 6.0 # TODO put this as option into make file, 6m is the altitude of Christchurch
    solpos = get_solarposition(pv_data.index,latitude=lat,longitude=lon,altitude=altitude,temperature=pv_data.temp_air,pressure=p*100)
    """DISC disc() is an empirical correlation developed at SERI (now NREL) in 1987. The direct normal irradiance (DNI) is related to 
    clearness index (kt) by two polynomials split at kt = 0.6, then combined with an exponential relation with airmass."""
    out_disc = irradiance.disc(pv_data.ghi, solpos.zenith, pv_data.index, p)
    df_disc = irradiance.complete_irradiance(solar_zenith=solpos.apparent_zenith, ghi=pv_data.ghi, dni=out_disc.dni, dhi=None)
    pv_data['dni']=df_disc.dni
                                                                              
    print(pv_data.head(5))

    if to_csv:
        pv_data.to_csv(weather_dir+"solar_data.csv")
        logging.info("Solar data formatted to feedinlib format.")


def feedin_windFormat(lon, lat, target_file, weather_dir, to_csv=False):
    """Get weather data in windpowerlib format."""
    wind_data = era5.weather_df_from_era5(era5_netcdf_filename=target_file,
                                          lib="windpowerlib",
                                          area=[lon, lat])
    print(wind_data.head(5))

    if to_csv:
        wind_data.to_csv(weather_dir+"wind_data.csv")
        logging.info("Wind data formatted to feedinlib format.")


if __name__ == "__main__":
    lon = float(sys.argv[1])
    lat = float(sys.argv[2])
    target_file = sys.argv[3]
    weather_dir = "../data/01_raw_input_data/"
    feedin_solarFormat(lon, lat, target_file, weather_dir, to_csv=True)
    feedin_windFormat(lon, lat, target_file, weather_dir, to_csv=True)
