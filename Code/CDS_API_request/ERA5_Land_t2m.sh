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
   echo "This script aims to download ERA5-Land temperature hourly data."
   echo "The script calls the python script ERA5_Land_t2m.py that uses CDS API to request and download data for a given year."
   echo "Find help on how to use CDS API at https://cds.climate.copernicus.eu/api-how-to"
   echo 
   echo "The script takes two arguments, corresponding to the desired period."
   echo "If someone wants to download the 1950-2020 period, they have to input 1950 and 2021 as their two arguments."
   echo "After downloading hourly data, daily mean, max and min are computed, and hourly data file is deleted."
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
wpath="/home/tmandonnet/ERA5-Land/t2m"
for ((year = $1 ; year < $2 ; year++ ))
do
	export YEAR="$year"
	python3 $wpath/ERA5_Land_t2m.py $year
	sbatch ERA5_Land_t2m_convert_suppress.sh $year
done