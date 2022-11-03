"""Scan temperature maps to extract heatwaves. Argument is either tg for mean, tx for max, or tn for min."""
import numpy as np
import numpy.ma as ma 
import netCDF4 as nc 
from datetime import date, timedelta, datetime
from tqdm import tqdm
import sys

scan_size = 35 #with resolution of 0.1 degree, 35 corresponds to 3.5 degrees
quantieme = 95 #95th percentile threshold
pourcent = 0.6

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

def scan(the_variable,scan_size,quantieme,pourcent) :
#--------------------------------------------
	#nc_file = '/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/temp_anomaly_summer_only_1950-2020_scaled_to_95th.nc'
	nc_file = 'D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/potential_heatwaves_'+the_variable+'_4_days_before_scan.nc'
	#nc_file = '/data/tmandonnet/E-OBS/0.1deg/temp_anomaly_summer_only_1950-2020_scaled_to_95th.nc'

	#the 'temp' variable is the daily mean, min or max temperature anomaly, set to zero when not exceeding the threshold defined by the 95th percentile temperature anomaly

	an = 71 #number of years 1950-2020
	scan_lon = scan_size
	scan_lat = scan_size
	print('the_variable =', the_variable)
	print('quantieme =',quantieme)
	print('scan_size =',0.1*scan_size,'°') 
	print('pourcent =', pourcent*100,'%')
	#date_list=[] #list that will record, in date format, the days corresponding to a sub-heatwave day (heatwave needs a temporal continuity criterion that is not considered in this script)

	f=nc.Dataset(nc_file, mode='r')
	lat_in=f.variables['lat'][:]
	lon_in=f.variables['lon'][:] 
	time_in=range(6532)

	#-------------------

	#nc_file_out=nc.Dataset("/data/tmandonnet/E-OBS/DetectionCanicule/compress_sub-heatwaves_tg_anomaly_threshold_95th_scan_size"+str(scan_size)+"_"+str(pourcent*100)+"%.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
	#nc_file_out=nc.Dataset("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/compress_sub-heatwaves_tg_anomaly_threshold_95th_scan_size"+str(scan_size)+"_"+str(pourcent*100)+"%.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
	nc_file_out=nc.Dataset("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_"+the_variable+"_anomaly_threshold_95th_scan_size"+str(scan_size)+"_"+str(pourcent*100)+"%.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

	#Define netCDF output file :
	nc_file_out.createDimension('lat', 465)    # latitude axis
	nc_file_out.createDimension('lon', 705)    # longitude axis
	nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to).
	nc_file_out.createDimension('nchar', 10) #in order to save dates on date format as strings

	nc_file_out.title="Daily "+temp_name_dict[the_variable]+"temperature anomaly for summer days corresponding to a sub-heatwave day, from 1950 to 2020"
	nc_file_out.subtitle="values put to zero where not exceeding 95th temperature anomaly threshold. Created with scan_cor.py on "+ datetime.today().strftime("%d/%m/%y")

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
	#create a table with all the dates of the considered data
	calendar=np.zeros((71,92),dtype=object) 
	for year in tqdm(range(an)) :
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
	#create 4D tables for the weight of cells and the land_sea_mask, each cell corresponding to the scanning window of shape (scan_lat,scan_lon)

	#-------------------

	#nc_file_mask="/data/tmandonnet/E-OBS/Mask/Mask_Europe.nc"
	nc_file_mask="D:/Ubuntu/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
	f_mask=nc.Dataset(nc_file_mask,mode='r')

	weight = np.cos(np.pi*lat_in/180) # the weight of each cell, depending on the latitude
	land_sea_mask=f_mask.variables['mask_all'][:] # mask in order to define land_sea_mask and sea_cpt_table_bool_4d
	sea_cpt_table_bool_4d=np.zeros((465,705,scan_lat,scan_lon))
	weight_table_4d=np.zeros((465,705,scan_lat,scan_lon))

	for i in tqdm(range(int((len(lat)-scan_lat)/2))) :
		for j in range(int((len(lon)-scan_lon)/2)) :
			weight_table_4d[i*2,j*2,:,:]=np.array([weight[i*2:i*2+scan_lat]]*scan_lon)
			sea_cpt_table_bool_4d[i*2,j*2,:,:]=np.array(land_sea_mask[i*2:i*2+scan_lat,j*2:j*2+scan_lon]==True)

	weight_table_2d=np.sum(weight_table_4d,-1) #sum the weight of one scanning window, longitude axis
	weight_table_2d=np.sum(weight_table_2d,-1) #sum the weight of one scanning window, latitude axis
	sea_cpt_table=sea_cpt_table_bool_4d*weight_table_4d
	sea_cpt_table=np.sum(sea_cpt_table,-1) #sum the weight of one scanning window, longitude axis
	sea_cpt_table=np.sum(sea_cpt_table,-1) #sum the weight of one scanning window, latitude axis
	
	print('4D tables have been created')

	#-------------------

	for year in tqdm(range(an)) :
		#print('year',year,'/70')
		red=ma.array(f.variables['temp'][year*92:(year+1)*92,:,:],mask=[land_sea_mask]*92) # start = 01/06 ; end = 31/08 ; SHAPE = (time,lat,lon)
		siz=np.shape(red)
		#make the scan operation of each zone in order to determine the heatwaves dates, stored into the netCDF file
		for t in range(92) :

			#print('day ', t, '/91, year ', year, '/70')
			cpt_table_bool=ma.array(np.zeros((siz[1],siz[2],scan_lat,scan_lon)),mask=False) #siz[1]=lat, siz[2]=lon

			if red[t,:,:].any() :
				for i in range(int((len(lat)-scan_lat)/2)) :
					for j in range(int((len(lon)-scan_lon)/2)) :
						cpt_table_bool[i*2,j*2,:,:]=ma.array(red[t,i*2:i*2+scan_lat,j*2:j*2+scan_lon]>0) #this takes time, could probably be improved
			
			cpt_table = cpt_table_bool*weight_table_4d

			cpt_table = np.sum(cpt_table,-1)
			cpt_table = np.sum(cpt_table,-1)

			detect_heatwave_table_bool=np.array(cpt_table > np.round((weight_table_2d-sea_cpt_table)*pourcent)) #each cell is the result of the matching scanning window
			#the previous line entails an issue on coastlines -> the scanning operation is biased on these points, I decided to correct it with a second scanning operation (scan_cor_2nd_time.py)
			if detect_heatwave_table_bool.any() : #Check if at least one of the scanning windows has detected a sub-heatwave
				ntimes=np.shape(temp)[0] #take the time dimension length in order to know the next index to use
				date_idx[ntimes]=year*92+t
				date_format[ntimes] = nc.stringtochar(np.array([calendar[year,t]], 'S10'))
				temp[ntimes,:,:]=ma.array(np.zeros((siz[1],siz[2])),mask=red[t,:,:].mask) #siz[1]=lat, siz[2]=lon
				stack_where=np.argwhere(detect_heatwave_table_bool)
				for i,j in stack_where:
					temp[ntimes,i:i+scan_lon,j:j+scan_lat] = red[t,i:i+scan_lon,j:j+scan_lat] #save the temperature anomalies responsible for the sub-heatwave
				#print("Number of recorded days :",ntimes+1)
	time[:]=range(ntimes+1)

	print('save done')
	print('Number of recorded sub-heatwave days :', ntimes+1)

	f.close()
	nc_file_out.close()
	f_mask.close()
	
scan(the_variable,scan_size,quantieme,pourcent)