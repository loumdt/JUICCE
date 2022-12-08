"""Scan temperature maps to extract heatwaves. Argument is either tg for mean, tx for max, or tn for min."""
import numpy as np
import numpy.ma as ma 
import netCDF4 as nc 
import matplotlib.pyplot as plt 
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 
import matplotlib.animation as animation
from tqdm import tqdm
import sys

import warnings
#warnings.filterwarnings("ignore", category=DeprecationWarning) 
#warnings.filterwarnings( "ignore", module = "matplotlib\..*" )

#-------------------

the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)


nc_file_mask="D:/Ubuntu/PFE/Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc" #file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
mask_all=f_mask.variables['mask_all'][:]

#-------------------

#nc_file_in="/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_tg_anomaly_threshold_95th_scan_size35_60.0%.nc" #this is the V1 output
#nc_file_in="/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_tg_anomaly_threshold_95th_scan_size35_60.0%.nc" #this is the V2 output
nc_file_in="D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_TWICE_"+the_variable+"_anomaly_threshold_95th_scan_size35_10.0%.nc" #this is the V3 output

print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
date_idx=f.variables['date_idx'][:] #date as the matching index of the summer-only netCDF file
date_format=f.variables['date_format'][:] #date as a string, dd/mm/yyyy format
date_format_readable=np.ndarray(np.shape(date_format)[0],dtype=object) #make date_format human-readable
date_format_readable_year_only=np.ndarray(np.shape(date_format)[0],dtype=object) #keep only the last four characters of the date (corresponding to the year)

for i in range(np.shape(date_format)[0]):
    date_format_readable[i]=str(date_format[i].tobytes())[2:-1]
    date_format_readable_year_only[i]=date_format_readable[i][-4:]

year_list=list(set(date_format_readable_year_only))
year_list.sort()

freq_cut = 1
recover_area = 0.4

nb_event=[]
idx_beg = np.array([])
idx_beg_2 = np.array([])
idx_end = np.array([])
date_beg = np.array([])
date_end = np.array([])


count_recorded_days=0
for i in tqdm(range(len(year_list))) : #for every year that appear to be in the file (probably every year from 1950 to 2020)
    indice=np.array([],dtype=np.int32)
    while count_recorded_days<len(time_in) and date_format_readable_year_only[count_recorded_days] == year_list[i] :
        indice = np.append(indice,int(count_recorded_days))
        count_recorded_days += 1
    #print(year_list[i])
    nb_event.append(np.zeros((100,1)))
    red_temp = ma.array(f.variables['temp'][indice,:,:],mask=[mask_all]*len(indice))
    dates = date_idx[indice]
    time_extract = time_in[indice]
    date_format = date_format_readable[indice]
    test = np.ones(np.shape(red_temp))*(red_temp!=0)

    del red_temp 

    cpt = 0
    compt = 0
    propa = 0
    date_propa_idx = np.array([])
    date_propa_format = np.array([])
    for i in range(1,len(indice)) :
        #print(i)
        dif = test[i,:,:] + test[i-1,:,:]
        ind_a = np.argwhere(test[i,:,:] == 1)
        ind_b = np.argwhere(test[i-1,:,:] == 1 )
        ind_c = np.argwhere(dif[:,:] == 2)
        #print(len(ind_a),len(ind_b),len(ind_c))
        if len(ind_c)/max(len(ind_a),len(ind_b)) > recover_area :
            if (dates[i] - dates[i-1]) > freq_cut :
                idx_beg = np.append(idx_beg,dates[i-cpt])
                idx_beg_2 = np.append(idx_beg_2,time_extract[i-cpt])
                date_beg = np.append(date_beg,date_format[i-cpt])
                idx_end = np.append(idx_end,dates[i-1])
                date_end = np.append(date_end,date_format[i-1])
                nb_event[-1][cpt] = nb_event[-1][cpt] + 1
                compt = compt + 1
                cpt = 1

            else :
                cpt = cpt +1
            propa = 1
            date_propa_idx = np.append(date_propa_idx,dates[i])
            date_propa_format = np.append(date_propa_format,date_format[i])
        else :
            if (cpt >= freq_cut) and propa == 1 :
                idx_beg = np.append(idx_beg,dates[i-cpt])
                idx_beg_2 = np.append(idx_beg_2,time_extract[i-cpt])
                date_beg = np.append(date_beg,date_format[i-cpt])
                idx_end = np.append(idx_end,dates[i-1])
                date_end = np.append(date_end,date_format[i-1])
                nb_event[-1][cpt] = nb_event[-1][cpt] + 1
                compt = compt + 1           
                cpt = 1
                propa = 0
            cpt = 1      
            propa = 0

nb_event=np.array(nb_event)
nb_event.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/nb_event_"+the_variable+"_V3.npy")
idx_beg.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/idx_beg_"+the_variable+"_V3.npy")
idx_end.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/idx_end_"+the_variable+"_V3.npy")
date_beg.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/date_beg_"+the_variable+"_V3.npy")
date_end.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/date_end_"+the_variable+"_V3.npy")

