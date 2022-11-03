filename = 'D:/Ubuntu/PFE/Data/E-OBS/0.1deg/temp_anomaly_summer_only_1950-2020.nc'
var = ncread(filename,'temp');
lat = ncread(filename,'lat');
lon = ncread(filename,'lon');
temps = ncread(filename,'time');
var_name = ncreadatt(filename,'temp','long_name');
var_unit = ncreadatt(filename,'temp','units');
save -v7.3 D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/tg_ano_JJA lat lon temps var var_name var_unit