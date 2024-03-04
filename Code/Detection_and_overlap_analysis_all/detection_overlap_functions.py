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
from matplotlib.font_manager import FontProperties
import cartopy.crs as ccrs 
import cartopy.feature as cfeature 
from shapely.geometry import Polygon
from shapely.geometry import Point
import shapely
from cartopy.io import shapereader
import geopandas


#%%
def compute_climatology_smooth(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021,year_beg_climatology=1950, year_end_climatology=2021):
    '''This function computes a climatology for each calendar day of the year. The seasonal cycle is then smoothed with a 31-day window. 
    By default, the climatology is computed over the studied period (default 1950-2021).
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m). 
    For instance, if studied period is 1990-2020 and climatology period is 1950-1980, these parameters should be set such as : year_beg=1990, year_end=2020, year_beg_climatology=1950, year_end_climatology=1980 '''
    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)

    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]

    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    long_name_dict = {'utci' : 'Universal Thermal Climate Index', 't2m' : '2 meters temperature', 'wbgt':'Wet Bulb Globe Temperature (Brimicombe et al., 2023)'}
    resolution = resolution_dict[database]
    #Load netcdf temperature (or climate comfort index) data file :
    nc_in_path = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_Europe_day_{resolution}deg_{year_beg}-{year_end}.nc") # path to netCDF data file
    f=nc.Dataset(nc_in_path, mode='r') #load file
    lat_in=f.variables['lat'][:] #load dimensions
    lon_in=f.variables['lon'][:]

    #-------------------------------------
    #import a xlsx table containing the index of each 1st january and 31st December
    df_bis_year = pd.read_excel(os.path.join(datadir,"Dates_converter.xlsx"),header=0, index_col=0)
    df_bis_year = df_bis_year.loc[year_beg_climatology:year_end_climatology,:] #select period to compute climatology
    nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
    idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year

    #-------------------------------------
    #Define netCDF output file :
    #Compute the temperature data averaged over the chosen period (default 1950-2021) for every calendar day of the year and store it in a netCDF file.
    nc_out_path = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_daily_avg_{year_beg_climatology}_{year_end_climatology}_smoothed.nc")
    pathlib.Path(nc_out_path).parents[0].mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary
    nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

    nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

    nc_file_out.title=f"Climatology of daily {temp_name_dict[daily_var]} {datavar}, averaged over {year_beg_climatology}-{year_end_climatology} for every day of the year, and smoothed to eliminate variability."
    nc_file_out.history = "Created with file run_all_detection_overlap_analysis.py on " + datetime.today().strftime("%d/%m/%y")

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    time = nc_file_out.createVariable('time', np.float32, ('time',))
    time.units = 'days of a bisextile year'
    time.long_name = 'time'
    # Define a 3D variable to hold the data
    output_var = nc_file_out.createVariable(datavar,np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
    output_var.units = f.variables[datavar].units
    output_var.long_name = long_name_dict[datavar]
    output_var.standard_name = datavar # this is a CF standard name

    # Write latitudes, longitudes.
    # Note: the ":" is necessary in these "write" statements -> you want to write the content and not to change the definition of the dimension
    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]
    time[:]=range(366)

    output_var[:,:,:]=ma.array(np.zeros((366,len(lat_in),len(lon_in))),mask=False) #set output netcdf variable

    print("Computing climatology...")
    for day_of_the_year in tqdm(range(366)): #Compute average daily temperature for each calendar day of the year, over the studied (default 1950-2021) period -> 366 days
        bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366] #indices of bisextile years
        not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365] #indices of non-bisextile years

        if day_of_the_year==59: #29th February
            stack_temp=ma.array(np.zeros((len(bis_years),len(lat_in),len(lon_in))),fill_value=np.nan)
            idx=0
            for i in bis_years:
                stack_temp[idx,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+day_of_the_year,:,:])
                idx+=1
            output_var[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

        elif day_of_the_year<59:#before 29th Feb, no issues
            stack_temp=ma.array(np.zeros((len(df_bis_year),len(lat_in),len(lon_in))),fill_value=np.nan)
            idx=0
            for i in range(len(df_bis_year)):
                stack_temp[idx,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+day_of_the_year,:,:])
                idx+=1
            output_var[day_of_the_year,:,:]=np.nanmean(stack_temp,axis=0)

        else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
            stack_temp=ma.array(np.zeros((len(df_bis_year),len(lat_in),len(lon_in))),fill_value=np.nan)
            idx=0
            for i in not_bis_years:
                stack_temp[idx,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+day_of_the_year-1,:,:])
                idx+=1
            for i in bis_years:
                stack_temp[idx,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+day_of_the_year,:,:])
                idx+=1
            output_var[day_of_the_year,:,:]=np.nanmean(stack_temp, axis=0)

    extended_temp=ma.array(np.zeros((366*3,len(lat_in),len(lon_in))))
    extended_temp[0:366,:,:]=output_var[:,:,:]

    extended_temp[366:732,:,:]=output_var[:,:,:]

    extended_temp[732:,:,:]=output_var[:,:,:]

    extended_temp[:] = ma.masked_outside(extended_temp[:],-300,400)

    smooth_span=15

    print("Smoothing...")

    for i in tqdm(range(366,732)):
        val_table=ma.array(np.zeros((2*smooth_span+1,len(lat_in),len(lon_in))))
        for j in range(-smooth_span,smooth_span+1,1):
            val_table[j]=extended_temp[i+j,:,:]
        val_table[:] = ma.masked_outside(val_table[:],-300,400)
        output_var[i-366,:,:] = np.nanmean(val_table[:],axis=0)
    output_var[:]=ma.masked_outside(output_var[:],-300,400)

    f.close()
    nc_file_out.close()
    return

