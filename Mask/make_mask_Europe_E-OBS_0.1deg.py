import numpy as np
import netCDF4 as nc 
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

nc_file = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/tg_ens_mean_0.1deg_reg_v23.1e.nc"

f=nc.Dataset(nc_file, mode='r')
lat_in=f.variables['latitude'][:]
lon_in=f.variables['longitude'][:]
lat_table=np.array([lat_in]*705).T
lon_table=np.array([lon_in]*465)


nc_file_out=nc.Dataset("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#Define netCDF output file :
print('nc_file_out',nc_file_out)
lat_dim = nc_file_out.createDimension('lat', 465)    # latitude axis
lon_dim = nc_file_out.createDimension('lon', 705)    # longitude axis
for dim in nc_file_out.dimensions.items():
    print(dim)

nc_file_out.title="Make mask for all Europe"


lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
# Define a 3D variable to hold the data
mask_all = nc_file_out.createVariable('mask_all',np.int32,('lat','lon')) # note: unlimited dimension is leftmost
mask_all.long_name = 'Africa is masked as well as ocean'

# Note: the ":" is necessary in these "write" statements
lat[:] = lat_in[:] 
lon[:] = lon_in[:]

mask_all[:,:]=f.variables['tg'][-6500,:,:].mask #this mask happens to be quite good

mask_all[:,:] = mask_all[:,:] - (lat_table>52.36)*(lon_table>5.047)*(lat_table<52.9)*(lon_table<5.66) #have to correct the Netherlands mask
mask_all[:,:] = mask_all[:,:] - (lat_table>52.8)*(lon_table>5.09)*(lat_table<53.03)*(lon_table<5.52)
mask_all[:,:] = mask_all[:,:] - (lat_table>52.85)*(lon_table>5.285)*(lat_table<53.07)*(lon_table<5.44)

mask_all[:,:] = mask_all[:,:] + (lat_table<33.5)*(lon_table>-13.07) #The most southern point of Europe is at 34.0°N
mask_all[:,:] = mask_all[:,:] + (lat_table<27.7)*(lon_table>-15.07)
mask_all[:,:] = mask_all[:,:] + (lat_table<35.94)*(lon_table>-10)*(lon_table<11.5)
mask_all[:,:] = mask_all[:,:] + (lat_table<37.7)*(lon_table>-1)*(lon_table<11.5)
mask_all[:,:] = mask_all[:,:] + (lat_table<35.8)*(lon_table>35)
mask_all[:,:] = mask_all[:,:] + (lat_table<36.6)*(lon_table>36.7)
mask_all[:,:] = mask_all[:,:] + (lat_table<36.95)*(lon_table>40.8)


mask_all[:,:] = mask_all[:,:]>0

titre='mask'

fig = plt.figure(1,figsize=(24,16))

proj_pc = ccrs.PlateCarree()
# my_proj, plot_coord_labels = ccrs.Mollweide(), False # Labels not supported yet for Mollweide
my_proj, plot_coord_labels = proj_pc, False # Labels or OK for PlateCarree

ax=plt.axes(projection=proj_pc)

ax.set_extent([-25, 45, 25, 71.5])

ax.stock_img()

ax.outline_patch.set_zorder(50)

ax.set_title(titre, fontsize='x-large')

ax.gridlines(draw_labels=plot_coord_labels,
                   xlocs=np.arange(25., 71., 47.),
                   ylocs=np.arange(-25., 45., 71.),
                   linestyle='--',
                   color='0.5',
                   linewidth=0.3,
                   zorder=20)

ax.add_feature(cfeature.BORDERS,linewidth=0.7)
ax.add_feature(cfeature.COASTLINE,linewidth=0.7)

CS1 = ax.pcolormesh(lon_in,lat_in,mask_all[:,:],cmap='spring',transform=proj_pc, vmin=0,vmax=1)

cax = plt.axes([0.35, 0.19, 0.35, 0.02])

plt.colorbar(CS1,cax=cax,orientation='horizontal')

plt.title('Temperature (°C)',{'position':(0.5,-2)})

plt.savefig('/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Mask/Mask_Europe.png')

plt.show()

nc_file_out.close()
f.close()