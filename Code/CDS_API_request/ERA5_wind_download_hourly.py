import cdsapi
import sys,os

client = cdsapi.Client()
## Output
y = sys.argv[1]
pout = os.path.join( os.environ["DATADIR"] , "ERA5" , "WBGT" , y)
if not os.path.isdir(pout):
    os.makedirs(pout)
fout = f"ERA5_Europe_025deg_hourly_U_wind_{y}010100-{y}123123.nc"

name = 'reanalysis-era5-single-levels'

request_Uwind = {
    'product_type': 'reanalysis',
    'format': 'netcdf',
    'variable': '10m_u_component_of_wind',
    'year': y,
    'month': [
        '01', '02', '03',
        '04', '05', '06',
        '07', '08', '09',
        '10', '11', '12',
    ],
    'day': [
        '01', '02', '03',
        '04', '05', '06',
        '07', '08', '09',
        '10', '11', '12',
        '13', '14', '15',
        '16', '17', '18',
        '19', '20', '21',
        '22', '23', '24',
        '25', '26', '27',
        '28', '29', '30',
        '31',
    ],
    'time': [
        '00:00', '01:00', '02:00',
        '03:00', '04:00', '05:00',
        '06:00', '07:00', '08:00',
        '09:00', '10:00', '11:00',
        '12:00', '13:00', '14:00',
        '15:00', '16:00', '17:00',
        '18:00', '19:00', '20:00',
        '21:00', '22:00', '23:00',
    ],
    'area': [71.5,-12.5,30,45,],
}
## Download U wind
client.retrieve(name = name , request = request_Uwind, target = os.path.join( pout , fout ))


fout = f"ERA5_Europe_025deg_hourly_V_wind_{y}010100-{y}123123.nc"
request_Vwind = {
    'product_type': 'reanalysis',
    'format': 'netcdf',
    'variable': '10m_v_component_of_wind',
    'year': y,
    'month': [
        '01', '02', '03',
        '04', '05', '06',
        '07', '08', '09',
        '10', '11', '12',
    ],
    'day': [
        '01', '02', '03',
        '04', '05', '06',
        '07', '08', '09',
        '10', '11', '12',
        '13', '14', '15',
        '16', '17', '18',
        '19', '20', '21',
        '22', '23', '24',
        '25', '26', '27',
        '28', '29', '30',
        '31',
    ],
    'time': [
        '00:00', '01:00', '02:00',
        '03:00', '04:00', '05:00',
        '06:00', '07:00', '08:00',
        '09:00', '10:00', '11:00',
        '12:00', '13:00', '14:00',
        '15:00', '16:00', '17:00',
        '18:00', '19:00', '20:00',
        '21:00', '22:00', '23:00',
    ],
    'area': [71.5,-12.5,30,45,],
}
## Download V_wind
client.retrieve(name = name , request = request_Vwind, target = os.path.join( pout , fout ))