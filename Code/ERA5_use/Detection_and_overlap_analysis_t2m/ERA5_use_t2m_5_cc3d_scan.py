#%%
#Import modules
import numpy as np #handle lists, tables, etc (arrays)
import numpy.ma as ma #handle masks and masked arrays
import cc3d #connected components patterns
import netCDF4 as nc #handle netCDF data (read and write)
import sys,os #use operating system command and read comand line arguments
from datetime import datetime
from tqdm import tqdm #feedback nice loading bars when using 'for' loops
import matplotlib
import matplotlib.pyplot as plt 
import pandas as pd
import matplotlib.animation as animation
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 
import pathlib
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
#Read arguments
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
#-------------------------------------
#define pathway to temperature data
nc_in_path = os.path.join(datadir , "ERA5" , "t2m" ,the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_scaled_"+str(threshold_value)+"th.nc") 
#Load temperature data file
f=nc.Dataset(nc_in_path, mode='r')#load input file dimensions/variables
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
date_idx_JJA = [int(i) for i in time_in.data]
time_in = np.ndarray(shape=np.shape(date_idx_JJA),dtype=int)
time_in[:] = date_idx_JJA[:]
date_idx_1950_in=f.variables['date_idx_1950'][:]
date_idx_1950_in = [int(i) for i in date_idx_1950_in.data]
dates_all_1950 = np.ndarray(shape=np.shape(date_idx_1950_in),dtype=int)
dates_all_1950[:] = date_idx_1950_in[:]
#%%
#Load ERA5 mask -> masked African and Middle-East countries, ocean and sea are not masked yet
nc_file_mask = os.path.join(datadir, "ERA5", "Mask", "Mask_Europe_1_ERA5_0.25deg.nc")#file to load the corrected mask for all Europe
f_mask=nc.Dataset(nc_file_mask,mode='r')
Mask_0 = f_mask.variables['mask'][:]
#%%
nc_file_potential_htws = os.path.join(datadir , "ERA5" , "Detection_Canicule" , "potential_heatwaves_"+the_variable+"_"+str(nb_days)+"days_before_scan_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th.nc")

f_pot_htws=nc.Dataset(nc_file_potential_htws, mode='r')
date_format=f_pot_htws.variables['date_format'][:] #date as a string, yyyy-mm-dd format
date_format_readable = [""]*len(time_in)
date_format_readable_year_only=[""]*len(time_in) #keep only the four characters of the date corresponding to the year
print("Computing calendar...")
for i in tqdm(range(len(date_format))) :
    date_format_readable[i] = "".join(date_format[:].astype(str).data[i])
    date_format_readable_year_only[i] = (date_format_readable[i])[:4]
#%%
#define pathway to output netCDF file, no need to create directory.
nc_out_path = os.path.join(datadir , "ERA5" , "Detection_Canicule" , "detected_heatwaves_"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_"+str(nb_days)+"days.nc")
#Create output netCDF file
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #mode='w' for 'write', 'a' for 'append'

#Create output file dimensions
lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', 92*(year_end-year_beg+1)) # unlimited time axis (can be appended to).

#Output file title and history for more detailed information (not necessary)
nc_file_out.title="Labels of CC3D for "+temp_name_dict[the_variable]+" temperature anomaly for JJA days from "+str(year_beg)+" to "+str(year_end)
nc_file_out.subtitle="values are set to zero not exceeding "+str(threshold_value)+"th temperature anomaly threshold, and labels are assigned to contiguous elements"
nc_file_out.history = "Created with ano_scale_jja_selec.py on " +datetime.today().strftime("%d/%m/%y")

#Create output file variables
# variable = nc_file_out.createVariable('variable_name',format, (dimensions))
lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.float32, ('time',))
time.units = 'days of JJA from '+str(year_beg)+' to '+str(year_end)
time.long_name = 'time'
date_idx_1950 = nc_file_out.createVariable('date_idx_1950', np.int32,('time',))
date_idx_1950.units = 'days from 01-01-1950'
date_idx_1950.long_name = 'date_index_1950'
# Define a 3D variable to hold the data
label = nc_file_out.createVariable('label',np.int32,('time','lat','lon')) # note: unlimited dimension is leftmost
label.long_name = 'cc3d_label'

#note : the [:] statements are necessary in these following statements. 
# Otherwise, you do not write in the content of the netCDF dimension but only create another local variable.
lat[:] = lat_in
lon[:] = lon_in
time[:]=range(92*(year_end-year_beg+1))
date_idx_1950[:]=date_idx_1950_in
#creating a masked array full of -9999
label[:] = ma.array(-9999*np.ones((len(time_in),len(lat_in),len(lon_in))),mask=[Mask_0]*(92*(year_end-year_beg+1))) #shape is time*lat*lon
#%%
f_land_sea_mask = nc.Dataset(os.path.join(datadir,"ERA5","Mask","Mask_Europe_land_only_ERA5_0.25deg.nc"),mode='r')
land_sea_mask = f_land_sea_mask.variables['mask'][:]
#%%
f_france_mask = nc.Dataset(os.path.join(datadir,"ERA5","Mask","Mask_France_ERA5_0.25deg.nc"),mode='r')
france_mask = f_france_mask.variables['mask'][:]
#%%
print("Computing cc3d.connected_components labels and dusting...")
#nb_htws_list = [0]*30

#for k in tqdm(range(30))  :
N_labels=0 #count the numbers of patterns
unique_htw_cc3d_idx = []

for year in tqdm(range((year_end-year_beg+1))) :#iterate over the years

    sub_htws = ma.masked_where([land_sea_mask]*92,f_pot_htws.variables['t2m'][year*92:(year+1)*92,:,:])
    sub_htws = ma.filled(sub_htws,fill_value=-9999)
    sub_htws = (sub_htws!=-9999)

    connectivity = 26 # only 4,8 (2D) and 26, 18, and 6 (3D) are allowed
    labels_in = cc3d.dust(sub_htws,775)#25*k) #int(0.6*14*14*nb_days))
    labels_out, N_added = cc3d.connected_components(labels_in, connectivity=connectivity,return_N=True) #return the table of lables and the number of added patterns
    #update output netCDF variable :
    label[year*92:(year+1)*92,:,:] = ma.array(labels_out,mask=[Mask_0]*92)
    label[year*92:(year+1)*92,:,:] = ma.masked_where(labels_out==0,label[year*92:(year+1)*92,:,:])
    label[year*92:(year+1)*92,:,:] += N_labels
    label[year*92:(year+1)*92,:,:] = ma.masked_where(sub_htws==0,label[year*92:(year+1)*92,:,:])

    for val in np.unique(label[year*92:(year+1)*92,:,:]) :
        try :
            unique_htw_cc3d_idx.append(int(val))
        except :
            pass
    #update N_labels
    N_labels+=N_added
    #nb_htws_list[k]=len(unique_htw_cc3d_idx)
#%%
print(len(unique_htw_cc3d_idx),"heatwaves detected")
#%%
elbow = False
#if elbow :
#    plt.figure()
#    plt.plot(range(30),nb_htws_list)
#    #plt.savefig('France_nb_htws.png')
#    plt.show()
#    k=1
#    while k<30 and nb_htws_list[k]<0.99*nb_htws_list[k-1] :
#        k=k+1
#    print(k)
#%%
#exit()
#%%
df_htw = pd.DataFrame(columns=['idx_beg_JJA','idx_end_JJA','idx_beg_1950','idx_end_1950'],index=unique_htw_cc3d_idx,data=None)
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

titre = "ERA5 daily "+temp_name_dict[the_variable]+" temperature anomaly (°C)"
#%%
#load JJA temperature anomaly data file
nc_file_temp = os.path.join(datadir, "ERA5", "t2m", the_variable+"_anomaly_JJA_only_"+str(year_beg)+"_"+str(year_end)+".nc")
#%%
f_temp=nc.Dataset(nc_file_temp, mode='r')
all_time_idx=[[-1]]*(len(unique_htw_cc3d_idx))
#%%
matplotlib.use('Agg')
output_dir_anim = os.path.join("Output", "ERA5" , the_variable ,
                          the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days", 
                          "animation_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days")
pathlib.Path(output_dir_anim).mkdir(parents=True,exist_ok=True)
#%%
#############################################################
#True for exporting mp4 animations of the detected heatwaves#
run_animation = False                                       #
#############################################################
#%%
for event in tqdm(unique_htw_cc3d_idx[:]):
    time_idx_var = [int(i) for i in np.unique(np.argwhere(label[:]==event)[:,0])]
    #if len(time_idx_var) != (np.max(time_idx_var)-np.min(time_idx_var)+1):
    #    print("Missing day in heatwave n°", event)
    dates_JJA = time_in[time_idx_var]
    dates_1950 = dates_all_1950[time_idx_var]
    df_htw.loc[event,'idx_beg_JJA'] = dates_JJA[0]
    df_htw.loc[event,'idx_end_JJA'] = dates_JJA[-1]
    df_htw.loc[event,'idx_beg_1950'] = dates_1950[0]
    df_htw.loc[event,'idx_end_1950'] = dates_1950[-1]
    #if event>0 :
    #    for i in range(len(all_time_idx)) :
    #        time_list = all_time_idx[i]
    #        if (dates_JJA[0] in time_list) or (dates_JJA[-1] in time_list) or (dates_JJA[0]==time_list[-1]+1) :
    #            df_htw.loc[event,'potentially_connected_heatwaves'].append(i+1)
    if run_animation :
        var_scatter = label[time_idx_var,:,:] #all labels of the chosen period
        nb_frames = len(time_idx_var)
        var = ma.array(f_temp.variables['t2m'][dates_JJA,:,:])-273.15 #convert K to °C
        var[:] = ma.masked_where([(Mask_0+land_sea_mask)>0]*nb_frames,var[:])
        min_val = min(-np.abs(np.min(var)),-np.abs(np.max(var))) 
        max_val = max(np.abs(np.min(var)),np.abs(np.max(var))) 
        
        the_levels=[0]*11#nb of color categories + 1
        for k in range(len(the_levels)):
            the_levels[k]=min_val+k*(max_val-min_val)/(len(the_levels)-1)

        X_scatt = np.ndarray(nb_frames,dtype=object)
        Y_scatt = np.ndarray(nb_frames,dtype=object)

        date_event = []

        for i in range(nb_frames) :
            X_scatt[i] = np.argwhere(var_scatter[i]==event)[:,1] #lon
            Y_scatt[i] = np.argwhere(var_scatter[i]==event)[:,0] #lat
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
            ax.scatter(X_scatt[i],Y_scatt[i],marker='o',s=1,alpha=1,color='black',transform=proj_pc,zorder=100)
            
            plt.colorbar(CS1,cax=cax,orientation='horizontal')
            plt.title('Temperature (°C) on '+' '+date_event[i],{'position':(0.5,-2)})
            return CS1

        def init():
            return draw(0)

        def update(i):
            return draw(i)


        anim = animation.FuncAnimation(fig, update, init_func=init, frames=nb_frames, blit=False, interval=0.15, repeat=False)

        #plt.show()
        filename_movie = os.path.join(output_dir_anim,
                                      "Heatwave_"+the_variable+"_n°"+str(event)+"_"+date_event[0]+"_"+date_event[-1]+".mp4")
        writervideo = animation.FFMpegWriter(fps=1)
        anim.save(filename_movie, writer=writervideo)
        plt.close()
    
    #all_time_idx[event]=list(dates_JJA.data)
 
f.close()
f_temp.close()
f_mask.close()
f_land_sea_mask.close()
nc_file_out.close()
f_pot_htws.close()
output_dir_df = os.path.join("Output", "ERA5" , the_variable ,
                          the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days")
df_htw.to_excel(os.path.join(output_dir_df,"df_htw_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days.xlsx"))
#%%