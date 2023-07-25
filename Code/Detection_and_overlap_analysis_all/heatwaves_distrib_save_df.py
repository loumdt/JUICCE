"""This script draws the distribution of the heatwaves found in ERA5 temperature data and the impact of those also found in EM-DAT, regarding several meteo and impact criteria"""
#%% IMPORT MODULES
#from scipy.linalg.special_matrices import companion 
import netCDF4 as nc
import numpy as np
import pandas as pd
from tqdm import tqdm
import numpy.ma as ma
import ast
import sys,os
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
#print input argument for feedback
print('the_variable :',the_variable)
print('year_beg :',year_beg)
print('year_end :',year_end)
print('threshold_value :',threshold_value)
print('nb_days :',nb_days)
#%% LOAD FILES
f_label = nc.Dataset(os.path.join(datadir,"ERA5","t2m","Detection_Canicule",f"detected_heatwaves_{the_variable}_anomaly_JJA_{year_beg}_{year_end}_threshold_{threshold_value}th_{nb_days}days.nc"))
time_in = f_label.variables['time'][:]
lat_in = f_label.variables['lat'][:]
lon_in = f_label.variables['lon'][:]

f_land_sea_mask = nc.Dataset(os.path.join(datadir,"ERA5","Mask","Mask_Europe_land_only_ERA5_0.25deg.nc"),mode='r')
land_sea_mask = f_land_sea_mask.variables['mask'][:]

f_temp = nc.Dataset(os.path.join(datadir,"ERA5","t2m","Detection_Canicule",f"potential_heatwaves_{the_variable}_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th.nc"))

f_Russo = nc.Dataset(os.path.join(datadir,"ERA5","t2m","Detection_Canicule",f"Russo_index_{the_variable}_anomaly_JJA_{year_beg}_{year_end}_threshold_{threshold_value}th.nc"))#path to the output netCDF file

f_gdp_cap = nc.Dataset(os.path.join(datadir,"ERA5","Socio_eco_maps","GDP_cap_ERA5_Europe_0.25deg.nc"))#path to the output netCDF file
#%%
f_pop_GHS_1975 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_1975_era5_grid_Europe.nc"))
f_pop_GHS_1980 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_1980_era5_grid_Europe.nc"))
f_pop_GHS_1985 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_1985_era5_grid_Europe.nc"))
f_pop_GHS_1990 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_1990_era5_grid_Europe.nc"))
f_pop_GHS_1995 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_1995_era5_grid_Europe.nc"))
f_pop_GHS_2000 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_2000_era5_grid_Europe.nc"))
f_pop_GHS_2005 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_2005_era5_grid_Europe.nc"))
f_pop_GHS_2010 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_2010_era5_grid_Europe.nc"))
f_pop_GHS_2015 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_2015_era5_grid_Europe.nc"))
f_pop_GHS_2020 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP","GHS_POP_2020_era5_grid_Europe.nc"))

#%% LOAD POPULATION FILES
#Redirect the different years towards the correct (nearest in time) population data file :
htw_year_to_pop_dict = {}
for year in range(1950,1978):
    htw_year_to_pop_dict[year]=f_pop_GHS_1975
for year in range(1978,1983):
    htw_year_to_pop_dict[year]=f_pop_GHS_1980
for year in range(1983,1988):
    htw_year_to_pop_dict[year]=f_pop_GHS_1985
for year in range(1988,1993):
    htw_year_to_pop_dict[year]=f_pop_GHS_1990
for year in range(1993,1998):
    htw_year_to_pop_dict[year]=f_pop_GHS_1995
for year in range(1998,2003):
    htw_year_to_pop_dict[year]=f_pop_GHS_2000
for year in range(2003,2008):
    htw_year_to_pop_dict[year]=f_pop_GHS_2005
for year in range(2008,2013):
    htw_year_to_pop_dict[year]=f_pop_GHS_2010
for year in range(2013,2018):
    htw_year_to_pop_dict[year]=f_pop_GHS_2015
for year in range(2018,2023) :
    htw_year_to_pop_dict[year]=f_pop_GHS_2020
