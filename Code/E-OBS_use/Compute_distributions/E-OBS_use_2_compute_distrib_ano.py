"""Compute, for every calendar day, the n-th percentile of the corresponding distribution of daily mean, 
max or min temperature anomaly, and save the threshold list into a npy file. 
The time span of the distribution is 15 days. Argument 1 is either tg for mean, tn for min or tx for max. 
Argument 2 is the percentile threshold (default 95). Arguments 3 and 4 correspond to the chosen period (default 1950 and 2021)."""
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from tqdm import tqdm
import sys
import pandas as pd

try : 
    the_variable = str(sys.argv[1])
except :
    the_variable='tg'

try : 
    threshold_value = sys.argv[2]
except :
    threshold_value = 95

try : 
    year_beg = int(sys.argv[3])
except :
    year_beg = 1950
    
try : 
    year_end = int(sys.argv[4])
except :
    year_end = 2021

print('the_variable :',the_variable)
print('threshold_value :',threshold_value)

nc_file_in="Data/E-OBS/0.1deg/"+the_variable+"_ens_mean_0.1deg_reg_v26.0e.nc"

print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['latitude']
lon_in=f.variables['longitude']
time_in=f.variables['time']

nc_file_anomaly="Data/E-OBS/0.1deg/"+the_variable+"_daily_avg_"+str(year_beg)+"_"+str(year_end)+"_smoothed.nc"  #path to the netCDF file
#load netCDF file of the smoothed daily average temperature for anomaly computation
f_anomaly=nc.Dataset(nc_file_anomaly, mode='r')
T_mean_ano=np.zeros((376,len(lat_in),len(lon_in)))
T_mean_ano[0:-10,:,:]=f_anomaly.variables['temp'][:,:,:]
T_mean_ano[-10:,:,:]=f_anomaly.variables['temp'][0:10,:,:]

#-------------------------------------
#import a xlsx table containing the index of each 1st january and 31st December
df_bis_year = pd.read_excel("Code/E-OBS_use/Compute_distributions/Dates_converter_1.xlsx",header=0, index_col=0)
df_bis_year = df_bis_year.loc[year_beg:year_end,:]
nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year

#-------------------------------------
nc_file_mask="Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0=f_mask.variables['mask_all'][:]

threshold_table=ma.array(np.zeros((366,len(lat_in),len(lon_in))),mask=[Mask_0]*366)

for day_of_the_year in tqdm(range(366)):
	list_table=[]
	threshold_table[day_of_the_year,:,:]=f.variables[the_variable][day_of_the_year,:,:]
	bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366]
	not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365]
	if day_of_the_year==59: #29th February
		for i in bis_years:
			for j in range(-7,8,1):
				list_table.append(f.variables[the_variable][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
	elif day_of_the_year<59:#before 29th Feb, no issues
		i=0 #year 1950, beginning of data
		for j in range(np.min([-day_of_the_year,-7]),8,1):
				list_table.append(f.variables[the_variable][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
		for i in range(70):
			for j in range(-7,8,1):
				list_table.append(f.variables[the_variable][idx_start_year[i+1]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
				
	else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
		for i in not_bis_years:
			for j in range(-7,8,1):
				list_table.append(f.variables[the_variable][idx_start_year[i]+day_of_the_year-1+j,:,:]-T_mean_ano[day_of_the_year-1+j,:,:])
		for i in bis_years[:-1]:
			for j in range(-7,8,1):
				list_table.append(f.variables[the_variable][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
		i = bis_years[-1]
		for j in range(-7,np.min([8,365-day_of_the_year]),1):
				list_table.append(f.variables[the_variable][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])

	list_table=ma.masked_outside(list_table,-100,100)		
	threshold_table[day_of_the_year,:,:]=np.percentile(list_table[:],threshold_value,axis=0)

f.close()
f_anomaly.close()
f_mask.close()
filename="Data/E-OBS/0.1deg/distrib_"+the_variable+"_ano_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"%_threshold_15days.npy"
threshold_table.dump(filename) #saving the distribution as a masked array in a numpy file