#!/bin/bash
#SBATCH --partition=zen16
#SBATCH --time=1-00:00:00
#SBATCH --mem=64G


## Load .bashrc
source $HOME/.bashrc
module purge
module load anaconda3-py/2021.11

conda activate dev_cds

################################################################################
# Help                                                                         #
################################################################################
Help()
{
   # Display Help
   echo "This script launches the stefanon_2_detect_heatwaves_4days_first_step.py script on the spirit server."
   echo "It takes 4 arguments :"
   echo "Argument 1 is either tg, tn or tx to chose the temperature variable (respectively mean, min or max)."
   echo "Argument 2 and 3 are the bounds of the studied period, given as years. Both bounds are included in calculation. Must be given as integers."
   echo "Argument 4 is the percentile threshold corresponding to the heatwave statistical definition (e.g. 95 for the 95th percentile threshold). Must be given as an integer."
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

export DATADIR="/data/tmandonnet" #set an environmental variable for the data directory, used in other scripts

wpath="/home/tmandonnet/E-OBS_use"
python3 $wpath/Scan_Stefanon/stefanon_4_scan_cor_2nd_time.py $1 $2 $3 $4