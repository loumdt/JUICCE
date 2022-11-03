filename = 'tx_EUR_JJA.nc'
var = ncread(filename,'tx');
lat = ncread(filename,'latitude');
lon = ncread(filename,'longitude');
temps = ncread(filename,'time');
var_name = ncreadatt(filename,'tx','long_name');
var_unit = ncreadatt(filename,'tx','units');
save -v7.3 /home/ajeze/Documents/DetectionCanicule/tx lat lon temps var var_name var_unit
