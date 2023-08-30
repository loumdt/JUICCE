"""Compute, for each calendar day, the daily mean, max or min temperature, averaged over the chosen period.
The seasonal cycle is then smoothed with a 31-day window.
Argument 1 is either tg for mean, tn for min or tx for max (default tg). 
Argument 2 and 3 are respectively the first year and the last year to be included in the computation (default 1950 and 2021)."""
#%%
import numpy as np
import numpy.ma as ma #use masked array
import netCDF4 as nc #load and write netcdf data
from datetime import datetime #create file history with creation date
from tqdm import tqdm #create a user-friendly feedback while script is running
import sys,os #read inputs
import pandas as pd #handle dataframes
import pathlib
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#read inputs or use defaults inputs
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
print('year_beg :',year_beg)
print('year_end :',year_end)
#%%
#Load netcdf temperature data file :
nc_in_path = os.path.join(datadir,"E-OBS","t2m",f"{the_variable}_ens_mean_0.1deg_reg_v26.0e.nc") # path to E-OBS data netCDF file
f=nc.Dataset(nc_in_path, mode='r') #load file
lat_in=f.variables['latitude'][:] #load dimensions
lon_in=f.variables['longitude'][:]
time_in=f.variables['time'][:]
#%%
#-------------------------------------
#import a xlsx table containing the index of each 1st january and 31st December
df_bis_year = pd.read_excel(os.path.join(datadir,"Dates_converter_E-OBS.xlsx"),header=0, index_col=0)
df_bis_year = df_bis_year.loc[year_beg:year_end,:] #select chosen period
nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year

#%%
#-------------------------------------
#Define netCDF output file :
#Compute the temperature data averaged over the chosen period (default 1950-2021) for every calendar day of the year and store it in a netCDF file.
nc_out_path = os.path.join(datadir,"E-OBS","t2m",the_variable+"_daily_avg_"+str(year_beg)+"_"+str(year_end)+"_smoothed.nc")
pathlib.Path(nc_out_path).parents[0].mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature, averaged over "+str(year_beg)+"-"+str(year_end)+" for every day of the year, and smoothed to eliminate variability."
nc_file_out.subtitle="To be used for temperature anomaly computation"
nc_file_out.history = "Created with file E-OBS_use_t2m_1_compute_climatology_smooth.py on " + datetime.today().strftime("%d/%m/%y")

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
t2m = nc_file_out.createVariable('t2m',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
t2m.units = '°C' # degrees Celsius
t2m.long_name = 't2m'
t2m.standard_name = '2m_temperature' # this is a CF standard name

nlats = len(lat_dim); nlons = len(lon_dim); ntimes = 366
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements -> you want to write the content and not to change the definition of the dimension
lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(366)

t2m[:,:,:]=ma.array(np.zeros((366,len(lat_in),len(lon_in))),mask=False) #set output netcdf variable
#%%
print("Computing climatology...")
for day_of_the_year in tqdm(range(366)): #Compute average daily temperature for each calendar day of the year, over the 1950-2020 period -> 366 days
	bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366] #indices of bisextile years
	not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365] #indices of non-bisextile years

	if day_of_the_year==59: #29th February
		stack_temp=ma.array(np.zeros((len(bis_years),len(lat_in),len(lon_in))),fill_value=np.nan)
		idx=0
		for i in bis_years:
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:])
			idx+=1
		t2m[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

	elif day_of_the_year<59:#before 29th Feb, no issues
		stack_temp=ma.array(np.zeros((len(df_bis_year),len(lat_in),len(lon_in))),fill_value=np.nan)
		idx=0
		for i in range(len(df_bis_year)):
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:])
			idx+=1
		t2m[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

	else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
		stack_temp=ma.array(np.zeros((len(df_bis_year),len(lat_in),len(lon_in))),fill_value=np.nan)
		idx=0
		for i in not_bis_years:
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year-1,:,:])
			idx+=1
		for i in bis_years:
			stack_temp[idx,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+day_of_the_year,:,:])
			idx+=1
		t2m[day_of_the_year,:,:]=np.nanmean(stack_temp, axis=0)

extended_temp=ma.array(np.zeros((366*3,len(lat_in),len(lon_in))))
extended_temp[0:366,:,:]=t2m[:,:,:]

extended_temp[366:732,:,:]=t2m[:,:,:]

extended_temp[732:,:,:]=t2m[:,:,:]

extended_temp[:] = ma.masked_outside(extended_temp[:],-300,400)

smooth_span=15

print("Smoothing...")

for i in tqdm(range(366,732)):
	val_table=ma.array(np.zeros((2*smooth_span+1,len(lat_in),len(lon_in))))
	for j in range(-smooth_span,smooth_span+1,1):
		val_table[j]=extended_temp[i+j,:,:]
	val_table[:] = ma.masked_outside(val_table[:],-300,400)
	t2m[i-366,:,:] = np.nanmean(val_table[:],axis=0)
t2m[:]=ma.masked_outside(t2m[:],-300,400)

f.close()
nc_file_out.close()