#%%
import numpy as np
import netCDF4 as nc 
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely.geometry import Polygon
from shapely.geometry import Point
from cartopy.io import shapereader
import geopandas


nc_file = "Data/E-OBS/0.1deg/tg_ens_mean_0.1deg_reg_v26.0e.nc"

f=nc.Dataset(nc_file, mode='r')
lat_in=f.variables['latitude'][:]
lon_in=f.variables['longitude'][:]
lat_table=np.array([lat_in]*len(lon_in)).T
lon_table=np.array([lon_in]*len(lat_in))

nc_file_out=nc.Dataset("Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#Define netCDF output file :
print('nc_file_out',nc_file_out)
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
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

mask_all[:,:]=f.variables['tg'][13500,:,:].mask #this mask happens to be quite good, 13500 days from 01 jan 1950
#%%

mask_all[:,:] = mask_all[:,:] + (lat_table<33.5)*(lon_table>-13.07) #The most southern point of Europe is at 34.0°N
mask_all[:,:] = mask_all[:,:] + (lat_table<27.7)*(lon_table>-15.07)
mask_all[:,:] = mask_all[:,:] + (lat_table<35.94)*(lon_table>-10)*(lon_table<11.5)
mask_all[:,:] = mask_all[:,:] + (lat_table<37.7)*(lon_table>-1)*(lon_table<11.5)
mask_all[:,:] = mask_all[:,:] + (lat_table<35.8)*(lon_table>35)
mask_all[:,:] = mask_all[:,:] + (lat_table<36.6)*(lon_table>36.7)
mask_all[:,:] = mask_all[:,:] + (lat_table<36.95)*(lon_table>40.8)

mask_all[:,:] = mask_all[:,:]>0

#%% Countries that must be corrected :
list_countries = ['Turkey']
#-------------------
mask_all[:,:] = mask_all[:,:] + (lat_table<37.5)*(lon_table>35.5)*(lon_table<44.8)
mask_all[:,:] = mask_all[:,:]>0
#-----------------------------------
#%%
def rect_from_bound(xmin, xmax, ymin, ymax):
    """Returns list of (x,y)'s for a rectangle"""
    xs = [xmax, xmin, xmin, xmax, xmax]
    ys = [ymax, ymax, ymin, ymin, ymax]
    return [(x, y) for x, y in zip(xs, ys)]

# request data for use by geopandas
resolution = '10m'
category = 'cultural'
name = 'admin_0_countries'

shpfilename = shapereader.natural_earth(resolution, category, name)
df = geopandas.read_file(shpfilename)
#%%
#-----------------------------------
for idx_country in range(len(list_countries)) :
    country = list_countries[idx_country]
    # get geometry of a country
    poly = [df.loc[df['ADMIN'] == country]['geometry'].values[0]]
    # create fig and axes using intended projection
    #ax.add_geometries(poly, crs=proj_pc, facecolor='none', edgecolor='black')
    pad1 = .1  #padding, degrees unit
    exts = [poly[0].bounds[0] - pad1, poly[0].bounds[2] + pad1, poly[0].bounds[1] - pad1, poly[0].bounds[3] + pad1]
    # make a mask polygon by polygon's difference operation
    # base polygon is a rectangle, another polygon is simplified country
    msk = Polygon(rect_from_bound(*exts)).difference( poly[0].simplify(0.01) )

    lat_list=np.array([])
    lon_list=np.array([])

    #for point in np.argwhere((mask_all[:]==0)):
    for point in np.argwhere(((lon_table>exts[0])*(lon_table<exts[1])*(lat_table>exts[2])*(lat_table<exts[3]))):
        if not msk.contains(Point((lon_in[point[1]],lat_in[point[0]]))) :
            mask_all[point[0],point[1]]=0
        if msk.contains(Point((lon_in[point[1]],lat_in[point[0]]))) :
            lat_list = np.append(lat_list,lat_in[point[0]])
            lon_list = np.append(lon_list,lon_in[point[1]])
#%%        
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
plt.savefig('Mask/Mask_Europe.png')
#plt.show()

nc_file_out.close()
f.close()