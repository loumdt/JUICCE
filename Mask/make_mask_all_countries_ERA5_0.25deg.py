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

#%% Countries that must be masked :
list_countries = ['Albania','Austria','Belarus','Belgium','Bosnia and Herzegovina','Bulgaria','Croatia','Cyprus','Czechia','Denmark',
'Estonia','Finland','France','Germany','Greece','Hungary','Iceland','Ireland','Italy','Latvia','Lithuania','Luxembourg','Montenegro',
'North Macedonia','Moldova','Netherlands','Norway','Poland','Portugal','Romania','Republic of Serbia','Russia','Slovakia','Slovenia','Spain','Sweden',
'Switzerland','Turkey','Ukraine','United Kingdom']
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
output_dir = os.path.join(datadir,"ERA5","Mask")
pathlib.Path(output_dir).mkdir(parents=True,exist_ok=True)
for country in list_countries :
    #print(country)
    if country == 'United Kingdom':#fix issues of spaces in filenames
        country2 = 'United_Kingdom'
    elif country == 'Republic of Serbia':
        country2= 'Serbia'
    elif country == 'North Macedonia':
        country2= 'Macedonia'
    else :
        country2 = country
    #Mask Africa and Middle-East
    nc_out_path = os.path.join(output_dir,"Mask_"+country2+"_ERA5_0.25deg.nc") #path to the output netCDF file
    nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') 
    #Define netCDF output file :
    lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis

    nc_file_out.title="Mask for "+country+" for ERA5 0.25° dataset"

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    # Define a 3D variable to hold the data
    mask = nc_file_out.createVariable('mask',np.int32,('lat','lon')) # note: unlimited dimension is leftmost
    mask.long_name = 'Only '+country+' is not masked'

    mask[:,:]=np.ones(np.shape(f.variables['t2m'][0,:,:]))
    
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
            mask[point[0],point[1]]=0
            
    mask[:] = mask[:]+(land_density[:]<0.5) #arbitrary value of 0.5 : if less than half of the pixel is land, we consider it as a sea or ocean pixel   
    mask[:,:] = mask[:,:]>0

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

    CS1 = ax.pcolormesh(lon_in,lat_in,mask[:,:],cmap='spring',transform=proj_pc, vmin=0,vmax=1)
    cax = plt.axes([0.35, 0.19, 0.35, 0.02])

    plt.colorbar(CS1,cax=cax,orientation='horizontal')
    plt.title('Mask',{'position':(0.5,-2)})
    plt.savefig('Mask/Mask_'+country2+'_only_ERA5.png')
    #plt.show()
    nc_file_out.close()
f.close()
f_density.close()