idx_heatwaves=0
heatwaves_dates = []
heatwaves_idx = []
heatwaves_idx_2 = []
for i in range(len(date_beg)):
    if idx_end[i]-idx_beg[i]>=3:
        heatwaves_dates.append([date_beg[i],date_end[i]])
        heatwaves_idx.append([idx_beg[i],idx_end[i]])
        heatwaves_idx_2.append([idx_beg_2[i],idx_end[i]-idx_beg[i]+1])


heatwaves_dates = np.array(heatwaves_dates)
heatwaves_idx = np.array(heatwaves_idx,dtype=np.int32)
heatwaves_idx_2 = np.array(heatwaves_idx_2,dtype=np.int32)

heatwaves_dates.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_dates_4days_"+the_variable+"_V3.npy")
heatwaves_idx.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_4days_"+the_variable+"_V3.npy")
heatwaves_idx_2.dump("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_2_4days_"+the_variable+"_V3.npy")

print(len(heatwaves_dates),"heatwaves recorded")
#exit()

#-------------------------------#
# Make animations for heatwaves #
#-------------------------------#

#projection
proj_pc = ccrs.PlateCarree() 

# my_proj, plot_coord_labels = ccrs.Mollweide(), False # Labels not supported yet for Mollweide
my_proj, plot_coord_labels = proj_pc, False # Labels or OK for PlateCarree

lons_mesh = lon_in
lats_mesh = lat_in

lon_in=np.array(lon_in)
lat_in=np.array(lat_in)

titre = "E-OBS daily "+temp_name_dict[the_variable]+" temperature anomaly (°C)"

nc_file_anomaly = 'D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_'+the_variable+'_summer_only_1950-2020.nc'
f_anomaly=nc.Dataset(nc_file_anomaly, mode='r')

for event in tqdm(range(len(heatwaves_idx))) :

    #print('Computing event', event+1, '/',len(heatwaves_idx))

    nb_frames = heatwaves_idx[event,1]-heatwaves_idx[event,0]+1
    var = ma.array(f_anomaly.variables['temp'][heatwaves_idx[event,0]:heatwaves_idx[event,1]+1,:,:])
    min_val = min(-np.abs(np.min(var)),-np.abs(np.max(var))) 
    max_val = max(np.abs(np.min(var)),np.abs(np.max(var))) 

    the_levels=[min_val,max_val] #values for colormap, centered on zero for better visibility

    X_scatt = np.ndarray(nb_frames,dtype=object)
    Y_scatt = np.ndarray(nb_frames,dtype=object)

    date_event = []
    #print(X_scatt)
    #print(Y_scatt)
    #print(date_event)

    for i in range(nb_frames) :
        #print(heatwaves_idx_2[event,0]+i)
        X_scatt[i] = np.argwhere(ma.array(f.variables['temp'][heatwaves_idx_2[event,0]+i,:,:])>0)[:,1]
        Y_scatt[i] = np.argwhere(ma.array(f.variables['temp'][heatwaves_idx_2[event,0]+i,:,:])>0)[:,0]
        X_scatt[i] = lon_in[X_scatt[i]]
        Y_scatt[i] = lat_in[Y_scatt[i]]
        date_event.append(date_format_readable[int(heatwaves_idx_2[event,0]+i)])
        
    #print(date_event)
    def make_figure():

        fig = plt.figure(event,figsize=(24,16))
        ax = plt.axes(projection=proj_pc)
        return fig,ax

    fig,ax = make_figure()
    cax = plt.axes([0.35, 0.05, 0.35, 0.02])
    def draw(i):
        ax.clear()
        ax.set_extent([lon_in[0]+0.1, lon_in[-1]-0.1, lat_in[-1]+0.1, lat_in[0]-0.1])
        ax.stock_img()
        #ax.outline_patch.set_zorder(50)
        ax.set_title(titre, fontsize='x-large')
        #ax.gridlines(draw_labels=plot_coord_labels,
                    #xlocs=np.arange(-25., 55, 71),
                    #ylocs=np.arange(25., 71., 47.),
                    #linestyle='--',
                    #color='0.5',
                    #linewidth=0.3,
                    #zorder=20)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(cfeature.COASTLINE)
        CS1 = ax.pcolormesh(lons_mesh,lats_mesh,var[i],cmap='seismic',transform=proj_pc, vmin=the_levels[0],vmax=the_levels[1])
        ax.scatter(X_scatt[i],Y_scatt[i],marker='o',s=0.2,alpha=0.7,color='black',transform=proj_pc,zorder=100)
        
        plt.colorbar(CS1,cax=cax,orientation='horizontal')
        plt.title('Temperature (°C) on '+' '+date_event[i],{'position':(0.5,-2)})
        return CS1

    def init():
        return draw(0)

    def update(i):
        return draw(i)


    anim = animation.FuncAnimation(fig, update, init_func=init, frames=nb_frames, blit=False, interval=0.15, repeat=False)

    #plt.show()

    filename_movie = "D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/Animation_detected_heatwaves_Stefanon_4days_scan_"+the_variable+"_size35_60.0%/Heatwaves_Stefanon_"+the_variable+"_n°"+str(event)+"_"+heatwaves_dates[event,0]+"_"+heatwaves_dates[event,1]+".mp4"
    writervideo = animation.FFMpegWriter(fps=1)
    anim.save(filename_movie, writer=writervideo)
    plt.close()


f.close()
f_mask.close()
f_anomaly.close()