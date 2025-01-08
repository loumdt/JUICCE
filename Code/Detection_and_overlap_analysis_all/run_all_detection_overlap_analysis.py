#%%
import numpy as np #basic math operators and optimized handle of arrays
import numpy.ma as ma #use masked array
import netCDF4 as nc #load and write netcdf data
from datetime import datetime #create file history with creation date
from tqdm import tqdm #create a user-friendly feedback while script is running
import sys,os #read inputs
import pandas as pd #handle dataframes
import pathlib #check existence and create folders

from detection_overlap_functions import *
from analysis_classification_plot_functions import *
#%%
# wbgt absolute thresholds : [33,30,26,28,25]
# utci absolute thresholds : [26,32,38,46]
# t2m absolute thresholds : [25,20]
database = 'ERA5' # 'ERA5' or 'E-OBS', default value is 'ERA5'
datavar = 't2m' # 't2m', 'wbgt' or 'utci' for ERA5 ; 't2m' for 'E-OBS', default value is 't2m'
daily_var = 'tx' # 'tg', 'tn' or 'tx' (mean, min, max), default value is 'tg'
year_beg = 1950 #beginning of the studied period, default 1950
year_end = 2021 #end of the studied period, default 2021

year_beg_climatology = 1950 #beginning of the climatology period, default 1950
year_end_climatology = 2021 #end of the climatology period, default 2021

anomaly = True #If True, the whole process is based on anomalies and not absolute values of temperature. If False, absolute values are used. Default is True

nb_days = 4 #nb of days used as a heatwave duration threshold, default value is 4
relative_threshold = True #If True, the threshold value should be a percentile and locally defined. If False, the threshold should be an absolute value. Default is True
threshold_value = 95 # If relative_threshold is True, percentile used as a threshold for heatwave occurence, value in ]0;100[, default value is 95 (consistent with default value of relative_threshold). If absolute value, expected to be a value in °C.
distrib_window_size = 15 #size (in days) of the temporal window that is used to compute the temperature distribution (on which is based the threshold) of each calendar day, default value is 15
run_animation=True
flex_time_span = 7 #In order to account for potential EM-DAT imprecisions, set a flexibility window of flex_time_span days, default value is 7

name_dict_anomaly = {True : 'anomaly', False : 'absolute'}
name_dict_threshold = {True : 'th', False : 'C'} #If relative threshold, value is a percentile; if absolute threshold, value is in °C

datadir = "Data/"
resolution_dict = {"ERA5" : "0.25", "E-OBS" : "0.1"}
resolution = resolution_dict[database]

count_all_impacts=True
#normalize_impact_country=False
#normalize_impact_affected_region=False

nb_top_events=10 #number of top detected events to look for in the litterature

if distrib_window_size%2==0:
    raise ValueError('distrib_window_size is even. It has to be odd so the window can be centered on the computed day.')
if relative_threshold==False and anomaly==True:
    raise ValueError("Using an absolute threshold can only work by working on absolute values, and not anomalies. The parameter 'anomaly' should be set to False.")
if relative_threshold==False and threshold_value>=60 and threshold_value<100 :
    raise ValueError("It seems that the value given for the threshold is a percentile and not an absolute value, but the parameter 'relative_threshold' is set to False.")

overwrite_files=False #If True, overwrite output files that already exists (may be relevant in case of code or data update)
# if overwrite_file is True or if output file does not exist : call function ; else pass
if (overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_daily_avg_{year_beg_climatology}_{year_end_climatology}_smoothed.nc"))==False) and anomaly==True: #Only used for anomaly computation
    print("\n Running compute_climatology_smooth... \n")
    compute_climatology_smooth(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology)

if (overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{year_beg_climatology}_{year_end_climatology}_{threshold_value}th_threshold_{distrib_window_size}days.nc"))==False) and relative_threshold==True :#Only used for relative thresholds
    print("\n Running compute_distrib_percentile... \n")
    compute_distrib_percentile(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, anomaly=anomaly)

if overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{year_beg}_{year_end}_scaled_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc"))==False :
    print("\n Running select_scale_jja... \n")
    select_scale_jja(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size,anomaly=anomaly, relative_threshold=relative_threshold)

if overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,"Detection_Heatwave",f"potential_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc"))==False :
    print("\n Running detect_potential_heatwaves... \n")
    detect_potential_heatwaves(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, nb_days=nb_days, anomaly=anomaly, relative_threshold=relative_threshold)

if overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,"Detection_Heatwave",f"detected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}.nc"))==False :
    print("\n Running cc3d_scan_heatwaves... \n")
    cc3d_scan_heatwaves(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, nb_days=nb_days, run_animation=run_animation, anomaly=anomaly, relative_threshold=relative_threshold)

