#!/usr/bin/env python3

#############################
## Yoann Robin             ##
## yoann.robin.k@gmail.com ##
#############################

import sys,os
import cdsapi


if __name__ == "__main__":
	
	## Parameters
	y     = sys.argv[1]
	year  = [y]
	area  = [71.5,-12.5,30,45,] #download European data (no Iceland)
	month = [ "{:{fill}{align}{n}}".format( m + 1 , fill = "0" , align = ">" , n = 2 ) for m in range(12) ]
	day   = [ "{:{fill}{align}{n}}".format( d + 1 , fill = "0" , align = ">" , n = 2 ) for d in range(31) ]
	time  = [ "{:{fill}{align}{n}}:00".format( t  , fill = "0" , align = ">" , n = 2 ) for t in range(24) ]
	
	## CDS parameter
	name = 'reanalysis-era5-pressure-levels' #can be found on CDS request form
	
	request = { 'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': 'geopotential',
            'pressure_level': '500',
            'year': year,
            'month': month,
            'day': day,
            'time': time,
            'area': area
            }
	
	## Output
	pout = os.path.join( os.environ["DATADIR"] , "ERA5" , "z500" , os.environ["YEAR"])
	if not os.path.isdir(pout):
		os.makedirs(pout)
	fout = f"ERA5_Global_025deg_hour_z500_{y}010100-{y}123123.nc"
	
	## Download
	client = cdsapi.Client()
	client.retrieve( name = name , request = request , target = os.path.join( pout , fout ) )
	
