""" Create an animation of the EM-DAT heatwaves not detected in E-OBS with Stefanon method ; temperature anomaly values 
with black dots on locations where the corresponding 95th temperature ANOMALY percentile of the given day is exceeded."""

import time 
start_time=time.time()

import netCDF4 as nc
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import matplotlib.animation as animation 
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 
from datetime import  date, timedelta 
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
#-------------------------------------

#nc_file="/data/tmandonnet/E-OBS/0.1deg/tg_ens_mean_0.1deg_reg_v23.1e.nc" ; #path to the netCDF file
#nc_file_anomaly="/data/tmandonnet/E-OBS/0.1deg/tg_daily_mean_ovr_70yrs_smoothed.nc" ; #path to the netCDF file

#nc_file='/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/tg_ens_mean_0.1deg_reg_v23.1e.nc'  #path to the netCDF file
nc_file = 'D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_anomaly_summer_only_1950-2020.nc'  #path to the netCDF file

f = nc.Dataset(nc_file,mode = 'r')
time_in = f.variables['time'][:]
lat_in = f.variables['lat'][:]
lon_in = f.variables['lon'][:]

#-------------------------------------

heatwaves_undetected_emdat=['1985-0257','1988-0298','1996-0362','2000-0324','2004-0333','2006-0348','2011-0329','2019-0650'] 
#all heatwaves recorded in EM-DAT that are not detected in E-OBS with Stefanon method

#dico = {htw_ID : [idx_begin,idx_end+1]}, indices in the summer-only calendar, starting on 01-06-1950
htw_dico = {'1985-0257': [3281,3287],'1988-0298': [3524,3530],
'1996-0362': [4261,4267], '2000-0324': [4600,4630], '2004-0333': [4998,5029], '2006-0348': [5180,5213],
'2011-0329': [5689,5697], '2019-0650': [6398,6438]}


