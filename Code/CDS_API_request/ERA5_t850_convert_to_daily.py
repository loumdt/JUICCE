#!/usr/bin/env python3

#############################
## Yoann Robin             ##
## yoann.robin.k@gmail.com ##
#############################

import sys,os
import datetime as dt

import numpy  as np
import pandas as pd
import xarray as xr


if __name__ == "__main__":
	
	## Parameters
	pin  = os.path.join( os.environ["DATADIR"] , "ERA5" , "t850" , os.environ["YEAR"])
	pout = os.path.join( os.environ["DATADIR"] , "ERA5" , "t850" , os.environ["YEAR"])
	
	## List files
	lfiles = os.listdir(pin)
	lfiles.sort()
	
	## Loop
	for f in lfiles:
		
		## Load hourly data
		idata = xr.open_dataset( os.path.join( pin , f ) )
		
		## Time axis
		year  = f.split("_")[-1][:4]
		timeh = idata.time
		timed = pd.date_range( f"{year}-01-01" , f"{year}-12-31" , freq = "d" )
		
		## Reformat the grid
		lat   = idata.latitude.values
		lon   = idata.longitude.values
		ilat  = np.argsort(lat)
		ilon  = np.argsort(lon)
		
		lat = lat[ilat]
		lon = lon[ilon]
		
		## Reformat data
		t850h = xr.DataArray( idata.t.values[:,ilat,:][:,:,ilon] , dims = ["time","lat","lon"] , coords = [timeh,lat,lon] )
		t850d = t850h.groupby("time.dayofyear").mean().rename( dayofyear = "time" ).assign_coords( time = timed )
		
		## Output
		odatah = xr.Dataset( { "t850" : t850h } )
		odatad = xr.Dataset( { "t850" : t850d } )
		
		## Add attributes
		odatah["time"].attrs["standard_name"] = "time"
		odatah["time"].attrs["long_name"]     = "Time axis"
		odatah["time"].attrs["axis"]          = "T"
		
		odatad["time"].attrs["standard_name"] = "time"
		odatad["time"].attrs["long_name"]     = "Time axis"
		odatad["time"].attrs["axis"]          = "T"
		
		odatah["lat"].attrs["standard_name"] = "latitude"
		odatah["lat"].attrs["long_name"]     = "latitude coordinate"
		odatah["lat"].attrs["units"]         = "degrees_north"
		odatah["lat"].attrs["axis"]          = "Y"
		
		odatad["lat"].attrs["standard_name"] = "latitude"
		odatad["lat"].attrs["long_name"]     = "latitude coordinate"
		odatad["lat"].attrs["units"]         = "degrees_north"
		odatad["lat"].attrs["axis"]          = "Y"
		
		odatah["lon"].attrs["standard_name"] = "longitude"
		odatah["lon"].attrs["long_name"]     = "longitude coordinate"
		odatah["lon"].attrs["units"]         = "degrees_east"
		odatah["lon"].attrs["axis"]          = "X"
		
		odatad["lon"].attrs["standard_name"] = "longitude"
		odatad["lon"].attrs["long_name"]     = "longitude coordinate"
		odatad["lon"].attrs["units"]         = "degrees_east"
		odatad["lon"].attrs["axis"]          = "X"
		
		odatah["t850"].attrs["coordinates"]   = "lat lon"
		odatah["t850"].attrs["standard_name"] = "t850"
		odatah["t850"].attrs["long_name"]     = "850 hPa temperature"
		odatah["t850"].attrs["units"]         = "K"
		
		odatad["t850"].attrs["coordinates"]   = "lat lon"
		odatad["t850"].attrs["standard_name"] = "t850"
		odatad["t850"].attrs["long_name"]     = "850 hPa temperature"
		odatad["t850"].attrs["units"]         = "K"
  

		product = 'reanalysis-era5-pressure-levels'
		
		odatah.attrs["title"]         = "ERA5"
		odatah.attrs["Conventions"]   = "CF-1.6"
		odatah.attrs["source"]        = "Climate Data Store"
		odatah.attrs["product"]       = product
		odatah.attrs["creation_date"] = str(dt.datetime.utcnow())[:19] + " (UTC)"
		
		odatad.attrs["title"]         = "ERA5"
		odatad.attrs["Conventions"]   = "CF-1.6"
		odatad.attrs["source"]        = "Climate Data Store"
		odatad.attrs["product"]       = product
		odatad.attrs["creation_date"] = str(dt.datetime.utcnow())[:19] + " (UTC)"
		
		## Encoding
		ny = lat.size
		nx = lon.size
		encodingh = { "time" : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (1,) , "units" : "hours since 1850-01-01 00:00:00" } ,
					  "lon"  : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (nx,) } ,
					  "lat"  : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (ny,) } ,
					  "t850"  : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (1,ny,nx) } }
		encodingd = { "time" : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (1,) , "units" : "days since 1850-01-01 00:00:00" } ,
					  "lon"  : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (nx,) } ,
					  "lat"  : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (ny,) } ,
					  "t850"  : { "dtype" : "float32" , "zlib" : True , "complevel": 5 , "chunksizes" : (1,ny,nx) } }
		
		## And now in netcdf
		pouth = pout
		if not os.path.isdir(pouth):
			os.makedirs(pouth)
		odatah.to_netcdf( os.path.join( pouth , f ) , encoding = encodingh )
		
		poutd = pout
		if not os.path.isdir(poutd):
			os.makedirs(poutd)
		foutd = f"ERA5_Europe_025deg_day_t850_{year}0101-{year}1231.nc"
		odatad.to_netcdf( os.path.join( poutd , foutd ) , encoding = encodingd )
	
		del idata
		del odatah
		del odatad
		del t850h
		del t850d
	
	print("Done")
