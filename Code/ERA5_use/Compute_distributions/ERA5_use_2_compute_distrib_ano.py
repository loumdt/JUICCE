"""Compute, for every calendar day, the n-th percentile of the corresponding distribution of daily mean, 
max or min temperature anomaly, and save the threshold list into a npy file. 
The time span of the distribution is 15 days. Argument 1 is either tg for mean, tn for min or tx for max (default tg). 
Arguments 2 and 3 correspond to the chosen period (default 1950 and 2021). Argument 4 is the percentile threshold (default 95). """
#%%
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from tqdm import tqdm
import sys,os
import pandas as pd
from datetime import datetime
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
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
    threshold_value = sys.argv[4]
except :
    threshold_value = 90

#%%
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
print('the_variable :',the_variable)
print('threshold_value :',threshold_value)
print('year_beg :',year_beg)
print('year_end :',year_end)
#%%

#Load netcdf temperature data file :
nc_in_path = os.path.join(datadir,"ERA5","t2m","ERA5_"+the_variable+"_Europe_day_0.25deg_1950-2021.nc") # path to ERA5 data netCDF file
print('nc_file_in',nc_in_path)
f=nc.Dataset(nc_in_path, mode='r') #load file
lat_in=f.variables['lat'][:] #load dimensions
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]

nc_file_anomaly=os.path.join(datadir,"ERA5","t2m",the_variable+"_daily_avg_"+str(year_beg)+"_"+str(year_end)+"_smoothed.nc")  #path to the netCDF file
#load netCDF file of the smoothed climatology daily average temperature for anomaly computation
f_mean=nc.Dataset(nc_file_anomaly, mode='r')
T_mean_ano=np.zeros((376,len(lat_in),len(lon_in)))
T_mean_ano[0:-10,:,:]=f_mean.variables['t2m'][:,:,:]
T_mean_ano[-10:,:,:]=f_mean.variables['t2m'][0:10,:,:]

nc_out_path = os.path.join(datadir,"ERA5","t2m","distrib_"+the_variable+"_ano_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_15days.nc")
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
#-----------
#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title=str(threshold_value)+"th percentile of the "+temp_name_dict[the_variable]+" temperature distribution, for each location, and calendar day (with a 15-day centered window). Computed for "+str(year_beg)+"-"+str(year_end)+"period."
nc_file_out.history = "Created with file ERA5_use_2_compute_distrib_ano.py on " + datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = 'days of a bisextile year'
time.long_name = 'time'
# Define a 3D variable to hold the data
threshold = nc_file_out.createVariable('threshold',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
threshold.units = '°C' # degrees Celsius
threshold.standard_name = 'air_temperature' # this is a CF standard name

nlats = len(lat_dim); nlons = len(lon_dim); ntimes = 366
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements

lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(366)

#-------------------------------------
#import a xlsx table containing the index of each 1st january and 31st December
df_bis_year = pd.read_excel(os.path.join(datadir,"Dates_converter_E-OBS.xlsx"),header=0, index_col=0)
df_bis_year = df_bis_year.loc[year_beg:year_end,:]
nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year


threshold[:,:,:]=ma.array(np.zeros((366,len(lat_in),len(lon_in))),mask=False)

bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366] #list of indices corresponding to leap years
not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365] #list of indices corresponding to non-leap years
last_year_is_bis = np.max(bis_years)>np.max(not_bis_years) #boolean value, True if the last year of the studied period is a leap year, False otherwise
#%%
for day_of_the_year in tqdm(range(366)):
	list_table=[]
	threshold[day_of_the_year,:,:]=f.variables['t2m'][day_of_the_year,:,:]
	if day_of_the_year==59: #29th February
		for i in bis_years:
			for j in range(-7,8,1):
				list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
	elif day_of_the_year<59:#before 29th Feb, no issues
		i=0
		for j in range(np.max([-day_of_the_year,-7]),8,1):
				list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
		for i in range(len(df_bis_year)-1):
			for j in range(-7,8,1):
				list_table.append(f.variables['t2m'][idx_start_year[i+1]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
				
	else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
		if last_year_is_bis : #if the last year of the period is a leap year
			for i in not_bis_years:
				for j in range(-7,8,1):
					list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year-1+j,:,:]-T_mean_ano[day_of_the_year-1+j,:,:])
			for i in bis_years[:-1]:
				for j in range(-7,8,1):
					list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
			i = bis_years[-1]
			for j in range(-7,np.min([8,365-day_of_the_year]),1):
					list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
		else : #if the last year of the period is not a leap year
			for i in not_bis_years[:-1]:
				for j in range(-7,8,1):
					list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year-1+j,:,:]-T_mean_ano[day_of_the_year-1+j,:,:])
			for i in bis_years:
				for j in range(-7,8,1):
					list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
			i = not_bis_years[-1]
			for j in range(-7,np.min([8,365-day_of_the_year]),1):
					list_table.append(f.variables['t2m'][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
	list_table=ma.masked_outside(list_table,-200,200)
	list_table = list_table - 273.15 #convert K to °C		
	threshold[day_of_the_year,:,:]=ma.array(np.percentile(list_table[:],threshold_value,axis=0),mask=False)
threshold = ma.masked_outside(threshold,-200,200)
f.close()
f_mean.close()
nc_file_out.close()