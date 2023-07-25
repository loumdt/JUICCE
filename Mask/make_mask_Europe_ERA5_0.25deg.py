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
import os
import pathlib
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
#Load netcdf temperature data file :
nc_in_path = os.path.join(datadir,"ERA5","t2m","ERA5_tg_Europe_day_0.25deg_1950-2021.nc") # path to ERA5 data netCDF file

f=nc.Dataset(nc_in_path, mode='r') #load file
lat_in=f.variables['lat'][:] #load dimensions
lon_in=f.variables['lon'][:]

lat_table=np.array([lat_in]*len(lon_in)).T
lon_table=np.array([lon_in]*len(lat_in))
#%%
#Load ERA5 land density file :
nc_land_density_path = os.path.join(datadir,"ERA5","Mask","land_sea_mask_ERA5_0.25deg.nc") # path to ERA5 data netCDF file

f_density=nc.Dataset(nc_land_density_path, mode='r') #load file
land_density = f_density.variables['land_density'][0,::-1,:]
#%%
#Mask Africa and Middle-East
output_dir = os.path.join(datadir,"ERA5","Mask")
pathlib.Path(output_dir).mkdir(parents=True,exist_ok=True)
nc_out_path = os.path.join(output_dir,"Mask_Europe_1_ERA5_0.25deg.nc") #path to the output netCDF file
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') 
#Define netCDF output file :
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis

nc_file_out.title="Africa and Middle-East are masked but not ocean"

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
# Define a 3D variable to hold the data
mask = nc_file_out.createVariable('mask',np.int32,('lat','lon')) # note: unlimited dimension is leftmost
mask.long_name = 'Africa and Middle-East are masked but not ocean'

#%%
#Mask Africa and Middle-East and ocean and sea
nc_out_name_all = os.path.join(output_dir,"Mask_Europe_land_only_ERA5_0.25deg.nc") #path to the output netCDF file
nc_file_out_all=nc.Dataset(nc_out_name_all,mode='w',format='NETCDF4_CLASSIC') 
#Define netCDF output file :
lat_dim = nc_file_out_all.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out_all.createDimension('lon', len(lon_in))    # longitude axis

nc_file_out_all.title="Make mask for all Europe"

lat_all = nc_file_out_all.createVariable('lat', np.float32, ('lat',))
lat_all.units = 'degrees_north'
lat_all.long_name = 'latitude'
lon_all = nc_file_out_all.createVariable('lon', np.float32, ('lon',))
lon_all.units = 'degrees_east'
lon_all.long_name = 'longitude'
# Define a 3D variable to hold the data
mask_all = nc_file_out_all.createVariable('mask',np.int32,('lat','lon')) # note: unlimited dimension is leftmost
mask_all.long_name = 'Africa, Middle-East, sea and ocean are masked'

# Note: the ":" is necessary in these "write" statements
lat_all[:] = lat_in[:] 
lon_all[:] = lon_in[:]

#%%

mask[:,:]=np.zeros(np.shape(f.variables['t2m'][0,:,:])) #this mask happens to be quite good, 13500 days from 01 jan 1950

#%% Countries that must be masked :
list_countries = ['Morocco','Algeria','Tunisia','Libya','Egypt','Palestine','Israel','Jordan','Lebanon','Syria','Saudi Arabia','Iraq','Iran']
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
for country in list_countries :
    #print(country)
    # get geometry of a country
    poly = [df.loc[df['ADMIN'] == country]['geometry'].values[0]]
    # create fig and axes using intended projection
    #ax.add_geometries(poly, crs=proj_pc, facecolor='none', edgecolor='black')
    pad1 = .1  #padding, degrees unit
    exts = [poly[0].bounds[0] - pad1, poly[0].bounds[2] + pad1, poly[0].bounds[1] - pad1, poly[0].bounds[3] + pad1]
    # make a mask polygon by polygon's difference operation
    # base polygon is a rectangle, another polygon is simplified country
    msk = Polygon(rect_from_bound(*exts)).difference( poly[0].simplify(0.01) )

    for point in np.argwhere(((lon_table>exts[0])*(lon_table<exts[1])*(lat_table>exts[2])*(lat_table<exts[3]))):
        if not msk.contains(Point((lon_in[point[1]],lat_in[point[0]]))) :
            mask[point[0],point[1]]=1
#%%        
mask[:,:] = mask[:,:]>0

mask_all[:] = mask[:]+(land_density[:]<0.5) #arbitrary value of 0.5 : if less than half of the pixel is land, we consider it as a sea or ocean pixel
mask_all[:] = mask_all[:] + (lat_table<34.5)
mask_all[:] = mask_all[:] + (lat_table<37.4)*(lon_table>-1.3)*(lon_table<11.3)
mask_all[:] = mask_all[:] + (lat_table<35.9)*(lon_table>-5.2)*(lon_table<-3.9)
mask_all[:] = mask_all[:]>0
titre='mask'

fig = plt.figure(1,figsize=(24,16))

proj_pc = ccrs.PlateCarree()
# my_proj, plot_coord_labels = ccrs.Mollweide(), False # Labels not supported yet for Mollweide
my_proj, plot_coord_labels = proj_pc, False # Labels or OK for PlateCarree

ax=plt.axes(projection=proj_pc)

ax.set_extent([-12.5, 45, 30, 71.5])
ax.stock_img()
#ax.outline_patch.set_zorder(50)
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
plt.title('Mask',{'position':(0.5,-2)})
plt.savefig('Mask/Mask_Europe_land_only_ERA5.png')
#plt.show()

nc_file_out.close()
nc_file_out_all.close()
f.close()