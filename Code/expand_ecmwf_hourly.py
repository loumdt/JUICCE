#%%
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
#%%
f = "D:/Ubuntu/These/JUICCE/Data/ERA5/utci/ECMWF_utci_19880930_v1.1_con_uncomplete.nc"
nc_file = nc.Dataset(f,mode='r')

time_in = nc_file.variables['time'][:]
lat_in = nc_file.variables['lat'][:]
lon_in = nc_file.variables['lon'][:]


#Define netCDF output file :
#Compute the temperature data averaged over the chosen period (default 1950-2021) for every calendar day of the year and store it in a netCDF file.
nc_out_path = "D:/Ubuntu/These/JUICCE/Data/ERA5/utci/ECMWF_utci_19880930_v1.1_con.nc"
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

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
time.units = "hours since 1988-9-30 00:00:00"
time.standard_name = 'time'
time.calendar = "proleptic_gregorian"
time.axis = "T"
# Define a 3D variable to hold the data
utci = nc_file_out.createVariable('utci',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
utci.code = 167
utci.table = 128
#utci.units = '°C' # degrees Celsius
#utci.long_name = 'wet bulb globe temperature Brimicombe'
#utci.standard_name = 'utci' # this is a CF standard name

# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements -> you want to write the content and not to change the definition of the dimension
lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(24)

#utci[:,:,:]=ma.array(np.zeros((24,len(lat_in),len(lon_in))),mask=False) #set output netcdf variable
utci[:len(time_in),:,:]=ma.array(nc_file.variables['utci'][:])
utci[len(time_in):24,:,:]=ma.masked_where(True,np.ones((24-len(time_in),len(lat_in),len(lon_in))))

nc_file.close()
nc_file_out.close()