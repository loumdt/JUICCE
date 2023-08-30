#!/bin/bash

################################################################################
# Help                                                                         #
################################################################################
Help()
{
   # Display Help
   echo "This script carries out a regridding process of the population density files to the E-OBS data grid."
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

cd ../..

declare -A coord_sys_dict
coord_sys_dict[Mollweide]='54009'
coord_sys_dict[WGS84]='4326'

echo "Download and extract data"
echo ""

echo "python Code/Pop_formatting/ghs_pop_download.py $1 $2"
python Code/Pop_formatting/ghs_pop_download.py $1 $2

cd Data/Pop/GHS_POP
for year in {1975..2020..5}
do
  echo ""
  if [ $1 = 'Mollweide' ]; then
    echo "Reproject ${year} ..."
    echo ""
    gdalwarp -t_srs EPSG:4326 GHS_POP_E${year}_GLOBE_R2022A_${coord_sys_dict[${1}]}_${2}_V1_0.tif GHS_POP_E${year}_GLOBE_R2022A_4326_${2}_V1_0.tif
    rm GHS_POP_E${year}_GLOBE_R2022A_${coord_sys_dict[${1}]}_${2}_V1_0.tif
    echo ""
  fi  
  echo "Convert ${year} to netCDF" 
  echo ""
  gdal_translate -of NetCDF GHS_POP_E${year}_GLOBE_R2022A_4326_${2}_V1_0.tif GHS_POP_E${year}_GLOBE_R2022A_4326_${2}_V1_0.nc
  rm GHS_POP_E${year}_GLOBE_R2022A_4326_${2}_V1_0.tif
  echo ""
  echo Regrid ${year} to E-OBS grid
  echo ""
  cdo -remapycon,Mask_Europe_E-OBS_0.1deg.nc GHS_POP_E${year}_GLOBE_R2022A_4326_${2}_V1_0.nc GHS_POP_${year}_eobs_grid_Europe.nc
done