"""This script draws the distribution of the heatwaves found in E-OBS temperature data and the impact of those also found in EM-DAT, regarding several meteo and impact criteria"""
#%% IMPORT MODULES
import time

#from scipy.linalg.special_matrices import companion 
start_time=time.time()

import netCDF4 as nc
import numpy as np
import pandas as pd
from tqdm import tqdm
import numpy.ma as ma
import sys

#%% CHOOSE VARIABLE
the_variable = str(sys.argv[1])
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)

#%% LOAD FILES
data = pd.read_excel("D:/Ubuntu/PFE/Data/EM-DAT/emdat_Europe_1950-2020_heatwaves_xlsx.xlsx")

nc_file = "D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_TWICE_"+the_variable+"_anomaly_threshold_95th_scan_size35_10.0%.nc" #netcdf file containing the heatwaves from E-OBS

f = nc.Dataset(nc_file,mode='r')
lon_in = f.variables['lon'][:]
lat_in = f.variables['lat'][:]

Russo_file = "D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/Russo_index_"+the_variable+"_summer_only_1950_2020.nc"
f_Russo = nc.Dataset(Russo_file,mode='r')

heatwaves_idx =   np.load("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_4days_"+the_variable+"_V3.npy",allow_pickle = True) #numpy file containing the days of the E-OBS heatwaves
heatwaves_idx_2 = np.load("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_2_4days_"+the_variable+"_V3.npy",allow_pickle = True) #numpy file containing the days of the E-OBS heatwaves
heatwaves_dates = np.load("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_dates_4days_"+the_variable+"_V3.npy",allow_pickle = True) #numpy file containing the dates of the E-OBS heatwaves

#--------------------------
#%% Define dictonaries to avoid an illegible code full of 'if'/'elif' :

htw_criteria = ['Global_mean','Spatial_extent','Duration','Max','Max_spatial','Temp_sum','Pseudo_Russo','Pop_unique','Global_mean_pop','Duration_pop','Max_pop','Max_spatial_pop',
'Spatial_extent_pop','Temp_sum_pop','Pseudo_Russo_pop','Temp_sum_pop_NL','Pseudo_Russo_pop_NL','Multi_index_temp','Multi_index_Russo','Multi_index_temp_NL','Multi_index_Russo_NL','extreme_bool','TotalDeaths','Impact_fct']
#htw_criteria = ['Multi_index_temp','extreme_bool','TotalDeaths','Impact_fct']
threshold_NL = 1000

stefanon_htw = np.array([],dtype=np.int32)
stefanon_htw_dico={}

htw_multi = {'tg' : [127,171], 'tx' : [120,169],'tn':[62]}
lines_htw_multi = {'tg':{127:[3,4],171:[14,15,16,17]},'tx':{120:[3,4],169:[14,15,16,17]},
'tn':{62:[3,4]}}
not_computed_htw_dict = {'tg' : [182,196,213,214,220,238,239,240,261,262,263,292,305],
'tx' : [172,192,204,206,207,213,231,232,249,250,259,276],
'tn':[107,119,120,139,151,153,154,208]} #heatwaves not directly computed
careful_htw_dict = {'tg' : [181,195,210,218,237,260,289,304], 
'tx' : [169,191,201,211,230,248,258,273],
'tn':[106,118,137,150,207]}
links_not_computed_dict = {'tg' : {181:[182],195:[196],210:[213,214],218:[220],237:[238,238,240],260:[261,262,263],289:[292],304:[305]},
'tx':{169:[172],191:[192],201:[204,206,207],211:[213],230:[231,232],248:[249,250],258:[259],273:[276]},
'tn':{106:[107],118:[119,120],137:[139],150:[151,153,154],207:[208]}}

#%% Define the list of heatwaves that are both present in EM-DAT and E-OBS
for i in data.index : 
    if data.loc[i,'Stefanon_detected_'+the_variable]=='Oui' :
        stefanon_htw = np.append(stefanon_htw,int(data.loc[i,'Detected_'+the_variable+'_file'][24:27])) #record the numbers of the heatwaves that were both found in E-OBS and EM-DAT
        if stefanon_htw[-1] not in htw_multi[the_variable] :
            stefanon_htw_dico[stefanon_htw[-1]] = i  #link between heatwave number and corresponding line in EM-DAT csv file

