"""Delete the temperature data if it is not strictly positive for at least 4 consecitive days. Argument is either tg for mean, tx for max, or tn for min."""
import numpy as np
import numpy.ma as ma 
import netCDF4 as nc 
from datetime import date, timedelta, datetime
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print("the_variable :",the_variable)
#nc_file = '/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/temp_anomaly_summer_only_1950-2020_scaled_to_95th.nc'
nc_file = 'D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_'+the_variable+'_anomaly_summer_only_1950-2020_scaled_to_95th.nc'
f=nc.Dataset(nc_file, mode='r')
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]

#-------------------

#nc_file_out=nc.Dataset("/data/tmandonnet/E-OBS/DetectionCanicule/potential_heatwaves_4_days_before_scan.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/potential_heatwaves_"+the_variable+"_4_days_before_scan.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', 465)    # latitude axis
lon_dim = nc_file_out.createDimension('lon', 705)    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to).
char_dim=nc_file_out.createDimension('nchar', 10) #in order to save dates on date format as strings

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature anomaly for summer days corresponding to a potential heatwave duration, from 1950 to 2020"
nc_file_out.subtitle="values put to zero where not exceeding 95th temperature anomaly threshold for 4 consecutive days or more. Created with detect_heatwaves_4days_first_step.py on "+ datetime.today().strftime("%d/%m/%y")

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
temp = nc_file_out.createVariable('temp',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
temp.units = '°C' # degrees Celsius
temp.standard_name = 'air_temperature' # this is a CF standard name

date_idx = nc_file_out.createVariable('date_idx', np.int32,('time',))
date_idx.units = 'days of summer containing a sub-heatwave from 1950 to 2020, recorded as the matching index of the temp_anomaly_summer_only_1950-2020_scaled_to_95th.nc file'
date_idx.long_name = 'date_index'
date_format = nc_file_out.createVariable('date_format', 'S1',('time','nchar'))
date_format.units = 'days of summer containing a sub-heatwave from 1950 to 2020, recorded as strings'
date_format.long_name = 'date_as_date_format'
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements
lat[:] = lat_in[:] 
lon[:] = lon_in[:]

#-------------------

#nc_file_mask="/data/tmandonnet/E-OBS/Mask/Mask_Europe.nc"
nc_file_mask="D:/Ubuntu/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc"
f_mask=nc.Dataset(nc_file_mask,mode='r')
mask_all=f_mask.variables['mask_all'][:]

#-------------------

#create a table with all the dates of the considered data
calendar=np.zeros((71,92),dtype=object) 
for year in range(71) :
    strt_date=date(year+1950,6,1) #start date of E-OBS data
    tps=0
    day_start_summer=day_num=str(int(time_in[year*92]))
    for day in time_in[year*92:(year+1)*92]:  #01/06 to 31/08 of the given year, change days since 1/1/1950 to dates, store it into calendar list
        day=int(day)
        day_num=str(day)
        day_num.rjust(3 + len(day_num), '0')
        res_date=strt_date + timedelta(days=int(day_num)-int(day_start_summer))
        res = res_date.strftime("%d-%m-%Y")
        calendar[year,tps]=res
        tps+=1
print('Summer calendar has been created on dd-mm-YYYY format from',calendar[0,0],'to',calendar[-1,-1])

#-------------------

for year in tqdm(range(71)) :
    #print('year',year,'/',70)
    stack_temp=ma.array(np.zeros((92,len(lat),len(lon))),mask=[mask_all]*92) #create a 3D variable that will hold the temperature anomalies when and where there are heatwaves
    stack_where=ma.array(np.zeros((len(lat),len(lon))),mask=mask_all)
    for day in range(92):
        temp_masked=ma.array(f.variables['temp'][year*92+day,:,:],mask=mask_all)
        stack_where[:,:]=stack_where[:,:]+np.ones((len(lat),len(lon)))*(temp_masked>0) #add one day to each potential heatwave location
        stack_where[:,:]=stack_where[:,:]*(temp_masked>0) #when not adding a day, have to set back the duration to zero
        for j,k in np.argwhere(stack_where >= 4):
            stack_temp[day-3:day+1,j,k]=f.variables['temp'][year*92+day-3:year*92+day+1,j,k] #record the last four days for the corresponding scanning window
        date_format[year*92+day] = nc.stringtochar(np.array([calendar[year,day]], 'S10'))
        date_idx[year*92+day]=year*92+day
    temp[year*92:(year+1)*92,:,:]=stack_temp[:,:,:]

time[:]=range(np.shape(temp)[0])

f.close()
nc_file_out.close
f_mask.close()