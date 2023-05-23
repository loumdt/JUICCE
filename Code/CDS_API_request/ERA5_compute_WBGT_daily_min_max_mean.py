#%%
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
from tqdm import tqdm
import sys,os
#%%
y = sys.argv[1]

f_path = f"/data/tmandonnet/ERA5/WBGT/{y}/"
nc_file_in = nc.Dataset(f_path+f"ERA5_Europe_025deg_hourly_WBGT_{y}010100-{y}123123.nc",mode='r')

time_in = nc_file_in.variables['time'][:]
lat_in = nc_file_in.variables['lat'][::-1]
lon_in = nc_file_in.variables['lon'][:]

dict_var = {'daymean':ma.mean,'daymax':ma.max,'daymin':ma.min}
#Define netCDF output file :
for var in dict_var :
    nc_file_out=nc.Dataset(f_path+f"ERA5_Europe_025deg_"+var+f"_WBGT_{y}0101-{y}1231.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

    lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.standard_name = "latitude"
    lat.long_name = 'latitude'
    lat.axis = "Y"
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.standard_name = 'longitude'
    lon.long_name = 'longitude'
    lon.axis = "X"
    time = nc_file_out.createVariable('time', np.float32, ('time',))
    time.units = f"days since {y}-01-01"
    time.long_name = 'time'
    time.calendar = "proleptic_gregorian"
    time.axis = "T"
    # Define a 3D variable to hold the data
    wbgt = nc_file_out.createVariable('wbgt',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
    wbgt.units = '°C' # degrees Celsius
    wbgt.long_name = 'wet bulb globe temperature Brimicombe'
    wbgt.standard_name = 'wbgt'

    # Write latitudes, longitudes.
    # Note: the ":" is necessary in these "write" statements -> you want to write the content and not to change the definition of the dimension
    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]
    time[:]=range(int(len(time_in)/24))
    for i in tqdm(range(len(time))):
        wbgt[i,:,:]=ma.array(dict_var[var](nc_file_in.variables['wbgt'][i*24:(i+1)*24,:,:],axis=0))
    nc_file_out.close()
    
nc_file_in.close()