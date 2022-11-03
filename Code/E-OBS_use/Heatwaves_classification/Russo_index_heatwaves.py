"""Compute the pseudo_Russo index map. Argument is either tg for mean, tx for max, or tn for min."""
import netCDF4 as nc
import numpy as np
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)

nc_file = "D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_"+the_variable+"_anomaly_summer_only_1950-2020_scaled_to_95th.nc" #netcdf file containing the heatwaves from E-OBS

f = nc.Dataset(nc_file,mode='r')
time_in = f.variables['time'][:]
lon_in = f.variables['lon'][:]
lat_in = f.variables['lat'][:]

temp_25_scaled = np.load("D:/Ubuntu/PFE/Data/E-OBS/0.1deg/distrib_"+the_variable+"_ano_npy_25%_threshold_15days.npy",allow_pickle = True) #numpy file containing the days of the E-OBS heatwaves
temp_75_scaled = np.load("D:/Ubuntu/PFE/Data/E-OBS/0.1deg/distrib_"+the_variable+"_ano_npy_75%_threshold_15days.npy",allow_pickle = True) #numpy file containing the dates of the E-OBS heatwaves

temp_25_scaled = temp_25_scaled[152:244,:,:]
temp_75_scaled = temp_75_scaled[152:244,:,:]

#-------------------
nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/Russo_index_"+the_variable+"_summer_only_1950_2020.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#Define netCDF output file :
nc_file_out.createDimension('lat', 465)    # latitude axis
nc_file_out.createDimension('lon', 705)    # longitude axis
nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to)

nc_file_out.title="Russo indices for the heatwaves found in E-OBS with Stefanon method for "+temp_name_dict[the_variable]+" temperature"
nc_file_out.subtitle="values put to zero where there is no heatwave"

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = 'days of summer containing a sub-heatwave from 1950 to 2020'
time.long_name = 'time'
# Define a 3D variable to hold the data
Russo_index = nc_file_out.createVariable('Russo_index',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
Russo_index.units = '°C' # degrees Celsius
date_idx = nc_file_out.createVariable('date_idx', np.int32,('time',))
date_idx.units = 'days of summer containing a sub-heatwave from 1950 to 2020, recorded as the matching index of the temp_anomaly_summer_only_1950-2020_scaled_to_95th.nc file'
date_idx.long_name = 'date_index'
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements
lat[:] = lat_in[:] 
lon[:] = lon_in[:]

for i in tqdm(range(71)):
    temp = f.variables['temp'][i*92:(i+1)*92,:,:]
    Russo_index[i*92:(i+1)*92,:,:] = (temp-temp_25_scaled)/(temp_75_scaled-temp_25_scaled)
f.close()
nc_file_out.close()