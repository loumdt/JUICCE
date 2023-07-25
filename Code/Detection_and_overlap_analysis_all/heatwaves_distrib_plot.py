"""This script draws the distribution of the heatwaves found in E-OBS temperature data and the impact of those also found in EM-DAT, regarding several meteo and impact criteria. Argument is either tg for mean, tx for max, or tn for min."""
#%%
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clrs
from scipy import signal
from scipy import stats
#from sklearn.metrics import roc_auc_score
import pandas as pd
from tqdm import tqdm
import sys,os
from adjustText import adjust_text
import ast
import pathlib
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
#--------------------------
# Define dictionaries:

def max_boundary(x) :
    if x<0 :
        x=0.95
    else :
        x=1.05
    return(x)

def min_boundary(x) :
    if x<0 :
        x=1.05
    else :
        x=0.95
    return(x)

def id_func(x) :
    return(x)

bins_dico_func = {"Global_mean": id_func, 
"Spatial_extent": np.log10,
"Duration": id_func, 
"Temp_sum": np.log10,
'Pseudo_Russo': np.log10, 
'Max_spatial' : np.log10, 
'Max': id_func,
"Global_mean_pop": np.log10, 
"Spatial_extent_pop": np.log10, 
"Duration_pop": np.log10, 
"Temp_sum_pop": np.log10,
'Pseudo_Russo_pop': np.log10, 
'Max_pop': np.log10,
'Max_spatial_pop': np.log10, 
'Temp_sum_pop_NL': np.log10, 
'Pseudo_Russo_pop_NL': np.log10, 
'Total_affected_pop':np.log10,
'Multi_index_Russo':np.log10,
'Multi_index_temp':np.log10, 
'Multi_index_Russo_NL':np.log10,
'Multi_index_temp_NL':np.log10,
'Mean_log_GDP':id_func,
'Mean_exp_GDP':id_func,
'Mean_inv_GDP':np.log10,
'GDP_inv_log_temp_sum':np.log10,
'GDP_inv_log_temp_mean':np.log10} #bins of the histogram

savgol_window_dico = {"Global_mean": 15, "Spatial_extent": 9, "Duration": 7, "Temp_sum":7,'Pseudo_Russo': 7, 'Pseudo_Russo_area': 7, 'Max_spatial': 9, 'Max': 7,
"Global_mean_pop": 15, "Spatial_extent_pop": 9, "Duration_pop": 7, "Temp_sum_pop":7,'Pseudo_Russo_pop': 7, 'Pseudo_Russo_area_pop': 7, 'Max_spatial_pop': 9, 'Max_pop': 7,
'Temp_sum_pop_NL': 9, 'Pseudo_Russo_pop_NL': 7, 'Pop_unique': 9, 'Multi_index_Russo':9, 'Multi_index_temp':9, 'Multi_index_Russo_NL':11, 'Multi_index_temp_NL':9} #window of the savitzky-golay filter for the histogram smoothing

clrs_dico = {"Total_Deaths": clrs.LogNorm(vmin=1, vmax=np.max(df_htw['Total_Deaths'])), "Total_Affected": clrs.Normalize(vmin=0, vmax=500), "Total_Damages": clrs.LogNorm(vmin=1, vmax=12120000) , "Impact_sum": clrs.LogNorm(vmin=1e4, vmax=np.max(df_htw['Impact_sum']))} #colormap depending on the selected criterion

criteria_dico = {"Global_mean": 'Global Mean temperature anomaly (°C) of the heatwave', "Spatial_extent": 'Cumulative area (km²) of the heatwave', 
"Duration": 'Duration of the heatwaves in days', "Temp_sum": 'Temperature anomaly multiplied by the normalized cell area',
'Pseudo_Russo': 'Sum of the Russo index over the heatwave', 'Pseudo_Russo_area': 'Sum of the Russo index over the heatwave multiplied by the normalized cell area for each point', 
'Max_spatial': 'Cumulative normalized area multiplied by the maximum temperature anomaly of the heatwave','Max' : 'maximum temperature anomaly of the heatwave'} #Title depending on the chosen impact criterion

units_dico = {"Global_mean": '(°C)', "Spatial_extent": '(km²)', "Duration": '(days)', "Temp_sum": '(°C)', 'Pseudo_Russo': '(dimensionless)', 'Pseudo_Russo_area': '(dimensionless)','Max_spatial': '(°C)', 'Max': '(°C)'} #units of the chosen meteo criterion

