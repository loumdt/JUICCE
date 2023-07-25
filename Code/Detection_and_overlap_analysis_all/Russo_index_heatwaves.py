"""Compute the pseudo_Russo index map. Argument is either tg for mean, tx for max, or tn for min."""
#%%
import netCDF4 as nc
import numpy as np
from tqdm import tqdm
import sys,os
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
#Read arguments
try : 
    the_variable = str(sys.argv[1])
except :
    the_variable='tg'

try : 
    year_beg = int(sys.argv[2])
except :
    year_beg = 1950
    
try : 
    year_end = int(sys.argv[3])
except :
    year_end = 2021

try : 
    threshold_value = int(sys.argv[4])
except :
    threshold_value = 95
    
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)
print('year_beg :',year_beg)
print('year_end :',year_end)
print('threshold_value :',threshold_value)
#%%
f_temp = nc.Dataset(os.path.join(datadir,"ERA5","t2m",f"{the_variable}_anomaly_JJA_{year_beg}_{year_end}_scaled_{threshold_value}th.nc"))#path to the output netCDF file

time_in = f_temp.variables['time'][:]
lon_in = f_temp.variables['lon'][:]
lat_in = f_temp.variables['lat'][:]

f_temp_25 = nc.Dataset(os.path.join(datadir,"ERA5","t2m",f"distrib_{the_variable}_ano_{year_beg}_{year_end}_{25}th_threshold_15days.nc"))
f_temp_75 = nc.Dataset(os.path.join(datadir,"ERA5","t2m",f"distrib_{the_variable}_ano_{year_beg}_{year_end}_{75}th_threshold_15days.nc"))

temp_25 = f_temp_25.variables['threshold'][152:244,:,:] #JJA days, 1st June to 31st August
temp_75 = f_temp_75.variables['threshold'][152:244,:,:] #JJA days, 1st June to 31st August
#%%
#-------------------
nc_file_out = nc.Dataset(os.path.join(datadir,"ERA5","t2m","Detection_Canicule",f"Russo_index_{the_variable}_anomaly_JJA_{year_beg}_{year_end}_threshold_{threshold_value}th.nc"),mode='w',format='NETCDF4_CLASSIC')#path to the output netCDF file

#Define netCDF output file :
nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
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
time.units = f'days of JJA from {year_beg} to {year_end}'
time.long_name = 'time'
# Define a 3D variable to hold the data
Russo_index = nc_file_out.createVariable('Russo_index',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
Russo_index.units = '°C' # degrees Celsius
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements
lat[:] = lat_in[:] 
lon[:] = lon_in[:]

for i in tqdm(range(year_end-year_beg+1)):
    temp = f_temp.variables['t2m'][i*92:(i+1)*92,:,:]
    Russo_index[i*92:(i+1)*92,:,:] = (temp-temp_25)/(temp_75-temp_25)
f_temp.close()
nc_file_out.close()
f_temp_25.close()
f_temp_75.close()