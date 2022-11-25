#!/bin/bash
#SBATCH --partition=zen16
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00

CWD=$(pwd)
#if [[ $CWD =~ (^|:)"/mnt/d/Ubuntu/These/JUICCE/Code/CDS_API_request"(|/)(:|$) ]]; then
if [[ $CWD =~ (^|:)"/d/Ubuntu/These/JUICCE/Code/CDS_API_request"(|/)(:|$) ]]; then
    source /c/Users/theom/anaconda3/etc/profile.d/conda.sh 
    conda activate testgdal
    #export DATADIR="/d/Ubuntu/These/Data"
    #wpath="/d/Ubuntu/These/JUICCE/Code/CDS_API_request"
    #export YEAR="$1"
    cdo daymean /d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc /d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_day_tg_${1}.nc
    cdo daymax /d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc /d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_day_tx_${1}.nc
    cdo daymin /d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc /d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_day_tn_${1}.nc
    rm "/d/Ubuntu/These/Data/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc"

else
    ## Load .bashrc
    source $HOME/.bashrc
    module purge
    module load anaconda3-py/2021.11

    conda activate dev_cds

    #export DATADIR="/data/tmandonnet" #set an environmental variable for the data directory, used in other scripts
    #wpath="/home/tmandonnet/ERA5-Land/t2m"
    #export YEAR="$1"
    cdo daymean /data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc /data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_day_tg_${1}.nc
    cdo daymax /data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc /data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_day_tx_${1}.nc
    cdo daymin /data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc /data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_day_tn_${1}.nc
    rm "/data/tmandonnet/ERA5-Land/t2m/$1/ERA5_Land_Global_01deg_hour_t2m_${1}010100-${1}123123.nc"
fi