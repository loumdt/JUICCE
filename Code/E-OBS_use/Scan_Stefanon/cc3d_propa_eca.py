#%%
import numpy as np
import numpy.ma as ma 
import netCDF4 as nc 
import matplotlib.pyplot as plt 
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 
import pandas as pd
import matplotlib.animation as animation
from tqdm import tqdm
import sys,os
import cc3d
#%%
try : 
	the_variable = str(sys.argv[1])
except :
	the_variable='tg'

try : 
	year_beg = int(sys.argv[2])
except :
	year_beg = 1950

try : 
	year_end = int(sys.argv[3])
except :
	year_end = 2021

try : 
	threshold_value = int(sys.argv[4])
except :
	threshold_value = 95
#%%
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
print('the_variable :',the_variable)
#%%
try :
    nc_file_label = os.path.join(os.environ["DATADIR"] , "E-OBS" , "0.1deg" , the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value-5)+"th_CC3D_LABELS.nc")
except :
    nc_file_label = "Data/E-OBS/0.1deg/"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value-5)+"th_CC3D_LABELS_v2.nc"#path to the output netCDF file
#%%
f_label=nc.Dataset(nc_file_label, mode='r')
#%%
try :
	nc_file_in = os.path.join(os.environ["DATADIR"] , "E-OBS" , "Detection_Canicule" ,"heatwaves_4days_scan_TWICE_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_scan_size35_10.0%.nc")
except :
    nc_file_in="Data/E-OBS/Detection_Canicule/heatwaves_4days_scan_TWICE_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_scan_size35_10.0%.nc"
#%%
#Load E-OBS Europe mask
try:
    nc_file_mask = os.path.join(os.environ["DATADIR"], "E-OBS", "Mask", "Mask_Europe_E-OBS_0.1deg.nc")#file to load the corrected mask for all Europe
except :
    nc_file_mask = "Data/E-OBS/Mask/Mask_Europe_E-OBS_0.1deg.nc"
#%%
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask_all'][:]
#%%
print('nc_file_in',nc_file_in)
f=nc.Dataset(nc_file_in, mode='r')
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
date_idx_JJA=f.variables['date_idx'][:]
date_idx_1950=f.variables['date_idx_1950'][:]
date_format=f.variables['date_format'][:] #date as a string, yyyy-mm-dd format
date_format_readable = [""]*len(date_idx_JJA)
date_format_readable_year_only=[""]*len(date_idx_JJA) #keep only the four characters of the date corresponding to the year
for i in tqdm(range(len(date_format))) :
    date_format_readable[i] = "".join(date_format[:].astype(str).data[i])
    date_format_readable_year_only[i] = (date_format_readable[i])[:4]
year_list=list(set(date_format_readable_year_only))
year_list.sort()
#%%
stored = np.zeros((len(time_in),len(lat_in),len(lon_in)))
#%%
unique_htw_cc3d_idx = []
for i in tqdm(range(len(time_in))) :
    temp = ma.filled(f.variables['temp'][i,:,:],fill_value=-9999)
    labels = ma.array(f_label.variables['label'][date_idx_JJA[i],:,:],dtype=int)
    indices = (temp!=-9999)*labels
    dusted = cc3d.dust(indices>0,294) # scan_lat*scan_lon*pourcent*4_days = 35*35*0.6*4 = 2940 -> 294 is negligible  with respect to our detection threshold
    indices = indices*(dusted>0)
    stored[i,:,:] = indices[:]
    for j in np.unique(indices):
        unique_htw_cc3d_idx.append(j)
    #if i == 10:
    #    break
#%%
unique_htw_cc3d_idx = np.unique(unique_htw_cc3d_idx)
unique_htw_cc3d_idx = np.array(unique_htw_cc3d_idx[1:-1],int) #removing 0 and masked items, that are in first and last positions
print(len(unique_htw_cc3d_idx),"heatwaves detected")
#exit()
#%%
df_htw = pd.DataFrame(columns=['htw_label','potentially_connected_heatwaves','connected_heatwaves'],index=range(len(unique_htw_cc3d_idx)),data=None)
#%%
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
#%%
#load JJA temperature anomaly data file
try:
    nc_file_temp = os.path.join(os.environ["DATADIR"], "E-OBS", "0.1deg", the_variable+"_anomaly_JJA_only_"+str(year_beg)+"_"+str(year_end)+".nc")
except :
    nc_file_temp = "Data/E-OBS/0.1deg/"+the_variable+"_anomaly_JJA_only_"+str(year_beg)+"_"+str(year_end)+".nc"
#%%
f_temp=nc.Dataset(nc_file_temp, mode='r')
def x_round(x):
        return round(x*4)/4 #find nearest 0.25 value in order to create contourf with 0.25°C precision

