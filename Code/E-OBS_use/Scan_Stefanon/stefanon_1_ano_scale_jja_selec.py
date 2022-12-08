"""Create a netCDF file with daily mean temperature anomaly for
concatenated JJAs for the chosen period (default 1950-2021) when and where the n-th (default 95th) percentile threshold is exceeded ; 
Otherwise, values are set to -9999 ;
Argument 1 is either tg for mean, tn for min or tx for max (default tg).
Argument 2 and 3 are the chosen period (default are 1950 and 2021).
Argument 4 is the chosen threshold (default 95)."""
#%%
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from datetime import datetime
from tqdm import tqdm
import sys
import pandas as pd
#%%
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

try : 
    threshold_value = int(sys.argv[4])
except :
    threshold_value = 95

print('the_variable :',the_variable)
#-------------------------------------
#Load temperature data file
nc_file_in="Data/E-OBS/0.1deg/"+the_variable+"_ens_mean_0.1deg_reg_v26.0e.nc"
print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['latitude']
lon_in=f.variables['longitude']
time_in=f.variables['time']
#-------------------------------------
#Load average climatology temperature file
nc_file_anomaly="Data/E-OBS/0.1deg/"+the_variable+"_daily_avg_"+str(year_beg)+"_"+str(year_end)+"_smoothed.nc"  #path to the netCDF file
f_anomaly=nc.Dataset(nc_file_anomaly, mode='r') 
T_mean=f_anomaly.variables['temp'][152:244,:,:]
#-------------------------------------
#Load E-OBS Europe mask
nc_file_mask="Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask_all'][:]
#-------------------------------------
#Only record the JJA temperatures and remove the values that do not exceed the n-th (default 95th) percentile threshold
nc_file_out=nc.Dataset("Data/E-OBS/0.1deg/"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value)+"th.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', 92*(year_end-year_beg+1)) # unlimited time axis (can be appended to).

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature anomaly for JJA days from "+str(year_beg)+" to "+str(year_end)
nc_file_out.subtitle="values put to zero where not exceeding "+str(threshold_value)+"th temperature anomaly threshold."
nc_file_out.history = "Created with ano_scale_jja_selec.py on " +datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = 'days of JJA from '+str(year_beg)+' to '+str(year_end)
time.long_name = 'time'
date_idx_1950 = nc_file_out.createVariable('date_idx_1950', np.int32,('time',))
date_idx_1950.units = 'days from 01-01-1950'
date_idx_1950.long_name = 'date_index_1950'
# Define a 3D variable to hold the data
temp = nc_file_out.createVariable('temp',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
temp.units = '°C' # degrees Celsius
temp.standard_name = 'air_temperature' # this is a CF standard name
temp.long_name = 'daily '+temp_name_dict[the_variable]+' temperature anomaly'
#-----------
#%%
#import a xlsx table containing the index of each 1st january and 31st December
df_bis_year = pd.read_excel("Code/E-OBS_use/Compute_distributions/Dates_converter_1.xlsx",header=0, index_col=0)
df_bis_year = df_bis_year.loc[year_beg:year_end,:]
nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year
#-------------------------------------
#%%
f_threshold = nc.Dataset('Data/E-OBS/0.1deg/distrib_'+the_variable+'_ano_'+str(year_beg)+'_'+str(year_end)+'_'+str(threshold_value)+'th_threshold_15days.nc', mode='r')
threshold_table = f_threshold.variables['threshold'][:]
threshold_table=ma.masked_outside(threshold_table[152:244,:,:],-60,60) #threshold of n-th (default 95th) temperature anomaly percentile for every day of JJA and location
#-------------------------------------
# Write latitudes, longitudes,time.
# Note: the ":" is necessary in these "write" statements
lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(92*(year_end-year_beg+1))
temp[:,:,:]=ma.array(np.zeros((92*(year_end-year_beg+1),len(lat_in),len(lon_in))),mask=[Mask_0]*(92*(year_end-year_beg+1))) # 92*(year_end-year_beg+1), 92 days of JJA times the number of years 
date_idx_1950[:]=np.zeros((92*(year_end-year_beg+1),))
#-------------------------------------
bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366]
not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365]
#%%
for i in tqdm(range(year_end-year_beg+1)) :
    bis_year_flag=(1-(df_bis_year.loc[i+year_beg,'Nb_days']-365)) #flag put to one for non leap years and to zero for leap years
    for j in range(92):#92 days of JJA for each year i
        temp[92*i+j,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+152-bis_year_flag+j,:,:]-T_mean[j,:,:],mask=Mask_0)
    ano_scale = np.zeros(np.shape(temp[i*92:(i+1)*92,:,:]))
    ano_scale = temp[i*92:(i+1)*92,:,:] - threshold_table
    ano_scale_bool = (ano_scale <0) #array for the mask : when condition is True, the n-th percentile is not exceeded, value should be masked
    temp[i*92:(i+1)*92,:,:] = temp[i*92:(i+1)*92,:,:]*(1-ano_scale_bool)+(-9999*ano_scale_bool) #set pixels that must be masked to -9999
    date_idx_1950[i*92:(i+1)*92] = range(idx_start_year[i]+152-bis_year_flag,idx_start_year[i]+152-bis_year_flag+92)
temp = ma.masked_outside(temp,-100,100)

f.close()
nc_file_out.close()
f_mask.close()
f_anomaly.close()
f_threshold.close()