#%%
import numpy as np
import numpy.ma as ma #use masked array
import netCDF4 as nc #load and write netcdf data
from datetime import date, timedelta, datetime #create file history with creation date
from tqdm import tqdm #create a user-friendly feedback while script is running
import os #read data directories
import pandas as pd #handle dataframes
import pathlib
import cc3d #connected components patterns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as clrs
from scipy import stats
from scipy import signal
from adjustText import adjust_text
import ast
from sklearn import metrics
#%%
def compute_Russo_HWMId(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15):
    """Compute the pseudo_Russo index map.
    Based on HWMId defined by Russo et al (2015, http://dx.doi.org/10.1088/1748-9326/10/12/124003 )."""

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('year_beg_climatolgy :',year_beg_climatology)
    print('year_end_climatolgy :',year_end_climatology)
    print('distrib_window_size :',distrib_window_size)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

    f_anomaly_meteo = nc.Dataset(os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_anomaly_JJA_{year_beg}_{year_end}_climatology_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc"))#path to the output netCDF file

    time_in = f_anomaly_meteo.variables['time'][:]
    lon_in = f_anomaly_meteo.variables['lon'][:]
    lat_in = f_anomaly_meteo.variables['lat'][:]

    f_anomaly_meteo_25p = nc.Dataset(os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_ano_{year_beg_climatology}_{year_end_climatology}_{25}th_threshold_{distrib_window_size}days.nc"))
    f_anomaly_meteo_75p = nc.Dataset(os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_ano_{year_beg_climatology}_{year_end_climatology}_{75}th_threshold_{distrib_window_size}days.nc"))

    var_25 = f_anomaly_meteo_25p.variables['threshold'][152:244,:,:] #JJA days, 1st June to 31st August
    var_75 = f_anomaly_meteo_75p.variables['threshold'][152:244,:,:] #JJA days, 1st June to 31st August

    #-------------------
    nc_file_out = nc.Dataset(os.path.join(datadir,database,datavar,f"Russo_HWMId_{database}_{datavar}_{daily_var}_ano_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc.nc"),mode='w',format='NETCDF4_CLASSIC')#path to the output netCDF file

    #Define netCDF output file :
    nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to)

    nc_file_out.title=f"Russo HWMId for {database}, daily {temp_name_dict[daily_var]} {datavar} anomaly"

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    time = nc_file_out.createVariable('time', np.float32, ('time',))
    time.units = f'days of JJA from {year_beg} to {year_end}'
    time.long_name = 'time'
    # Define a 3D variable to hold the data
    Russo_HWMId = nc_file_out.createVariable('Russo_HWMId',np.float64,('time','lat','lon')) # note: unlimited dimension is leftmost
    Russo_HWMId.units = '°C' # degrees Celsius
    # Write latitudes, longitudes.
    # Note: the ":" is necessary in these "write" statements
    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]
    time[:] = time_in[:]

    for i in tqdm(range(year_end-year_beg+1)):
        var = f_anomaly_meteo.variables[datavar][i*92:(i+1)*92,:,:]
        Russo_HWMId[i*92:(i+1)*92,:,:] = (var-var_25)/(var_75-var_25)
    f_anomaly_meteo.close()
    nc_file_out.close()
    f_anomaly_meteo_25p.close()
    f_anomaly_meteo_75p.close()
    return

#%%
def create_heatwaves_metrics_database(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,flex_time_span=7, count_all_impacts=True):
    '''This function is used to create the dataset of the metrics of the detected heatwaves. The set of detected heatwaves depends on all the parameters.'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatolgy :',year_beg_climatology)
    print('year_end_climatolgy :',year_end_climatology)
    print('nb_days :',nb_days)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    # LOAD FILES
    f_label = nc.Dataset(os.path.join(datadir,database,datavar,"Detection_Heatwave",f"detected_heatwaves_{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc"),mode='r')
    time_in = f_label.variables['time'][:]
    lat_in = f_label.variables['lat'][:]
    lon_in = f_label.variables['lon'][:]

    f_land_sea_mask = nc.Dataset(os.path.join(datadir,database,"Mask",f"Mask_Europe_land_only_{database}_{resolution}deg.nc"),mode='r')
    land_sea_mask = f_land_sea_mask.variables['mask'][:]

    f_temp = nc.Dataset(os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_anomaly_JJA_{year_beg}_{year_end}_climatology_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc"),mode='r')
    f_Russo = nc.Dataset(os.path.join(datadir,database,datavar,f"Russo_HWMId_{database}_{datavar}_{daily_var}_ano_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc.nc"),mode='r')#path to the output netCDF file
    f_gdp_cap = nc.Dataset(os.path.join(datadir,database,"Socio_eco_maps",f"GDP_cap_{database}_Europe_{resolution}deg.nc"),mode='r')#path to the output netCDF file
    
    f_pop_GHS_1975 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_1975_{database}_grid_Europe.nc"))
    f_pop_GHS_1980 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_1980_{database}_grid_Europe.nc"))
    f_pop_GHS_1985 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_1985_{database}_grid_Europe.nc"))
    f_pop_GHS_1990 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_1990_{database}_grid_Europe.nc"))
    f_pop_GHS_1995 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_1995_{database}_grid_Europe.nc"))
    f_pop_GHS_2000 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_2000_{database}_grid_Europe.nc"))
    f_pop_GHS_2005 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_2005_{database}_grid_Europe.nc"))
    f_pop_GHS_2010 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_2010_{database}_grid_Europe.nc"))
    f_pop_GHS_2015 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_2015_{database}_grid_Europe.nc"))
    f_pop_GHS_2020 = nc.Dataset(os.path.join(datadir,"Pop","GHS_POP",f"GHS_POP_2020_{database}_grid_Europe.nc"))
    #LOAD POPULATION FILES
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

    output_dir = os.path.join("Output",database,f"{datavar}_{daily_var}",
                            f"{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    df_htw = pd.read_excel(os.path.join(output_dir,f"df_htws_V0_detected_{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.xlsx"),header=0,index_col=0)
    df_emdat_not_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0) #heatwaves are not merged by event, they are dissociated when affecting several countries
    df_emdat_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves_merged.xlsx"),header=0, index_col=0) #heatwaves are merged by event number Dis No 
    # #Read txt file containing detected heatwaves to create detected heatwaves list
    with open(os.path.join(output_dir,f"emdat_detected_heatwaves_{database}_{datavar}_{daily_var}_ano_JJA_{nb_days}ds_bf_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}ds_wndw_clmgy_{year_beg_climatology}_{year_end_climatology}_flex_time_{flex_time_span}_days.txt"),'r') as f_txt:
        detected_htw_list = f_txt.readlines()
    f_txt.close()
    # #Remove '\n' from strings
    emdat_to_meteo_db_id_dico_not_merged = {}
    emdat_heatwaves_list = []
    for i in range(len(detected_htw_list)) :
        emdat_to_meteo_db_id_dico_not_merged[detected_htw_list[i][:13]] = ast.literal_eval(detected_htw_list[i][14:-1])#Remove '\n' from strings
        emdat_heatwaves_list = np.append(emdat_heatwaves_list,emdat_to_meteo_db_id_dico_not_merged[detected_htw_list[i][:13]])
    emdat_heatwaves_list = [int(i) for i in np.unique(emdat_heatwaves_list)]
    #%% #Need to consider the possibility that several EM-DAT heatwaves are not distinguishable in meteo database
    htw_multi = []
    inverted_emdat_to_meteo_db_id_dico_not_merged = {}
    for htw,v in emdat_to_meteo_db_id_dico_not_merged.items() :
        for val in v :
            try : 
                inverted_emdat_to_meteo_db_id_dico_not_merged[val].append(htw[:9])
            except :
                inverted_emdat_to_meteo_db_id_dico_not_merged[val]=[htw[:9]]
    for k,v in inverted_emdat_to_meteo_db_id_dico_not_merged.items():
        inverted_emdat_to_meteo_db_id_dico_not_merged[k]=[s for s in np.unique(inverted_emdat_to_meteo_db_id_dico_not_merged[k])]
        if len(inverted_emdat_to_meteo_db_id_dico_not_merged[k])>1:
            htw_multi.append(k)
    #--------------------------
    #%% #For all EM-DAT merged event, record every associated EM-DAT not merged heatwave (dico_merged_htw) that are detected in meteo database, and record every associated meteo database heatwave (dico_merged_label)
    emdat_to_meteo_db_id_dico_merged_htw = {}
    emdat_to_meteo_db_id_dico_merged_label = {}
    for i in df_emdat_merged.index.values[:]:
        dis_no = str(df_emdat_merged.loc[i,'disasterno'])
        for k,v in emdat_to_meteo_db_id_dico_not_merged.items():
            if dis_no in k :
                try :
                    emdat_to_meteo_db_id_dico_merged_htw[dis_no].append(k)
                    emdat_to_meteo_db_id_dico_merged_label[dis_no] = np.append(emdat_to_meteo_db_id_dico_merged_label[dis_no],v)
                except :
                    emdat_to_meteo_db_id_dico_merged_htw[dis_no]=[k]
                    emdat_to_meteo_db_id_dico_merged_label[dis_no]=[v]
    not_computed_htw = []
    links_not_computed_dict = {}
    for k,v in emdat_to_meteo_db_id_dico_merged_label.items():
        emdat_to_meteo_db_id_dico_merged_label[k]=[int(i) for i in np.unique(v)]
        if len(emdat_to_meteo_db_id_dico_merged_label[k])>1:
            not_computed_htw = np.append(not_computed_htw,emdat_to_meteo_db_id_dico_merged_label[k][1:])
            links_not_computed_dict[emdat_to_meteo_db_id_dico_merged_label[k][0]]=[int(i) for i in emdat_to_meteo_db_id_dico_merged_label[k][1:]]
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

    for htw_id in tqdm(df_htw.index.values[:]) : #list of heatwaves detected in the meteo database
        if htw_id not in not_computed_htw :
            df_htw.loc[htw_id,'Computed_heatwave']=True
            new_computed_htw = [htw_id]
            if htw_id in careful_htw : #create list of all heatwaves that are not distinguishable from the htw_id heatwave (either because of EM-DAT overlap or meteo database overlap)
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
            table_Russo = f_Russo.variables['Russo_HWMId'][(year-year_beg)*92:(year-year_beg+1)*92,:,:]
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
      
            if htw_id in emdat_heatwaves_list :
                df_htw.loc[htw_id,'Extreme_heatwave'] = True
                #Compute impact metrics
                disasterno_list = []
                for i in new_computed_htw :
                    if count_all_impacts : #count all affected countries according to EM-DAT
                        dis_no_name = 'disasterno'
                        disasterno_list = np.append(disasterno_list,inverted_emdat_to_meteo_db_id_dico_not_merged[i])
                    else : #count only visibly affected countries according to the meteorological database
                        dis_no_name = 'Dis No'
                        disasterno_list = np.append(disasterno_list,[emdat_to_meteo_db_id_dico_merged_htw[k] for k in inverted_emdat_to_meteo_db_id_dico_not_merged[i]])
                disasterno_list = [st for st in np.unique(disasterno_list)]
                df_impact = df_emdat_not_merged[df_emdat_not_merged[dis_no_name].isin(disasterno_list)]
                df_impact = df_impact.fillna(value=0)
                df_htw.loc[htw_id,'Total_Deaths'] = int(df_impact['Total Deaths'].sum())
                df_htw.loc[htw_id,'Total_Affected'] = int(df_impact['Total Affected'].sum())
                df_htw.loc[htw_id,'Material_Damages'] = (df_impact["Total Damages, Adjusted ('000 US$)"].sum())*1e3 #in 2022 US$
                df_htw.loc[htw_id,'Impact_sum'] = (int(df_htw.loc[htw_id,'Total_Deaths'])*(2.94e6*1.366/0.80645161)+ #2.94e6 US$ is Europe mean VSL according to WHO 2014, convert €2014 to US$2014 (*1.366),  then convert US$2014 to US$2022 (/0.806)
                int(df_htw.loc[htw_id,'Total_Affected'])*(97e3*1.366/0.80645161)+ #mean value of affected people, convert €2014 to US$2014 (*1.366),  then convert US$2014 to US$2022 (/0.806)
                (df_htw.loc[htw_id,'Material_Damages'])) #socio-economic calculation, in 2022 US$

    #Save dataframe 
    df_htw.to_excel(os.path.join(output_dir,f"df_htws_detected{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"))
    #close netCDF files
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
    return

#%%
def compute_heatwaves_metrics_scores(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,flex_time_span=7, count_all_impacts=True):
    '''This function is used to compute the scores of the metrics of the detected heatwaves. The set of detected heatwaves depends on all the parameters.'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatolgy :',year_beg_climatology)
    print('year_end_climatolgy :',year_end_climatology)
    print('nb_days :',nb_days)
    print('count_all_impacts :',count_all_impacts)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    count_all_impacts = True #True : count all affected countries according to EM-DAT ; False : #count only visibly affected countries according to ERA5
    dataframe_dir = os.path.join("Output",database,f"{datavar}_{daily_var}",
                                        f"{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    df_htw = pd.read_excel(os.path.join(dataframe_dir,
                                        f"df_htws_detected{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"),header=0,index_col=0)
    impact_criteria = ['Total_Deaths','Total_Affected','Material_Damages','Impact_sum']
    meteo_criteria=df_htw.columns.values[np.argwhere((df_htw.columns.values)=='Global_mean')[0][0]:]
    arr = []
    for i in range(len(impact_criteria)) :
        arr+=[impact_criteria[i]]*4
    arrays = [arr, ['r_pearson', 'p-value', 'roc_auc', 'Global_score']*len(impact_criteria)]

    col_idx = pd.MultiIndex.from_arrays(arrays, names=('impact', 'metric'))
    df_scores = pd.DataFrame(columns=col_idx, index = meteo_criteria,data=None)

    figs_output_dir = os.path.join(dataframe_dir,f"figs_flex_time_span_{flex_time_span}","roc_curve")
    pathlib.Path(figs_output_dir).mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary

    for chosen_impact in tqdm(impact_criteria) :
        for chosen_meteo in meteo_criteria :
            extreme_list_impact = [df_htw.loc[i,chosen_impact] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
            extreme_list_meteo = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
            meteo_list = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Computed_heatwave']==True].index.values[:]]
            extreme_bool_list = [int(df_htw.loc[i,'Extreme_heatwave']) for i in df_htw[df_htw['Computed_heatwave']==True].index.values[:]]
            Rpearson = stats.pearsonr(extreme_list_impact,extreme_list_meteo)
            roc_auc = metrics.roc_auc_score(extreme_bool_list,meteo_list)
            df_scores.loc[chosen_meteo,(chosen_impact,'r_pearson')] = Rpearson[0]
            df_scores.loc[chosen_meteo,(chosen_impact,'p-value')] = Rpearson[1]
            df_scores.loc[chosen_meteo,(chosen_impact,'roc_auc')] = roc_auc
            df_scores.loc[chosen_meteo,(chosen_impact,'Global_score')] = np.sqrt(np.abs(Rpearson[0]*roc_auc))
            #display roc_curve
            if chosen_impact==impact_criteria[0] : #save this fig only once since it does not depend on the impact criterion
                fpr, tpr, thresholds = metrics.roc_curve(extreme_bool_list,meteo_list)
                display = metrics.RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc,estimator_name=chosen_meteo)
                display.plot()
                plt.plot([0, 1], [0, 1], "k--", label="chance level (AUC = 0.5)")
                plt.axis("square")
                plt.xlabel("False Positive Rate")
                plt.ylabel("True Positive Rate")
                plt.title(f"ROC curve: {chosen_meteo}")
                plt.legend()
                plt.savefig(os.path.join(figs_output_dir,f"roc_curve_{chosen_meteo}.png"))
                plt.close()
    df_scores.to_excel(os.path.join(dataframe_dir,f"df_scores_{'count_all_impacts'*(count_all_impacts)}_flex_time_span_{flex_time_span}_days.xlsx"))
    return

