"""Delete the temperature data if it is not strictly positive for at least the given number of consecutive days. 
Argument 1 is either tg for mean, tx for max, or tn for min (default tg).
Argument 2 and 3 are the chosen period (default 1950 and 2021).
Argument 4 is the chosen percentile threshold (default 95).
Argument 5 is the chosen minimal duration (default 4).
"""
#%%
import numpy as np
import numpy.ma as ma 
import netCDF4 as nc 
from datetime import date, timedelta, datetime
from tqdm import tqdm
import sys,os
import pathlib
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
    
try : 
    nb_days = int(sys.argv[5])
except :
    nb_days = 4
#%%
print("the_variable :",the_variable)
nc_in_path = os.path.join(datadir , "ERA5" , "t2m" , the_variable+'_anomaly_JJA_'+str(year_beg)+'_'+str(year_end)+'_scaled_'+str(threshold_value)+'th.nc')
#%%    
f=nc.Dataset(nc_in_path, mode='r')
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
#%%
#-------------------
nc_out_path = os.path.join(datadir , "ERA5" ,"t2m", "Detection_Canicule" , "potential_heatwaves_"+the_variable+"_"+str(nb_days)+"days_before_scan_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th.nc")
pathlib.Path(nc_out_path).parents[0].mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to).
char_dim=nc_file_out.createDimension('nchar', 10) #in order to save dates on date format as strings

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature anomaly for JJA days corresponding to a potential heatwave duration, from "+str(year_beg)+" to "+str(year_end)
nc_file_out.subtitle="values are masked where and when not exceeding "+str(threshold_value)+"th temperature anomaly threshold for "+str(nb_days)+" consecutive days or more. Created with detect_heatwaves_4days_first_step.py on "+ datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = 'days of JJA containing a sub-heatwave from '+str(year_beg)+' to '+str(year_end)
time.long_name = 'time'
# Define a 3D variable to hold the data
t2m = nc_file_out.createVariable('t2m',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
t2m.units = '°C' # degrees Celsius
t2m.standard_name = 'air_temperature' # this is a CF standard name

date_idx = nc_file_out.createVariable('date_idx', np.int32,('time',))
date_idx.units = 'days of JJA containing a sub-heatwave from '+str(year_beg)+' to '+str(year_end)+', recorded as the matching index of the '+str(the_variable)+'_anomaly_JJA_'+str(year_beg)+'_'+str(year_end)+'_scaled_'+str(threshold_value)+'th.nc file'
date_idx.long_name = 'date_index'
date_idx_1950 = nc_file_out.createVariable('date_idx_1950', np.int32,('time',))
date_idx_1950.units = 'days from 01-01-1950'
date_idx_1950.long_name = 'date_index_1950'
date_format = nc_file_out.createVariable('date_format', 'S1',('time','nchar'))
date_format.units = 'days on YYYY-mm-dd format'
date_format.long_name = 'date_as_date_format'
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements
lat[:] = lat_in[:] 
lon[:] = lon_in[:]
#-------------------
#create a table with all the dates of the considered data
calendar=np.zeros(((year_end-year_beg+1),92),dtype=object) 
for year in range((year_end-year_beg+1)) :
    strt_date=date(year+year_beg,6,1) #start date of ERA5 data
    tps=0
    day_start_JJA=day_num=str(int(time_in[year*92]))
    for day in time_in[year*92:(year+1)*92]:  #01/06 to 31/08 of the given year, change days since 1/1/1950 to dates, store it into calendar list
        day=int(day)
        day_num=str(day)
        day_num.rjust(3 + len(day_num), '0')
        res_date=strt_date + timedelta(days=int(day_num)-int(day_start_JJA))
        res = res_date.strftime("%Y-%m-%d")
        calendar[year,tps]=res
        tps+=1
print('Summer calendar has been created on YYYY-mm-dd format from',calendar[0,0],'to',calendar[-1,-1])
#%%
#-------------------
date_idx_1950[:]=f.variables['date_idx_1950'][:]
for year in tqdm(range((year_end-year_beg+1))) :
    stack_temp=ma.array(-9999*np.ones((92,len(lat_in),len(lon_in))),mask=False) #create a 3D variable that will hold the temperature anomalies when and where there are heatwaves
    stack_where=ma.array(np.zeros((len(lat_in),len(lon_in))),mask=False)
    for day in range(92):
        temp_masked_filled=ma.filled(f.variables['t2m'][year*92+day,:,:],fill_value=-9999)
        stack_where[:,:]=stack_where[:,:]+np.ones((len(lat_in),len(lon_in)))*(temp_masked_filled!=-9999) #add one day to each potential heatwave location
        stack_where[:,:]=stack_where[:,:]*(temp_masked_filled!=-9999) #when not adding a day, have to set back the duration to zero
        if day>=nb_days-1 :
            #for j,k in np.argwhere(stack_where >= nb_days):
            #    stack_temp[day-(nb_days-1):day+1,j,k]=f.variables['temp'][year*92+day-(nb_days-1):year*92+day+1,j,k]
            stack_temp[day-(nb_days-1):day+1,:,:] = stack_temp[day-(nb_days-1):day+1,:,:]*(stack_temp[day-(nb_days-1):day+1,:,:]!=-9999)+f.variables['t2m'][year*92+day-(nb_days-1):year*92+day+1,:,:]*((stack_where>=nb_days)*stack_temp[day-(nb_days-1):day+1,:,:]==-9999)+(-9999*((stack_where<nb_days)*(stack_temp[day-(nb_days-1):day+1,:,:]==-9999))) #record the last four days for the corresponding scanning window
        date_format[year*92+day] = nc.stringtochar(np.array([calendar[year,day]], 'S10'))
        date_idx[year*92+day]=year*92+day
    t2m[year*92:(year+1)*92,:,:]=stack_temp[:,:,:]
t2m[:] = ma.masked_outside(t2m[:],-300,400)
time[:]=range(np.shape(t2m)[0])

f.close()
nc_file_out.close()