#%%
df_htw = pd.read_excel(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days",f"df_htw_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days.xlsx"),header=0,index_col=0)
df_emdat_not_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0) #heatwaves are not merged by event, they are dissociated when affecting several countries
df_emdat_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves_merged.xlsx"),header=0, index_col=0) #heatwaves are merged by event number Dis No
#%% 
# #Read txt file containing detected heatwaves to create detected heatwaves list
with open(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days",f"emdat_detected_heatwaves_ERA5_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days.txt"),'r') as f_txt:
    detected_htw_list = f_txt.readlines()
f_txt.close()
# #Remove '\n' from strings
emdat_to_era5_id_dico_not_merged = {}
emdat_heatwaves_list = []
for i in range(len(detected_htw_list)) :
    emdat_to_era5_id_dico_not_merged[detected_htw_list[i][:13]] = ast.literal_eval(detected_htw_list[i][14:-1])#Remove '\n' from strings
    emdat_heatwaves_list = np.append(emdat_heatwaves_list,emdat_to_era5_id_dico_not_merged[detected_htw_list[i][:13]])
emdat_heatwaves_list = [int(i) for i in np.unique(emdat_heatwaves_list)]
#%% #Need to consider the possibility that several EM-DAT heatwaves are not distinguishable in ERA5
htw_multi = []
inverted_emdat_to_era5_id_dico_not_merged = {}
for htw,v in emdat_to_era5_id_dico_not_merged.items() :
    for val in v :
        try : 
            inverted_emdat_to_era5_id_dico_not_merged[val].append(htw[:9])
        except :
            inverted_emdat_to_era5_id_dico_not_merged[val]=[htw[:9]]
for k,v in inverted_emdat_to_era5_id_dico_not_merged.items():
    inverted_emdat_to_era5_id_dico_not_merged[k]=[s for s in np.unique(inverted_emdat_to_era5_id_dico_not_merged[k])]
    if len(inverted_emdat_to_era5_id_dico_not_merged[k])>1:
        htw_multi.append(k)
#--------------------------
#%% #For all EM-DAT merged event, record every associated EM-DAT not merged heatwave (dico_merged_htw) that are detected in ERA5, and record every associated ERA5 heatwave (dico_merged_label)
emdat_to_era5_id_dico_merged_htw = {}
emdat_to_era5_id_dico_merged_label = {}
for i in df_emdat_merged.index.values[:]:
    dis_no = str(df_emdat_merged.loc[i,'disasterno'])
    for k,v in emdat_to_era5_id_dico_not_merged.items():
        if dis_no in k :
            try :
                emdat_to_era5_id_dico_merged_htw[dis_no].append(k)
                emdat_to_era5_id_dico_merged_label[dis_no] = np.append(emdat_to_era5_id_dico_merged_label[dis_no],v)
            except :
                emdat_to_era5_id_dico_merged_htw[dis_no]=[k]
                emdat_to_era5_id_dico_merged_label[dis_no]=[v]
not_computed_htw = []
links_not_computed_dict = {}
for k,v in emdat_to_era5_id_dico_merged_label.items():
    emdat_to_era5_id_dico_merged_label[k]=[int(i) for i in np.unique(v)]
    if len(emdat_to_era5_id_dico_merged_label[k])>1:
        not_computed_htw = np.append(not_computed_htw,emdat_to_era5_id_dico_merged_label[k][1:])
        links_not_computed_dict[emdat_to_era5_id_dico_merged_label[k][0]]=[int(i) for i in emdat_to_era5_id_dico_merged_label[k][1:]]
not_computed_htw = [int(i) for i in not_computed_htw]
careful_htw = list(links_not_computed_dict.keys())

#%%
htw_criteria = ['Global_mean','Spatial_extent','Duration','Max','Max_spatial','Temp_sum','Pseudo_Russo','Total_affected_pop','Global_mean_pop','Duration_pop','Max_pop','Max_spatial_pop',
'Spatial_extent_pop','Temp_sum_pop','Pseudo_Russo_pop','Temp_sum_pop_NL','Pseudo_Russo_pop_NL','Multi_index_temp','Multi_index_Russo','Multi_index_temp_NL','Multi_index_Russo_NL','Mean_log_GDP',
'Mean_exp_GDP','Mean_inv_GDP','GDP_inv_log_temp_sum','GDP_inv_log_temp_mean']
#htw_criteria = ['Multi_index_temp']
threshold_NL = 1000
#%% 
coeff_PL = 1000
#%%
#Do not forget to change this boolean if necessary
count_all_impacts = True
print("count_all_impacts :",count_all_impacts)

#%%
df_htw['Computed_heatwave'] = False
df_htw['Extreme_heatwave'] = False
df_htw['Total_Deaths'] = None
df_htw['Total_Affected'] = None
df_htw['Material_Damages'] = None
df_htw['Impact_sum'] = None

for htw_charac in htw_criteria:
    df_htw[htw_charac] = None

res_lat = np.abs(np.mean(lat_in[1:]-lat_in[:-1])) #latitude resolution in degrees
res_lon = np.abs(np.mean(lon_in[1:]-lon_in[:-1])) #longitude resolution in degrees

cell_area = np.array([6371**2*np.cos(np.pi*lat_in/180)*res_lat*np.pi/180*res_lon*np.pi/180]*len(lon_in)).T # the area in km² of each cell, depending on the latitude
cell_area_3d = np.array([cell_area]*92)
cell_area_3d_ratio = cell_area_3d/(6371**2*res_lat*np.pi/180*res_lon*np.pi/180) #each cell area as a percentage of the maximum possible cell area (obtained with lat=0°) in order to correctly weigh each cell when carrying out average

gdp_time = f_gdp_cap.variables['time'][:]

for htw_id in tqdm(df_htw.index.values[:]) : #list of heatwaves detected in ERA5
    if htw_id not in not_computed_htw :
        df_htw.loc[htw_id,'Computed_heatwave']=True
        new_computed_htw = [htw_id]
        if htw_id in careful_htw : #create list of all heatwaves that are not distinguishable from the htw_id heatwave (either because of EM-DAT overlap or ERA5 overlap)
            old_computed_htw = []
            while new_computed_htw!=old_computed_htw :
                old_computed_htw = new_computed_htw
                for i in old_computed_htw :
                    if i in links_not_computed_dict.keys() :
                        new_computed_htw = np.append(new_computed_htw,links_not_computed_dict[i])
                new_computed_htw = [int(j) for j in np.unique(new_computed_htw)]
        #Compute meteo metrics
        year = df_htw.loc[htw_id,'Year']
        data_label = f_label.variables['label'][(year-year_beg)*92:(year-year_beg+1)*92,:,:]
        vals = np.array(new_computed_htw)
        mask_htw = ~np.isin(data_label,vals)
        table_temp = f_temp.variables['t2m'][(year-year_beg)*92:(year-year_beg+1)*92,:,:]
        #table_temp = table_temp.data*(data_label == vals[:, None, None, None])[0].data
        table_temp = ma.masked_where(mask_htw+(land_sea_mask>0), table_temp)
        table_Russo = f_Russo.variables['Russo_index'][(year-year_beg)*92:(year-year_beg+1)*92,:,:]
        #table_Russo = table_Russo.data*(data_label == vals[:, None, None, None])[0].data
        table_Russo = ma.masked_where(mask_htw+(land_sea_mask>0), table_Russo)
        pop0 = htw_year_to_pop_dict[year].variables['Band1'][:] #Population density
        pop = ma.array([pop0]*np.shape(table_temp)[0])
        pop = ma.masked_where(mask_htw,pop) #population density set to zero for points that are not affected by the considered heatwave(s)
        pop_unique = pop0*(np.nanmean(pop,axis=0)>0) #population density set to zero for points that are not affected by the considered heatwave(s) and "flattened" into a 2D array
        area_unique = cell_area*(pop_unique>0) #cell area set to zero for points that are not affected by the considered heatwave(s)
        duration = len(np.unique(np.where((data_label == vals[:, None, None, None])[0].data)[0]))
        affected_pop = np.nansum(pop_unique*cell_area)
        gdp_cap_map = f_gdp_cap.variables['gdp_cap'][np.argwhere(np.array(gdp_time)==year)[0][0],:,:]
        gdp_cap_map = ma.masked_where(np.nanmean(pop,axis=0)==0,gdp_cap_map)
        gdp_cap_map = ma.masked_where(gdp_cap_map==0,gdp_cap_map)
        #mean temperature anomaly over every point recorded as a part of the heatwave
        masked_temp = ma.masked_where(table_temp==0,table_temp)
        df_htw.loc[htw_id,'Global_mean'] = np.nanmean(table_temp*cell_area_3d_ratio)
        df_htw.loc[htw_id,'Global_mean_pop'] = df_htw.loc[htw_id,'Global_mean']*affected_pop
        #area of the considered heatwave in km²
        df_htw.loc[htw_id,'Spatial_extent'] = np.nansum(area_unique)
        df_htw.loc[htw_id,'Spatial_extent_pop'] = df_htw.loc[htw_id,'Spatial_extent']*affected_pop
        #duration in days
        df_htw.loc[htw_id,'Duration'] = duration
        df_htw.loc[htw_id,'Duration_pop'] = df_htw.loc[htw_id,'Duration']*affected_pop
        #Sum of the normalized cell area multiplied by the temperature anomaly of every point recorded as a part of the heatwave
        df_htw.loc[htw_id,'Temp_sum'] = np.nansum(table_temp*cell_area_3d_ratio)
        df_htw.loc[htw_id,'Temp_sum_pop'] = df_htw.loc[htw_id,'Temp_sum']*affected_pop
        #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
        df_htw.loc[htw_id,'Pseudo_Russo'] = np.nansum(cell_area_3d_ratio*table_Russo)
        df_htw.loc[htw_id,'Pseudo_Russo_pop'] = df_htw.loc[htw_id,'Pseudo_Russo']*affected_pop
        #maximum of the temperature anomaly of the heatwave, multiplied by the cumulative normalized area
        df_htw.loc[htw_id,'Max_spatial'] = np.max(table_temp)*np.nansum(area_unique) 
        df_htw.loc[htw_id,'Max_spatial_pop'] = df_htw.loc[htw_id,'Max_spatial']*affected_pop
        #maximum temperature anomaly of the heatwave
        df_htw.loc[htw_id,'Max'] = np.max(table_temp)
        df_htw.loc[htw_id,'Max_pop'] = df_htw.loc[htw_id,'Max']*affected_pop
        #Total affected population
        df_htw.loc[htw_id,'Total_affected_pop'] = affected_pop
        #
        df_htw.loc[htw_id,'Temp_sum_pop_NL'] = np.nansum(cell_area_3d_ratio*table_temp*coeff_PL*(pop_unique>threshold_NL))*np.nansum(pop_unique*cell_area*(pop_unique>threshold_NL))+np.nansum(cell_area_3d_ratio*table_temp*(pop_unique<=threshold_NL))*np.nansum(pop_unique*cell_area*(pop_unique<=threshold_NL))
        #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
        df_htw.loc[htw_id,'Pseudo_Russo_pop_NL'] = np.nansum(cell_area_3d_ratio*table_Russo*coeff_PL*(pop_unique>threshold_NL))*np.nansum(pop_unique*cell_area*(pop_unique>threshold_NL))+np.nansum(cell_area_3d_ratio*table_Russo*(pop_unique<=threshold_NL))*np.nansum(pop_unique*cell_area*(pop_unique<=threshold_NL))
        #
        df_htw.loc[htw_id,'Multi_index_Russo'] =  np.nansum((cell_area_3d_ratio*table_Russo*pop_unique)) #np.nansum((cell_area**2*table_Russo*pop_unique))
        #
        df_htw.loc[htw_id,'Multi_index_temp'] =  np.nansum((cell_area_3d_ratio*table_temp*pop_unique)) #np.nansum((cell_area**2*table_temp*pop_unique))
        #
        df_htw.loc[htw_id,'Multi_index_Russo_NL'] = np.nansum((cell_area_3d_ratio*table_Russo*pop_unique*coeff_PL*(pop_unique>threshold_NL))) + np.nansum((cell_area_3d_ratio*table_Russo*pop_unique*(pop_unique<=threshold_NL))) #np.nansum((cell_area**2*table_Russo*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*table_Russo*pop_unique*(pop_unique<=threshold_NL)))
        #
        df_htw.loc[htw_id,'Multi_index_temp_NL'] = np.nansum((cell_area_3d_ratio*table_temp*pop_unique*coeff_PL*(pop_unique>threshold_NL))) + np.nansum((cell_area_3d_ratio*table_temp*pop_unique*(pop_unique<=threshold_NL))) # np.nansum((cell_area**2*temp*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*temp*pop_unique*(pop_unique<=threshold_NL)))
        #
        df_htw.loc[htw_id,'Mean_log_GDP'] = -np.log10(np.nanmean(gdp_cap_map*pop0))
        
        df_htw.loc[htw_id,'Mean_exp_GDP'] = np.exp(-np.nanmean(gdp_cap_map*pop0))
        
        df_htw.loc[htw_id,'Mean_inv_GDP'] = 1/(np.nanmean(gdp_cap_map*pop0))
        
        df_htw.loc[htw_id,'GDP_inv_log_temp_sum'] = (np.nansum((1/np.log10(gdp_cap_map))*table_temp*cell_area_3d_ratio))
        
        df_htw.loc[htw_id,'GDP_inv_log_temp_mean'] = (np.nanmean((1/np.log10(gdp_cap_map))*pop0*table_temp*cell_area_3d_ratio))
            #elif htw_charac == 'Multi_index_temp_NL' :
            #    max_area = np.max(cell_area)
            #    cell_area = cell_area/max_area
            #    temp = np.nansum(temp,axis=0)
            #    meteo_list=np.append(meteo_list,np.sum((cell_area**2*temp*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*temp*pop_unique*(pop_unique<=threshold_NL))))
#%%        
        if htw_id in emdat_heatwaves_list :
            df_htw.loc[htw_id,'Extreme_heatwave'] = True
            #Compute impact metrics
            disasterno_list = []
            for i in new_computed_htw :
                if count_all_impacts : #count all affected countries according to EM-DAT
                    dis_no_name = 'disasterno'
                    disasterno_list = np.append(disasterno_list,inverted_emdat_to_era5_id_dico_not_merged[i])
                else : #count only visibly affected countries according to ERA5
                    dis_no_name = 'Dis No'
                    disasterno_list = np.append(disasterno_list,[emdat_to_era5_id_dico_merged_htw[k] for k in inverted_emdat_to_era5_id_dico_not_merged[i]])
            disasterno_list = [st for st in np.unique(disasterno_list)]
            df_impact = df_emdat_not_merged[df_emdat_not_merged[dis_no_name].isin(disasterno_list)]
            df_impact = df_impact.fillna(value=0)
            df_htw.loc[htw_id,'Total_Deaths'] = int(df_impact['Total Deaths'].sum())
            df_htw.loc[htw_id,'Total_Affected'] = int(df_impact['Total Affected'].sum())
            df_htw.loc[htw_id,'Material_Damages'] = (df_impact["Total Damages, Adjusted ('000 US$)"].sum())*1e3 #in 2022 US$
            df_htw.loc[htw_id,'Impact_sum'] = (int(df_htw.loc[htw_id,'Total_Deaths'])*(2.94e6*1.366/0.80645161)+ #2.94e6 US$ is Europe mean VSL according to WHO 2014, convert €2014 to US$2014 (*1.366),  then convert US$2014 to US$2022 (/0.806)
            int(df_htw.loc[htw_id,'Total_Affected'])*(97e3*1.366/0.80645161)+ #mean value of affected people, convert €2014 to US$2014 (*1.366),  then convert US$2014 to US$2022 (/0.806)
            (df_htw.loc[htw_id,'Material_Damages'])) #socio-economic calculation, in 2022 US$
#%%
#Save dataframe
df_htw.to_excel(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days",f"df_htw_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days"+"_count_all_impacts"*count_all_impacts+".xlsx"))
#%%
f_label.close()
f_Russo.close()
f_temp.close()
f_pop_GHS_1975.close()
f_pop_GHS_1980.close()
f_pop_GHS_1985.close()
f_pop_GHS_1990.close()
f_pop_GHS_1995.close()
f_pop_GHS_2000.close()
f_pop_GHS_2005.close()
f_pop_GHS_2010.close()
f_pop_GHS_2015.close()
f_pop_GHS_2020.close()