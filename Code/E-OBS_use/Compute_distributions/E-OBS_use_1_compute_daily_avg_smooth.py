"""Compute, for each calendar day, the daily mean, max or min temperature, averaged over the chosen period (default 1950-2021).
The seasonal cycle is then smoothed with a 31-day window.
Argument 1 is either tg for mean, tn for min or tx for max. 
Argument 2 and 3 are respectively the first year and the last year to be included in the computation."""
#%%
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from datetime import datetime
from tqdm import tqdm
import sys
import pandas as pd

try : 
    the_variable = str(sys.argv[1])
except :
    the_variable='tg'
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

try : 
    year_beg = int(sys.argv[2])
except :
    year_beg = 1950
    
try : 
    year_end = int(sys.argv[3])
except :
    year_end = 2021

print('the_variable :',the_variable)
#%%
nc_file_in="Data/E-OBS/0.1deg/"+the_variable+"_ens_mean_0.1deg_reg_v26.0e.nc" # path to E-OBS data netCDF file

print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['latitude']
lon_in=f.variables['longitude']
time_in=f.variables['time']
#%%
#-------------------------------------
#import a xlsx table containing the index of each 1st january and 31st December
df_bis_year = pd.read_excel("Code/E-OBS_use/Compute_distributions/Dates_converter_1.xlsx",header=0, index_col=0)
df_bis_year = df_bis_year.loc[year_beg:year_end,:]
nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year

#%%
#-------------------------------------

#Compute the temperature data averaged over the chosen period (default 1950-2021) for every calendar day of the year and store it in a netCDF file.
nc_file_out=nc.Dataset("Data/E-OBS/0.1deg/"+the_variable+"_daily_avg_"+str(year_beg)+"_"+str(year_end)+"_smoothed.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#-----------
#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature, averaged over "+str(year_beg)+"-"+str(year_end)+" for every day of the year, and smoothed to eliminate variability."
nc_file_out.subtitle="To be used for temperature anomaly computation"
nc_file_out.history = "Created with file compute_daily_average_for_anomaly.py on " + datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float64, ('time',))
time.units = 'days of a bisextile year'
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
time[:]=range(366)

#-----------

nc_file_mask="Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask_all'][:] #corrected mask

temp[:,:,:]=ma.array(np.zeros((366,len(lat_in),len(lon_in))),mask=[Mask_0]*366)
#%%
print("Computing climatology...")
for day_of_the_year in tqdm(range(366)): #Compute average daily temperature for each calendar day of the year, over the 1950-2020 period -> 366 days

	#print("day of the year", day_of_the_year)
	bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366] #indices of bisextile years
	not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365] #indices of non-bisextile years

	if day_of_the_year==59: #29th February
		stack_temp=ma.array(np.zeros((len(bis_years),len(lat_in),len(lon_in))),mask=[Mask_0]*len(bis_years),fill_value=np.nan)
		idx=0
		for i in bis_years:
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:],mask=Mask_0)
			idx+=1
		temp[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

	elif day_of_the_year<59:#before 29th Feb, no issues
		stack_temp=ma.array(np.zeros((len(df_bis_year),len(lat_in),len(lon_in))),mask=[Mask_0]*len(df_bis_year),fill_value=np.nan)
		idx=0
		for i in range(len(df_bis_year)):
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:],mask=Mask_0)
			idx+=1
		temp[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

	else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
		stack_temp=ma.array(np.zeros((len(df_bis_year),len(lat_in),len(lon_in))),mask=[Mask_0]*len(df_bis_year),fill_value=np.nan)
		idx=0
		for i in not_bis_years:
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year-1,:,:],mask=Mask_0)
			idx+=1
		for i in bis_years:
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:],mask=Mask_0)
			idx+=1
		temp[day_of_the_year,:,:]=np.nanmean(stack_temp, axis=0)

extended_temp=ma.array(np.zeros((366*3,len(lat_in),len(lon_in))),mask=False)
extended_temp[0:366,:,:]=temp[:,:,:]
extended_temp[0:366,:,:]=ma.array(extended_temp[0:366,:,:],mask=[Mask_0]*366)

extended_temp[366:732,:,:]=temp[:,:,:]
extended_temp[366:732,:,:]=ma.array(extended_temp[366:732,:,:],mask=[Mask_0]*366)

extended_temp[732:,:,:]=temp[:,:,:]
extended_temp[732:,:,:]=ma.array(extended_temp[732:,:,:],mask=[Mask_0]*366)

extended_temp = ma.masked_outside(extended_temp,-100,100)

smooth_span=15

print("Smoothing...")

for i in tqdm(range(366,732)):
	val_table=ma.array(np.zeros((2*smooth_span+1,len(lat_in),len(lon_in))),mask=[Mask_0]*(2*smooth_span+1))
	for j in range(-smooth_span,smooth_span+1,1):
		val_table[j]=extended_temp[i+j,:,:]
	val_table = ma.masked_outside(val_table,-100,100)
	temp[i-366,:,:] = np.nanmean(val_table,axis=0)
temp=ma.masked_outside(temp,-100,100)

f.close()
nc_file_out.close()
f_mask.close()