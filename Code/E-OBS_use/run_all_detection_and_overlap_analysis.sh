#!/bin/bash

################################################################################
# Help                                                                         #
################################################################################
Help()
{
   # Display Help
   echo "This script launches the entire ERA5 heatwave detection and overlap with EM-DAT analysis."
   echo "It takes 5 arguments :"
   echo "Argument 1 is tg, tn or tx to chose the temperature variable (respectively mean, min or max)."
   echo "Argument 2 and 3 are the bounds of the studied period, given as years. Both bounds are included in calculation. Must be given as integers."
   echo "Argument 4 is the percentile threshold corresponding to the heatwave statistical definition (e.g. 95 for the 95th percentile threshold). Must be given as an integer."
   echo "Argument 5 is the duration threshold of a heatwave point, i.e. the minimum number of consecutive days that must exceed the given threshold in order for a point to be part of a heatwave. Must be given as an integer."
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

cd ../..

echo "Temperature variable is $1"
echo "Studied period is $2 - $3"
echo "Percentile threshold is ${4}th"
echo "Duration threshold is $5 days"

#check, at each step, if the output netCDF file already exists

echo \n \n
echo "Climatology computation"
FILE=Data/ERA5/t2m/${1}_daily_avg_${2}_${3}_smoothed.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_1_compute_climatology_smooth.py $1 $2 $3"
    python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_1_compute_climatology_smooth.py $1 $2 $3
fi

echo \n \n
echo "Percentile computation"
FILE=Data/ERA5/t2m/distrib_${1}_ano_${2}_${3}_${4}th_threshold_15days.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_2_compute_distrib_ano_percentile.py $1 $2 $3 $4"
    python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_2_compute_distrib_ano_percentile.py $1 $2 $3 $4
fi

echo \n \n
echo "Create masks"
FILE=Data/ERA5/Mask/Mask_Europe_land_only_ERA5_0.25deg.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Mask/make_mask_Europe_ERA5_0.25deg.py"
    python Mask/make_mask_Europe_ERA5_0.25deg.py
fi
FILE=Data/ERA5/Mask/Mask_United_Kingdom_ERA5_0.25deg.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Mask/make_mask_all_countries_ERA5_0.25deg.py"
    python Mask/make_mask_all_countries_ERA5_0.25deg.py
fi

echo \n \n
echo "Cut the temperature data to JJA and keep only values exceeding percentile threshold (2 output files)"
FILE=Data/ERA5/t2m/${1}_anomaly_JJA_${2}_${3}_scaled_${4}th.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_3_ano_scale_jja_selec.py $1 $2 $3 $4"
    python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_3_ano_scale_jja_selec.py $1 $2 $3 $4
fi

echo \n \n
echo "keep only values exceeding percentile threshold for at least $5 consecutive days"
FILE=Data/ERA5/t2m/Detection_Canicule/potential_heatwaves_${1}_${5}days_before_scan_${2}_${3}_${4}th.nc.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_4_detect_potential_heatwaves_nb_days.py $1 $2 $3 $4 $5"
    python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_4_detect_potential_heatwaves_nb_days.py $1 $2 $3 $4 $5
fi

echo \n \n
echo "Carry out connected components algorithm scanning"
FILE=Data/ERA5/t2m/Detection_Canicule/detected_heatwaves_${1}_anomaly_JJA_${2}_${3}_threshold_${4}th_${5}days.nc
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_5_cc3d_scan.py $1 $2 $3 $4 $5"
    python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_5_cc3d_scan.py $1 $2 $3 $4 $5
fi

echo \n \n
echo "Analyze overlap with EM-DAT recorded heatwaves. Exporting to txt files"
FILE=Data/ERA5/Output/ERA5/$1/${1}_${2}_${3}_${4}th_threshold_${5}days/emdat_undetected_heatwaves_ERA5_${1}_${2}_${3}_${4}th_threshold_${5}days.txt
if test -f "$FILE"; then
    echo "$FILE already exists, skipping this step"
else
    echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_6_analyse_overlap_EM-DAT.py $1 $2 $3 $4 $5"
    python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_6_analyse_overlap_EM-DAT.py $1 $2 $3 $4 $5
fi

echo \n \n
echo "Create animation for EM-DAT undetected heatwaves"
echo "python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_7_undetected_heatwaves_animation.py $1 $2 $3 $4 $5"
python Code/ERA5_use/Detection_and_overlap_analysis_t2m/ERA5_use_t2m_7_undetected_heatwaves_animation.py $1 $2 $3 $4 $5