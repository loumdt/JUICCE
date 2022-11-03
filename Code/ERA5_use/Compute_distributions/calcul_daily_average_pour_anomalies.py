"""Compute, for each calendar day, the daily mean, max or min temperature, averaged over the period 1950-2020. Argument is either tg for mean, tn for min or tx for max"""
#%%
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from datetime import datetime
from tqdm import tqdm
import sys
import pandas as pd

#the_variable = str(sys.argv[1])
the_variable = 'tg'
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)

nc_file_in="D:/Ubuntu/PFE/Data/ERA5/era5_"+the_variable+".nc" # path to E-OBS data netCDF file

print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['lat']
lon_in=f.variables['lon']
time_in=f.variables['time']
#%%
#-------------------------------------
#import a csv table containing the index of each 1st january and 31st December
csv_bis_year=pd.read_excel("D:/Ubuntu/PFE/JUICCE/Code/ERA5_use/Compute_distributions/Dates_converter_Feuille_1.xlsx")
#store the list of the years and the number of days they contain, along with the beginning time index of each year (from 01/01/1950)
nb_day_in_year=list(csv_bis_year.iloc[2:,1].values) #365 or 366, depending on whether the year is bisextile or not
idx_start_year=list(csv_bis_year.iloc[2:,4].values) #index of 1st january for each year
idx_end_year=list(csv_bis_year.iloc[2:,5].values) #index of 31st december for each year

csv_day_idx=pd.read_excel("D:/Ubuntu/PFE/JUICCE/Code/ERA5_use/Compute_distributions/Dates_converter_Feuille_2.xlsx")
idx_day_of_year_bis=list(csv_day_idx.iloc[:,5].values)#index of each day of a bisextile year from 0 to 365
day_of_year_bis=list(csv_day_idx.iloc[:,3].values) #dates from 1st january to 31st december for a bisextile year
#%%

#-------------------------------------

#Compute the temperature data averaged over 1950-2020 for every calendar day of the year and store it in a netCDF file.

nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/ERA5/era5_"+the_variable+"_daily_mean_ovr_42yrs.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#-----------
#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', 187)    # latitude axis
lon_dim = nc_file_out.createDimension('lon', 281)    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature, averaged over 1979-2020 for every day of the year"
nc_file_out.subtitle="to be used for temperature anomaly computation"
nc_file_out.history = "Created with file calcul_daily_mean_pour_anomalies.py on " + datetime.today().strftime("%d/%m/%y")

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

nc_file_mask="D:/Ubuntu/PFE/Data/ERA5/land_sea_mask_era5.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['land_density'][:] #corrected mask
Mask_0 = (Mask_0<0.5) #mask sea cells, where there are less than 50% land
temp[:,:,:]=ma.array(np.zeros((366,187,281)),mask=[Mask_0]*366)
#%%
for day_of_the_year in tqdm(range(366)): #Compute average daily temperature for each calendar day of the year, over the 1950-2020 period -> 366 days

	#print("day of the year", day_of_the_year)
	bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366] #indices of bisextile years
	not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365] #indices of non-bisextile years

	if day_of_the_year==59: #29th February
		stack_temp=ma.array(np.zeros((len(bis_years),187,281)),mask=[Mask_0]*len(bis_years),fill_value=np.nan)
		idx=0
		for i in bis_years:
			stack_temp[idx,:,:]=f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:]-273.15
			idx+=1
		temp[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

	elif day_of_the_year<59:#before 29th Feb, no issues
		stack_temp=ma.array(np.zeros((42,187,281)),mask=[Mask_0]*42,fill_value=np.nan)
		idx=0
		for i in range(42):
			stack_temp[idx,:,:]=f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:]-273.15
			idx+=1
		temp[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

	else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
		stack_temp=ma.array(np.zeros((42,187,281)),mask=False,fill_value=np.nan)
		idx=0
		for i in not_bis_years:
			stack_temp[idx,:,:]=f.variables[the_variable][idx_start_year[i]+day_of_the_year-1,:,:]-273.15
			idx+=1
		for i in bis_years:
			stack_temp[idx,:,:]=f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:]
			idx+=1
		temp[day_of_the_year,:,:]=np.nanmean(stack_temp, axis=0)
#%%
f.close()
nc_file_out.close()
f_mask.close()