all_time_idx=[[-1]]*(len(unique_htw_cc3d_idx))
#%%
run_animation = False
#for event in tqdm(range(349,len(unique_htw_cc3d_idx))) : #resume in 2014 because of error
for event in tqdm(range(len(unique_htw_cc3d_idx))) :
    htw_label = unique_htw_cc3d_idx[event]
    df_htw.loc[event,'htw_label']=htw_label
    time_idx_var = [int(i) for i in np.unique(np.argwhere(stored==htw_label)[:,0])]
    dates_JJA = date_idx_JJA[time_idx_var]
    df_htw.loc[event,'potentially_connected_heatwaves']=[]
    if event>0 :
        for i in range(len(all_time_idx)) :
            time_list = all_time_idx[i]
            if (dates_JJA[0] in time_list) or (dates_JJA[-1] in time_list) or (dates_JJA[0]==time_list[-1]+1) :
                df_htw.loc[event,'potentially_connected_heatwaves'].append(i)
    if run_animation :
        var_scatter = stored[time_idx_var,:,:] #all labels of the chosen period
        nb_frames = len(time_idx_var)
        var = ma.array(f_temp.variables['temp'][dates_JJA,:,:])
        #var_range = ma.array(f.variables['temp'][heatwaves_idx_2[event,0]:heatwaves_idx_2[event,0]+heatwaves_idx_2[event,1],:,:])
        min_val = min(-np.abs(np.min(var)),-np.abs(np.max(var))) 
        max_val = max(np.abs(np.min(var)),np.abs(np.max(var))) 
        
        the_levels=[0]*9
        for k in range(len(the_levels)):
            the_levels[k]=min_val+k*(max_val-min_val)/(len(the_levels)-1)

        X_scatt = np.ndarray(nb_frames,dtype=object)
        Y_scatt = np.ndarray(nb_frames,dtype=object)

        date_event = []

        for i in range(nb_frames) :
            X_scatt[i] = np.argwhere(var_scatter[i]==htw_label)[:,1] #lon
            Y_scatt[i] = np.argwhere(var_scatter[i]==htw_label)[:,0] #lat
            X_scatt[i] = lon_in[X_scatt[i]]
            Y_scatt[i] = lat_in[Y_scatt[i]]
            date_event.append(date_format_readable[time_idx_var[i]])
            
        def make_figure():
            fig = plt.figure(event,figsize=(24,16))
            ax = plt.axes(projection=proj_pc)
            return fig,ax

        fig,ax = make_figure()
        cax = plt.axes([0.35, 0.05, 0.35, 0.02])
        def draw(i):
            ax.clear()
            ax.set_extent([lon_in[0]+0.1, lon_in[-1]-0.1, lat_in[-1]+0.1, lat_in[0]-0.1])
            ax.set_title(titre, fontsize='x-large')
            ax.add_feature(cfeature.BORDERS)
            ax.add_feature(cfeature.LAND)
            ax.add_feature(cfeature.OCEAN)
            ax.add_feature(cfeature.COASTLINE,linewidth=0.3)
            ax.add_feature(cfeature.LAKES, alpha=0.5)
            ax.add_feature(cfeature.RIVERS, alpha=0.5)
            #CS1 = ax.pcolormesh(lons_mesh,lats_mesh,var[i],cmap='cividis',transform=proj_pc, vmin=the_levels[0],vmax=the_levels[1])
            CS1 = ax.contourf(lons_mesh,lats_mesh,var[i],cmap='cividis',transform=proj_pc, levels=the_levels)
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
        try :
            filename_movie = os.path.join(os.environ["DATADIR"] , "Output", "E-OBS" , "CC3D_animation_v3_"+the_variable ,"Heatwaves_Stefanon_"+the_variable+"_n°"+str(event)+"_"+date_event[0]+"_"+date_event[-1]+".mp4")
        except :
            filename_movie = "Output/E-OBS/CC3D_animation_v3_"+the_variable+"/Heatwaves_Stefanon_"+the_variable+"_n°"+str(event)+"_"+date_event[0]+"_"+date_event[-1]+".mp4"
        writervideo = animation.FFMpegWriter(fps=1)
        anim.save(filename_movie, writer=writervideo)
        plt.close()
    
    all_time_idx[event]=list(dates_JJA.data)

