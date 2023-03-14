#%%
import numpy as np
import netCDF4 as nc
import numpy.ma as ma
import pandas as pd
from tqdm import tqdm
import sys,os
import matplotlib
import matplotlib.pyplot as plt 
import pandas as pd
import matplotlib.animation as animation
from datetime import datetime
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 
import pathlib
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#read inputs or use defaults inputs
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
    
try : 
    nb_days = int(sys.argv[5])
except :
    nb_days = 4
#%%
#create dictionary for temperature name
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
#print input argument for feedback
print('the_variable :',the_variable)
print('threshold_value :',threshold_value)
print('year_beg :',year_beg)
print('year_end :',year_end)
print('nb_days :',nb_days)
#%%
df_emdat = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0)
flex_time_span = 7 #In order to account for potential EM-DAT imprecisions, we set a flexibility window of 7 days
#%% 
# # cc3d labels netCDF file
nc_file_in = os.path.join(datadir , "ERA5" ,"t2m", "Detection_Canicule" , "detected_heatwaves_"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_"+str(nb_days)+"days.nc")

f=nc.Dataset(nc_file_in,mode='r')
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
date_idx_JJA = [int(i) for i in time_in.data]
time_in = np.ndarray(shape=np.shape(date_idx_JJA),dtype=int)
time_in[:] = date_idx_JJA[:]

#%%
nc_file_potential_htws = os.path.join(datadir , "ERA5" , "t2m", "Detection_Canicule" , "potential_heatwaves_"+the_variable+"_"+str(nb_days)+"days_before_scan_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th.nc")
print('nc_file_potential_htws',nc_file_potential_htws)
f_pot_htws=nc.Dataset(nc_file_potential_htws, mode='r')
date_format=f_pot_htws.variables['date_format'][:] #date as a string, yyyy-mm-dd format
date_format_readable = [""]*len(time_in)
date_format_readable_year_only=[""]*len(time_in) #keep only the four characters of the date corresponding to the year
print("Computing calendar...")
for i in tqdm(range(len(date_format))) :
    date_format_readable[i] = "".join(date_format[:].astype(str).data[i])
    date_format_readable_year_only[i] = (date_format_readable[i])[:4]

#%%
#Load ERA5 mask -> masked African and Middle-East countries, ocean and sea are not masked yet
nc_file_mask = os.path.join(datadir, "ERA5", "Mask", "Mask_Europe_1_ERA5_0.25deg.nc")#file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask'][:]
#%%
f_land_sea_mask = nc.Dataset(os.path.join(datadir,"ERA5","Mask","Mask_Europe_land_only_ERA5_0.25deg.nc"),mode='r')
land_sea_mask = f_land_sea_mask.variables['mask'][:]
#%% 
#load JJA temperature anomaly data file
nc_file_temp = os.path.join(datadir, "ERA5", "t2m", the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+".nc")
f_temp=nc.Dataset(nc_file_temp, mode='r')
        
#%% 
# #Link EM-DAT country names format to netCDF mask country names format
country_dict = {'Albania':'Albania', 'Austria':'Austria', 'Belarus':'Belarus',
                'Belgium':'Belgium', 'Bosnia and Herzegovina':'Bosnia_and_Herzegovina',
                'Bulgaria':'Bulgaria', 'Canary Is':None, 'Croatia':'Croatia', 'Cyprus':'Cyprus', 
                'Czech Republic (the)':'Czechia', 'Denmark':'Denmark', 'Estonia':'Estonia', 
                'Finland':'Finland', 'France':'France', 'Germany':'Germany', 'Greece':'Greece', 
                'Hungary':'Hungary', 'Iceland':'Iceland', 'Ireland':'Ireland', 
                'Italy':'Italy', 'Latvia':'Latvia', 'Lithuania':'Lithuania',
                'Luxembourg':'Luxembourg', 'Montenegro':'Montenegro',
                'Macedonia (the former Yugoslav Republic of)':'Macedonia',
                'Moldova':'Moldova', 'Netherlands (the)':'Netherlands', 'Norway':'Norway', 
                'Poland':'Poland','Portugal':'Portugal', 'Romania':'Romania',
                'Russian Federation (the)':'Russia', 'Serbia':'Serbia', 
                'Serbia Montenegro':'Serbia', #The corresponding heatwave happened in Serbia, cf 'Location' data of EM-DAT
                'Slovakia':'Slovakia', 'Slovenia':'Slovenia', 'Spain':'Spain', 'Sweden':'Sweden',
                'Switzerland':'Switzerland', 'Turkey':'Turkey',
                'United Kingdom of Great Britain and Northern Ireland (the)':'United_Kingdom',
                'Ukraine':'Ukraine','Yugoslavia':'Serbia'} #The corresponding heatwave happened in Serbia, cf 'Location' data of EM-DAT
#%%
# #indices of beggining and end of month for a JJA set of data (92 days from 1st June to 31st August)
beg_month_only_idx_dict = {6:0,7:30,8:61} #30 days in June, 31 days in July and August
end_month_only_idx_dict = {6:29,7:60,8:91} #30 days in June, 31 days in July and August
#%% 
# #Read txt file containing undetected heatwaves to create undetected heatwaves list
with open(os.path.join("Output","ERA5",the_variable,the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days","emdat_undetected_heatwaves_ERA5_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days.txt"),'r') as f_txt:
    undetected_htw_list = f_txt.readlines()
f_txt.close()
# #Remove '\n' from strings
for i in range(len(undetected_htw_list)) :
    undetected_htw_list[i] = undetected_htw_list[i][:-1]
#%%
output_dir_anim = os.path.join("Output", "ERA5" , the_variable,
                                      the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days", 
                                      "animation_undetected_heatwaves_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days")
pathlib.Path(output_dir_anim).mkdir(parents=True,exist_ok=True)
for idx in tqdm(df_emdat.index.values) :
    if df_emdat.loc[idx,'Dis No'] in undetected_htw_list :
        country=df_emdat.loc[idx,'Country']
        year_event = df_emdat.loc[idx,'Year']
        labels_cc3d = f.variables['label'][(year_event-year_beg)*92:(year_event-year_beg+1)*92,:,:] #load all JJA cc3d label data for the given year
        temp = f_temp.variables['t2m'][(year_event-year_beg)*92:(year_event-year_beg+1)*92,:,:]
        if np.isnan(df_emdat.loc[idx,'Start Day']) :
            month_beg_event = int(df_emdat.loc[idx,'Start Month'])
            month_end_event = int(df_emdat.loc[idx,'End Month'])
            idx_beg = beg_month_only_idx_dict[month_beg_event]
            idx_end = end_month_only_idx_dict[month_end_event]+1
            
        elif np.isnan(df_emdat.loc[idx,'End Day']) :
            day_beg_event = int(df_emdat.loc[idx,'Start Day'])
            month_beg_event = int(df_emdat.loc[idx,'Start Month'])
            month_end_event = int(df_emdat.loc[idx,'End Month'])
            idx_beg = np.max([0, beg_month_only_idx_dict[month_beg_event] + day_beg_event-1 - flex_time_span])
            idx_end = end_month_only_idx_dict[month_end_event]+1

        else : #start day and end day are known
            day_beg_event = int(df_emdat.loc[idx,'Start Day'])
            month_beg_event = int(df_emdat.loc[idx,'Start Month'])
            day_end_event = int(df_emdat.loc[idx,'End Day'])
            month_end_event = int(df_emdat.loc[idx,'End Month'])
            idx_beg = np.max([0, beg_month_only_idx_dict[month_beg_event] + day_beg_event-1 - flex_time_span])
            idx_end = np.min([92,beg_month_only_idx_dict[month_end_event] + day_end_event + flex_time_span])
        
        labels_cc3d = ma.filled(labels_cc3d[idx_beg:idx_end,:,:],fill_value=-9999)
        labels_cc3d = (labels_cc3d!=-9999)
        temp = temp[idx_beg:idx_end,:,:]
        
        # make animation
        
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

        titre = "ERA5 daily "+temp_name_dict[the_variable]+" temperature anomaly (°C).\nEM-DAT heatwave recorded in "+country
        
        matplotlib.use('Agg')
        
        temp[:] = ma.masked_where([(Mask_0+land_sea_mask)>0]*(np.shape(temp)[0]),temp[:])
        nb_frames = np.shape(temp)[0]
        min_val = min(-np.abs(np.min(temp)),-np.abs(np.max(temp))) 
        max_val = max(np.abs(np.min(temp)),np.abs(np.max(temp))) 
        
        the_levels=[0]*11#nb of color categories + 1
        for k in range(len(the_levels)):
            the_levels[k]=min_val+k*(max_val-min_val)/(len(the_levels)-1)

        X_scatt = np.ndarray(nb_frames,dtype=object)
        Y_scatt = np.ndarray(nb_frames,dtype=object)

        date_event = date_format_readable[(year_event-year_beg)*92+idx_beg:(year_event-year_beg)*92+idx_end]

        for i in range(nb_frames) :
            X_scatt[i] = np.argwhere(labels_cc3d[i])[:,1] #lon
            Y_scatt[i] = np.argwhere(labels_cc3d[i])[:,0] #lat
            X_scatt[i] = lon_in[X_scatt[i]]
            Y_scatt[i] = lat_in[Y_scatt[i]]
                        
        def make_figure():
            fig = plt.figure(idx,figsize=(24,16))
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
            CS1 = ax.contourf(lons_mesh,lats_mesh,temp[i],cmap='cividis',transform=proj_pc, levels=the_levels)
            ax.scatter(X_scatt[i],Y_scatt[i],marker='o',s=1,alpha=1,color='black',transform=proj_pc,zorder=100)
            
            plt.colorbar(CS1,cax=cax,orientation='horizontal')
            plt.title('Temperature anomaly (°C) on '+' '+date_event[i],{'position':(0.5,-2)})
            return CS1

        def init():
            return draw(0)

        def update(i):
            return draw(i)


        anim = animation.FuncAnimation(fig, update, init_func=init, frames=nb_frames, blit=False, interval=0.15, repeat=False)

        #plt.show()
        filename_movie = os.path.join(output_dir_anim, 
                                      "Undetected_heatwave_"+the_variable+"_"+df_emdat.loc[idx,'Dis No']+"_"+date_event[0]+"_"+date_event[-1]+".mp4")
        writervideo = animation.FFMpegWriter(fps=1)
        anim.save(filename_movie, writer=writervideo)
        plt.close()
      
#%%  
f_land_sea_mask.close()
f.close()
f_mask.close()
f_temp.close()