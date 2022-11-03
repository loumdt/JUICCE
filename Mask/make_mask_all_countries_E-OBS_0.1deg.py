import numpy as np
import netCDF4 as nc 
from shapely.geometry import Polygon
from shapely.geometry import Point
from cartopy.io import shapereader
import cartopy.crs as ccrs
import geopandas
import matplotlib.pyplot as plt
import cartopy.feature as cfeature

nc_file = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/tg_ens_mean_0.1deg_reg_v23.1e.nc"

f=nc.Dataset(nc_file, mode='r')
lat_in=f.variables['latitude'][:]
lon_in=f.variables['longitude'][:]
lat_table=np.array([lat_in]*705).T
lon_table=np.array([lon_in]*465)

#Issue with 'Malta' (probably too small)

#Issue with :
#'Norway', quite long but OK
#'Portugal', issue with the minimum longitude, corrected manually
#'Russia', quite long but OK


list_countries = ['Albania','Austria','Belarus','Belgium','Bosnia and Herzegovina','Bulgaria','Croatia','Cyprus','Czechia','Denmark',
'Estonia','Finland','France','Germany','Greece','Hungary','Iceland','Ireland','Italy','Latvia','Lithuania','Luxembourg','Montenegro',
'Macedonia','Moldova','Netherlands','Norway','Poland','Portugal','Romania','Republic of Serbia','Russia','Slovakia','Slovenia','Spain','Sweden',
'Switzerland','Turkey','Ukraine','United Kingdom']

#-------------------

nc_file_mask="/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc"
f_mask=nc.Dataset(nc_file_mask,mode='r')
mask_all=f_mask.variables['mask_all'][:]

#-----------------------------------

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

#-----------------------------------
#for idx_country in range(len(list_countries)) :
#    country = list_countries[idx_country]
#    print([df.loc[df['ADMIN'] == country]['ADMIN'].values[0]])
#exit()

for idx_country in range(len(list_countries)) :

    country = list_countries[idx_country]

    print('Computing mask for '+country)

    country2=country

    if country == 'United Kingdom':#fix issues of spaces in filenames
        country2 = 'United_Kingdom'
    elif country == 'Republic of Serbia':
        country2= 'Serbia'

    #Define netCDF output file :
    nc_file_out = nc.Dataset("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Mask/mask_"+country2+"_E-OBS_0.1deg.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
    lat_dim = nc_file_out.createDimension('lat', 465)    # latitude axis
    lon_dim = nc_file_out.createDimension('lon', 705)    # longitude axis

    nc_file_out.title="Mask for "+country+" for E-OBS 0.1° dataset"


    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    # Define a 3D variable to hold the data
    mask_country = nc_file_out.createVariable('mask_'+country2,np.float32,('lat','lon')) # note: unlimited dimension is leftmost
    mask_country.long_name = '1 when masked, else 0. All countries are masked except '+country
    # Note: the ":" is necessary in these "write" statements
    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]

    mask_country[:,:]=mask_all[:,:]

    titre='mask'

    fig = plt.figure(idx_country,figsize=(24,16))

    proj_pc = ccrs.PlateCarree()
    # my_proj, plot_coord_labels = ccrs.Mollweide(), False # Labels not supported yet for Mollweide
    my_proj, plot_coord_labels = proj_pc, False # Labels or OK for PlateCarree

    ax=plt.axes(projection=proj_pc)

    ax.set_extent([-25, 45, 25, 71.5])

    ax.stock_img()

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


    # get geometry of a country
    poly = [df.loc[df['ADMIN'] == country]['geometry'].values[0]]

    # create fig and axes using intended projection
    #ax.add_geometries(poly, crs=proj_pc, facecolor='none', edgecolor='black')

    pad1 = .1  #padding, degrees unit
    exts = [poly[0].bounds[0] - pad1, poly[0].bounds[2] + pad1, poly[0].bounds[1] - pad1, poly[0].bounds[3] + pad1]
    ax.set_extent([-25, 45, 25, 71])


    # make a mask polygon by polygon's difference operation
    # base polygon is a rectangle, another polygon is simplified country
    msk = Polygon(rect_from_bound(*exts)).difference( poly[0].simplify(0.01) )
    msk_pc  = proj_pc.project_geometry(msk, proj_pc)

    ax.gridlines(draw_labels=True)

    lat_list=np.array([])
    lon_list=np.array([])
    for point in np.argwhere(mask_country[:]==0):
        mask_country[point[0],point[1]]=int(msk.contains(Point((lon_in[point[1]],lat_in[point[0]]))))
        if msk.contains(Point((lon_in[point[1]],lat_in[point[0]]))) :
            lat_list = np.append(lat_list,lat_in[point[0]])
            lon_list = np.append(lon_list,lon_in[point[1]])

    #print(np.min(lat_list),np.max(lat_list),np.min(lon_list),np.max(lon_list))

    mask_country[:,:] = mask_country[:,:] + (lat_table<np.min(lat_list))
    mask_country[:,:] = mask_country[:,:] + (lat_table>np.max(lat_list))
    if country == 'Portugal' :
        mask_country[:,:] = mask_country[:,:] + (lon_table<-9.56)
    else :
        mask_country[:,:] = mask_country[:,:] + (lon_table<np.min(lon_list))
    mask_country[:,:] = mask_country[:,:] + (lon_table>np.max(lon_list))

    mask_country[:,:]=mask_country[:,:]>0

    CS1 = ax.pcolormesh(lon_in,lat_in,mask_country[:,:],cmap='spring',transform=proj_pc, vmin=0,vmax=1)

    cax = plt.axes([0.35, 0.19, 0.35, 0.02])

    plt.colorbar(CS1,cax=cax,orientation='horizontal')

    plt.savefig('/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Mask/test_mask'+country2+'.png')

    #plt.show()

    nc_file_out.close()
f.close()
f_mask.close()