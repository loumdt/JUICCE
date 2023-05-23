#!/bin/bash
#SBATCH --partition=zen4
#SBATCH --time=7-00:00:00
date  ## echo the date at start
## Load .bashrc
source $HOME/.bashrc
module purge
#module load gnu/10.2.0
#module load python/3.8-anaconda
module load anaconda3-py/2021.11

conda activate dev_cds

################################################################################
# Help                                                                         #
################################################################################
Help()
{
   # Display Help
   echo "This script aims to download ERA5 Mean Radiant Temperature data."
   echo "The script calls the python script ERA5_MRT_download_daily.py that uses CDS API to request and download data for a given year."
   echo "Find help on how to use CDS API at https://cds.climate.copernicus.eu/api-how-to"
   echo 
   echo "The script takes two arguments, corresponding to the desired period, both given bounds are included."
   echo "After downloading hourly data, daily mean is computed."
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

export DATADIR="/data/tmandonnet" #set an environmental variable for the data directory, used in other scripts

## Loop
wpath="/home/tmandonnet/ERA5/WBGT"
for ((year = $1 ; year <= $2 ; year++ ))
do
	export YEAR="$year"
	#python3 $wpath/ERA5_MRT_download_hourly.py $year
   #python3 $wpath/ERA5_wind_download_hourly.py $year
   extract_folder=$DATADIR/ERA5/WBGT/ERA5_Global_025deg_hourly_MRT_${year}0101-${year}1231
   if [ -d "$FILE" ]; then
      true
   else
      mkdir $extract_folder
   fi
   tar -xvf $DATADIR/ERA5/WBGT/ERA5_Global_025deg_hourly_MRT_${year}0101-${year}1231.tar.gz -C $extract_folder
   #rm $DATADIR/ERA5/WBGT/ERA5_Global_025deg_hourly_MRT_${year}0101-${year}1231.zip
   #i=1
   #for file in $DATADIR/ERA5/WBGT/ERA5_Global_025deg_hourly_MRT_${year}0101-${year}1231/*
   #do 
   #   var=${file#*mrt_}
   #   var=${var%_v1*}
   #   ncks -d lat,30.,71.5 -d lon,-12.5,45. $file $DATADIR/ERA5/WBGT/${year}/ERA5_Europe_025deg_MRT_${year}_n${var}.nc
   #   rm $file
   #   ((i++))
   #done
   #cdo mergetime $DATADIR/ERA5/WBGT/${year}/ERA5_Europe_025deg_MRT_${year}_n*.nc $DATADIR/ERA5/WBGT/${year}/ERA5_Europe_025deg_MRT_${year}.nc
   #rm -r $DATADIR/ERA5/WBGT/ERA5_Global_025deg_hourly_MRT_${year}0101-${year}1231
   #rm $DATADIR/ERA5/WBGT/${year}/ERA5_Europe_025deg_MRT_${year}_n*.nc
   #python3 $wpath/ERA5_compute_WBGT_hourly.py $year
done
date  ## echo the date at end