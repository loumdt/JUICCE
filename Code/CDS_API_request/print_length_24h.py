import sys,os
import numpy as np
import netCDF4 as nc

datadir="/data/tmandonnet/ERA5/UTCI"

for year in range(1950,2022):
    print(str(year))
    directory = os.path.join(datadir,str(year))
    for filename in os.listdir(directory) :
        if len(nc.Dataset(os.path.join(directory,filename),mode='r').variables['time'][:]) != 24 :
            print(str(year),filename)
print("end")