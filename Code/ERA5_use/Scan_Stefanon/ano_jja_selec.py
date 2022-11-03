"""Create a netCDF file with daily mean temperature anomaly for concatenated summers from 1950 to 2020. Argument is either tg for mean, tn for min or tx for max"""

import numpy as np
import numpy.ma as ma
import netCDF4 as nc
import csv
from datetime import datetime
from tqdm import tqdm
import sys


the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable) #daily mean temperature, or max, or min

nc_file_in="D:/Ubuntu/PFE/Data/E-OBS/0.1deg/"+the_variable+"_ens_mean_0.1deg_reg_v23.1e.nc"


print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['latitude']
lon_in=f.variables['longitude']
time_in=f.variables['time']

#-------------------------------------
nc_file_anomaly="D:/Ubuntu/PFE/Data/E-OBS/0.1deg/"+the_variable+"_daily_mean_ovr_70yrs_smoothed.nc"  #path to the netCDF file

f_anomaly=nc.Dataset(nc_file_anomaly, mode='r') 
T_mean=f_anomaly.variables['temp'][152:244,:,:]
#-------------------------------------

nc_file_mask="D:/Ubuntu/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask_all'][:]


#Only record the summer temperatures

nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_"+the_variable+"_summer_only_1950-2020.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#-----------
csv_bis_year=csv.reader(open("D:/Ubuntu/PFE/Code/E-OBS_use/Moyennes_mensuelles/Dates_converter_Feuille_1.csv","r"))
bis_year_list=list(csv_bis_year) #store the list of the years and the number of days they contain, along with the beginning time index of each year (from 01/01/1950)
nb_day_in_year=[int(ligne[1]) for ligne in bis_year_list[2:]] #365 or 366, depending on whether the year is bisextile or not
idx_start_year=[int(ligne[4]) for ligne in bis_year_list[2:]] #index of 1st january for each year
idx_end_year=[int(ligne[5]) for ligne in bis_year_list[2:]] #index of 31st december for each year


csv_day_idx=csv.reader(open("D:/Ubuntu/PFE/Code/E-OBS_use/Moyennes_mensuelles/Dates_converter_Feuille_2.csv","r"))
day_idx_list=list(csv_day_idx) #store the list of the index of each day of a bisextile and non-bisextile years (0 to 364 or 0 to 365)
idx_day_of_year_bis=[int(ligne[5]) for ligne in day_idx_list[2:]] #index of each day of a bisextile year from 0 to 365
day_of_year_bis=[ligne[3] for ligne in day_idx_list[2:]] #dates from 1st january to 31st december for a bisextile year


#-------------------------------------

#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', 465)    # latitude axis
lon_dim = nc_file_out.createDimension('lon', 705)    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to).

nc_file_out.title="Daily "+temp_name_dict[the_variable]+" temperature for summer days from 1950 to 2020"

nc_file_out.subtitle="to be used for heatwaves analysis. Created with ano_jja_selec.py on " + datetime.today().strftime("%d/%m/%y")

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float64, ('time',))
time.units = 'days of summer from 1950 to 2020'
time.long_name = 'time'
# Define a 3D variable to hold the data
temp = nc_file_out.createVariable('temp',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
temp.units = '°C' # degrees Celsius
temp.standard_name = 'air_temperature' # this is a CF standard name

nlats = len(lat_dim); nlons = len(lon_dim); ntimes = 6532 # 92*71
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements

lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(6532) # 92*71

#-----------
temp[:,:,:]=ma.array(np.zeros((6532,465,705)),mask=False) # 6532 = 92*71

#-------------------------------------
bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366]
not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365]



for i in tqdm(range(71)) :
    #print("summer ", i, "/70")
    bis_year_flag=1 #flag put to one for non-bisextile year
    for p in range(len(bis_years)) :
        if bis_years[p]== i+1950 :
            bis_year_flag=0 #if the considered year is bisextile, put flag to zero
    for j in range(92):
        temp[92*i+j,:,:]=ma.array(f.variables[the_variable][idx_start_year[i]+152-bis_year_flag+j,:,:]-T_mean[j,:,:],mask=Mask_0)

temp = ma.masked_outside(temp,-100,100)

print(np.max(temp),np.min(temp))

f.close()
f_anomaly.close()
f_mask.close()
nc_file_out.close()