stefanon_htw = np.unique(stefanon_htw)
not_computed_htw = np.array(not_computed_htw_dict[the_variable],dtype=np.int32) #all of these heatwaves are merged with other ones, so we must not count them twice
careful_htw = np.array(careful_htw_dict[the_variable],dtype=np.int32) #the heatwaves with which the previous ones are merged
print(stefanon_htw)
#--------------------------
cell_area = np.array([6371**2*np.cos(np.pi*lat_in/180)*0.1*np.pi/180*0.1*np.pi/180]*705).T # the area in km² of each cell, depending on the latitude

computed_htw_list = np.array([],dtype=object)

for i in range(len(heatwaves_idx_2)) : #each heatwave has a number, ranging from 0 to 305 in my case
    if i not in not_computed_htw :
        computed_htw_list = np.append(computed_htw_list,str(i))
df = pd.DataFrame(np.ones((len(computed_htw_list),len(htw_criteria))), index = computed_htw_list, columns = htw_criteria)

#%% LOAD POPULATION FILES

pop_file_worldpop = "D:/Ubuntu/PFE/Data/Pop/WorldPop/World_pop_all_2000-2020_e-obs_grid.nc"
f_pop_WP = nc.Dataset(pop_file_worldpop,mode='r')
pop_file_GHS= "D:/Ubuntu/PFE/Data/Pop/GHS_pop/GHS_pop_all_e-obs_grid.nc"
f_pop_GHS = nc.Dataset(pop_file_GHS,mode='r')
pop_table = ma.array(np.zeros((23,len(lat_in),len(lon_in))))
pop_table[0:2,:,:] = ma.array([f_pop_GHS.variables['pop_density'][:]])
pop_table[2:,:,:] = ma.array([f_pop_WP.variables['pop_density'][:]])

coeff_PL = 1000

#%% COMPUTE DISTRIBUTIONS AND VISUALISE

