import cdsapi
import sys,os

c = cdsapi.Client()

## Output
y = sys.argv[1]
pout = os.path.join( os.environ["DATADIR"] , "ERA5" , "WBGT")
if not os.path.isdir(pout):
    os.makedirs(pout)
fout = f"ERA5_Global_025deg_hourly_MRT_{y}0101-{y}1231.tar.gz"

## CDS parameter
#name = 'reanalysis-era5-pressure-levels' #can be found on CDS request form
name = 'derived-utci-historical'

request = {'variable': 'mean_radiant_temperature',
    'version': '1_1',
    'product_type': 'consolidated_dataset',
    'format': 'tgz',
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
        ]
    }

## Download
client = cdsapi.Client()
client.retrieve(name = name , request = request, target = os.path.join( pout , fout ) )