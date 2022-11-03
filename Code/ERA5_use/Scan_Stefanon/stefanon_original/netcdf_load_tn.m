filename = 'tn_EUR_MJJAS.nc'
var = ncread(filename,'tn');
lat = ncread(filename,'latitude');
lon = ncread(filename,'longitude');
temps = ncread(filename,'time');
var_name = ncreadatt(filename,'tn','long_name');
var_unit = ncreadatt(filename,'tn','units');
save -v7.3 /home/ajeze/Documents/DetectionCanicule/tn lat lon temps var var_name var_unit