#-------------------------------------
for i in tqdm(range(len(heatwaves_undetected_emdat))) :
    #print("Computing heatwave "+heatwaves_undetected_emdat[i])
    var = f.variables['temp'][htw_dico[heatwaves_undetected_emdat[i]][0]:htw_dico[heatwaves_undetected_emdat[i]][1],:,:]
    min_val=min(-np.abs(np.min(var)),-np.abs(np.max(var))) 
    max_val=max(np.abs(np.min(var)),np.abs(np.max(var))) 

    the_levels=[min_val,max_val] #values for colormap, centered on zero for better visibility
    if heatwaves_undetected_emdat[i] == '2019-0650' :
        the_levels=[-15,15] #values for colormap, centered on zero for better visibility

    #print("the_levels :" ,the_levels)

    proj_pc = ccrs.PlateCarree() 

    # my_proj, plot_coord_labels = ccrs.Mollweide(), False # Labels not supported yet for Mollweide
    my_proj, plot_coord_labels = proj_pc, False # Labels or OK for PlateCarree

    titre="E-OBS Daily Mean Temperature anomaly (°C)" 

    #-------------------------------------


    threshold_table=np.load('/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/distrib_tg_ano_npy_95%_threshold_15days.npy',allow_pickle=True)
    #threshold_table=np.load('/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/0.1deg/distrib_tg_npy_95%_threshold_11days.npy',allow_pickle=True)
    new_time_beg = (htw_dico[heatwaves_undetected_emdat[i]][0])%92 # On which day of summer does the heatwave begins
    new_time_end = (htw_dico[heatwaves_undetected_emdat[i]][1])%92 # On which day of summer does the heatwave ends
    threshold_table=ma.masked_outside(threshold_table[152+new_time_beg:152+new_time_end,:,:],-60,60) #threshold of 95th temperature percentile for every day and location


    X_scatt=np.ndarray((np.shape(var)[0],),dtype=object)
    Y_scatt=np.ndarray((np.shape(var)[0],),dtype=object)
    year = int(heatwaves_undetected_emdat[i][0:4])
    strt_date=date(year,6,1) #start date of E-OBS data

    calendar=[0]*np.shape(var)[0]

    #print(np.shape(var))
    #print(np.shape(threshold_table))
    #print(np.argwhere(var[0,:,:]>threshold_table[0,:,:]))
    #for k in range(np.shape(var)[0]) :
    #    X_scatt[k] = lon_in(np.where(var[k,:,:]>threshold_table[k,:,:])[1])
    #    Y_scatt[k] = lat_in(np.where(var[k,:,:]>threshold_table[k,:,:])[0])

    #print(np.shape(X_scatt))
    t=0
    for day in time_in[htw_dico[heatwaves_undetected_emdat[i]][0]:htw_dico[heatwaves_undetected_emdat[i]][1]]:  #01/06 to 31/08, change days since 1/1/1950 to dates, store it into calendar list
        day=int(day-time_in[(year-1950)*92])
        day_num=str(day)
        day_num.rjust(3 + len(day_num), '0')
        res_date=strt_date + timedelta(days=int(day_num))
        res = res_date.strftime("%d-%m-%Y")
        calendar[t]=res
        X_scatt[t] = lon_in[np.argwhere(var[t,:,:]>threshold_table[t,:,:])[:,1]]
        Y_scatt[t] = lat_in[np.argwhere(var[t,:,:]>threshold_table[t,:,:])[:,0]]
        t+=1

    lons_mesh = lon_in
    lats_mesh = lat_in

    print(calendar)

    def make_figure():

        fig=plt.figure(1,figsize=(24,16))
        ax=plt.axes(projection=proj_pc)
        return fig,ax

    fig,ax = make_figure() #initialise figure

    def draw(k):
        ax.clear() #clear axes in order to accelerate plot (otherwise, superposition of each day -> longer and longer...)
        ax.set_extent([lon_in[0]+0.1, lon_in[-1]-0.1, lat_in[-1]+0.1, lat_in[0]-0.1])
        ax.stock_img()
        #ax.outline_patch.set_zorder(50)
        ax.set_title(titre, fontsize='x-large')
        ax.gridlines(draw_labels=plot_coord_labels,
                    xlocs=np.arange(-25., 55, 71),
                    ylocs=np.arange(25., 71., 47.),
                    linestyle='--',
                    color='0.5',
                    linewidth=0.3,
                    zorder=20)
        ax.add_feature(cfeature.BORDERS) #Add countries borders on the map
        CS1 = ax.pcolormesh(lons_mesh,lats_mesh,var[k],cmap='seismic',transform=proj_pc, vmin=the_levels[0],vmax=the_levels[1])
        ax.scatter(X_scatt[k],Y_scatt[k],marker='o',s=0.2,alpha=0.7,color='black',transform=proj_pc,zorder=100) #scatter plot of the locations for which 95th percentile threshold is exceeded for at least 3 consecutive days
        date=calendar[k]
        cax = plt.axes([0.35, 0.05, 0.35, 0.02])
        plt.colorbar(CS1,cax=cax,orientation='horizontal')
        plt.title('Temperature anomaly (°C) on '+' '+date,{'position':(0.5,-2)})
        return CS1

    def init():
        return draw(0)

    def update(k):
        return draw(k)

    anim = animation.FuncAnimation(fig, update, init_func=init, frames=np.shape(var)[0], blit=False, interval=0.15, repeat=False)

    #plt.show()
    #f2 = r"/home/tmandonnet/E-OBS_use/Animation_ext_temp/Heat_wave_2003_anomaly_threshold.mp4" 
    filename_movie = '/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/Undetected_heatwaves/Undetected_'+heatwaves_undetected_emdat[i]+'.mp4'
    writervideo = animation.FFMpegWriter(fps=1) 
    anim.save(filename_movie, writer=writervideo) #save video
    fig.clear()
f.close()