#%%
import numpy as np
import netCDF4 as nc
import numpy.ma as ma
import pandas as pd
from tqdm import tqdm
import sys,os
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
flex_time_span = 7 #In order to account for potential EM-DAT imprecisions, we set a flexibility window of 7 days.
#%%
nc_file_in = os.path.join(datadir , "ERA5" , "Detection_Canicule" , "detected_heatwaves_"+the_variable+"_anomaly_JJA_"+str(year_beg)+"_"+str(year_end)+"_threshold_"+str(threshold_value)+"th_"+str(nb_days)+"days.nc")

f=nc.Dataset(nc_file_in,mode='r')
lat_in=f.variables['lat'][:]
lon_in=f.variables['lon'][:]
time_in=f.variables['time'][:]
date_idx_JJA = [int(i) for i in time_in.data]
time_in = np.ndarray(shape=np.shape(date_idx_JJA),dtype=int)
time_in[:] = date_idx_JJA[:]
#%% #Link EM-DAT country names format to netCDF mask country names format
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
#indices of beggining and end of month for a JJA set of data (92 days from 1st June to 31st August)
beg_month_only_idx_dict = {6:0,7:30,8:61} #30 days in June, 31 days in July and August
end_month_only_idx_dict = {6:29,7:60,8:91} #30 days in June, 31 days in July and August
#%%
ignored_events = ['1994-0759-ROU','2004-0361-SPI']
undetected_heatwaves = []
detected_heatwaves = []
for emdat_event in tqdm(df_emdat.index.values[:]) :
    if df_emdat.loc[emdat_event,'Dis No'] not in ignored_events :
        country=df_emdat.loc[emdat_event,'Country']
        f_mask=nc.Dataset(os.path.join(datadir, "ERA5","Mask","Mask_"+country_dict[country]+"_ERA5_0.25deg.nc"),mode='r')
        mask_country = f_mask.variables['mask'][:,:]
        htw_list = []
        year_event = df_emdat.loc[emdat_event,'Year']
        labels_cc3d = f.variables['label'][(year_event-year_beg)*92:(year_event-year_beg+1)*92,:,:] #load all JJA data for the given year
        labels_cc3d[:] = ma.masked_where([mask_country]*92,labels_cc3d)
        if np.isnan(df_emdat.loc[emdat_event,'Start Day']) :
            month_beg_event = int(df_emdat.loc[emdat_event,'Start Month'])
            month_end_event = int(df_emdat.loc[emdat_event,'End Month'])
            labels_cc3d = labels_cc3d[beg_month_only_idx_dict[month_beg_event]:end_month_only_idx_dict[month_end_event]+1,:,:]
            for i in np.unique(labels_cc3d[:]) :
                try :
                    htw_list.append(int(i))
                except :
                    pass
        
        elif np.isnan(df_emdat.loc[emdat_event,'End Day']) :
            day_beg_event = int(df_emdat.loc[emdat_event,'Start Day'])
            month_beg_event = int(df_emdat.loc[emdat_event,'Start Month'])
            month_end_event = int(df_emdat.loc[emdat_event,'End Month'])
            idx_beg = np.max([0, beg_month_only_idx_dict[month_beg_event] + day_beg_event-1 - flex_time_span])
            idx_end = end_month_only_idx_dict[month_end_event]+1
            labels_cc3d = labels_cc3d[idx_beg:idx_end,:,:]
            for i in np.unique(labels_cc3d[:]) :
                try :
                    htw_list.append(int(i))
                except :
                    pass
        else :
            day_beg_event = int(df_emdat.loc[emdat_event,'Start Day'])
            month_beg_event = int(df_emdat.loc[emdat_event,'Start Month'])
            day_end_event = int(df_emdat.loc[emdat_event,'End Day'])
            month_end_event = int(df_emdat.loc[emdat_event,'End Month'])
            idx_beg = np.max([0, beg_month_only_idx_dict[month_beg_event] + day_beg_event-1 - flex_time_span])
            idx_end = np.min([92,beg_month_only_idx_dict[month_end_event] + day_end_event + flex_time_span])
            labels_cc3d = labels_cc3d[idx_beg:idx_end,:,:]
            for i in np.unique(labels_cc3d[:]) :
                try :
                    htw_list.append(int(i))
                except :
                    pass
        if htw_list==[] :
            undetected_heatwaves.append(df_emdat.loc[emdat_event,'Dis No'])
        else :
            detected_heatwaves.append(str(df_emdat.loc[emdat_event,'Dis No'])+" "+str(htw_list))
            
output_dir = os.path.join("Output","ERA5",the_variable,the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days")
pathlib.Path(output_dir).mkdir(parents=True,exist_ok=True)
with open(os.path.join(output_dir,"emdat_undetected_heatwaves_ERA5_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days.txt"), 'w') as output :
    for row in undetected_heatwaves:
        output.write(str(row) + '\n')
        
with open(os.path.join(output_dir,"emdat_detected_heatwaves_ERA5_"+the_variable+"_"+str(year_beg)+"_"+str(year_end)+"_"+str(threshold_value)+"th_threshold_"+str(nb_days)+"days.txt"), 'w') as output :
    for row in detected_heatwaves:
        output.write(str(row) + '\n')

f.close()
f_mask.close()