#%%
def plot_heatwaves_distribution(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,flex_time_span=7, count_all_impacts=True):
    '''This function is used to plot the distribution of the detected heatwaves according to different metrics. The set of detected heatwaves depends on all the parameters.'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatolgy :',year_beg_climatology)
    print('year_end_climatolgy :',year_end_climatology)
    print('nb_days :',nb_days)
    print('count_all_impacts :',count_all_impacts)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    count_all_impacts = True #True : count all affected countries according to EM-DAT ; False : #count only visibly affected countries according to ERA5
    dataframe_dir = os.path.join("Output",database,f"{datavar}_{daily_var}",
                                        f"{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    df_htw = pd.read_excel(os.path.join(dataframe_dir,
                                        f"df_htws_detected{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"),header=0,index_col=0)
    
    def max_boundary(x) :
        if x<0 :
            x=0.95
        else :
            x=1.05
        return(x)

    def min_boundary(x) :
        if x<0 :
            x=1.05
        else :
            x=0.95
        return(x)

    def id_func(x) :
        return(x)

    dict_func = {"Global_mean": id_func, 
    "Spatial_extent": np.log10,
    "Duration": id_func, 
    "Temp_sum": np.log10,
    'Pseudo_Russo': np.log10, 
    'Max_spatial' : np.log10, 
    'Max': id_func,
    "Global_mean_pop": np.log10, 
    "Spatial_extent_pop": np.log10, 
    "Duration_pop": np.log10, 
    "Temp_sum_pop": np.log10,
    'Pseudo_Russo_pop': np.log10, 
    'Max_pop': np.log10,
    'Max_spatial_pop': np.log10, 
    'Temp_sum_pop_NL': np.log10, 
    'Pseudo_Russo_pop_NL': np.log10, 
    'Total_affected_pop':np.log10,
    'Multi_index_Russo':np.log10,
    'Multi_index_temp':np.log10, 
    'Multi_index_Russo_NL':np.log10,
    'Multi_index_temp_NL':np.log10,
    'Mean_log_GDP':id_func,
    'Mean_exp_GDP':id_func,
    'Mean_inv_GDP':np.log10,
    'GDP_inv_log_temp_sum':np.log10,
    'GDP_inv_log_temp_mean':np.log10} #bins of the histogram

    clrs_dico = {"Total_Deaths": clrs.LogNorm(vmin=1, vmax=np.max(df_htw['Total_Deaths'])), "Total_Affected": clrs.Normalize(vmin=0, vmax=500), "Total_Damages": clrs.LogNorm(vmin=1, vmax=12120000) , "Impact_sum": clrs.LogNorm(vmin=1e4, vmax=np.max(df_htw['Impact_sum']))} #colormap depending on the selected criterion

    #impact_criteria = ['TotalDeaths', 'Impact_fct']
    #meteo_criteria = ['Global_mean','Spatial_extent','Duration','Max','Max_spatial','Temp_sum','Pseudo_Russo','Pop_unique','Global_mean_pop','Duration_pop','Max_pop','Max_spatial_pop',
    #'Spatial_extent_pop','Temp_sum_pop','Pseudo_Russo_pop','Temp_sum_pop_NL','Pseudo_Russo_pop_NL','Multi_index_temp','Multi_index_Russo','Multi_index_temp_NL','Multi_index_Russo_NL']

    df_emdat_not_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0) #heatwaves are not merged by event, they are dissociated when affecting several countries
    df_emdat_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves_merged.xlsx"),header=0, index_col=0) #heatwaves are merged by event number Dis No
    
    # #Read txt file containing detected heatwaves to create detected heatwaves list
    with open(os.path.join(dataframe_dir,f"emdat_detected_heatwaves_{database}_{datavar}_{daily_var}_ano_JJA_{nb_days}ds_bf_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}ds_wndw_clmgy_{year_beg_climatology}_{year_end_climatology}_flex_time_{flex_time_span}_days.txt"),'r') as f_txt:
        detected_htw_list = f_txt.readlines()
    f_txt.close()
    # #Remove '\n' from strings
    emdat_to_era5_id_dico_not_merged = {}
    emdat_heatwaves_list = []
    for i in range(len(detected_htw_list)) :
        emdat_to_era5_id_dico_not_merged[detected_htw_list[i][:13]] = ast.literal_eval(detected_htw_list[i][14:-1])#Remove '\n' from strings
        emdat_heatwaves_list = np.append(emdat_heatwaves_list,emdat_to_era5_id_dico_not_merged[detected_htw_list[i][:13]])
    emdat_heatwaves_list = [int(i) for i in np.unique(emdat_heatwaves_list)]
    #Need to consider the possibility that several EM-DAT heatwaves are not distinguishable in ERA5
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
    #For all EM-DAT merged event, record every associated EM-DAT not merged heatwave (dico_merged_htw) that are detected in ERA5, and record every associated ERA5 heatwave (dico_merged_label)
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

    figs_output_dir = os.path.join(dataframe_dir,f"figs_flex_time_span_{flex_time_span}",f"distrib{'_count_all_impacts'*count_all_impacts}")
    pathlib.Path(figs_output_dir).mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary

    impact_criteria = ['Total_Deaths']#[Total_Deaths,Total_Affected,Material_Damages,Impact_sum]
    #List of metrics
    meteo_criteria=df_htw.columns.values[np.argwhere((df_htw.columns.values)=='Global_mean')[0][0]:]#all metrics, starting with Global_mean

    for chosen_impact in impact_criteria :
        scatter_list_impact = [df_htw.loc[i,chosen_impact] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
        for chosen_meteo in meteo_criteria :
            scatter_list_meteo = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
            meteo_list = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Computed_heatwave']==True].index.values[:]]

            min_val = np.min(meteo_list)
            max_val = np.max(meteo_list)
            print(chosen_meteo,'min',np.min(meteo_list),'max',np.max(meteo_list))
            fig = plt.figure(1,figsize=(24,16),facecolor='white')
            if dict_func[chosen_meteo] == id_func :
                Y,bins_edges=np.histogram(meteo_list,bins=np.linspace(start=min_val*min_boundary(min_val), stop=max_val*max_boundary(max_val), num=30)) #histogram of the E-OBS heatwaves distribution
            elif dict_func[chosen_meteo] == np.log10 :
                Y,bins_edges=np.histogram(meteo_list,bins=np.logspace(start=np.log10(min_val*min_boundary(min_val)), stop=np.log10(max_val*max_boundary(max_val)), num=30)) #histogram of the E-OBS heatwaves distribution
            X=[0]*len(Y)

            for k in range(len(Y)) :
                X[k]=(bins_edges[k+1]+bins_edges[k])/2
            Y=np.array(Y)
            Y2=signal.savgol_filter(Y, 9,3)#savgol_window_dico[chosen_meteo], 3) #smooth the histogram edges with a savitzky-golay filter
            if dict_func[chosen_meteo] == (id_func) : 
                plt.plot(X,Y,'ko')
                plt.plot(X,Y2,'r-')
            elif dict_func[chosen_meteo] == np.log10: #have to plot on semilog scale for these criteria
                plt.semilogx(X,Y,'ko')
                plt.semilogx(X,Y2,'r-')
            plt.plot(X,Y,'ko')
            plt.plot(X,Y2,'r-')
            plt.ylim([-2,50])
            plt.xlim([min_val*min_boundary(min_val),max_val*max_boundary(max_val)])
            plt.axvline(np.percentile(meteo_list,25),linewidth=2) #add 1st quartile of the meteo criterion list
            plt.axvline(np.median(meteo_list),linewidth=2) #add median of the meteo criterion list
            plt.axvline(np.percentile(meteo_list,75),linewidth=2) #add 3rd quartile of the meteo criterion list
            plt.grid()
            plt.xlabel(chosen_meteo,size=25)#+' '+units_dico[chosen_meteo])
            plt.ylabel('Frequency',size=25)
            plt.title(f'Heatwaves distribution over {chosen_meteo} criterion',size=25)# ('+criteria_dico[chosen_meteo]+')',y=1)

            texts=[]
            for k in range(len(scatter_list_meteo)):
                closest_x = min(range(len(X)), key=lambda i: abs(X[i]-scatter_list_meteo[k]))
                plt.scatter(np.linspace(scatter_list_meteo[k],scatter_list_meteo[k],1000),np.linspace(0,Y2[closest_x],1000),c=[scatter_list_impact[k]]*1000,edgecolor=None, cmap = 'YlOrRd',norm=clrs_dico[chosen_impact],linewidths=4)
                texts.append(plt.annotate(df_htw[df_htw['Extreme_heatwave']==True].index.values[k],(scatter_list_meteo[k],Y2[closest_x]),size=15))
            adjust_text(texts, only_move={'points':'y', 'texts':'y'}, arrowprops=dict(arrowstyle="->", color='k', lw=1))
            cax = plt.axes([0.35, 0.02, 0.35, 0.02])
            plt.title('Impact of the extreme heatwaves ('+chosen_impact+')',y=1,size=25)
            plt.colorbar(cax=cax,orientation='horizontal')
            #plt.tight_layout()
            plt.savefig(os.path.join(figs_output_dir,f"distrib_{chosen_impact}_{chosen_meteo}_{'_count_all_impacts'*count_all_impacts}.png"))
            fig.clear()
            #plt.show()
    return

#%%
def analysis_top_detected_events(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,flex_time_span=7,nb_top_events=30,best_scoring_index='Multi_index_Russo',count_all_impacts=True):
    '''This function is used to search for the top detected heatwaves in an alternate impact database.'''
    #combinations = [['ERA5','t2m'],['ERA5','wbgt'],['E-OBS','t2m']]
    #for database,datavar in combinations :
    
    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatolgy :',year_beg_climatology)
    print('year_end_climatolgy :',year_end_climatology)
    print('nb_days :',nb_days)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    #Link databse country names format to netCDF mask country names format
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
                    'Ukraine':'Ukraine','Yugoslavia':'Serbia',#The corresponding heatwave happened in Serbia, cf 'Location' data of EM-DAT
                    'England':'United_Kingdom','England and Wales':'United_Kingdom','Czech Republic':'Czechia'} 
    
    dict_country_labels = {'Albania': 1, 'Austria': 2, 'Belarus': 3, 'Belgium': 4, 'Bosnia_and_Herzegovina': 5, 
                           'Bulgaria': 6, 'Croatia': 7, 'Cyprus': 8, 'Czechia': 9, 'Denmark': 10, 'Estonia': 11, 
                           'Finland': 12, 'France': 13, 'Germany': 14, 'Greece': 15, 'Hungary': 16, 'Iceland': 17, 
                           'Ireland': 18, 'Italy': 19, 'Latvia': 20, 'Lithuania': 21, 'Luxembourg': 22, 
                           'Montenegro': 23, 'Macedonia': 24, 'Moldova': 25, 'Netherlands': 26, 'Norway': 27, 
                           'Poland': 28, 'Portugal': 29, 'Romania': 30, 'Russia': 31, 'Serbia': 32, 'Slovakia': 33, 
                           'Slovenia': 34, 'Spain': 35, 'Sweden': 36, 'Switzerland': 37, 'Turkey': 38, 
                           'United_Kingdom': 39, 'Ukraine': 40}
    
    inv_dict_country_labels = {v: k for k, v in dict_country_labels.items()}
    
    
    
    output_dir_df = os.path.join("Output",database,f"{datavar}_{daily_var}" ,
                            f"{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    df_htw = pd.read_excel(os.path.join(output_dir_df,f"df_htws_detected{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"), header=0, index_col=0)
    df_impact_alternate = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","Lucy_Hammond_ETE_data_V2.xlsx"), header=0, index_col=0)
    df_impact_alternate = df_impact_alternate[df_impact_alternate['Country'].isin(country_dict.keys())]

    df_htw = df_htw[df_htw['Computed_heatwave']==True]
    df_htw = df_htw[np.isnan(df_htw['Total_Deaths'])]#we study top events that are not recorded in EM-DAT
    top_events_id = np.sort(df_htw.sort_values(by=best_scoring_index).index[-nb_top_events:])
    df_htw = df_htw[df_htw.index.isin(top_events_id)]

    nc_file_label = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"detected_heatwaves_{database}_{datavar}_{daily_var}_anomaly_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    f_label=nc.Dataset(nc_file_label,mode='r')

    lat_in = f_label.variables['lat'][:]
    lon_in = f_label.variables['lon'][:]

    country_labels = np.zeros((92,len(lat_in),len(lon_in)),dtype=int)
    for ctry in dict_country_labels.keys():
        mask_file = nc.Dataset(os.path.join(datadir,database,"Mask",f"Mask_{ctry}_{database}_{resolution}deg.nc"),mode='r')
        country_labels=np.maximum(country_labels,[~np.array(mask_file.variables['mask'][:],dtype=bool)*dict_country_labels[ctry]]*92) #assign a country label to each point of the map. np.maximum() is used to avoid the superposition of labels : a few pixels are assigned to several countries.
    overlap_list_dict = {}
    affected_countries_labels_dict = {}

    output_overlap_df = pd.DataFrame(columns=['Year','idx_beg_JJA','idx_end_JJA','idx_beg_all_year','idx_end_all_year','detected_affected_countries','Hammond_htw_indices','Hammond_affected_countries','Hammond_deaths'],index=None,data=None)
    
    for htw_id in tqdm(df_htw.index) :
        year_event = df_htw.loc[htw_id,'Year']
        start_date_idx_all_year = df_htw.loc[htw_id,'idx_beg_all_year']#idx_beg_all_year
        end_date_idx_all_year = df_htw.loc[htw_id,'idx_end_all_year']#idx_end_all_year
        
        overlap_list = []
        labels_cc3d = f_label.variables['label'][(year_event-year_beg)*92:(year_event-year_beg+1)*92,:,:] #load all JJA label data for the given year
        
        for impact_idx in df_impact_alternate.index :
            idx_beg_impact = (df_impact_alternate.loc[impact_idx,'Start date'].date() - date(year_beg,1,1)).days
            idx_end_impact = (df_impact_alternate.loc[impact_idx,'End date'].date() - date(year_beg,1,1)).days
            if ((start_date_idx_all_year>=idx_beg_impact and start_date_idx_all_year<=idx_end_impact) or (end_date_idx_all_year>=idx_beg_impact and end_date_idx_all_year<=idx_end_impact)) or ((idx_beg_impact>=start_date_idx_all_year and idx_beg_impact<=end_date_idx_all_year) or (idx_end_impact>=start_date_idx_all_year and idx_end_impact<=end_date_idx_all_year)) :
                f_mask = nc.Dataset(os.path.join(datadir, database,"Mask",f"Mask_{country_dict[df_impact_alternate.loc[impact_idx,'Country']]}_{database}_{resolution}deg.nc"),mode='r')
                mask_country = f_mask.variables['mask'][:]
                if np.any(ma.masked_where([mask_country]*92,(labels_cc3d==htw_id))) : #if there is also a spatial overlap (check only at the country level).
                    overlap_list.append(impact_idx)
        overlap_list_dict[htw_id]=overlap_list
        affected_countries_labels_dict[htw_id] = [int(val) for val in np.unique((ma.filled(labels_cc3d,fill_value=0)==htw_id)*country_labels)[1:]] #ignore value 0
        hammond_affected_countries = [df_impact_alternate.loc[index,'Country'] for index in overlap_list]
        hammond_deaths = np.sum([df_impact_alternate.loc[index,'Deaths'] for index in overlap_list])
        output_overlap_df.loc[htw_id]=[year_event,df_htw.loc[htw_id,'idx_beg_JJA'],df_htw.loc[htw_id,'idx_end_JJA'],start_date_idx_all_year,end_date_idx_all_year,[inv_dict_country_labels[country] for country in affected_countries_labels_dict[htw_id]],overlap_list,hammond_affected_countries,hammond_deaths]
        
    output_overlap_df.to_excel(os.path.join(output_dir_df,f"top_{nb_top_events}_events_overlap_{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"))

    #with open(os.path.join(output_dir_df,f"top_unrecorded_heatwaves_{database}_{datavar}_{daily_var}_ano_JJA_{nb_days}ds_bf_scan_{year_beg}_{year_end}_{threshold_value}th_{distrib_window_size}ds_wndw_clmgy_{year_beg_climatology}_{year_end_climatology}_flex_time_{flex_time_span}_ds.txt"), 'w') as output :
    #    for k,v in overlap_list_dict.items() :
    #        output.write(str(k) + ' ' + str(v) + ' ' + str([inv_dict_country_labels[country] for country in affected_countries_labels_dict[k]]) + '\n') #*(len(v)>0)
            
    #faire plutôt un dataframe avec ces infos + récupérer ce qui overlap avec le doc Lucy Hammond pour avoir toutes les infos d'un coup
    return