#!/bin/bash
#SBATCH --partition=zen4
#SBATCH --time=7-00:00:00


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
   echo "This script aims to download ERA5 t850 data."
   echo "The script calls the python script ERA5_t850_download_hourly.py that uses CDS API to request and download data for a given year."
   echo "Find help on how to use CDS API at https://cds.climate.copernicus.eu/api-how-to"
   echo 
   echo "The script takes two arguments, corresponding to the desired period, both given bounds are included."
   echo "After downloading hourly data, daily mean id computed."
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
	python3 $wpath/ERA5_t850_download_hourly.py $year
	sbatch ERA5_t850_sbatch_convert_to_daily.sh $year
done