#!/bin/bash
#SBATCH --partition=zen16
#SBATCH --mem=32G
#SBATCH --time=1-00:00:00

## Load .bashrc
source $HOME/.bashrc
module purge
module load anaconda3-py/2021.11

conda activate dev_cds

export DATADIR="/data/tmandonnet" #set an environmental variable for the data directory, used in other scripts
wpath="/home/tmandonnet/ERA5/z500"
export YEAR="$1"
python3 $wpath/ERA5_z500_convert_to_daily.py $1