if overwrite_files or os.path.exists(os.path.join("Output",database,f"{datavar}_{daily_var}" ,f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}",f"emdat_detected_heatwaves_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{threshold_value}{name_dict_threshold[relative_threshold]}_flex_time_{flex_time_span}_days.txt"))==False :
    print("\n Running analyse_impact_overlap... \n")
    analyse_impact_overlap(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, nb_days=nb_days, flex_time_span=flex_time_span, anomaly=anomaly, relative_threshold=relative_threshold)

if overwrite_files or os.path.exists(os.path.join("Output",database,f"{datavar}_{daily_var}",f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}",f"maps_undetected_htws_flex_{flex_time_span}_ds"))==False :
    print("\n Running undetected_heatwaves_animation... \n")
    undetected_heatwaves_animation(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, nb_days=nb_days, flex_time_span=flex_time_span, anomaly=anomaly, relative_threshold=relative_threshold)

#compute 25th and 75th distribution percentile for Russo_HWMId calculation.
if overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{year_beg_climatology}_{year_end_climatology}_{25}th_threshold_{distrib_window_size}days.nc"))==False :
    print("\n Running compute_distrib_ano_percentile... \n")
    compute_distrib_percentile(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=25, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, anomaly=anomaly)
if overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,f"distrib_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{year_beg_climatology}_{year_end_climatology}_{75}th_threshold_{distrib_window_size}days.nc"))==False :
    print("\n Running compute_distrib_ano_percentile... \n")
    compute_distrib_percentile(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=75, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, anomaly=anomaly)
if overwrite_files or os.path.exists(os.path.join(datadir,database,datavar,f"Russo_HWMId_{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_{year_beg_climatology}_{year_end_climatology}_{distrib_window_size}days.nc.nc"))==False :
    print("\n Running compute_Russo_HWMId... \n")
    compute_Russo_HWMId(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size, anomaly=anomaly)

if overwrite_files or os.path.exists(os.path.join("Output",database,f"{datavar}_{daily_var}",f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}",f"df_htws_detected{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"))==False :
    print("\n Running create_heatwaves_indices_database... \n")
    create_heatwaves_indices_database(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size,count_all_impacts=count_all_impacts, anomaly=anomaly, relative_threshold=relative_threshold)#,normalize_impact_country=normalize_impact_country,normalize_impact_affected_region=normalize_impact_affected_region)

if overwrite_files or os.path.exists(os.path.join("Output",database,f"{datavar}_{daily_var}",f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}",f"df_scores{'_count_all_impacts'*(count_all_impacts)}_flex_time_span_{flex_time_span}_days.xlsx"))==False :
    print("\n Running compute_heatwaves_indices_scores... \n")
    compute_heatwaves_indices_scores(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size,count_all_impacts=count_all_impacts, anomaly=anomaly, relative_threshold=relative_threshold)#,normalize_impact_country=normalize_impact_country,normalize_impact_affected_region=normalize_impact_affected_region)

if overwrite_files or os.path.exists(os.path.join("Output",database,f"{datavar}_{daily_var}",f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}",f"figs_flex_time_span_{flex_time_span}",f"distrib{'_count_all_impacts'*count_all_impacts}"))==False :
    print("\n Running plot_heatwaves_distribution... \n")
    plot_heatwaves_distribution(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size,count_all_impacts=count_all_impacts, anomaly=anomaly, relative_threshold=relative_threshold)#,normalize_impact_country=normalize_impact_country,normalize_impact_affected_region=normalize_impact_affected_region)

if overwrite_files or os.path.exists(os.path.join("Output",database,f"{datavar}_{daily_var}",f"{database}_{datavar}_{daily_var}_{name_dict_anomaly[anomaly]}_JJA_{nb_days}days_before_scan_{year_beg}_{year_end}_{threshold_value}{name_dict_threshold[relative_threshold]}_{distrib_window_size}days_window_climatology_{year_beg_climatology}_{year_end_climatology}",f"top_{nb_top_events}_events_overlap{'_count_all_impacts'*count_all_impacts}_flex_time_{flex_time_span}days.xlsx"))==False :
    print("\n Running analysis_top_detected_events... \n")
    analysis_top_detected_events(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, year_beg_climatology=year_beg_climatology, year_end_climatology=year_end_climatology, distrib_window_size=distrib_window_size,count_all_impacts=count_all_impacts,nb_top_events=nb_top_events, anomaly=anomaly, relative_threshold=relative_threshold)#,normalize_impact_country=normalize_impact_country,normalize_impact_affected_region=normalize_impact_affected_region)