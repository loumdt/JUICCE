"""Create a netCDF file with daily mean temperature anomaly for
concatenated summers from 1950 to 2020 when 95th percentile threshold is exceeded ; 
set to zero elsewhere ;
input file is supposed to contain summers only. Argument is either tg for mean, tn for min or tx for max"""

import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from datetime import datetime
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)
#-------------------------------------

nc_file = "D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_"+the_variable+"_summer_only_1950-2020.nc"
f=nc.Dataset(nc_file, mode='r')
lat_in=f.variables['lat'] [:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]

#-------------------------------------

threshold_table=np.load('D:/Ubuntu/PFE/Data/E-OBS/0.1deg/distrib_'+the_variable+'_ano_npy_95%_threshold_15days.npy',allow_pickle=True)
#threshold_table=np.load('D:/Ubuntu/PFE/Data/E-OBS/0.1deg/distrib_tg_npy_95%_threshold_15days.npy',allow_pickle=True)
threshold_table=ma.masked_outside(threshold_table[152:244,:,:],-60,60) #threshold of 95th temperature anomaly percentile for every day of summer and location

#-------------------------------------

#Only record the summer temperatures and remove the values that do not exceed the 95th percentile threshold
#nc_file_out=nc.Dataset("/data/tmandonnet/E-OBS/0.1deg/tg_daily_mean_ovr_70yrs.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_"+the_variable+"_anomaly_summer_only_1950-2020_scaled_to_95th.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#-------------------------------------

#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', 465)    # latitude axis
lon_dim = nc_file_out.createDimension('lon', 705)    # longitude axis
time_dim = nc_file_out.createDimension('time', 6532) # unlimited time axis (can be appended to).

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature anomaly for summer days from 1950 to 2020"
nc_file_out.subtitle="values put to zero where not exceeding 95th temperature anomaly threshold. Created with ano_scale_jja_selec.py on " +datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = 'days of summer from 1950 to 2020'
time.long_name = 'time'
# Define a 3D variable to hold the data
temp = nc_file_out.createVariable('temp',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
temp.units = '°C' # degrees Celsius
temp.standard_name = 'air_temperature' # this is a CF standard name
temp.long_name = 'daily '+temp_name_dict[the_variable]+' temperature anomaly'

# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements

lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(6532)

#-----------
temp[:,:,:]=ma.array(np.zeros((6532,465,705)),mask=False) # 6532 = 92*71

#-------------------------------------
#red, on ne garde les anomalies que pour les jours où ano>T95, sinon on met tout à zéro
for year in tqdm(range(71)) :
    #print('year',year,'/70')
    var=f.variables['temp'][year*92:(year+1)*92,:,:] # start= 01/06 ; end = 31/08 ; SHAPE=(time,lat,lon)
    ano_scale = np.zeros(np.shape(var))
    ano_scale = var - threshold_table
    ano_scale_bool = (ano_scale >=0)
    temp[year*92:(year+1)*92,:,:]=(ano_scale_bool*var)

f.close()
nc_file_out.close()