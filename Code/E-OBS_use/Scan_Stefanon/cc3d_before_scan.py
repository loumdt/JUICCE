#%%
import numpy as np
import numpy.ma as ma
import cc3d
import netCDF4 as nc
import sys,os
from datetime import datetime
from tqdm import tqdm

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
#%%
#-------------------------------------
#Load temperature data file
try :
	nc_file_in = os.path.join(os.environ["DATADIR"] , "E-OBS" , "0.1deg" ,the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value-5)+"th.nc")
except :
    nc_file_in="Data/E-OBS/0.1deg/"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value-5)+"th.nc"
#%%    
print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['lat']
lon_in=f.variables['lon']
time_in=f.variables['time']
date_idx_1950_in=f.variables['date_idx_1950']

#%%
#Load E-OBS Europe mask
try:
    nc_file_mask = os.path.join(os.environ["DATADIR"], "E-OBS", "Mask", "Mask_Europe_E-OBS_0.1deg.nc")#file to load the corrected mask for all Europe
except :
    nc_file_mask = "Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc"
#%%
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask_all'][:]
#%%

#%%
try :
	nc_file_scanned = os.path.join(os.environ["DATADIR"] , "E-OBS" , "Detection_Canicule" ,"heatwaves_4days_scan_TWICE_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_scan_size35_10.0%.nc")
except :
    nc_file_scanned = "Data/E-OBS/Detection_Canicule/heatwaves_4days_scan_TWICE_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_scan_size35_10.0%.nc"
#%%
print('nc_file_scanned',nc_file_scanned)
f_scanned=nc.Dataset(nc_file_scanned, mode='r')
time_in_scanned=f_scanned.variables['time'][:]
date_idx_JJA_scanned=f_scanned.variables['date_idx'][:]
date_idx_JJA_scanned = [int(i) for i in date_idx_JJA_scanned.data]
#%%
try :
    nc_out_name = os.path.join(os.environ["DATADIR"] , "E-OBS" , "0.1deg" , the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value-5)+"th_CC3D_LABELS.nc")
except :
    nc_out_name = "Data/E-OBS/0.1deg/"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value-5)+"th_CC3D_LABELS_v2.nc"#path to the output netCDF file

nc_file_out=nc.Dataset(nc_out_name,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file


lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', 92*(year_end-year_beg+1)) # unlimited time axis (can be appended to).

nc_file_out.title="Labels of CC3D for "+temp_name_dict[the_variable]+" temperature anomaly for JJA days from "+str(year_beg)+" to "+str(year_end)
nc_file_out.subtitle="values are set to zero not exceeding "+str(threshold_value)+"th temperature anomaly threshold, and labels are assigned to contiguous elements"
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
label = nc_file_out.createVariable('label',np.int32,('time','lat','lon')) # note: unlimited dimension is leftmost
label.long_name = 'cc3d_label'

lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(92*(year_end-year_beg+1))
date_idx_1950[:]=date_idx_1950_in[:]

label[:] = ma.array(-9999*np.ones((len(time_in),len(lat_in),len(lon_in))),mask=[Mask_0]*(92*(year_end-year_beg+1)))
N_labels=0
#%%
for year in tqdm(range((year_end-year_beg+1))) :
    labels_in = np.array(ma.filled(f.variables['temp'][year*92:(year+1)*92,:,:],fill_value=-9999))
    labels_in = (labels_in!=-9999) # ones where 90th percentile threshold is exceeded, zeros elsewhere
    for day in range(92): #92 JJA days
        if year*92+day not in date_idx_JJA_scanned :
            labels_in[day,:,:]=np.zeros((len(lat_in),len(lon_in)))
    #labels_in = ma.array(f.variables['temp'][year*92:(year+1)*92,:,:])
    connectivity = 26 # only 4,8 (2D) and 26, 18, and 6 (3D) are allowed
    labels_out,N_added = cc3d.connected_components(labels_in, connectivity=connectivity,return_N=True)
    label[year*92:(year+1)*92,:,:]=ma.array(labels_out,mask=[Mask_0]*92)
    label[year*92:(year+1)*92,:,:] = ma.masked_where(labels_out==0,label[year*92:(year+1)*92,:,:])
    label[year*92:(year+1)*92,:,:] += N_labels
    N_labels+=N_added