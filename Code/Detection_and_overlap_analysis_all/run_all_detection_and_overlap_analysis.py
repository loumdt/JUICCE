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

database = 'ERA5' # 'ERA5' or 'E-OBS', default value is 'ERA5'
datavar = 't2m' # 't2m', 'wbgt' or 'utci' for ERA5 ; 't2m' for 'E-OBS', default value is 't2m'
daily_var = 'tg' # 'tg', 'tn' or 'tx' (mean, min, max), default value is 'tg'
year_beg = 1950 #beginning of the studied period, default 1950
year_end = 2021 #end of the studied period, default 2021
nb_days = 4 #nb of days used as a heatwave duration threshold, default value is 4
threshold_value = 95 #percentile used as a threshold for heatwave occurence, value in ]0;100[, default value is 95
threshold_window_size = 15 #size (in days) of the temporal window that is used to compute the temperature distribution (on which is based the threshold) of each calendar day, default value is 15
historical_climatology_only = False #set on True if you want only 1950-1980 climatology, False if you want the climatology to end same as the studied period. default value is False
start_study_period_later=False #set on True if the studied period starts later than the climatology period, False if they start on the same year. default value is False
run_animation=True
flex_time_span = 7 #In order to account for potential EM-DAT imprecisions, set a flexibility window of flex_time_span days, default value is 7

#overwrite_files=True

compute_climatology_smooth(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, historical_climatology=historical_climatology_only)

compute_distrib_ano_percentile(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, historical_climatology=historical_climatology_only, year_beg_later=start_study_period_later, threshold_window_size=threshold_window_size)

select_ano_scale_jja(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, historical_climatology=historical_climatology_only, year_beg_later=start_study_period_later, threshold_window_size=threshold_window_size)

detect_potential_heatwaves(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, historical_climatology=historical_climatology_only, year_beg_later=start_study_period_later, threshold_window_size=threshold_window_size, nb_days=nb_days)

cc3d_scan_heatwaves(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, historical_climatology=historical_climatology_only, year_beg_later=start_study_period_later, threshold_window_size=threshold_window_size, nb_days=nb_days, run_animation=run_animation)

analyse_impact_overlap(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, historical_climatology=historical_climatology_only, year_beg_later=start_study_period_later, threshold_window_size=threshold_window_size, nb_days=nb_days, flex_time_span=flex_time_span)

undetected_heatwaves_animation(database=database, datavar=datavar, daily_var=daily_var, year_beg=year_beg, year_end=year_end, threshold_value=threshold_value, historical_climatology=historical_climatology_only, year_beg_later=start_study_period_later, threshold_window_size=threshold_window_size, nb_days=nb_days, flex_time_span=flex_time_span)

count_all_impacts=True
normalize_impact_country=False
normalize_impact_affected_region=False