"""Compute, for every calendar day, the 95th percentile of the corresponding distribution of daily mean, max or min temperature anomaly, and save the threshold list into a npy file. The time span of the distribution is 15 days. Argument 1 is either tg for mean, tn for min or tx for max. Argument 2 is the percentile threshold"""
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
import csv
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])
threshold_value = sys.argv[2]
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)
print('threshold_value :',threshold_value)

nc_file_in="D:/Ubuntu/PFE/Data/E-OBS/0.1deg/"+the_variable+"_ens_mean_0.1deg_reg_v23.1e.nc"

print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['latitude']
lon_in=f.variables['longitude']
time_in=f.variables['time']

nc_file_anomaly='D:/Ubuntu/PFE/Data/E-OBS/0.1deg/'+the_variable+'_daily_mean_ovr_70yrs_smoothed.nc'  #path to the netCDF file
#load netCDF file of the smoothed daily average temperature for anomaly computation
f_anomaly=nc.Dataset(nc_file_anomaly, mode='r')
T_mean_ano=np.zeros((376,465,705))
T_mean_ano[0:-10,:,:]=f_anomaly.variables['temp'][:,:,:]
T_mean_ano[-10:,:,:]=f_anomaly.variables['temp'][0:10,:,:]

#-------------------------------------

csv_bis_year=csv.reader(open("D:/Ubuntu/PFE/Data/EM-DAT/Dates_converter_Feuille_1.csv","r"))
bis_year_list=list(csv_bis_year) #store the list of the years and the number of days they contain, along with the beginning time index of each year (from 01/01/1950)
nb_day_in_year=[int(ligne[1]) for ligne in bis_year_list[2:]] #365 or 366, depending on whether the year is bisextile or not
idx_start_year=[int(ligne[4]) for ligne in bis_year_list[2:]] #index of 1st january for each year
idx_end_year=[int(ligne[5]) for ligne in bis_year_list[2:]] #index of 31st december for each year


csv_day_idx=csv.reader(open("D:/Ubuntu/PFE/Data/EM-DAT/Dates_converter_Feuille_2.csv","r"))
day_idx_list=list(csv_day_idx) #store the list of the index of each day of a bisextile and non-bisextile years (0 to 364 or 0 to 365)
idx_day_of_year_bis=[int(ligne[5]) for ligne in day_idx_list[2:]] #index of each day of a bisextile year from 0 to 365
day_of_year_bis=[ligne[3] for ligne in day_idx_list[2:]] #dates from 1st january to 31st december for a bisextile year


#-------------------------------------


#nc_file_mask="/data/tmandonnet/E-OBS/Mask/Mask_Europe.nc"
nc_file_mask="D:/Ubuntu/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')

Mask_0=f_mask.variables['mask_all'][:]
Mask_all=[Mask_0]*366

threshold_table=ma.array(np.zeros((366,465,705)),mask=Mask_all)

for day_of_the_year in tqdm(range(366)):
	list_table=[]
	threshold_table[day_of_the_year,:,:]=f.variables[the_variable][day_of_the_year,:,:]
	#print("day of the year", day_of_the_year)
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
filename="D:/Ubuntu/PFE/Data/E-OBS/0.1deg/distrib_"+the_variable+"_ano_npy_"+str(threshold_value)+"%_threshold_15days.npy"
threshold_table.dump(filename) #saving the distribution as a masked array in a numpy file