for htw_charac in tqdm(htw_criteria[:-3]) :
    impact_list = np.array([]) #record the impact of the EM-DAT heatwaves
    death_list = np.array([]) #record the impact of the EM-DAT heatwaves
    meteo_list = np.array([]) #record the meteo criterion of the E-OBS heatwaves
    idx_scatt = np.array([],dtype=np.int32) #record the meteo criterion of the EM-DAT heatwaves
    nb_htw_scatt = np.array([],dtype=np.int32) #record the numbers of the EM-DAT heatwaves
    for i in range(len(heatwaves_idx_2)) : #each heatwave has a number, ranging from 0 to 305 in mean case, 0 to 304 in max case, 0 to 123 in min case
        #print(i)
        if the_variable == 'tg' : #link heatwaves to the correct year for pop grid
            if i<=110 : #Pop from year 1975 for years 1950-1982 (GHS_pop)
                pop0 = ma.array(pop_table[0,:,:])
            elif i<=148 : #Pop from year 1990 for years 1983-1995 (GHS_pop)
                pop0 = ma.array(pop_table[1,:,:])
            elif i<=176 : #Pop from year 2000 for years 1996-2000 (WorldPop)
                pop0 = ma.array(pop_table[2,:,:])
            elif i<= 184: #Pop from year 2001 for year 2001 (WorldPop)
                pop0 = ma.array(pop_table[3,:,:])
            elif i<=190 : #Pop from year 2002 for year 2002 (WorldPop)
                pop0 = ma.array(pop_table[4,:,:])
            elif i<= 196: #Pop from year 2003 for year 2003 (WorldPop)
                pop0 = ma.array(pop_table[5,:,:])
            elif i<= 201: #Pop from year 2004 for year 2004 (WorldPop)
                pop0 = ma.array(pop_table[6,:,:])
            elif i<= 208: #Pop from year 2005 for year 2005 (WorldPop)
                pop0 = ma.array(pop_table[7,:,:])
            elif i<=216 : #Pop from year 2006 for year 2006 (WorldPop)
                pop0 = ma.array(pop_table[8,:,:])
            elif i<=223 : #Pop from year 2007 for year 2007 (WorldPop)
                pop0 = ma.array(pop_table[9,:,:])
            elif i<=229 : #Pop from year 2008 for year 2008 (WorldPop)
                pop0 = ma.array(pop_table[10,:,:])
            elif i<=236 : #Pop from year 2009 for year 2009 (WorldPop)
                pop0 = ma.array(pop_table[11,:,:])
            elif i<=242 : #Pop from year 2010 for year 2010 (WorldPop)
                pop0 = ma.array(pop_table[12,:,:])
            elif i<=246 : #Pop from year 2011 for year 2011 (WorldPop)
                pop0 = ma.array(pop_table[13,:,:])
            elif i<=255 : #Pop from year 2012 for year 2012 (WorldPop)
                pop0 = ma.array(pop_table[14,:,:])
            elif i<=264 : #Pop from year 2013 for year 2013 (WorldPop)
                pop0 = ma.array(pop_table[15,:,:])
            elif i<=269 : #Pop from year 2014 for year 2014 (WorldPop)
                pop0 = ma.array(pop_table[16,:,:])
            elif i<=276 : #Pop from year 2015 for year 2015 (WorldPop)
                pop0 = ma.array(pop_table[17,:,:])
            elif i<=281 : #Pop from year 2016 for year 2016 (WorldPop)
                pop0 = ma.array(pop_table[18,:,:])
            elif i<=287 : #Pop from year 2017 for year 2017 (WorldPop)
                pop0 = ma.array(pop_table[19,:,:])
            elif i<=292 : #Pop from year 2018 for year 2018 (WorldPop)
                pop0 = ma.array(pop_table[20,:,:])
            elif i<=300 : #Pop from year 2019 for year 2019 (WorldPop)
                pop0 = ma.array(pop_table[21,:,:])
            else : #Pop from year 2020 for year 2020 (WorldPop)
                pop0 = ma.array(pop_table[22,:,:])
        elif the_variable == 'tx' : 
            if i<=105 : #Pop from year 1975 for years 1950-1982 (GHS_pop)
                pop0 = ma.array(pop_table[0,:,:])
            elif i<=144 : #Pop from year 1990 for years 1983-1995 (GHS_pop)
                pop0 = ma.array(pop_table[1,:,:])
            elif i<=173 : #Pop from year 2000 for years 1996-2000 (WorldPop)
                pop0 = ma.array(pop_table[2,:,:])
            elif i<= 180: #Pop from year 2001 for year 2001 (WorldPop)
                pop0 = ma.array(pop_table[3,:,:])
            elif i<=186 : #Pop from year 2002 for year 2002 (WorldPop)
                pop0 = ma.array(pop_table[4,:,:])
            elif i<= 192: #Pop from year 2003 for year 2003 (WorldPop)
                pop0 = ma.array(pop_table[5,:,:])
            elif i<= 196: #Pop from year 2004 for year 2004 (WorldPop)
                pop0 = ma.array(pop_table[6,:,:])
            elif i<= 199: #Pop from year 2005 for year 2005 (WorldPop)
                pop0 = ma.array(pop_table[7,:,:])
            elif i<=209 : #Pop from year 2006 for year 2006 (WorldPop)
                pop0 = ma.array(pop_table[8,:,:])
            elif i<=215 : #Pop from year 2007 for year 2007 (WorldPop)
                pop0 = ma.array(pop_table[9,:,:])
            elif i<=221 : #Pop from year 2008 for year 2008 (WorldPop)
                pop0 = ma.array(pop_table[10,:,:])
            elif i<=228 : #Pop from year 2009 for year 2009 (WorldPop)
                pop0 = ma.array(pop_table[11,:,:])
            elif i<=234 : #Pop from year 2010 for year 2010 (WorldPop)
                pop0 = ma.array(pop_table[12,:,:])
            elif i<=237 : #Pop from year 2011 for year 2011 (WorldPop)
                pop0 = ma.array(pop_table[13,:,:])
            elif i<=245 : #Pop from year 2012 for year 2012 (WorldPop)
                pop0 = ma.array(pop_table[14,:,:])
            elif i<=250 : #Pop from year 2013 for year 2013 (WorldPop)
                pop0 = ma.array(pop_table[15,:,:])
            elif i<=254 : #Pop from year 2014 for year 2014 (WorldPop)
                pop0 = ma.array(pop_table[16,:,:])
            elif i<=261 : #Pop from year 2015 for year 2015 (WorldPop)
                pop0 = ma.array(pop_table[17,:,:])
            elif i<=265 : #Pop from year 2016 for year 2016 (WorldPop)
                pop0 = ma.array(pop_table[18,:,:])
            elif i<=270 : #Pop from year 2017 for year 2017 (WorldPop)
                pop0 = ma.array(pop_table[19,:,:])
            elif i<=277 : #Pop from year 2018 for year 2018 (WorldPop)
                pop0 = ma.array(pop_table[20,:,:])
            elif i<=285 : #Pop from year 2019 for year 2019 (WorldPop)
                pop0 = ma.array(pop_table[21,:,:])
            else : #Pop from year 2020 for year 2020 (WorldPop)
                pop0 = ma.array(pop_table[22,:,:])
        elif the_variable == 'tn' :
            if i<=52 : #Pop from year 1975 for years 1950-1982 (GHS_pop)
                pop0 = ma.array(pop_table[0,:,:])
            elif i<=78 : #Pop from year 1990 for years 1983-1995 (GHS_pop)
                pop0 = ma.array(pop_table[1,:,:])
            elif i<=103 : #Pop from year 2000 for years 1996-2000 (WorldPop)
                pop0 = ma.array(pop_table[2,:,:])
            elif i<= 108: #Pop from year 2001 for year 2001 (WorldPop)
                pop0 = ma.array(pop_table[3,:,:])
            elif i<=113 : #Pop from year 2002 for year 2002 (WorldPop)
                pop0 = ma.array(pop_table[4,:,:])
            elif i<= 120: #Pop from year 2003 for year 2003 (WorldPop)
                pop0 = ma.array(pop_table[5,:,:])
            elif i<= 125: #Pop from year 2004 for year 2004 (WorldPop)
                pop0 = ma.array(pop_table[6,:,:])
            elif i<= 129: #Pop from year 2005 for year 2005 (WorldPop)
                pop0 = ma.array(pop_table[7,:,:])
            elif i<=135 : #Pop from year 2006 for year 2006 (WorldPop)
                pop0 = ma.array(pop_table[8,:,:])
            elif i<=142 : #Pop from year 2007 for year 2007 (WorldPop)
                pop0 = ma.array(pop_table[9,:,:])
            elif i<=145 : #Pop from year 2008 for year 2008 (WorldPop)
                pop0 = ma.array(pop_table[10,:,:])
            elif i<=149 : #Pop from year 2009 for year 2009 (WorldPop)
                pop0 = ma.array(pop_table[11,:,:])
            elif i<=155 : #Pop from year 2010 for year 2010 (WorldPop)
                pop0 = ma.array(pop_table[12,:,:])
            elif i<=160 : #Pop from year 2011 for year 2011 (WorldPop)
                pop0 = ma.array(pop_table[13,:,:])
            elif i<=167 : #Pop from year 2012 for year 2012 (WorldPop)
                pop0 = ma.array(pop_table[14,:,:])
            elif i<=172 : #Pop from year 2013 for year 2013 (WorldPop)
                pop0 = ma.array(pop_table[15,:,:])
            elif i<=178 : #Pop from year 2014 for year 2014 (WorldPop)
                pop0 = ma.array(pop_table[16,:,:])
            elif i<=186 : #Pop from year 2015 for year 2015 (WorldPop)
                pop0 = ma.array(pop_table[17,:,:])
            elif i<=192 : #Pop from year 2016 for year 2016 (WorldPop)
                pop0 = ma.array(pop_table[18,:,:])
            elif i<=197 : #Pop from year 2017 for year 2017 (WorldPop)
                pop0 = ma.array(pop_table[19,:,:])
            elif i<=203 : #Pop from year 2018 for year 2018 (WorldPop)
                pop0 = ma.array(pop_table[20,:,:])
            elif i<=210 : #Pop from year 2019 for year 2019 (WorldPop)
                pop0 = ma.array(pop_table[21,:,:])
            else : #Pop from year 2020 for year 2020 (WorldPop)
                pop0 = ma.array(pop_table[22,:,:])
        if i not in not_computed_htw and i not in careful_htw:
            temp = ma.array(f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:])
            temp = ma.masked_where(temp==0,temp) #mask where heatwave is not happening
            russo_idx_map = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:])
            cell_area_3d = np.array([cell_area]*np.shape(temp)[0])
            pop = ma.array([pop0]*np.shape(temp)[0])
            pop_unique = ma.masked_where(temp==0,pop)
            pop_unique = np.nanmean(pop_unique,axis=0)
            if htw_charac == 'Global_mean' : #mean temperature anomaly over every point recorded as a part of the heatwave
                max_area = np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list = np.append(meteo_list,np.mean(cell_area_3d*temp))
            elif htw_charac == 'Spatial_extent' : #area of the considered heatwave in km²
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.sum(area_unique))
            elif htw_charac == 'Duration' : #duration in days
                meteo_list = np.append(meteo_list,heatwaves_idx_2[i,1]) 
            elif htw_charac == 'Temp_sum' : #Sum of the normalized cell area multiplied by the temperature anomaly of every point recorded as a part of the heatwave
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp))
            elif htw_charac == 'Pseudo_Russo' : #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list=np.append(meteo_list,np.sum(cell_area_3d*russo_idx_map*(temp>0)))
            elif htw_charac == 'Max_spatial' : #maximum of the temperature anomaly of the heatwave, multiplied by the cumulative normalized area
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.max(temp)*np.sum(area_unique)) 
            elif htw_charac == 'Max' : #maximum temperature anomaly of the heatwave
                meteo_list = np.append(meteo_list, np.max(temp))
            elif htw_charac == 'Global_mean_pop' :
                max_area = np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list = np.append(meteo_list,np.mean(cell_area_3d*temp)*np.mean(cell_area*pop_unique))
            elif htw_charac == 'Spatial_extent_pop' : #area of the considered heatwave in km²
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.sum(area_unique)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Duration_pop' : #duration in days
                meteo_list = np.append(meteo_list,heatwaves_idx_2[i,1]*np.mean(pop_unique*cell_area)) 
            elif htw_charac == 'Temp_sum_pop' : #Sum of the normalized cell area multiplied by the temperature anomaly of every point recorded as a part of the heatwave
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Pseudo_Russo_pop' : #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list=np.append(meteo_list,np.sum(cell_area_3d*russo_idx_map*(temp>0))*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Max_pop' : #maximum temperature anomaly of the heatwave
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.max(temp)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Max_spatial_pop' : #maximum of the temperature anomaly of the heatwave, multiplied by the cumulative normalized area
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.max(temp)*np.sum(area_unique)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Pop_unique' : #maximum temperature anomaly of the heatwave
                meteo_list = np.append(meteo_list, np.sum(pop_unique*cell_area))
            elif htw_charac == 'Temp_sum_pop_NL' :
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp*coeff_PL*(pop_unique>threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique>threshold_NL))+np.sum(cell_area_3d*temp*(pop_unique<=threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique<=threshold_NL)))
            elif htw_charac == 'Pseudo_Russo_pop_NL' : #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                cell_area_3d = np.array([cell_area]*np.shape(russo_idx_map)[0])
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list=np.append(meteo_list,np.sum(cell_area_3d*russo_idx_map*coeff_PL*(pop_unique>threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique>threshold_NL))+np.sum(cell_area_3d*russo_idx_map*(temp>0)*(pop_unique<=threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique<=threshold_NL)))
            elif htw_charac == 'Multi_index_Russo' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                russo_idx_map = np.nansum(russo_idx_map,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*russo_idx_map*pop_unique)))
            elif htw_charac == 'Multi_index_temp' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                temp = np.nansum(temp,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*temp*pop_unique)))
            elif htw_charac == 'Multi_index_Russo_NL' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                russo_idx_map = np.nansum(russo_idx_map,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*russo_idx_map*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*russo_idx_map*pop_unique*(pop_unique<=threshold_NL))))
            elif htw_charac == 'Multi_index_temp_NL' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                temp = np.nansum(temp,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*temp*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*temp*pop_unique*(pop_unique<=threshold_NL))))
        
        elif i in careful_htw :
            htws_concat = links_not_computed_dict[the_variable][i]
            if len(htws_concat) == 1 : # two heatwaves to merge
                temp1 = ma.array(f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:])
                temp2 = ma.array(f.variables['temp'][heatwaves_idx_2[htws_concat[0],0]:heatwaves_idx_2[htws_concat[0],0]+heatwaves_idx_2[htws_concat[0],1],:,:])
                
                temp = ma.concatenate((temp1,temp2),axis=0)
                del temp1
                del temp2
                temp = ma.masked_where(temp==0,temp)

                russo_idx_map1 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:])
                russo_idx_map2 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[htws_concat[0],0]:heatwaves_idx[htws_concat[0],0]+heatwaves_idx_2[htws_concat[0],1],:,:])

                russo_idx_map = ma.concatenate((russo_idx_map1,russo_idx_map2),axis=0)
                del russo_idx_map1
                del russo_idx_map2
                russo_idx_map = ma.masked_where(temp==0,russo_idx_map)
            elif len(htws_concat) == 2 : #three heatwaves to merge
                temp1 = ma.array(f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:])
                temp2 = ma.array(f.variables['temp'][heatwaves_idx_2[htws_concat[0],0]:heatwaves_idx_2[htws_concat[0],0]+heatwaves_idx_2[htws_concat[0],1],:,:])
                temp3 = ma.array(f.variables['temp'][heatwaves_idx_2[htws_concat[1],0]:heatwaves_idx_2[htws_concat[1],0]+heatwaves_idx_2[htws_concat[1],1],:,:])

                temp = ma.concatenate((temp1,temp2,temp3),axis=0)

                del temp1
                del temp2
                del temp3
                temp = ma.masked_where(temp==0,temp)

                russo_idx_map1 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:])
                russo_idx_map2 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[htws_concat[0],0]:heatwaves_idx[htws_concat[0],0]+heatwaves_idx_2[htws_concat[0],1],:,:])
                russo_idx_map3 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[htws_concat[1],0]:heatwaves_idx[htws_concat[1],0]+heatwaves_idx_2[htws_concat[1],1],:,:])

                russo_idx_map = ma.concatenate((russo_idx_map1,russo_idx_map2,russo_idx_map3),axis=0)
                del russo_idx_map1
                del russo_idx_map2
                del russo_idx_map3
                russo_idx_map = ma.masked_where(temp==0,russo_idx_map)
            elif len(htws_concat) == 3 : #three heatwaves to merge
                temp1 = ma.array(f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:])
                temp2 = ma.array(f.variables['temp'][heatwaves_idx_2[htws_concat[0],0]:heatwaves_idx_2[htws_concat[0],0]+heatwaves_idx_2[htws_concat[0],1],:,:])
                temp3 = ma.array(f.variables['temp'][heatwaves_idx_2[htws_concat[1],0]:heatwaves_idx_2[htws_concat[1],0]+heatwaves_idx_2[htws_concat[1],1],:,:])
                temp4 = ma.array(f.variables['temp'][heatwaves_idx_2[htws_concat[2],0]:heatwaves_idx_2[htws_concat[2],0]+heatwaves_idx_2[htws_concat[2],1],:,:])

                temp = ma.concatenate((temp1,temp2,temp3,temp4),axis=0)

                del temp1
                del temp2
                del temp3
                del temp4
                temp = ma.masked_where(temp==0,temp)

                russo_idx_map1 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:])
                russo_idx_map2 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[htws_concat[0],0]:heatwaves_idx[htws_concat[0],0]+heatwaves_idx_2[htws_concat[0],1],:,:])
                russo_idx_map3 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[htws_concat[1],0]:heatwaves_idx[htws_concat[1],0]+heatwaves_idx_2[htws_concat[1],1],:,:])
                russo_idx_map4 = ma.array(f_Russo.variables['Russo_index'][heatwaves_idx[htws_concat[2],0]:heatwaves_idx[htws_concat[2],0]+heatwaves_idx_2[htws_concat[2],1],:,:])

                russo_idx_map = ma.concatenate((russo_idx_map1,russo_idx_map2,russo_idx_map3,russo_idx_map4),axis=0)
                del russo_idx_map1
                del russo_idx_map2
                del russo_idx_map3
                del russo_idx_map4
                russo_idx_map = ma.masked_where(temp==0,russo_idx_map)

            pop = ma.array([pop0]*np.shape(temp)[0])
            pop_unique = ma.masked_where(temp==0,pop)
            pop_unique = np.nanmean(pop_unique,axis=0)
            cell_area_3d = np.array([cell_area]*np.shape(temp)[0])
            if htw_charac == 'Global_mean' : #mean temperature anomaly over every point recorded as a part of the heatwave
                max_area = np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list = np.append(meteo_list,np.mean(cell_area_3d*temp))
            elif htw_charac == 'Spatial_extent' : #area of the considered heatwave in km²
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.sum(area_unique))
            elif htw_charac == 'Duration' : #duration in days
                duration = 0
                for htw in [i,*htws_concat] :
                    duration+=heatwaves_idx_2[htw,1]
                meteo_list = np.append(meteo_list,duration)
            elif htw_charac == 'Temp_sum' : #Sum of the normalized cell area multiplied by the temperature anomaly of every point recorded as a part of the heatwave
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp))
            elif htw_charac == 'Pseudo_Russo' : #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                cell_area_3d = np.array([cell_area]*np.shape(russo_idx_map)[0])
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list=np.append(meteo_list,np.sum(cell_area_3d*russo_idx_map*(temp>0)))
            elif htw_charac == 'Max_spatial' : #maximum of the temperature anomaly of the heatwave, multiplied by the cumulative normalized area
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.max(temp)*np.sum(area_unique))
            elif htw_charac == 'Max' : #maximum temperature anomaly of the heatwave
                meteo_list = np.append(meteo_list, np.max(temp))
            elif htw_charac == 'Global_mean_pop' :
                max_area = np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list = np.append(meteo_list,np.mean(cell_area_3d*temp)*np.sum(cell_area*pop_unique))
            elif htw_charac == 'Spatial_extent_pop' : #area of the considered heatwave in km²
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.sum(area_unique)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Duration_pop' : #duration in days
                meteo_list = np.append(meteo_list,heatwaves_idx_2[i,1]*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Temp_sum_pop' : #Sum of the normalized cell area multiplied by the temperature anomaly of every point recorded as a part of the heatwave
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp)*np.sum(pop_unique*cell_area)) 
            elif htw_charac == 'Pseudo_Russo_pop' : #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                cell_area_3d = np.array([cell_area]*np.shape(russo_idx_map)[0])
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list=np.append(meteo_list,np.sum(cell_area_3d*russo_idx_map*(temp>0))*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Max_pop' : #maximum temperature anomaly of the heatwave
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.max(temp)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Max_spatial_pop' : #maximum of the temperature anomaly of the heatwave, multiplied by the cumulative normalized area
                area_unique = ma.masked_where(temp==0,cell_area_3d)
                area_unique = np.nanmean(area_unique,axis=0)
                meteo_list = np.append(meteo_list, np.max(temp)*np.sum(area_unique)*np.sum(pop_unique*cell_area))
            elif htw_charac == 'Pop_unique' : #maximum temperature anomaly of the heatwave
                meteo_list = np.append(meteo_list, np.sum(pop_unique*cell_area))
            elif htw_charac == 'Temp_sum_pop_NL' :
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area #area of each cell in km², normalized by the area of the largest cell of the E-OBS grid
                meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp*coeff_PL*(pop_unique>threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique>threshold_NL))+np.sum(cell_area_3d*temp*(pop_unique<=threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique<=threshold_NL)))
            elif htw_charac == 'Pseudo_Russo_pop_NL' : #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                cell_area_3d = np.array([cell_area]*np.shape(russo_idx_map)[0])
                max_area=np.max(cell_area)*np.ones(np.shape(cell_area_3d))
                cell_area_3d=cell_area_3d/max_area
                meteo_list=np.append(meteo_list,np.sum(cell_area_3d*russo_idx_map*coeff_PL*(pop_unique>threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique>threshold_NL))+np.sum(cell_area_3d*russo_idx_map*(temp>0)*(pop_unique<=threshold_NL))*np.sum(pop_unique*cell_area*(pop_unique<=threshold_NL)))
            elif htw_charac == 'Multi_index_Russo' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                russo_idx_map = np.nansum(russo_idx_map,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*russo_idx_map*pop_unique)))
            elif htw_charac == 'Multi_index_temp' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                temp = np.nansum(temp,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*temp*pop_unique)))
            elif htw_charac == 'Multi_index_Russo_NL' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                russo_idx_map = np.nansum(russo_idx_map,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*russo_idx_map*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*russo_idx_map*pop_unique*(pop_unique<=threshold_NL))))
            elif htw_charac == 'Multi_index_temp_NL' :
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                temp = np.nansum(temp,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*temp*pop_unique*coeff_PL*(pop_unique>threshold_NL)) + (cell_area**2*temp*pop_unique*(pop_unique<=threshold_NL))))

        if i in stefanon_htw and i not in not_computed_htw and i not in htw_multi[the_variable] :
            death_list = np.append(death_list, int(data.loc[stefanon_htw_dico[i],'TotalDeaths'])) #find selected impact in the csv file
            #Impact_fct_1 = Total_Damages_1000_USD + TotalDeaths*3.8e6 USD + TotalAffected * 200k US$
            impact_list = np.append(impact_list, int(data.loc[stefanon_htw_dico[i],'TotalDeaths'])*(2.94e3/0.9259898057) + #3.8 French VSL, 2.94 Europe mean VSL according to WHO 2014
            int(data.loc[stefanon_htw_dico[i],'TotalAffected'])*(97/0.9259898057) + 
            int(data.loc[stefanon_htw_dico[i],'Total_Damages_1000_USD'])/float(data.loc[stefanon_htw_dico[i],'CPI'])) #find selected impact in the csv file
            idx_scatt = np.append(idx_scatt,meteo_list[-1]) 
            nb_htw_scatt = np.append(nb_htw_scatt,i)
        elif i in htw_multi[the_variable] :
            impact_multi_htw_death=0
            impact_multi_htw_impact=0
            for line in lines_htw_multi[the_variable][i] :
                impact_multi_htw_death += int(data.loc[line,'TotalDeaths']) #find selected impact in the csv file
                impact_multi_htw_impact += (int(data.loc[line,'TotalDeaths'])*(2.94e3/0.9259898057) + #3.8 French VSL, 2.94 Europe mean VSL according to WHO 2014
                        int(data.loc[line,'TotalAffected'])*(97/0.9259898057) + #convert $ from 2014 t dollar from 2019
                        int(data.loc[line,'Total_Damages_1000_USD'])/float(data.loc[line,'CPI'])) #find selected impact in the csv file
            impact_list = np.append(impact_list,impact_multi_htw_impact)
            death_list = np.append(death_list,impact_multi_htw_death)
            idx_scatt = np.append(idx_scatt,meteo_list[-1])
            nb_htw_scatt = np.append(nb_htw_scatt,i)

        if i in stefanon_htw and i not in not_computed_htw:
            df.loc[str(i),'extreme_bool'] = 1
            df.loc[str(i),'Impact_fct'] = impact_list[-1]
            df.loc[str(i),'TotalDeaths'] = death_list[-1]
        elif i not in not_computed_htw :
            df.loc[str(i),'extreme_bool'] = 0
            df.loc[str(i),'Impact_fct'] = 0
            df.loc[str(i),'TotalDeaths'] = 0

        #-------------#
        # draw figure #
        #-------------#

    #print(htw_charac,'min',np.min(meteo_list),'max',np.max(meteo_list))
    df.loc[:,htw_charac] = meteo_list
df.to_excel("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/characteristics_htws_"+the_variable+".xlsx")
df.to_csv("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/characteristics_htws_"+the_variable+".csv")


f_Russo.close()
f.close()
f_pop_GHS.close()
f_pop_WP.close()