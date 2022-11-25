#!/bin/bash
#SBATCH --time=3-00:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --mem=36gb

## Load .bashrc
source $HOME/.bashrc
module purge
module load gcc/11.2.0
module load anaconda3-py/2021.11
conda activate dev


## Loop
wpath="/home/tmandonnet/ERA5-Land/t2m"
python3 $wpath/ERA5_convert_tn.py

