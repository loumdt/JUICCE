import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from thermofeel import *
import sys,os
from tqdm import tqdm

y = sys.argv[1]

t2m_path = "/data/ajeze/ERA5/t2m/hour/t2m/"
t2m_file = nc.Dataset(t2m_path+f"ERA5_NorthAtlantic_hour_t2m_{y}010100-{y}123123.nc",mode='r')

mrt_path = f"/data/tmandonnet/ERA5/WBGT/{y}/"
mrt_file = nc.Dataset(mrt_path+f"ERA5_Europe_025deg_MRT_{y}.nc",mode='r')

U_wind_file = nc.Dataset(mrt_path+f"ERA5_Europe_025deg_hourly_U_wind_{y}010100-{y}123123.nc",mode='r')
V_wind_file = nc.Dataset(mrt_path+f"ERA5_Europe_025deg_hourly_V_wind_{y}010100-{y}123123.nc",mode='r')

lat_in = U_wind_file.variables['latitude'][:]
lon_in = U_wind_file.variables['longitude'][:]
time_in = U_wind_file.variables['time'][:]

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx
idx_max_lat_t2m = find_nearest(t2m_file.variables['lat'][:],np.max(lat_in))+1
idx_max_lon_t2m = find_nearest(t2m_file.variables['lon'][:],np.max(lon_in))+1
#-------------------------------------
#Define netCDF output file :
#Compute the temperature data averaged over the chosen period (default 1950-2021) for every calendar day of the year and store it in a netCDF file.
nc_file_out=nc.Dataset(mrt_path+f"ERA5_Europe_025deg_hourly_WBGT_{y}010100-{y}123123.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title=f"Hourly WBGT for year {y}"

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = f'hours from 1900-01-01 00:00'
time.long_name = 'time'

lat[:] = lat_in[:]
lon[:] = lon_in[:]
time[:] = time_in[:]

# Define a 3D variable to hold the data
wbgt = nc_file_out.createVariable('wbgt',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
wbgt.units = '°C' # degrees Celsius
wbgt.long_name = 'Wet Bulb Globe Temperature (Brimicombe et al, 2023)'
wbgt.standard_name = 'wbgt_Brimicombe' # this is a CF standard name
wbgt[:,:,:] = ma.array(np.zeros((len(time_in),len(lat_in),len(lon_in))),mask=False)
for i in tqdm(range(len(time_in)//24)) :
    t2m = t2m_file.variables['t2m'][i*24:(i+1)*24,:idx_max_lat_t2m,:idx_max_lon_t2m]
    mrt = mrt_file.variables['mrt'][i*24:(i+1)*24,:,:]
    va = np.sqrt((U_wind_file.variables['u10'][i*24:(i+1)*24,:,:])**2+(V_wind_file.variables['v10'][i*24:(i+1)*24,:,:])**2)
    wbgt[i*24:(i+1)*24,:,:] = calculate_wbgt(t2m, mrt, va)

mrt_file.close()
nc_file_out.close()
t2m_file.close()
U_wind_file.close()
V_wind_file.close()