#%%
def compute_distrib_percentile(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,anomaly=True):
    '''This function computes, for every calendar day, the n-th (n is the threshold_value, default 95) percentile of the corresponding distribution of daily. 
    By default, the distribution is computed over the default studied period (1950-2021).
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m)'''

    if distrib_window_size%2==0:
        raise ValueError('distrib_window_size is even. It has to be odd so the window can be centered on the computed day.')
        
    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)
    print('distrib_window_size :',distrib_window_size)

    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]

    name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
    #name_dict_threshold = {True : 'th', False : 'C'}

    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    #Load netcdf temperature (or climate comfort index) data file :               
    nc_in_path = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_Europe_day_{resolution}deg_{year_beg}-{year_end}.nc") # path to netCDF data file
    f=nc.Dataset(nc_in_path, mode='r') #load file
    lat_in=f.variables['lat'][:] #load dimensions
    lon_in=f.variables['lon'][:]

    if anomaly :
        nc_file_anomaly=os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_daily_avg_{year_beg_climatology}_{year_end_climatology}_smoothed.nc")  #path to the netCDF climatology file
        #load netCDF file of the smoothed climatology daily average temperature for anomaly computation
        f_mean=nc.Dataset(nc_file_anomaly, mode='r')
        T_mean_ano=np.zeros((376,len(lat_in),len(lon_in)))
        T_mean_ano[0:-10,:,:]=f_mean.variables[datavar][:,:,:]
        T_mean_ano[-10:,:,:]=f_mean.variables[datavar][0:10,:,:]

    #path to output netCDF file, no need to check the existence of parents directory, already created in previous function
    nc_out_path = os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{year_beg_climatology}_{year_end_climatology}_{threshold_value}th_threshold_{distrib_window_size}days.nc")
    nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
    #-----------
    #Define netCDF output file :
    nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

    nc_file_out.title=f"{threshold_value}th percentile of the {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} distribution, for each location, and calendar day (with a {distrib_window_size}-day centered window). Computed for {year_beg_climatology}-{year_end_climatology}period."
    nc_file_out.history = "Created with file run_all_detection_overlap_analysis.py on " + datetime.today().strftime("%d/%m/%y")

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    time = nc_file_out.createVariable('time', np.float32, ('time',))
    time.units = 'days of a bisextile year'
    time.long_name = 'time'
    # Define a 3D variable to hold the data
    threshold = nc_file_out.createVariable('threshold',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
    threshold.units = '°C' # degrees Celsius
    threshold.standard_name = datavar # this is a CF standard name

    # Write latitudes, longitudes.
    # Note: the ":" is necessary in these "write" statements

    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]
    time[:]=range(366)

    #-------------------------------------
    #import a xlsx table containing the index of each 1st january and 31st December
    df_bis_year = pd.read_excel(os.path.join(datadir,"Dates_converter.xlsx"),header=0, index_col=0)
    df_bis_year = df_bis_year.loc[year_beg_climatology:year_end_climatology,:]
    nb_day_in_year = np.array(df_bis_year.loc[:,"Nb_days"].values) #365 or 366, depending on whether the year is bisextile or not
    idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year


    threshold[:]=ma.array(np.zeros((366,len(lat_in),len(lon_in))),mask=False)

    bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==366] #list of indices corresponding to leap years
    not_bis_years=[idx for idx,e in enumerate(nb_day_in_year) if e==365] #list of indices corresponding to non-leap years
    last_year_is_bis = np.max(bis_years)>np.max(not_bis_years) #boolean value, True if the last year of the studied period is a leap year, False otherwise
    if anomaly :
        for day_of_the_year in tqdm(range(366)):
            list_table=[]
            threshold[day_of_the_year,:,:]=f.variables[datavar][day_of_the_year,:,:] 
            if day_of_the_year==59: #29th February
                for i in bis_years:
                    for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                        list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
            elif day_of_the_year<59:#before 29th Feb, no issues
                i=0
                for j in range(np.max([-day_of_the_year,-(distrib_window_size//2)]),distrib_window_size//2+1,1):
                        list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
                for i in range(len(df_bis_year)-1):
                    for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                        list_table.append(f.variables[datavar][idx_start_year[i+1]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
                        
            else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
                if last_year_is_bis : #if the last year of the period is a leap year
                    for i in not_bis_years:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year-1+j,:,:]-T_mean_ano[day_of_the_year-1+j,:,:])
                    for i in bis_years[:-1]:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
                    i = bis_years[-1]
                    for j in range(-(distrib_window_size//2),np.min([distrib_window_size//2+1,365-day_of_the_year]),1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
                else : #if the last year of the period is not a leap year
                    for i in not_bis_years[:-1]:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year-1+j,:,:]-T_mean_ano[day_of_the_year-1+j,:,:])
                    for i in bis_years:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
                    i = not_bis_years[-1]
                    for j in range(-(distrib_window_size//2),np.min([distrib_window_size//2+1,365-day_of_the_year]),1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:]-T_mean_ano[day_of_the_year+j,:,:])
            threshold[day_of_the_year,:,:]=ma.array(np.percentile(list_table[:],threshold_value,axis=0),mask=False)
    else : #anomaly is False (i.e. we work with absolute values)
        for day_of_the_year in tqdm(range(366)):
            list_table=[]
            threshold[day_of_the_year,:,:]=f.variables[datavar][day_of_the_year,:,:] 
            if day_of_the_year==59: #29th February
                for i in bis_years:
                    for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                        list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:])
            elif day_of_the_year<59:#before 29th Feb, no issues
                i=0
                for j in range(np.max([-day_of_the_year,-(distrib_window_size//2)]),distrib_window_size//2+1,1):
                        list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:])
                for i in range(len(df_bis_year)-1):
                    for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                        list_table.append(f.variables[datavar][idx_start_year[i+1]+day_of_the_year+j,:,:])
                        
            else: #After 29th Feb, have to distinguish bisextile and non-bisextile years
                if last_year_is_bis : #if the last year of the period is a leap year
                    for i in not_bis_years:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year-1+j,:,:])
                    for i in bis_years[:-1]:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:])
                    i = bis_years[-1]
                    for j in range(-(distrib_window_size//2),np.min([distrib_window_size//2+1,365-day_of_the_year]),1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:])
                else : #if the last year of the period is not a leap year
                    for i in not_bis_years[:-1]:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year-1+j,:,:])
                    for i in bis_years:
                        for j in range(-(distrib_window_size//2),distrib_window_size//2+1,1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:])
                    i = not_bis_years[-1]
                    for j in range(-(distrib_window_size//2),np.min([distrib_window_size//2+1,365-day_of_the_year]),1):
                            list_table.append(f.variables[datavar][idx_start_year[i]+day_of_the_year+j,:,:])
            threshold[day_of_the_year,:,:]=ma.array(np.percentile(list_table[:],threshold_value,axis=0),mask=False)
    threshold[:] = ma.masked_outside(threshold[:],-300,400)
    f.close()
    if anomaly :
        f_mean.close()
    nc_file_out.close()
    return

#%%
def select_scale_jja(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15, anomaly=True, relative_threshold=True):
    '''This function creates a netCDF file with daily min, mean or max temperature (or climate comfort index) (anomaly or absolute) for concatenated JJAs for the chosen period (default 1950-2021) when and where the n-th (default 95th) percentile threshold of the climatology distribution (or an absolute value in °C) is exceeded ; 
    Otherwise, values are set to -9999.
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m)'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)

    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
        
    name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
    name_dict_threshold = {True : 'th', False : 'C'}
    
    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
    long_name_dict = {'utci' : 'Universal Thermal Climate Index', 't2m' : '2 meters temperature', 'wbgt':'Wet Bulb Globe Temperature (Brimicombe et al., 2023)'}
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    #-------------------------------------
    #Load temperature data file
    nc_in_path=os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_Europe_day_{resolution}deg_{year_beg}-{year_end}.nc")
    f=nc.Dataset(nc_in_path, mode='r')
    lat_in=f.variables['lat'][:]
    lon_in=f.variables['lon'][:]
    #-------------------------------------
    if anomaly :
        #Load average climatology temperature file
        nc_file_climatology_mean=os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_daily_avg_{year_beg_climatology}_{year_end_climatology}_smoothed.nc")  #path to the netCDF climatology file
        f_climatology_mean=nc.Dataset(nc_file_climatology_mean, mode='r') 
        T_mean=f_climatology_mean.variables[datavar][152:244,:,:]
    #-------------------------------------
    #Only record the JJA temperatures and REMOVE the values that do not exceed the n-th (default 95th) percentile (or absolute value in °C) threshold
    #No need to create directory, already created in previous scripts
    nc_out_name = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_scaled_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    nc_file_out=nc.Dataset(nc_out_name,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file
    #Define netCDF output file :
    nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out.createDimension('time', 92*(year_end-year_beg+1)) # unlimited time axis (can be appended to).

    nc_file_out.title=f"Daily {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} for JJA days from {year_beg} to {year_end}"
    nc_file_out.subtitle=f"values put to zero where not exceeding {threshold_value}{name_dict_threshold[relative_threshold]} {datavar} {name_dict_anomaly[anomaly]} threshold." +f" This threshold was computed over the {year_beg_climatology}-{year_end_climatology} climatology, with a {distrib_window_size} days window."*relative_threshold
    nc_file_out.history = "Created with run_all_detection_overlap_analysis.py on " +datetime.today().strftime("%d/%m/%y")

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    time = nc_file_out.createVariable('time', np.float32, ('time',))
    time.units = 'days of JJA from '+str(year_beg)+' to '+str(year_end)
    time.long_name = 'time'
    date_idx_all_year = nc_file_out.createVariable('date_idx_all_year', np.int32,('time',))
    date_idx_all_year.units = f'days from 01-01-{year_beg}'
    date_idx_all_year.long_name = 'date_idx_all_year'
    # Define a 3D variable to hold the data
    output_var = nc_file_out.createVariable(datavar,np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
    output_var.units = '°C' # degrees Celsius
    output_var.standard_name = datavar # this is a CF standard name
    output_var.long_name = long_name_dict[datavar]
    #-----------
    #Only record the JJA temperatures and KEEP the values that do not exceed the n-th (default 95th) percentile threshold
    nc_out_not_scaled_path = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_climatology_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc")#path to the output netCDF file
    nc_file_out_not_scaled=nc.Dataset(nc_out_not_scaled_path,mode='w',format='NETCDF4_CLASSIC') 
    #Define netCDF output file :
    nc_file_out_not_scaled.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out_not_scaled.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out_not_scaled.createDimension('time', 92*(year_end-year_beg+1)) # unlimited time axis (can be appended to).

    nc_file_out_not_scaled.title=f"Daily {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} for JJA days from {year_beg} to {year_end}"
    nc_file_out_not_scaled.history = "Created with run_all_detection_overlap_analysis.py on " +datetime.today().strftime("%d/%m/%y")

    lat_not_scaled = nc_file_out_not_scaled.createVariable('lat', np.float32, ('lat',))
    lat_not_scaled.units = 'degrees_north'
    lat_not_scaled.long_name = 'latitude'
    lon_not_scaled = nc_file_out_not_scaled.createVariable('lon', np.float32, ('lon',))
    lon_not_scaled.units = 'degrees_east'
    lon_not_scaled.long_name = 'longitude'
    time_not_scaled = nc_file_out_not_scaled.createVariable('time', np.float32, ('time',))
    time_not_scaled.units = 'days of JJA from '+str(year_beg)+' to '+str(year_end)
    time_not_scaled.long_name = 'time'
    date_idx_all_year_not_scaled = nc_file_out_not_scaled.createVariable('date_idx_all_year', np.int32,('time',))
    date_idx_all_year_not_scaled.units = f'days from 01-01-{year_beg}'
    date_idx_all_year_not_scaled.long_name = 'date_idx_all_year_not_scaled'
    # Define a 3D variable to hold the data
    output_var_not_scaled = nc_file_out_not_scaled.createVariable(datavar,np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
    output_var_not_scaled.units = '°C' # degrees Celsius
    output_var_not_scaled.standard_name = datavar # this is a CF standard name
    output_var_not_scaled.long_name = long_name_dict[datavar]
    #-----------
    #import a xlsx table containing the index of each 1st january and 31st December
    df_bis_year = pd.read_excel(os.path.join(datadir,"Dates_converter.xlsx"),header=0, index_col=0)
    df_bis_year = df_bis_year.loc[year_beg:year_end,:]
    idx_start_year = np.array(df_bis_year.loc[:,"Idx_start"].values) #index of 1st january for each year
    #-------------------------------------
    if relative_threshold :
        f_threshold_name = os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{year_beg_climatology}_{year_end_climatology}_{threshold_value}th_threshold_{distrib_window_size}days.nc")
        f_threshold = nc.Dataset(f_threshold_name, mode='r')
        threshold_table = f_threshold.variables['threshold'][:]
        threshold_table=ma.masked_outside(threshold_table[152:244,:,:],-300,400) #threshold of n-th (default 95th) temperature anomaly (or absolute temperature) percentile for every day of JJA and location
    else :
        threshold_table = threshold_value #in this case, threshold_table is only a scalar
    #-------------------------------------
    # Write latitudes, longitudes,time.
    # Note: the ":" is necessary in these "write" statements
    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]
    time[:]=range(92*(year_end-year_beg+1))
    output_var[:,:,:]=ma.array(np.zeros((92*(year_end-year_beg+1),len(lat_in),len(lon_in))),mask=False) # 92*(year_end-year_beg+1), 92 days of JJA times the number of years 
    date_idx_all_year[:]=np.zeros((92*(year_end-year_beg+1),))
    #-------------------------------------
    lat_not_scaled[:] = lat_in[:] 
    lon_not_scaled[:] = lon_in[:]
    time_not_scaled[:]=range(92*(year_end-year_beg+1))
    output_var_not_scaled[:,:,:]=ma.array(np.zeros((92*(year_end-year_beg+1),len(lat_in),len(lon_in))),mask=False) # 92*(year_end-year_beg+1), 92 days of JJA times the number of years 
    date_idx_all_year_not_scaled[:]=np.zeros((92*(year_end-year_beg+1),))
    
    if anomaly :
        for i in tqdm(range(year_end-year_beg+1)) :
            bis_year_flag=(1-(df_bis_year.loc[i+year_beg,'Nb_days']-365)) #flag put to one for non leap years and to zero for leap years
            for j in range(92):#92 days of JJA for each year i
                output_var[92*i+j,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+152-bis_year_flag+j,:,:] - T_mean[j,:,:])
                output_var_not_scaled[92*i+j,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+152-bis_year_flag+j,:,:] - T_mean[j,:,:])
            var_scaled = np.zeros(np.shape(output_var[i*92:(i+1)*92,:,:]))
            var_scaled = output_var[i*92:(i+1)*92,:,:] - threshold_table
            var_scaled_bool = (var_scaled <0) #array for the mask : when condition is True, the threshold is not exceeded, value should be masked
            output_var[i*92:(i+1)*92,:,:] = output_var[i*92:(i+1)*92,:,:]*(1-var_scaled_bool)+(-9999*var_scaled_bool) #set pixels that must be masked to -9999
            date_idx_all_year[i*92:(i+1)*92] = range(idx_start_year[i]+152-bis_year_flag,idx_start_year[i]+152-bis_year_flag+92)
            date_idx_all_year_not_scaled[i*92:(i+1)*92] = range(idx_start_year[i]+152-bis_year_flag,idx_start_year[i]+152-bis_year_flag+92)
        
    else :
        for i in tqdm(range(year_end-year_beg+1)) :
            bis_year_flag=(1-(df_bis_year.loc[i+year_beg,'Nb_days']-365)) #flag put to one for non leap years and to zero for leap years
            for j in range(92):#92 days of JJA for each year i
                output_var[92*i+j,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+152-bis_year_flag+j,:,:])
                output_var_not_scaled[92*i+j,:,:]=ma.array(f.variables[datavar][idx_start_year[i]+152-bis_year_flag+j,:,:])
            var_scaled = np.zeros(np.shape(output_var[i*92:(i+1)*92,:,:]))
            var_scaled = output_var[i*92:(i+1)*92,:,:] - threshold_table
            var_scaled_bool = (var_scaled <0) #array for the mask : when condition is True, the threshold is not exceeded, value should be masked
            output_var[i*92:(i+1)*92,:,:] = output_var[i*92:(i+1)*92,:,:]*(1-var_scaled_bool)+(-9999*var_scaled_bool) #set pixels that must be masked to -9999
            date_idx_all_year[i*92:(i+1)*92] = range(idx_start_year[i]+152-bis_year_flag,idx_start_year[i]+152-bis_year_flag+92)
            date_idx_all_year_not_scaled[i*92:(i+1)*92] = range(idx_start_year[i]+152-bis_year_flag,idx_start_year[i]+152-bis_year_flag+92)
    
    output_var[:] = ma.masked_outside(output_var[:],-300,400)

    f.close()
    nc_file_out.close()
    if anomaly :
        f_climatology_mean.close()
    nc_file_out_not_scaled.close()
    if relative_threshold :
        f_threshold.close()
    return

#%%
def detect_potential_heatwaves(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4, anomaly=True, relative_threshold=True):
    '''This function deletes the temperature anomaly (or absolute values) data if it is not strictly positive for at least the given number of consecutive days (default value is 4 days). Since it is meant to be used on the output of select_var_scaled_jja, "strictly positive" means that the value exceeds the threshold_value percentile of the climatology distribution (or the absolute threshold if relative_threshold is set to False).
    Otherwise, values are set to -9999.
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m)'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)
    print('nb_days :',nb_days)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
    name_dict_threshold = {True : 'th', False : 'C'}
    
    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
    long_name_dict = {'utci' : 'Universal Thermal Climate Index', 't2m' : '2 meters temperature', 'wbgt':'Wet Bulb Globe Temperature (Brimicombe et al., 2023)'}
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    
    nc_in_path = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_scaled_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")   
    f=nc.Dataset(nc_in_path, mode='r')
    lat_in=f.variables['lat'][:]
    lon_in=f.variables['lon'][:]
    time_in=f.variables['time'][:]
    #-------------------
    nc_out_path = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"potential_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    pathlib.Path(nc_out_path).parents[0].mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary
    nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

    #Define netCDF output file :
    nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out.createDimension('time', None) # unlimited time axis (can be appended to).
    nc_file_out.createDimension('nchar', 10) #in order to save dates on date format as strings

    nc_file_out.title=f"Daily {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} for JJA days corresponding to a potential heatwave duration (here {nb_days} days), from {year_beg} to {year_end}." + f" The threshold is the {threshold_value}th percentile of the climatology distribution ({year_beg_climatology}-{year_end_climatology}, {distrib_window_size}-days centered window)."*relative_threshold + f" The threshold is {threshold_value}°C"*(1-relative_threshold)
    nc_file_out.subtitle=f"values are masked where and when not exceeding {threshold_value}{name_dict_threshold[relative_threshold]} temperature {name_dict_anomaly[anomaly]} threshold for {nb_days} consecutive days or more. Created with run_all_detection_overlap_analysis.py on "+ datetime.today().strftime("%d/%m/%y")

    lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
    lat.units = 'degrees_north'
    lat.long_name = 'latitude'
    lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
    lon.units = 'degrees_east'
    lon.long_name = 'longitude'
    time = nc_file_out.createVariable('time', np.float32, ('time',))
    time.units = f'days of JJA containing a sub-heatwave from {year_beg} to {year_end}'
    time.long_name = 'time'
    # Define a 3D variable to hold the data
    output_var = nc_file_out.createVariable(datavar,np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
    output_var.units = '°C' # degrees Celsius
    output_var.standard_name = datavar # this is a CF standard name

    date_idx = nc_file_out.createVariable('date_idx', np.int32,('time',))
    date_idx.units = f"days of JJA containing a sub-heatwave from {year_beg} to {year_end}, recorded as the matching index of the file {database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_scaled_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc"
    date_idx.long_name = 'date_index'
    date_idx_all_year = nc_file_out.createVariable('date_idx_all_year', np.int32,('time',))
    date_idx_all_year.units = f'days from 01-01-{year_beg}'
    date_idx_all_year.long_name = 'date_index_all_year'
    date_format = nc_file_out.createVariable('date_format', 'S1',('time','nchar'))
    date_format.units = 'days on YYYY-mm-dd format'
    date_format.long_name = 'date_as_date_format'
    # Write latitudes, longitudes.
    # Note: the ":" is necessary in these "write" statements
    lat[:] = lat_in[:] 
    lon[:] = lon_in[:]
    #-------------------
    #create a table with all the dates of the considered data
    calendar=np.zeros(((year_end-year_beg+1),92),dtype=object) 
    for year in range((year_end-year_beg+1)) :
        strt_date=date(year+year_beg,6,1) #start date of ERA5 data
        tps=0
        day_start_JJA=day_num=str(int(time_in[year*92]))
        for day in time_in[year*92:(year+1)*92]:  #01/06 to 31/08 of the given year, change days since 1/1/year_beg to dates, store it into calendar list
            day=int(day)
            day_num=str(day)
            day_num.rjust(3 + len(day_num), '0')
            res_date=strt_date + timedelta(days=int(day_num)-int(day_start_JJA))
            res = res_date.strftime("%Y-%m-%d")
            calendar[year,tps]=res
            tps+=1
    print('Summer calendar has been created on YYYY-mm-dd format from',calendar[0,0],'to',calendar[-1,-1])

    #-------------------
    date_idx_all_year[:]=f.variables['date_idx_all_year'][:]
    for year in tqdm(range((year_end-year_beg+1))) :
        stack_temp=ma.array(-9999*np.ones((92,len(lat_in),len(lon_in))),mask=False) #create a 3D variable that will hold the temperature anomalies (or absolute values) when and where there are heatwaves
        stack_where=ma.array(np.zeros((len(lat_in),len(lon_in))),mask=False)
        for day in range(92):
            temp_masked_filled=ma.filled(f.variables[datavar][year*92+day,:,:],fill_value=-9999)
            stack_where[:,:]=stack_where[:,:]+np.ones((len(lat_in),len(lon_in)))*(temp_masked_filled!=-9999) #add one day to each potential heatwave location
            stack_where[:,:]=stack_where[:,:]*(temp_masked_filled!=-9999) #when not adding a day, have to set back the duration to zero
            if day>=nb_days-1 :
                #for j,k in np.argwhere(stack_where >= nb_days):
                #    stack_temp[day-(nb_days-1):day+1,j,k]=f.variables['temp'][year*92+day-(nb_days-1):year*92+day+1,j,k]
                stack_temp[day-(nb_days-1):day+1,:,:] = stack_temp[day-(nb_days-1):day+1,:,:]*(stack_temp[day-(nb_days-1):day+1,:,:]!=-9999)+f.variables[datavar][year*92+day-(nb_days-1):year*92+day+1,:,:]*((stack_where>=nb_days)*stack_temp[day-(nb_days-1):day+1,:,:]==-9999)+(-9999*((stack_where<nb_days)*(stack_temp[day-(nb_days-1):day+1,:,:]==-9999))) #record the last four days for the corresponding scanning window
            date_format[year*92+day] = nc.stringtochar(np.array([calendar[year,day]], 'S10'))
            date_idx[year*92+day]=year*92+day
        output_var[year*92:(year+1)*92,:,:]=stack_temp[:,:,:]
    output_var[:] = ma.masked_outside(output_var[:],-300,400)
    time[:]=range(np.shape(output_var)[0])

    f.close()
    nc_file_out.close()
    
#%%
def cc3d_scan_heatwaves(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,run_animation=True, anomaly=True, relative_threshold=True):
    '''This function carries out a cc3d scan (https://pypi.org/project/connected-components-3d/) to detect heatwaves in the meteorological database (default ERA5, t2m, tg).
    The heatwaves point are labeled with a number corresponding to a heatwave identifier.
    Otherwise, values are set to -9999.
    The detection threshold depends on the parameters used precedently, which is why all the above parameters are required.
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m).'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)
    print('nb_days :',nb_days)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
    name_dict_threshold = {True : 'th', False : 'C'}
    
    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    dust_threshold = int(775 * (float(resolution_dict['ERA5'])/float(resolution))**2)
    #-------------------------------------
    #define pathway to temperature data
    nc_in_path = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_scaled_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    #Load temperature data file
    f=nc.Dataset(nc_in_path, mode='r')#load input file dimensions/variables
    lat_in=f.variables['lat'][:]
    lon_in=f.variables['lon'][:]
    time_in=f.variables['time'][:]
    date_idx_JJA = [int(i) for i in time_in.data]
    time_in = np.ndarray(shape=np.shape(date_idx_JJA),dtype=int)
    time_in[:] = date_idx_JJA[:]
    date_idx_all_year_in=f.variables['date_idx_all_year'][:]
    date_idx_all_year_in = [int(i) for i in date_idx_all_year_in.data]
    dates_all_all_year = np.ndarray(shape=np.shape(date_idx_all_year_in),dtype=int)
    dates_all_all_year[:] = date_idx_all_year_in[:]

    nc_file_potential_htws = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"potential_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")

    f_pot_htws=nc.Dataset(nc_file_potential_htws, mode='r')
    date_format=f_pot_htws.variables['date_format'][:] #date as a string, yyyy-mm-dd format
    date_format_readable = [""]*len(time_in)
    date_format_readable_year_only=[""]*len(time_in) #keep only the four characters of the date corresponding to the year
    print("Computing calendar...")
    for i in tqdm(range(len(date_format))) :
        date_format_readable[i] = "".join(date_format[:].astype(str).data[i])
        date_format_readable_year_only[i] = (date_format_readable[i])[:4]
    #define pathway to output netCDF file, no need to create directory.
    nc_out_path = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"detected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    #Create output netCDF file
    nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #mode='w' for 'write', 'a' for 'append'

    #Create output file dimensions
    nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
    nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
    nc_file_out.createDimension('time', 92*(year_end-year_beg+1)) # unlimited time axis (can be appended to).

    #Output file title and history for more detailed information (not necessary)
    nc_file_out.title=f"Labels of CC3D for {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} for JJA days from {year_beg} to {year_end}"
    nc_file_out.subtitle=f"values are set to zero not exceeding {threshold_value}{name_dict_threshold[relative_threshold]} {datavar} {name_dict_anomaly[anomaly]} threshold, and labels are assigned to contiguous elements." + f" The threshold is the {threshold_value}th percentile of the climatology distribution ({year_beg_climatology}-{year_end_climatology}, {distrib_window_size}-days centered window)."*relative_threshold + f" The threshold is {threshold_value}°C"*(1-relative_threshold)
    nc_file_out.history = "Created with run_all_detection_overlap_analysis.py on " +datetime.today().strftime("%d/%m/%y")

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
    date_idx_all_year = nc_file_out.createVariable('date_idx_all_year', np.int32,('time',))
    date_idx_all_year.units = f'days from 01-01-{year_beg}'
    date_idx_all_year.long_name = 'date_index_all_year'
    # Define a 3D variable to hold the data
    label = nc_file_out.createVariable('label',np.int32,('time','lat','lon')) # note: unlimited dimension is leftmost
    label.long_name = 'cc3d_label'

    #note : the [:] statements are necessary in these following statements. 
    #Otherwise, you do not write in the content of the netCDF dimension but only create another local variable.
    lat[:] = lat_in
    lon[:] = lon_in
    time[:]=range(92*(year_end-year_beg+1))
    date_idx_all_year[:]=date_idx_all_year_in
    f_land_sea_mask = nc.Dataset(os.path.join(datadir,database,"Mask",f"Mask_Europe_land_only_{database}_{resolution}deg.nc"),mode='r')
    land_sea_mask = f_land_sea_mask.variables['mask'][:]
    f_france_mask = nc.Dataset(os.path.join(datadir,database,"Mask",f"Mask_France_{database}_{resolution}deg.nc"),mode='r')
    france_mask = f_france_mask.variables['mask'][:]
    #creating a masked array full of -9999
    label[:] = ma.array(-9999*np.ones((len(time_in),len(lat_in),len(lon_in))),mask=[land_sea_mask]*(92*(year_end-year_beg+1))) #shape is time*lat*lon
    
    print("Computing cc3d.connected_components labels and dusting...")
    #nb_htws_list = [0]*30

    #for k in tqdm(range(30))  :
    N_labels=0 #count the numbers of patterns
    unique_htw_cc3d_idx = []

    for year in tqdm(range((year_end-year_beg+1))) :#iterate over the years

        sub_htws = ma.masked_where([land_sea_mask]*92,f_pot_htws.variables[datavar][year*92:(year+1)*92,:,:])
        sub_htws = ma.filled(sub_htws,fill_value=-9999)
        sub_htws = (sub_htws!=-9999)

        connectivity = 26 # only 4,8 (2D) and 26, 18, and 6 (3D) are allowed
        labels_in = cc3d.dust(sub_htws,dust_threshold)#25*k) #int(0.6*14*14*nb_days))
        labels_out, N_added = cc3d.connected_components(labels_in, connectivity=connectivity,return_N=True) #return the table of lables and the number of added patterns
        #update output netCDF variable :
        label[year*92:(year+1)*92,:,:] = ma.array(labels_out,mask=[land_sea_mask]*92)
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
    print(len(unique_htw_cc3d_idx),"heatwaves detected")
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
    #exit()
    df_htw = pd.DataFrame(columns=['Year','idx_beg_JJA','idx_end_JJA','idx_beg_all_year','idx_end_all_year'],index=unique_htw_cc3d_idx,data=None)
    #-------------------------------#
    # Make animations for heatwaves #
    #-------------------------------#
    #projection
    proj_pc = ccrs.PlateCarree() 
    lons_mesh = lon_in
    lats_mesh = lat_in
    lon_in=np.array(lon_in)
    lat_in=np.array(lat_in)

    title = f"{database} daily {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} (°C)"
    #load JJA temperature anomaly (or absolute values) data file
    nc_file_temp = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_climatology_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc")
    f_temp=nc.Dataset(nc_file_temp, mode='r')
    all_time_idx=[[-1]]*(len(unique_htw_cc3d_idx))
    matplotlib.use('Agg')
    output_dir_anim = os.path.join("Output",database,f"{datavar}_{daily_var}" ,
                            f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}", 
                            "animated_maps")
    pathlib.Path(output_dir_anim).mkdir(parents=True,exist_ok=True)

    for event in tqdm(unique_htw_cc3d_idx[:]):
        time_idx_var = [int(i) for i in np.unique(np.argwhere(label[:]==event)[:,0])]

        dates_JJA = time_in[time_idx_var]
        dates_all_year = dates_all_all_year[time_idx_var]
        df_htw.loc[event,'idx_beg_JJA'] = dates_JJA[0]
        df_htw.loc[event,'idx_end_JJA'] = dates_JJA[-1]
        df_htw.loc[event,'idx_beg_all_year'] = dates_all_year[0]
        df_htw.loc[event,'idx_end_all_year'] = dates_all_year[-1]
        df_htw.loc[event,'Year'] = int(year_beg+dates_JJA[0]//92) #year of the heatwave event

        if run_animation :
            var_scatter = label[time_idx_var,:,:] #all labels of the chosen period
            nb_frames = len(time_idx_var)
            var = ma.array(f_temp.variables[datavar][dates_JJA,:,:])
            var[:] = ma.masked_where([(land_sea_mask)>0]*nb_frames,var[:])
            min_val = min(np.floor(-np.abs(np.min(var))),np.floor(-np.abs(np.max(var))))
            max_val = max(np.ceil(np.abs(np.min(var))),np.ceil(np.abs(np.max(var)))) 
            
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
                ax.set_title(title, fontsize='x-large')
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
            filename_movie = os.path.join(output_dir_anim,
                                        f"Heatwave_n°{event}_{date_event[0]}_{date_event[-1]}_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.mp4")
            writervideo = animation.FFMpegWriter(fps=1)
            anim.save(filename_movie, writer=writervideo)
            plt.close()
        
        #all_time_idx[event]=list(dates_JJA.data)
    
    f.close()
    f_temp.close()
    f_land_sea_mask.close()
    nc_file_out.close()
    f_pot_htws.close()
    output_dir_df = os.path.join("Output",database,f"{datavar}_{daily_var}" ,
                            f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    df_htw.to_excel(os.path.join(output_dir_df,f"df_htws_V0_detected_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.xlsx"))
    return

#%%
def analyse_impact_overlap(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,flex_time_span=7, anomaly=True, relative_threshold=True):
    '''This function is used to analyse the spatial and temporal overlap between EM-DAT heatwaves and the meteorological database heatwaves (default ERA5) detected with the CC3D scan.
    The detection threshold depends on the parameters used precedently, which is why all these parameters are required.
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m)'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)
    print('nb_days :',nb_days)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
    name_dict_threshold = {True : 'th', False : 'C'}
    
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    df_emdat = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0)
    df_emdat = df_emdat[(df_emdat['Year']>=year_beg) & (df_emdat['Year']<=year_end)] #only keep events of the studied period (default 1950-2021)
    nc_file_in = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"detected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    f=nc.Dataset(nc_file_in,mode='r')
    time_in=f.variables['time'][:]
    date_idx_JJA = [int(i) for i in time_in.data]
    time_in = np.ndarray(shape=np.shape(date_idx_JJA),dtype=int)
    time_in[:] = date_idx_JJA[:]
    #Link EM-DAT country names format to netCDF mask country names format
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
    #indices of beggining and end of month for a JJA set of data (92 days from 1st June to 31st August)
    beg_month_only_idx_dict = {6:0,7:30,8:61} #30 days in June, 31 days in July and August
    end_month_only_idx_dict = {6:29,7:60,8:91} #30 days in June, 31 days in July and August
    
    ignored_events = ['1994-0759-ROU','2004-0361-SPI'] #'1994-0759-ROU' occured in May, '2004-0361-SPI' occured in Canary Island which is not in the studied area
    
    undetected_heatwaves = []
    detected_heatwaves = []
    for emdat_event in tqdm(df_emdat.index.values[:]) :
        if df_emdat.loc[emdat_event,'Dis No'] not in ignored_events :
            country=df_emdat.loc[emdat_event,'Country']
            f_mask=nc.Dataset(os.path.join(datadir, database,"Mask",f"Mask_{country_dict[country]}_{database}_{resolution}deg.nc"),mode='r')
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
    output_dir = os.path.join("Output",database,f"{datavar}_{daily_var}" ,
                            f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    pathlib.Path(output_dir).mkdir(parents=True,exist_ok=True)
    with open(os.path.join(output_dir,f"emdat_undetected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{threshold_value}{name_dict_threshold[relative_threshold]}_flex_time_{flex_time_span}_days.txt"), 'w') as output :
        for row in undetected_heatwaves:
            output.write(str(row) + '\n')
            
    with open(os.path.join(output_dir,f"emdat_detected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{threshold_value}{name_dict_threshold[relative_threshold]}_flex_time_{flex_time_span}_days.txt"), 'w') as output :
        for row in detected_heatwaves:
            output.write(str(row) + '\n')

    f.close()
    f_mask.close()
    return

#%%
def undetected_heatwaves_animation(database='ERA5', datavar='t2m', daily_var='tg', year_beg=1950, year_end=2021, threshold_value=95, year_beg_climatology=1950, year_end_climatology=2021, distrib_window_size=15,nb_days=4,flex_time_span=7, anomaly=True, relative_threshold=True):
    '''This function is used to create animated maps for the dates around which EM-DAT heatwaves are not detected in the meteorological database (default ERA5).
    The detection threshold depends on the parameters used precedently, which is why all the above parameters are required.
    This function can be used with several databases and variables : ERA5 (t2m, wbgt and utci) and E-OBS (t2m)'''

    print('database :',database)
    print('datavar :',datavar)
    print('daily_var :',daily_var)
    print('year_beg :',year_beg)
    print('year_end :',year_end)
    print('threshold_value :',threshold_value)
    print('year_beg_climatology :',year_beg_climatology)
    print('year_end_climatology :',year_end_climatology)
    print('nb_days :',nb_days)
    
    if os.name == 'nt' :
        datadir = "Data/"
    else : 
        datadir = os.environ["DATADIR"]
    
    name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
    name_dict_threshold = {True : 'th', False : 'C'}
    
    temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
    resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
    resolution = resolution_dict[database]
    
    #Link EM-DAT country names to cartopy country names for polygon plotting (2D maps)
    country_dict_cartopy = {'Albania':'Albania', 'Austria':'Austria', 'Belarus':'Belarus',
                    'Belgium':'Belgium', 'Bosnia and Herzegovina':'Bosnia and Herzegovina',
                    'Bulgaria':'Bulgaria', 'Canary Is':None, 'Croatia':'Croatia', 'Cyprus':'Cyprus', 
                    'Czech Republic (the)':'Czechia', 'Denmark':'Denmark', 'Estonia':'Estonia', 
                    'Finland':'Finland', 'France':'France', 'Germany':'Germany', 'Greece':'Greece', 
                    'Hungary':'Hungary', 'Iceland':'Iceland', 'Ireland':'Ireland', 
                    'Italy':'Italy', 'Latvia':'Latvia', 'Lithuania':'Lithuania',
                    'Luxembourg':'Luxembourg', 'Montenegro':'Montenegro',
                    'Macedonia (the former Yugoslav Republic of)':'North Macedonia',
                    'Moldova':'Moldova', 'Netherlands (the)':'Netherlands', 'Norway':'Norway', 
                    'Poland':'Poland','Portugal':'Portugal', 'Romania':'Romania',
                    'Russian Federation (the)':'Russia', 'Serbia':'Republic of Serbia', 
                    'Serbia Montenegro':'Republic of Serbia', #The corresponding heatwave happened in Serbia, cf 'Location' data of EM-DAT
                    'Slovakia':'Slovakia', 'Slovenia':'Slovenia', 'Spain':'Spain', 'Sweden':'Sweden',
                    'Switzerland':'Switzerland', 'Turkey':'Turkey',
                    'United Kingdom of Great Britain and Northern Ireland (the)':'United Kingdom',
                    'Ukraine':'Ukraine','Yugoslavia':'Republic of Serbia'} #The corresponding heatwave happened in Serbia, cf 'Location' data of EM-DAT
    resolution_cartopy = '10m'
    category = 'cultural'
    name = 'admin_0_countries'

    shpfilename = shapereader.natural_earth(resolution_cartopy, category, name)
    df_countries = geopandas.read_file(shpfilename)
    
    df_emdat = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0)
    # load cc3d labels netCDF file
    nc_file_in = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"detected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")

    f=nc.Dataset(nc_file_in,mode='r')
    lat_in=f.variables['lat'][:]
    lon_in=f.variables['lon'][:]
    time_in=f.variables['time'][:]
    date_idx_JJA = [int(i) for i in time_in.data]
    time_in = np.ndarray(shape=np.shape(date_idx_JJA),dtype=int)
    time_in[:] = date_idx_JJA[:]

    nc_file_potential_htws = os.path.join(datadir,database,datavar,"Detection_Heatwave",f"potential_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc")
    f_pot_htws=nc.Dataset(nc_file_potential_htws, mode='r')
    date_format=f_pot_htws.variables['date_format'][:] #date as a string, yyyy-mm-dd format
    date_format_readable = [""]*len(time_in)
    date_format_readable_year_only=[""]*len(time_in) #keep only the four characters of the date corresponding to the year
    print("Computing calendar...")
    for i in tqdm(range(len(date_format))) :
        date_format_readable[i] = "".join(date_format[:].astype(str).data[i])
        date_format_readable_year_only[i] = (date_format_readable[i])[:4]

    #Load ERA5 mask -> masked African and Middle-East countries, ocean and sea
    f_land_sea_mask = nc.Dataset(os.path.join(datadir,database,"Mask",f"Mask_Europe_land_only_{database}_{resolution}deg.nc"),mode='r')
    land_sea_mask = f_land_sea_mask.variables['mask'][:]
    #load JJA temperature anomaly data file
    nc_file_temp = os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_climatology_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc")
    f_temp=nc.Dataset(nc_file_temp, mode='r')
    # #indices of beggining and end of month for a JJA set of data (92 days from 1st June to 31st August)
    beg_month_only_idx_dict = {6:0,7:30,8:61} #30 days in June, 31 days in July and August
    end_month_only_idx_dict = {6:29,7:60,8:91} #30 days in June, 31 days in July and August
    # #Read txt file containing undetected heatwaves to create undetected heatwaves list
    output_dir = os.path.join("Output",database,f"{datavar}_{daily_var}" ,
                            f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}")
    with open(os.path.join(output_dir,f"emdat_undetected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{threshold_value}{name_dict_threshold[relative_threshold]}_flex_time_{flex_time_span}_days.txt"),'r') as f_txt:
        undetected_htw_list = f_txt.readlines()
    f_txt.close()
    # #Remove '\n' from strings
    for i in range(len(undetected_htw_list)) :
        undetected_htw_list[i] = undetected_htw_list[i][:-1]
    output_dir_anim = os.path.join("Output",database,f"{datavar}_{daily_var}" ,
                            f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}", 
                            f"maps_undetected_htws_flex_{flex_time_span}_ds")
    pathlib.Path(output_dir_anim).mkdir(parents=True,exist_ok=True)
    
    sub_df_emdat = df_emdat[df_emdat['Dis No'].isin(undetected_htw_list)]
    sub_df_emdat = sub_df_emdat.sort_values(by='Total Deaths',ascending=False)
    sub_df_emdat = sub_df_emdat.fillna(0)
    undetected_heatwaves_grouped=np.unique(sub_df_emdat.loc[:,'disasterno'])
    df_emdat_grouped = pd.DataFrame(index=undetected_heatwaves_grouped,columns=['Total Deaths','Affected Countries (Total Deaths)'])#'Affected Countries','Affected Countries (Total Deaths)'])
    htw_most_impact_df = pd.DataFrame(index=df_emdat_grouped.index,columns=['index','disasterno','country','Total Deaths'])
    count_iterations=0
    for label in df_emdat_grouped.index.values :
        #df_emdat_grouped.loc[label,'Affected Countries'] = ', '.join([country_dict_cartopy[ctry] for ctry in (sub_df_emdat[sub_df_emdat['disasterno']==label])['Country'].tolist()])
        df_emdat_grouped.loc[label,'Total Deaths'] = int((sub_df_emdat[sub_df_emdat['disasterno']==label])['Total Deaths'].sum())
        l1 = [country_dict_cartopy[ctry] for ctry in (sub_df_emdat[sub_df_emdat['disasterno']==label])['Country'].tolist()]
        l2 = [int (i) for i in (sub_df_emdat[sub_df_emdat['disasterno']==label])['Total Deaths'].tolist()]
        list = [f"{i} ({str(j)})" for (i,j) in zip(l1,l2)]
        if len(list) > 3 :
            list[3]='\\\\'+list[3]
            
        df_emdat_grouped.loc[label,'Affected Countries (Total Deaths)'] = ', '.join(list)
        htw_most_impact_df.loc[label,'index'] = (sub_df_emdat[sub_df_emdat['disasterno']==label])['Total Deaths'].idxmax()
        htw_most_impact_df.loc[label,'disasterno'] = sub_df_emdat.loc[(sub_df_emdat[sub_df_emdat['disasterno']==label])['Total Deaths'].idxmax(),'Dis No']
        htw_most_impact_df.loc[label,'country'] = l1[0]
        htw_most_impact_df.loc[label,'Total Deaths'] = np.sum(l2)
        count_iterations+=1
        
    df_emdat_grouped = df_emdat_grouped.sort_values(by='Total Deaths',ascending=False)
    htw_most_impact_df = htw_most_impact_df.sort_values(by='Total Deaths',ascending=False)
    plotted_htw_label = htw_most_impact_df['index'].iloc[0:3].values
    plotted_htw_var = [[],[],[]]
    plotted_htw_count = 0
    plotted_htw_country = ['','','']
    for i in range(3):
        country_list = df_emdat_grouped.iloc[i,1].split(", ")
        country_list[0] = "\\textbf{"+country_list[0]+"}"
        df_emdat_grouped.iloc[i,1] = ', '.join(country_list)
    for idx in tqdm(df_emdat.index.values) :
        if df_emdat.loc[idx,'Dis No'] in undetected_htw_list :
            country=df_emdat.loc[idx,'Country']
            year_event = df_emdat.loc[idx,'Year']
            labels_cc3d = f.variables['label'][(year_event-year_beg)*92:(year_event-year_beg+1)*92,:,:] #load all JJA cc3d label data for the given year
            temp = f_temp.variables[datavar][(year_event-year_beg)*92:(year_event-year_beg+1)*92,:,:]
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
            
            #-------------------------------#
            # Make animations for heatwaves #
            #-------------------------------#
            #projection
            proj_pc = ccrs.PlateCarree() 
            lons_mesh = lon_in
            lats_mesh = lat_in

            lon_in=np.array(lon_in)
            lat_in=np.array(lat_in)

            title = f"{database} daily {temp_name_dict[daily_var]} {datavar} {name_dict_anomaly[anomaly]} (°C).\nEM-DAT heatwave recorded in {country}."
            
            matplotlib.use('Agg')
            
            temp[:] = ma.masked_where([(land_sea_mask)>0]*(np.shape(temp)[0]),temp[:])
            nb_frames = np.shape(temp)[0]
            min_val = min(np.floor(-np.abs(np.min(temp))),np.floor(-np.abs(np.max(temp))))
            max_val = max(np.ceil(np.abs(np.min(temp))),np.ceil(np.abs(np.max(temp))))
            
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
                ax.set_title(title, fontsize='x-large')
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
                plt.title(f"Temperature {name_dict_anomaly[anomaly]} (°C) on {date_event[i]}",{'position':(0.5,-2)})
                return CS1

            def init():
                return draw(0)

            def update(i):
                return draw(i)


            anim = animation.FuncAnimation(fig, update, init_func=init, frames=nb_frames, blit=False, interval=0.15, repeat=False)

            plt.show()
            filename_movie = os.path.join(output_dir_anim, 
                                        f"Undetected_heatwave_{df_emdat.loc[idx,'Dis No']}_{date_event[0]}_{date_event[-1]}_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}_flex_time_{flex_time_span}_ds.mp4")
            writervideo = animation.FFMpegWriter(fps=1)
            anim.save(filename_movie, writer=writervideo)
            ax.clear()
            plt.close()
            # Make 2D map of the heatwave :
            fig_map = plt.figure(figsize=(24,16))
            ax_map = plt.axes(projection=proj_pc)
            ax.clear()
            ax_map.set_extent([lon_in[0]+0.1, lon_in[-1]-0.1, lat_in[-1]+0.1, lat_in[0]-0.1])
            title = f'Temperature {name_dict_anomaly[anomaly]} (°C) average between {date_event[0]} and {date_event[-1]}.\nEM-DAT heatwave recorded in {country}.'
            ax_map.set_title(title, fontsize=25)
            ax_map.add_feature(cfeature.BORDERS)
            ax_map.add_feature(cfeature.LAND)
            ax_map.add_feature(cfeature.OCEAN)
            ax_map.add_feature(cfeature.COASTLINE,linewidth=0.3)
            ax_map.add_feature(cfeature.LAKES, alpha=0.5)
            ax_map.add_feature(cfeature.RIVERS, alpha=0.5)
            new_var = np.nanmean(temp[:],axis=0)
            if idx in plotted_htw_label :
                dis_no = (htw_most_impact_df[htw_most_impact_df['index']==idx]).index.values[0]
                plotted_htw_count = int(np.argwhere(df_emdat_grouped.index==dis_no)[0][0])
                plotted_htw_var[plotted_htw_count] = new_var
                plotted_htw_country[plotted_htw_count] = (htw_most_impact_df[htw_most_impact_df['index']==idx])['country'].values[0]
            min_val = min(np.floor(-np.abs(np.min(new_var))),np.floor(-np.abs(np.max(new_var))))
            max_val = max(np.ceil(np.abs(np.min(new_var))),np.ceil(np.abs(np.max(new_var))))
            the_levels=[0]*11#nb of color categories + 1
            for k in range(len(the_levels)):
                the_levels[k]=min_val+k*(max_val-min_val)/(len(the_levels)-1)
            cax = plt.axes([0.35, 0.06, 0.35, 0.02])
            CS1 = ax_map.contourf(lons_mesh,lats_mesh,new_var,cmap='bwr',transform=proj_pc, levels=the_levels)
            cbar = fig_map.colorbar(CS1,cax=cax,ax=ax_map,orientation='horizontal')
            cbar.ax.tick_params(labelsize=20)
            ax.scatter(X_scatt[i],Y_scatt[i],marker='o',s=1,alpha=1,color='black',transform=proj_pc,zorder=100)
            poly = df_countries.loc[df_countries['ADMIN'] == country_dict_cartopy[country]]['geometry'].values[0]
            try :
                ax_map.plot(*poly.exterior.xy,'green',linewidth=3)
            except :#in case the country is not Polygon but MultiPolygon
                for geom in poly.geoms :
                    ax_map.plot(*geom.exterior.xy,'green',linewidth=3)
            plt.title(f'Temperature {name_dict_anomaly[anomaly]} (°C) average between {date_event[0]} and {date_event[-1]}',{'position':(0.5,-2)})
            plt.savefig(os.path.join(output_dir_anim,f"Undetected_htw_{df_emdat.loc[idx,'Dis No']}_{date_event[0]}_{date_event[-1]}.png"))
            plt.close()
    
    # Make 3maps+table plot
    plt.rcParams['text.usetex'] = True
    fig_subplot = plt.figure(figsize=(16,12))
    ax1=fig_subplot.add_subplot(234,projection=ccrs.PlateCarree()).set_title('\\textbf{b}',loc='left')
    ax2=fig_subplot.add_subplot(235,projection=ccrs.PlateCarree()).set_title('\\textbf{c}',loc='left')
    ax3=fig_subplot.add_subplot(236,projection=ccrs.PlateCarree()).set_title('\\textbf{d}',loc='left')
    ax4=fig_subplot.add_subplot(211).set_title('\\textbf{a}',loc='left')
    ax_count=0
    min_val=0
    max_val=0
    for ax in [ax1.axes,ax2.axes,ax3.axes] :
        new_var = plotted_htw_var[ax_count]
        min_val = min(min_val,min(np.floor(-np.abs(np.min(new_var))),np.floor(-np.abs(np.max(new_var)))))
        max_val = max(max_val,max(np.ceil(np.abs(np.min(new_var))),np.ceil(np.abs(np.max(new_var)))))
        ax_count+=1
        
    the_levels=[0]*11#nb of color categories + 1
    for k in range(len(the_levels)):
        the_levels[k]=min_val+k*(max_val-min_val)/(len(the_levels)-1)
    ax_count=0 
    for ax in [ax1.axes,ax2.axes,ax3.axes] :
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.COASTLINE,linewidth=0.3)
        ax.add_feature(cfeature.LAKES, alpha=0.5)
        ax.add_feature(cfeature.RIVERS, alpha=0.5)
        new_var = plotted_htw_var[ax_count]
        country = plotted_htw_country[ax_count]
        CS1 = ax.contourf(lons_mesh,lats_mesh,new_var,cmap='bwr',transform=proj_pc, levels=the_levels)
        #ax.scatter(X_scatt[i],Y_scatt[i],marker='o',s=1,alpha=1,color='black',transform=proj_pc,zorder=100)
        poly = df_countries.loc[df_countries['ADMIN'] == country]['geometry'].values[0]
        try :
            ax.plot(*poly.exterior.xy,'green',linewidth=3)
        except :#in case the country is not Polygon but MultiPolygon
            for geom in poly.geoms :
                ax.plot(*geom.exterior.xy,'green',linewidth=3)
        ax.set_extent([poly.bounds[0]-0.1,poly.bounds[2]+0.1,poly.bounds[1]-0.1,poly.bounds[3]+0.1])
        ax_count+=1
    cax = plt.axes([0.2, 0.1, 0.6, 0.025])
    cbar = fig_subplot.colorbar(CS1,cax=cax,orientation='horizontal')
    cbar.set_label('Average of daily maximum WBGT anomaly (°C)', rotation=0, size=25)
    cbar.ax.tick_params(labelsize=20)
    
    table = ax4.axes.table(cellText=df_emdat_grouped.values,
            rowLabels=df_emdat_grouped.index,
            colLabels=df_emdat_grouped.columns,loc='center',cellLoc='center',colWidths=[0.15,0.5])
    cellDict = table.get_celld()
    for i in range(0,len(df_emdat_grouped.columns)):
        cellDict[(0,i)].set_height(.1)
        #cellDict[(0,i)].set_text_props(ha="center")
        cellDict[(1,i)].set_height(4.2/30)
        for j in range(2,len(df_emdat_grouped.values)+1):
            cellDict[(j,i)].set_height(2.1/30)
            #cellDict[(j,i)].set_text_props(ha="left")
            if i==0 :
                cellDict[(j,-1)].set_height(2.1/30)
    #for i in range(-1,len(df_emdat_grouped.columns)):
    #    for j in range(1,4):
    #        cellDict[(j,i)].set_text_props(fontproperties=FontProperties(weight='bold'))
    cellDict[(0, 0)].set_facecolor("lightgray")
    cellDict[(0, 1)].set_facecolor("lightgray")
    cellDict[(1,-1)].set_height(4.2/30)
    ax4.axes.set_axis_off()
    table.auto_set_font_size(False)
    table.set_fontsize(15)
    plt.savefig(os.path.join(output_dir_anim,f"Undetected_htw_subplots.pdf"),dpi=1200)
    plt.close()
    f_land_sea_mask.close()
    f.close()
    f_temp.close()
    return