#%%
from scipy import stats
from sklearn import metrics
import pandas as pd
import sys,os
import pathlib
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
#Read arguments
try : 
    the_variable = str(sys.argv[1])
except :
    the_variable='tg'

try : 
    year_beg = int(sys.argv[2])
except :
    year_beg = 1950
    
try : 
    year_end = int(sys.argv[3])
except :
    year_end = 2021

try : 
    threshold_value = int(sys.argv[4])
except :
    threshold_value = 95
    
try : 
    nb_days = int(sys.argv[5])
except :
    nb_days = 4
#%%
#create dictionary for temperature name
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}
#print input argument for feedback
print('the_variable :',the_variable)
print('year_beg :',year_beg)
print('year_end :',year_end)
print('threshold_value :',threshold_value)
print('nb_days :',nb_days)
#%%
count_all_impacts = True #True : count all affected countries according to EM-DAT ; False : #count only visibly affected countries according to ERA5
print("count_all_impacts :",count_all_impacts)
#%%
df_htw = pd.read_excel(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days",f"df_htw_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days"+"_count_all_impacts"*count_all_impacts+".xlsx"),header=0,index_col=0)
#%%
impact_criteria = ['Total_Deaths','Total_Affected','Material_Damages','Impact_sum']
meteo_criteria=df_htw.columns.values[np.argwhere((df_htw.columns.values)=='Global_mean')[0][0]:]
arr = []
for i in range(len(impact_criteria)) :
    arr+=[impact_criteria[i]]*4
arrays = [arr, ['r_pearson', 'p-value', 'roc_auc', 'Global_score']*len(impact_criteria)]

col_idx = pd.MultiIndex.from_arrays(arrays, names=('impact', 'metric'))

df_scores = pd.DataFrame(columns=col_idx, index = meteo_criteria,data=None)

pathlib.Path("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days","figs","roc_curve").mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary
#%%
for chosen_impact in tqdm(impact_criteria) :
    for chosen_meteo in meteo_criteria :
        extreme_list_impact = [df_htw.loc[i,chosen_impact] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
        extreme_list_meteo = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
        meteo_list = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Computed_heatwave']==True].index.values[:]]
        extreme_bool_list = [int(df_htw.loc[i,'Extreme_heatwave']) for i in df_htw[df_htw['Computed_heatwave']==True].index.values[:]]
        Rpearson = stats.pearsonr(extreme_list_impact,extreme_list_meteo)
        roc_auc = metrics.roc_auc_score(extreme_bool_list,meteo_list)
        df_scores.loc[chosen_meteo,(chosen_impact,'r_pearson')] = Rpearson[0]
        df_scores.loc[chosen_meteo,(chosen_impact,'p-value')] = Rpearson[1]
        df_scores.loc[chosen_meteo,(chosen_impact,'roc_auc')] = roc_auc
        df_scores.loc[chosen_meteo,(chosen_impact,'Global_score')] = Rpearson[0]*roc_auc
        #display roc_curve
        if chosen_impact==impact_criteria[0] : #save this fig only once since it does not depend on the impact criterion
            fpr, tpr, thresholds = metrics.roc_curve(extreme_bool_list,meteo_list)
            display = metrics.RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc,estimator_name=chosen_meteo)
            display.plot()
            plt.plot([0, 1], [0, 1], "k--", label="chance level (AUC = 0.5)")
            plt.axis("square")
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title(f"ROC curve: {chosen_meteo}")
            plt.legend()
            plt.savefig(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days","figs","roc_curve",f"roc_curve_{chosen_meteo}.png"))
            plt.close()
#%%
df_scores.to_excel(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days",f"df_scores_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days"+"_count_all_impacts"*count_all_impacts+".xlsx"))