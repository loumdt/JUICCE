import time 
start_time=time.time()

import netCDF4 as nc
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return (idx,array[idx])

#-------------------

nc_file_mask = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask = nc.Dataset(nc_file_mask,mode='r')
mask_all = f_mask.variables['mask_all'][:]


pop_table = np.ma.array(np.zeros((2,465,705)),mask=[mask_all]*2)

file_grid_target = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_TWICE_tg_anomaly_threshold_95th_scan_size35_10.0%.nc"

f_grid = nc.Dataset(file_grid_target,mode='r')
lat_grid = f_grid.variables['lat'][:]
lon_grid = f_grid.variables['lon'][:]

#-------------------
i_year=0
for year in [1975,1990] : #,2000,2015] :
    print(year)
    file_in = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/Pop/GHS_POP_E"+str(year)+"_GLOBE_R2019A_4326_30ss_V1_0/pop_GHS_"+str(year)+".nc"

    f = nc.Dataset(file_in,mode='r')
    lat_in = f.variables['lat'][:]
    lon_in = f.variables['lon'][:]

    new_lat_idx = np.ones((len(lat_grid),1),dtype=np.int32)
    new_lat_idx_bounds = np.ones((len(lat_grid),2),dtype=np.int32)
    new_lat_bounds = np.ones((len(lat_grid),2),dtype=np.float32)
    for i in range(len(lat_grid)):
        new_lat_idx[i] = find_nearest(lat_in,lat_grid[i])[0]
        new_lat_idx_bounds[i,0] = find_nearest(lat_in,lat_grid[i]-0.05)[0]
        new_lat_idx_bounds[i,1] = find_nearest(lat_in,lat_grid[i]+0.05)[0]
        new_lat_bounds[i,0] = find_nearest(lat_in,lat_grid[i]-0.05)[1]
        new_lat_bounds[i,1] = find_nearest(lat_in,lat_grid[i]+0.05)[1]

    new_lon_idx = np.ones((len(lon_grid),1),dtype=np.int32)
    new_lon_idx_bounds = np.ones((len(lon_grid),2),dtype=np.int32)
    new_lon_bounds = np.ones((len(lon_grid),2),dtype=np.float32)
    for i in range(len(lon_grid)):
        new_lon_idx[i] = find_nearest(lon_in,lon_grid[i])[0]
        new_lon_idx_bounds[i,0] = find_nearest(lon_in,lon_grid[i]-0.05)[0]
        new_lon_idx_bounds[i,1] = find_nearest(lon_in,lon_grid[i]+0.05)[0]
        new_lon_bounds[i,0] = find_nearest(lon_in,lon_grid[i]-0.05)[1]
        new_lon_bounds[i,1] = find_nearest(lon_in,lon_grid[i]+0.05)[1]  

    nc_file_out=nc.Dataset("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/Pop/GHS_pop/GHS_pop_"+str(year)+"_e-obs_grid.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

    #Define netCDF output file :
    #print('nc_file_out',nc_file_out)
    nc_file_out.createDimension('lat', 465)    # latitude axis
    nc_file_out.createDimension('lon', 705)    # longitude axis

    nc_file_out.title="GHS population density for year " + str(year)
    nc_file_out.subtitle="adapted for E-OBS 0.1° resolution grid"

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    pop_density = nc_file_out.createVariable('pop_density',np.float32, ('lat','lon'))
    pop_density.units = 'inhabitants per squared kilometers'
    pop_density.long_name = 'Population density in '+str(year)

    lat[:] = lat_grid[:]
    lon[:] = lon_grid[:]

    pop = f.variables['Band1'][int(new_lat_idx_bounds[0,0]):int(new_lat_idx_bounds[-1,-1]+1),int(new_lon_idx_bounds[0,0]):int(new_lon_idx_bounds[-1,-1]+1)]
    lat_in_2 = lat_in[int(new_lat_idx[0]):int(new_lat_idx[-1]+1)]
    lon_in_2 = lon_in[int(new_lon_idx[0]):int(new_lon_idx[-1]+1)]
    print(pop)
    print('\n input file')
    print('max',np.max(pop))
    print('min',np.min(pop))

    proj_pc = ccrs.PlateCarree()

    pop_density[:] = np.ma.array(np.zeros((len(lat_grid),len(lon_grid))),mask = False)

    #cell_area = np.array([6371**2*np.cos(np.pi*lat_grid/180)*0.1*np.pi/180*0.1*np.pi/180]*705).T # the area in km² of each cell, depending on the latitude
    cell_area = np.zeros((len(lat_grid),len(lon_grid)))

    for i in range(len(lat_grid)) :
        #print(i)
        for j in range(len(lon_grid)) :
            cell_area[i,j] = 6371**2*np.cos(np.pi*lat_grid[i]/180)*(new_lat_bounds[i,1]-new_lat_bounds[i,0])*np.pi/180*(new_lon_bounds[j,1]-new_lon_bounds[j,0])*np.pi/180
            pop_density[i,j] = (np.sum(pop[int(new_lat_idx_bounds[i,0]-new_lat_idx_bounds[0,0]):int(new_lat_idx_bounds[i,1]-new_lat_idx_bounds[0,0]),int(new_lon_idx_bounds[j,0]-new_lon_idx_bounds[0,0]):int(new_lon_idx_bounds[j,1]-new_lon_idx_bounds[0,0])]))/cell_area[i,j]
            #pop_density[i,j] = (np.mean(pop[int(new_lat_idx_bounds[i,0]-new_lat_idx_bounds[0,0]):int(new_lat_idx_bounds[i,1]-new_lat_idx_bounds[0,0]),int(new_lon_idx_bounds[j,0]-new_lon_idx_bounds[0,0]):int(new_lon_idx_bounds[j,1]-new_lon_idx_bounds[0,0])]))#/cell_area[i,j]


    mask_bis = np.array(mask_all==False)

    pop_density = np.ma.masked_where(mask_all,pop_density)
    pop_density = np.ma.masked_greater_equal(pop_density,1e12)

    print('pop_européenne :', np.sum(pop_density*cell_area))
    print('max',np.max(pop_density),'min',np.min(pop_density))
    print('max',np.max(pop_density*cell_area),'min',np.min(pop_density*cell_area))

    pop_table[i_year,:,:]=pop_density[:]

    print(np.shape(pop_density))
    print(np.argmax(pop_density))

    print('mask',pop_density.mask.all())

    proj_pc = ccrs.PlateCarree()
    fig=plt.figure(1,figsize=(24,16))
    ax=plt.axes(projection=proj_pc)
    ax.clear() #clear axes in order to accelerate plot (otherwise, superposition of each day -> longer and longer...)
    ax.set_extent([lon[0]+0.1, lon[-1]-0.1, lat[-1]+0.1, lat[0]-0.1])
    ax.stock_img()
    ax.outline_patch.set_zorder(50)

    ax.add_feature(cfeature.BORDERS) #Add countries borders on the map
    CS1 = ax.pcolormesh(lon_grid,lat_grid,pop_density,cmap='seismic',transform=proj_pc,vmin=0,vmax=1.5e3)
    #CS1 = ax.pcolormesh(lon_grid,lat_grid,mask_bis,cmap='seismic',transform=proj_pc)

    cax = plt.axes([0.35, 0.05, 0.35, 0.02])
    plt.colorbar(CS1,cax=cax,orientation='horizontal')

    print("Temps d'exécution : %f secondes" %(time.time()-start_time))
    i_year+=1
    f.close()
    nc_file_out.close()

    plt.show()



nc_file_out=nc.Dataset("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/Pop/GHS_pop/GHS_pop_all_e-obs_grid.nc",mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

#Define netCDF output file :
print('nc_file_out',nc_file_out)
nc_file_out.createDimension('lat', 465)    # latitude axis
nc_file_out.createDimension('lon', 705)    # longitude axis
nc_file_out.createDimension('time', 2)    # time axis

nc_file_out.title="GHS population density for years 1975, and 1990"
nc_file_out.subtitle="adapted for E-OBS 0.1° resolution grid"

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time_out = nc_file_out.createVariable('time', np.int32, ('time',))
time_out.units = 'time'
time_out.long_name = 'time'
years = nc_file_out.createVariable('years', np.int32, ('time',))
years.units = 'years'
pop_density = nc_file_out.createVariable('pop_density',np.float32, ('time','lat','lon'))
pop_density.units = 'inhabitants per squared kilometers'
pop_density.long_name = 'Population density'

time_out[:] = range(2)
years[:] = [1975,1990]
lat[:] = lat_grid[:]
lon[:] = lon_grid [:]

pop_density[:] = pop_table[:]

f_grid.close()
f_mask.close()
nc_file_out.close()