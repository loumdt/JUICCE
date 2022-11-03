"""Smooth a temperature variable over a year, with a 21-day window. Argument is either tg for mean, tn for min or tx for max"""
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from datetime import datetime
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)

nc_file="D:/Ubuntu/PFE/Data/E-OBS/0.1deg/"+the_variable+"_daily_mean_ovr_70yrs.nc" #path to the netCDF file

print('nc_file',nc_file)
f=nc.Dataset(nc_file, mode='r')
var=f.variables['temp'][:,:,:]
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
#print("Min var :", np.min(var))
#print("Max var :", np.max(var))

nc_file_mask="D:/Ubuntu/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')

Mask_0=f_mask.variables['mask_all'][:]
Mask_all=[Mask_0]*366

extended_temp=ma.array(np.zeros((366*3,465,705)),mask=False)
extended_temp[0:366,:,:]=var[:,:,:]
extended_temp[0:366,:,:]=ma.array(extended_temp[0:366,:,:],mask=Mask_all)

extended_temp[366:732,:,:]=var[:,:,:]
extended_temp[366:732,:,:]=ma.array(extended_temp[366:732,:,:],mask=Mask_all)

extended_temp[732:,:,:]=var[:,:,:]
extended_temp[732:,:,:]=ma.array(extended_temp[732:,:,:],mask=Mask_all)


extended_temp = ma.masked_outside(extended_temp,-100,100)	

#print("Min extended_temp :", np.min(extended_temp))
#print("Max extended_temp :", np.max(extended_temp))


#-------------------------------------

#Compute the temperature data averaged over 1950-2020 for every day of the year and store it in a netCDF file.

nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/E-OBS/0.1deg/"+the_variable+"_daily_mean_ovr_70yrs_smoothed.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#-----------
#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', 465)    # latitude axis
lon_dim = nc_file_out.createDimension('lon', 705)    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title="Smoothed daily "+temp_name_dict[the_variable]+" temperature, averaged over 1950-2020 for every day of the year"
nc_file_out.subtitle="to be used for temperature anomaly computation"
nc_file_out.history = "Created with file lissage_moyenne.py on " + datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float64, ('time',))
time.units = 'days of a bisextile year from 0 to 365'
time.long_name = 'time'
# Define a 3D variable to hold the data
temp = nc_file_out.createVariable('temp',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
temp.units = '°C' # degrees Celsius
temp.standard_name = 'air_temperature' # this is a CF standard name

nlats = len(lat_dim); nlons = len(lon_dim); ntimes = 366
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements

lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=time_in[:]

temp[:,:,:]=ma.array(np.zeros((366,465,705)),mask=Mask_all)

smooth_span=10

for i in tqdm(range(366,732)):
	#print(i-366)
	val_table=ma.array(np.zeros((2*smooth_span+1,465,705)),mask=[Mask_0]*(2*smooth_span+1))
	for j in range(-smooth_span,smooth_span+1,1):
		val_table[j]=extended_temp[i+j,:,:]
	val_table = ma.masked_outside(val_table,-100,100)
	temp[i-366,:,:] = np.nanmean(val_table,axis=0)

temp=ma.masked_outside(temp,-100,100)
f.close()
f_mask.close()
nc_file_out.close()