f.close()
f_temp.close()
f_label.close()
f_mask.close()
try :
    df_htw.to_excel(os.path.join(os.environ["DATADIR"] , "Output", "E-OBS" ,"df_htw_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+".xlsx"))
except :
    df_htw.to_excel("Output/E-OBS/df_htw_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_v2.xlsx")
#%%
exit()
#%%
##############
## SCANNING ##
##############

for i in tqdm(range(len(date_format))) :
    date_format_readable[i] = "".join(date_format[:].astype(str).data[i])
    date_format_readable_year_only[i] = (date_format_readable[i])[:4]
year_list=list(set(date_format_readable_year_only))
year_list.sort()

scan_lat=35
scan_lon=35

weight = np.cos(np.pi*lat_in/180) # the weight of each cell, depending on the latitude
land_sea_mask=f_mask.variables['mask_all'][:] # mask in order to define land_sea_mask and sea_cpt_table_bool_4d
sea_cpt_table_bool_4d=np.zeros((len(lat_in),len(lon_in),scan_lat,scan_lon))
weight_table_4d=np.zeros((len(lat_in),len(lon_in),scan_lat,scan_lon))

for i in tqdm(range((len(lat_in)-scan_lat))) :
    for j in range((len(lon_in)-scan_lon)) :
        weight_table_4d[i,j,:,:]=np.array([weight[i:i+scan_lat]]*scan_lon)
        sea_cpt_table_bool_4d[i,j,:,:]=np.array(land_sea_mask[i:i+scan_lat,j:j+scan_lon]==True)

weight_table_2d=np.sum(weight_table_4d,-1) #sum the weight of one scanning window, longitude axis
weight_table_2d=np.sum(weight_table_2d,-1) #sum the weight of one scanning window, latitude axis
sea_cpt_table=sea_cpt_table_bool_4d*weight_table_4d
sea_cpt_table=np.sum(sea_cpt_table,-1) #sum the weight of one scanning window, longitude axis
sea_cpt_table=np.sum(sea_cpt_table,-1) #sum the weight of one scanning window, latitude axis

print('4D tables have been created')

#-------------------

for i in tqdm(range(len(time_in))) :
    temp = ma.filled(f.variables['temp'][i,:,:],fill_value=-9999)
    labels = ma.array(f_label.variables['label'][date_idx_JJA[i],:,:],dtype=int)
    indices = (temp!=-9999)*labels
    if indices.any():
       arr_1D = np.delete(arr_1D, np.where(arr_1D == 8)) 
       
       
count_recorded_days=0
for i in tqdm(range(len(year_list))) : #for every year that is in the file
    dict_match = {}
    idx_days=np.array([],dtype=np.int32)
    while count_recorded_days<len(time_in) and date_format_readable_year_only[count_recorded_days] == year_list[i] :
        idx_days = np.append(idx_days,int(count_recorded_days))
        count_recorded_days += 1
    dates = [date_idx_JJA[i] for i in range(len(date_idx_JJA)) if i in idx_days]
    time_extract = [time_in[i] for i in range(len(time_in)) if i in idx_days]
    time_1950 = [date_idx_1950[i] for i in range(len(date_idx_1950)) if i in idx_days]
    date_format = [date_format_readable[i] for i in range(len(date_format_readable)) if i in idx_days]
    temp = ma.filled(f.variables['temp'][idx_days,:,:],fill_value=-9999)
    labels = ma.array(f_label.variables['label'][dates,:,:],dtype=int)
    indices = (temp!=-9999)*labels
    red_temp = ma.array(f.variables['temp'][idx_days,:,:])
    red_temp = ma.filled(red_temp,fill_value=-9999)
    for j in range(np.shape(labels)[0]):
        for k in range((len(lat_in)-scan_lat)) :
                for l in range((len(lon_in)-scan_lon)) :
                    pass

for year in tqdm(range(an)) :
    red = ma.array(f.variables['temp'][year*92:(year+1)*92,:,:])#,mask=[land_sea_mask]*92) # start = 01/06 ; end = 31/08 ; SHAPE = (time,lat,lon)
    red = ma.masked_values(red,-9999) #mask values that do not exceed the percentile threshold
    siz = np.shape(red) #siz[1]=lat, siz[2]=lon
    #make the scan operation of each zone in order to determine the heatwaves dates, stored into the netCDF file
    for t in range(92) :
        cpt_table_bool=ma.array(np.zeros((siz[1],siz[2],scan_lat,scan_lon)),mask=False) #siz[1]=lat, siz[2]=lon

        if not red[t,:,:].mask.all() :
            for i in range((len(lat)-scan_lat)) :
                for j in range((len(lon)-scan_lon)) :
                    cpt_table_bool[i,j,:,:]=ma.array(1-red[t,i:i+scan_lat,j:j+scan_lon].mask) #this takes time, could probably be improved
        
        cpt_table = cpt_table_bool*weight_table_4d

        cpt_table = np.sum(cpt_table,-1)
        cpt_table = np.sum(cpt_table,-1)

        detect_heatwave_table_bool=np.array(cpt_table > np.round((weight_table_2d-sea_cpt_table)*pourcent)) #each cell is the result of the matching scanning window
        #the previous line entails an issue on coastlines -> the scanning operation is biased on these points, I decided to correct it with a second scanning operation (stefanon_4_scan_cor_2nd_time.py)
        if detect_heatwave_table_bool.any() : #Check if at least one of the scanning windows has detected a sub-heatwave
            ntimes=np.shape(temp)[0] #take the time dimension length in order to know the next index to use
            date_idx[ntimes]=year*92+t
            date_format[ntimes] = nc.stringtochar(np.array([calendar[year,t]], 'S10'))
            temp[ntimes,:,:]=ma.array(-9999*np.ones((siz[1],siz[2])),mask=red[t,:,:].mask) #siz[1]=lat, siz[2]=lon
            stack_where=np.argwhere(detect_heatwave_table_bool)
            for i,j in stack_where:
                temp[ntimes,i:i+scan_lon,j:j+scan_lat] = red[t,i:i+scan_lon,j:j+scan_lat] #save the temperature anomalies responsible for the sub-heatwave
time[:]=range(ntimes+1)
temp[:]=ma.masked_outside(temp,-100,100)
print('save done')
print('Number of recorded sub-heatwave days :', ntimes+1)