#impact_criteria = ['TotalDeaths', 'Impact_fct']
#meteo_criteria = ['Global_mean','Spatial_extent','Duration','Max','Max_spatial','Temp_sum','Pseudo_Russo','Pop_unique','Global_mean_pop','Duration_pop','Max_pop','Max_spatial_pop',
#'Spatial_extent_pop','Temp_sum_pop','Pseudo_Russo_pop','Temp_sum_pop_NL','Pseudo_Russo_pop_NL','Multi_index_temp','Multi_index_Russo','Multi_index_temp_NL','Multi_index_Russo_NL']

#%%
df_emdat_not_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves.xlsx"),header=0, index_col=0) #heatwaves are not merged by event, they are dissociated when affecting several countries
df_emdat_merged = pd.read_excel(os.path.join(datadir,"GDIS_EM-DAT","EMDAT_Europe-1950-2022-heatwaves_merged.xlsx"),header=0, index_col=0) #heatwaves are merged by event number Dis No
#%% 
# #Read txt file containing detected heatwaves to create detected heatwaves list
with open(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days",f"emdat_detected_heatwaves_ERA5_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days.txt"),'r') as f_txt:
    detected_htw_list = f_txt.readlines()
f_txt.close()
# #Remove '\n' from strings
emdat_to_era5_id_dico_not_merged = {}
emdat_heatwaves_list = []
for i in range(len(detected_htw_list)) :
    emdat_to_era5_id_dico_not_merged[detected_htw_list[i][:13]] = ast.literal_eval(detected_htw_list[i][14:-1])#Remove '\n' from strings
    emdat_heatwaves_list = np.append(emdat_heatwaves_list,emdat_to_era5_id_dico_not_merged[detected_htw_list[i][:13]])
emdat_heatwaves_list = [int(i) for i in np.unique(emdat_heatwaves_list)]
#%% #Need to consider the possibility that several EM-DAT heatwaves are not distinguishable in ERA5
htw_multi = []
inverted_emdat_to_era5_id_dico_not_merged = {}
for htw,v in emdat_to_era5_id_dico_not_merged.items() :
    for val in v :
        try : 
            inverted_emdat_to_era5_id_dico_not_merged[val].append(htw[:9])
        except :
            inverted_emdat_to_era5_id_dico_not_merged[val]=[htw[:9]]
for k,v in inverted_emdat_to_era5_id_dico_not_merged.items():
    inverted_emdat_to_era5_id_dico_not_merged[k]=[s for s in np.unique(inverted_emdat_to_era5_id_dico_not_merged[k])]
    if len(inverted_emdat_to_era5_id_dico_not_merged[k])>1:
        htw_multi.append(k)
#--------------------------
#%% #For all EM-DAT merged event, record every associated EM-DAT not merged heatwave (dico_merged_htw) that are detected in ERA5, and record every associated ERA5 heatwave (dico_merged_label)
emdat_to_era5_id_dico_merged_htw = {}
emdat_to_era5_id_dico_merged_label = {}
for i in df_emdat_merged.index.values[:]:
    dis_no = str(df_emdat_merged.loc[i,'disasterno'])
    for k,v in emdat_to_era5_id_dico_not_merged.items():
        if dis_no in k :
            try :
                emdat_to_era5_id_dico_merged_htw[dis_no].append(k)
                emdat_to_era5_id_dico_merged_label[dis_no] = np.append(emdat_to_era5_id_dico_merged_label[dis_no],v)
            except :
                emdat_to_era5_id_dico_merged_htw[dis_no]=[k]
                emdat_to_era5_id_dico_merged_label[dis_no]=[v]
not_computed_htw = []
links_not_computed_dict = {}
for k,v in emdat_to_era5_id_dico_merged_label.items():
    emdat_to_era5_id_dico_merged_label[k]=[int(i) for i in np.unique(v)]
    if len(emdat_to_era5_id_dico_merged_label[k])>1:
        not_computed_htw = np.append(not_computed_htw,emdat_to_era5_id_dico_merged_label[k][1:])
        links_not_computed_dict[emdat_to_era5_id_dico_merged_label[k][0]]=[int(i) for i in emdat_to_era5_id_dico_merged_label[k][1:]]
not_computed_htw = [int(i) for i in not_computed_htw]
careful_htw = list(links_not_computed_dict.keys())
#%%
pathlib.Path("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days","figs","distrib"+"_count_all_impacts"*count_all_impacts).mkdir(parents=True, exist_ok=True) #create output directory and parent directories if necessary

#%%
impact_criteria = ['Total_Deaths']#[Total_Deaths,Total_Affected,Material_Damages,Impact_sum]
#List of metrics
meteo_criteria=df_htw.columns.values[np.argwhere((df_htw.columns.values)=='Global_mean')[0][0]:]#all metrics, starting with Global_mean

for chosen_impact in impact_criteria :
    scatter_list_impact = [df_htw.loc[i,chosen_impact] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
    for chosen_meteo in meteo_criteria :
        scatter_list_meteo = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Extreme_heatwave']==True].index.values[:]]
        meteo_list = [df_htw.loc[i,chosen_meteo] for i in df_htw[df_htw['Computed_heatwave']==True].index.values[:]]

        min_val = np.min(meteo_list)
        max_val = np.max(meteo_list)
        print(chosen_meteo,'min',np.min(meteo_list),'max',np.max(meteo_list))
        fig = plt.figure(1,figsize=(24,16),facecolor='white')
        if bins_dico_func[chosen_meteo] == id_func :
            Y,bins_edges=np.histogram(meteo_list,bins=np.linspace(start=min_val*min_boundary(min_val), stop=max_val*max_boundary(max_val), num=30)) #histogram of the E-OBS heatwaves distribution
        elif bins_dico_func[chosen_meteo] == np.log10:
            Y,bins_edges=np.histogram(meteo_list,bins=np.logspace(start=np.log10(min_val*min_boundary(min_val)), stop=np.log10(max_val*max_boundary(max_val)), num=30)) #histogram of the E-OBS heatwaves distribution
        X=[0]*len(Y)

        for k in range(len(Y)) :
            X[k]=(bins_edges[k+1]+bins_edges[k])/2
        Y=np.array(Y)
        Y2=signal.savgol_filter(Y, 9,3)#savgol_window_dico[chosen_meteo], 3) #smooth the histogram edges with a savitzky-golay filter
        if bins_dico_func[chosen_meteo] == (id_func) : 
            plt.plot(X,Y,'ko')
            plt.plot(X,Y2,'r-')
        elif bins_dico_func[chosen_meteo] == np.log10: #have to plot on semilog scale for these criteria
            plt.semilogx(X,Y,'ko')
            plt.semilogx(X,Y2,'r-')
        plt.plot(X,Y,'ko')
        plt.plot(X,Y2,'r-')
        plt.ylim([-2,50])
        plt.xlim([min_val*min_boundary(min_val),max_val*max_boundary(max_val)])
        plt.axvline(np.percentile(meteo_list,25),linewidth=2) #add 1st quartile of the meteo criterion list
        plt.axvline(np.median(meteo_list),linewidth=2) #add median of the meteo criterion list
        plt.axvline(np.percentile(meteo_list,75),linewidth=2) #add 3rd quartile of the meteo criterion list
        plt.grid()
        plt.xlabel(chosen_meteo,size=25)#+' '+units_dico[chosen_meteo])
        plt.ylabel('Frequency',size=25)
        plt.title('Heatwaves distribution over '+chosen_meteo+' criterion',size=25)# ('+criteria_dico[chosen_meteo]+')',y=1)

        texts=[]
        for k in range(len(scatter_list_meteo)):
            closest_x = min(range(len(X)), key=lambda i: abs(X[i]-scatter_list_meteo[k]))
            plt.scatter(np.linspace(scatter_list_meteo[k],scatter_list_meteo[k],1000),np.linspace(0,Y2[closest_x],1000),c=[scatter_list_impact[k]]*1000,edgecolor=None, cmap = 'YlOrRd',norm=clrs_dico[chosen_impact],linewidths=4)
            texts.append(plt.annotate(df_htw[df_htw['Extreme_heatwave']==True].index.values[k],(scatter_list_meteo[k],Y2[closest_x]),size=15))
        adjust_text(texts, only_move={'points':'y', 'texts':'y'}, arrowprops=dict(arrowstyle="->", color='k', lw=1))
        cax = plt.axes([0.35, 0.02, 0.35, 0.02])
        plt.title('Impact of the extreme heatwaves ('+chosen_impact+')',y=1,size=25)
        plt.colorbar(cax=cax,orientation='horizontal')
        #plt.tight_layout()
        plt.savefig(os.path.join("Output","ERA5",the_variable,f"{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days","figs","distrib"+"_count_all_impacts"*count_all_impacts,f"distrib_{chosen_impact}_{chosen_meteo}_{the_variable}_{year_beg}_{year_end}_{threshold_value}th_threshold_{nb_days}days"+"_count_all_impacts"*count_all_impacts+".png"))
        fig.clear()
        #plt.show()
#%%