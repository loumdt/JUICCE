#%%
import netCDF4 as nc
import pandas as pd
import numpy as np
import numpy.ma as ma
import pathlib
import sys,os
from tqdm import tqdm
#%% #Link WorldBank country names format to netCDF mask country names format
country_dict = {'Albania': 'Albania',
 'Austria': 'Austria',
 'Belarus': 'Belarus',
 'Belgium': 'Belgium',
 'Bosnia_and_Herzegovina': 'Bosnia and Herzegovina',
 'Bulgaria': 'Bulgaria',
 'Croatia': 'Croatia',
 'Cyprus': 'Cyprus',
 'Czechia': 'Czechia',
 'Denmark': 'Denmark',
 'Estonia': 'Estonia',
 'Finland': 'Finland',
 'France': 'France',
 'Germany': 'Germany',
 'Greece': 'Greece',
 'Hungary': 'Hungary',
 'Iceland': 'Iceland',
 'Ireland': 'Ireland',
 'Italy': 'Italy',
 'Latvia': 'Latvia',
 'Lithuania': 'Lithuania',
 'Luxembourg': 'Luxembourg',
 'Montenegro': 'Montenegro',
 'Macedonia': 'North Macedonia',
 'Moldova': 'Moldova',
 'Netherlands': 'Netherlands',
 'Norway': 'Norway',
 'Poland': 'Poland',
 'Portugal': 'Portugal',
 'Romania': 'Romania',
 'Russia': 'Russian Federation',
 'Serbia': 'Serbia',
 'Slovakia': 'Slovak Republic',
 'Slovenia': 'Slovenia',
 'Spain': 'Spain',
 'Sweden': 'Sweden',
 'Switzerland': 'Switzerland',
 'Turkey': 'Turkiye',
 'United_Kingdom': 'United Kingdom',
 'Ukraine': 'Ukraine'}
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
try : 
    year_beg = int(sys.argv[1])
except :
    year_beg = 1950
    
try : 
    year_end = int(sys.argv[2])
except :
    year_end = 2021
#%%
df_gdp_cap_WorldBank = pd.read_excel(os.path.join(datadir,"WorldBank","GDP_cap_world_1960_2021_constant$_2015.xlsx"),header=3,index_col=0)

#%%
f_land_sea_mask = nc.Dataset(os.path.join(datadir,"E-OBS","Mask","Mask_Europe_E-OBS_0.1deg.nc"),mode='r')
land_sea_mask = f_land_sea_mask.variables['mask'][:]
lat_in = f_land_sea_mask.variables['lat'][:]
lon_in = f_land_sea_mask.variables['lon'][:]
#%%
#-------------------------------------
#Define netCDF output file :
nc_out_path = os.path.join(datadir,"E-OBS","Socio_eco_maps","GDP_cap_E-OBS_Europe_0.1deg.nc")
pathlib.Path(nc_out_path).parents[0].mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary
nc_file_out=nc.Dataset(nc_out_path,mode='w',format='NETCDF4_CLASSIC') #path to the output netCDF file

lat_dim = nc_file_out.createDimension('lat', len(lat_in))    # latitude axis
lon_dim = nc_file_out.createDimension('lon', len(lon_in))    # longitude axis
time_dim = nc_file_out.createDimension('time', None) # unlimited axis (can be appended to).

nc_file_out.title="Yearly GDP per capita for period "+str(year_beg)+"-"+str(year_end)+" according to WorldBank data"
nc_file_out.subtitle="When missing value, looking for nearest (in time) available value"

lat = nc_file_out.createVariable('lat', np.float32, ('lat',))
lat.units = 'degrees_north'
lat.long_name = 'latitude'
lon = nc_file_out.createVariable('lon', np.float32, ('lon',))
lon.units = 'degrees_east'
lon.long_name = 'longitude'
time = nc_file_out.createVariable('time', np.int32, ('time',))
time.units = 'days of a bisextile year'
time.long_name = 'time'
# Define a 3D variable to hold the data
gdp_cap = nc_file_out.createVariable('gdp_cap',np.float32,('time','lat','lon')) # note: unlimited dimension is leftmost
gdp_cap.units = '2015_US$' # 2015 US$
gdp_cap.long_name = 'GDP per capita'
gdp_cap.standard_name = 'gdp_cap' # this is a CF standard name
#%%
# Write latitudes, longitudes.
# Note: the ":" is necessary in these "write" statements -> you want to write the content and not to change the definition of the dimension
lat[:] = lat_in[:] 
lon[:] = lon_in[:]
time[:]=range(year_beg,year_end+1)
#%%
gdp_cap[:,:,:]=ma.array(np.zeros((len(time),len(lat_in),len(lon_in))),mask=False) #set output netcdf variable

#%%
for country in tqdm(country_dict.keys()):
    f_mask=nc.Dataset(os.path.join(datadir, "E-OBS","Mask","Mask_"+country+"_E-OBS_0.1deg.nc"),mode='r')
    mask_country = f_mask.variables['mask'][:,:]
    for year in time :
        year=int(year)
        try :
            gdp_cap_value = df_gdp_cap_WorldBank.loc[country_dict[country],str(year)]
        except :
            pass
        i=1
        while 'gdp_cap_value' not in locals() or np.isnan(gdp_cap_value) :
            try :
                gdp_cap_value = df_gdp_cap_WorldBank.loc[country_dict[country],str(year-i)]
            except :
                pass
            try :
                gdp_cap_value = df_gdp_cap_WorldBank.loc[country_dict[country],str(year+i)]
            except :
                pass
            i+=1
        gdp_cap[year-year_beg,:,:]=gdp_cap[year-year_beg,:,:]+gdp_cap_value*(mask_country==0)
        del(gdp_cap_value)