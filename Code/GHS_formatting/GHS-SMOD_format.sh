#!/bin/bash

source /c/Users/theom/anaconda3/etc/profile.d/conda.sh 
conda activate testgdal

for year in {1975..2020..5}
do
    print "Hello $i"
    FILE_IN_TIF="D:\Ubuntu\M2_EEET\Stage_CIRED\Data\GHS\SMOD\GHS_SMOD_POP$1_GLOBE_R2019A_54009_1K_V2_0\GHS_SMOD_POP$1_GLOBE_R2019A_54009_1K_V2_0.tif"
    FILE_OUT_TIF="D:\Ubuntu\M2_EEET\Stage_CIRED\Data\GHS\SMOD\GHS_SMOD_POP$1_GLOBE_R2019A_54009_1K_V2_0\GHS_SMOD_POP$1_GLOBE_R2019A_54009_250_V2_0.tif"
    FILE_OUT_TIF_2="D:\Ubuntu\M2_EEET\Stage_CIRED\Data\GHS\SMOD\GHS_SMOD_POP$1_GLOBE_R2019A_54009_1K_V2_0\GHS_SMOD_$1_250_reproj.tif"

    echo "Modifying $FILE_IN_TIF"

    echo "gdal_translate 1k to 250m"
    gdal_translate -tr 250.0 250.0 "$FILE_IN_TIF" "$FILE_OUT_TIF"
    echo "gdal_warp EPSG:54009 to EPSG:4326"
    gdalwarp -t_srs EPSG:4326 "$FILE_OUT_TIF" "$FILE_OUT_TIF_2"
    rm "$FILE_OUT_TIF"
    echo "gdal_translate tif to netCDF"
    gdal_translate -of NetCDF "$FILE_OUT_TIF_2" "D:\Ubuntu\M2_EEET\Stage_CIRED\Data\GHS\SMOD\ghs_smod_$1_9ss_4326.nc"
    rm "$FILE_OUT_TIF_2"

done