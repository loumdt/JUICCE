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
import sys
from adjustText import adjust_text
#%%
#the_variable = 'tg'
#%%
the_variable = str(sys.argv[1])
#%%
temp_name_dict = {'tg':'mean','tx':'max','tn':'min'}

print('the_variable :',the_variable)

data = pd.read_excel("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/characteristics_htws_"+the_variable+".xlsx")

data.rename(columns={"Unnamed: 0":"Htw_ID"},inplace = True)

#--------------------------
# Define dictionaries:

bins_dico_func = {"Global_mean": "linear", 
"Spatial_extent": "log",
"Duration": "linear", 
"Temp_sum": "log",
'Pseudo_Russo': "log", 
'Max_spatial' : "log", 
'Max': "linear",
"Global_mean_pop": "log", 
"Spatial_extent_pop": "log", 
"Duration_pop": "log", 
"Temp_sum_pop": "log",
'Pseudo_Russo_pop': "log", 
'Max_pop': "log",
'Max_spatial_pop': "log", 
'Temp_sum_pop_NL': "log", 
'Pseudo_Russo_pop_NL': "log", 
'Pop_unique':"log",
'Multi_index_Russo':"log",
'Multi_index_temp':"log", 
'Multi_index_Russo_NL':"log",
'Multi_index_temp_NL':"log"} #bins of the histogram

savgol_window_dico = {"Global_mean": 15, "Spatial_extent": 9, "Duration": 7, "Temp_sum":7,'Pseudo_Russo': 7, 'Pseudo_Russo_area': 7, 'Max_spatial': 9, 'Max': 7,
"Global_mean_pop": 15, "Spatial_extent_pop": 9, "Duration_pop": 7, "Temp_sum_pop":7,'Pseudo_Russo_pop': 7, 'Pseudo_Russo_area_pop': 7, 'Max_spatial_pop': 9, 'Max_pop': 7,
'Temp_sum_pop_NL': 9, 'Pseudo_Russo_pop_NL': 7, 'Pop_unique': 9, 'Multi_index_Russo':9, 'Multi_index_temp':9, 'Multi_index_Russo_NL':11, 'Multi_index_temp_NL':9} #window of the savitzky-golay filter for the histogram smoothing

clrs_dico = {"TotalDeaths": clrs.LogNorm(vmin=1, vmax=72210), "Total_Affected": clrs.Normalize(vmin=0, vmax=500), "Total_Damages": clrs.LogNorm(vmin=1, vmax=12120000) , "Impact_fct": clrs.LogNorm(vmin=1e4, vmax=157e6)} #colormap depending on the selected criterion

criteria_dico = {"Global_mean": 'Global Mean temperature anomaly (°C) of the heatwave', "Spatial_extent": 'Cumulative area (km²) of the heatwave', 
"Duration": 'Duration of the heatwaves in days', "Temp_sum": 'Temperature anomaly multiplied by the normalized cell area',
'Pseudo_Russo': 'Sum of the Russo index over the heatwave', 'Pseudo_Russo_area': 'Sum of the Russo index over the heatwave multiplied by the normalized cell area for each point', 
'Max_spatial': 'Cumulative normalized area multiplied by the maximum temperature anomaly of the heatwave','Max' : 'maximum temperature anomaly of the heatwave'} #Title depending on the chosen impact criterion

units_dico = {"Global_mean": '(°C)', "Spatial_extent": '(km²)', "Duration": '(days)', "Temp_sum": '(°C)', 'Pseudo_Russo': '(dimensionless)', 'Pseudo_Russo_area': '(dimensionless)','Max_spatial': '(°C)', 'Max': '(°C)'} #units of the chosen meteo criterion

#impact_criteria = ['TotalDeaths', 'Impact_fct']
#meteo_criteria = ['Global_mean','Spatial_extent','Duration','Max','Max_spatial','Temp_sum','Pseudo_Russo','Pop_unique','Global_mean_pop','Duration_pop','Max_pop','Max_spatial_pop',
#'Spatial_extent_pop','Temp_sum_pop','Pseudo_Russo_pop','Temp_sum_pop_NL','Pseudo_Russo_pop_NL','Multi_index_temp','Multi_index_Russo','Multi_index_temp_NL','Multi_index_Russo_NL']

impact_criteria = ['TotalDeaths']
meteo_criteria=['Max','Multi_index_temp_NL']

stefanon_htw = np.array([],dtype=np.int32)
stefanon_htw_dico={}

htw_multi = {'tg' : [127,171], 'tx' : [120,169],'tn':[62]}
lines_htw_multi = {'tg':{127:[3,4],171:[14,15,16,17]},'tx':{120:[3,4],169:[14,15,16,17]},
'tn':{62:[3,4]}}
not_computed_htw_dict = {'tg' : [182,196,213,214,220,238,239,240,261,262,263,292,305],
'tx' : [172,192,204,206,207,213,231,232,249,250,259,276],
'tn':[107,119,120,139,151,153,154,208]} #heatwaves not directly computed
careful_htw_dict = {'tg' : [181,195,210,218,237,260,289,304], 
'tx' : [169,191,201,211,230,248,258,273],
'tn':[106,118,137,150,207]}
links_not_computed_dict = {'tg' : {181:[182],195:[196],210:[213,214],218:[220],237:[238,238,240],260:[261,262,263],289:[292],304:[305]},
'tx':{169:[172],191:[192],201:[204,206,207],211:[213],230:[231,232],248:[249,250],258:[259],273:[276]},
'tn':{106:[107],118:[119,120],137:[139],150:[151,153,154],207:[208]}}

em_dat_htw_ID_dico = {'tg':{124 : '1987-0596-GRC', 127 : '1988-0XXX-SEE',
132 : '1990-0085-FRA', 144 : '1995-0363-RUS', 146 : '1995-0157-ESP', 
159 : '1998-0204-ITA', 161 : '1998-0250-ROU', 164 : '1999-0702-LTU', 
171 : '2000-03XX-SEE', 181 : '2001-0404-RUS', 195 : '2003-0391-WE', 
200 : '2004-0361-ESP', 202 : '2005-0820-PRT', 205 : '2005-0756-ROU',
210 : '2006-0383-WE', 218 : '2007-0235-SE', 237 : '2010-0372-RUS', 
260 : '2013-0549-GBR', 271 :'2015-0410-WE' , 289 : '2018-0235-WE', 
296 : '2019-0296-WE', 298 : '2019-0366-WE', 304 : '2020-0530-WE'},
'tx':{121 : '1985-0257-GRC',127 : '1987-0596-GRC', 131 : '1988-0XXX-SEE',
137 : '1990-0085-FRA', 151 : '1995-0363-RUS', 153 : '1995-0157-ESP', 
166 : '1998-0204-ITA', 169 : '1998-0250-ROU', 171 : '1999-0702-LTU', 
180 : '2000-03XX-SEE', 189 : '2001-0404-RUS', 201 : '2003-0391-WE', 
205 : '2004-0361-ESP', 209 : '2005-0756-ROU',
212 : '2006-0383-WE', 223 : '2007-0235-SE', 242 : '2010-0372-RUS', 
260 : '2013-0549-GBR', 269 :'2015-0410-WE' , 285 : '2018-0235-WE', 
293 : '2019-0296-WE', 295 : '2019-0366-WE', 304 : '2020-0530-WE'},
'tn':{37 : '1995-0363-RUS', 43 : '1999-0702-LTU',
61 : '2003-0391-WE', 72 : '2007-0235-SE', 83 : '2010-0372-RUS',
93 : '2013-0549-GBR', 102 :'2015-0410-WE', 117 : '2019-0296-WE', 
118 : '2019-0366-WE', 123 : '2020-0530-WE'}}

#--------------------------
#%%
emdat_htw = np.zeros((len(impact_criteria),len(meteo_criteria),data.loc[:,'extreme_bool'].sum(),3)) #impact,meteo,htw (htw_impact,htw_meteo,htw_number) in order to evalujate correlations at the end
fig, ax = plt.subplots(nrows=1, ncols=2,facecolor='white',figsize=(30,16))
#fig = plt.figure(1,figsize=(30,16))
nb_impact = 0
for chosen_impact in impact_criteria :
    nb_meteo = 0
    for chosen_meteo in tqdm(meteo_criteria) :
        plt.subplot(1,2,nb_meteo+1)
        #print('\n Computing '+chosen_impact+' and '+chosen_meteo+' ...')

        extreme_htw_bool = np.array([],dtype=np.int32) #record the extreme heatwaves (boolean list) in order to compute roc_auc_score()
        impact_list = np.array([]) #record the impact of the EM-DAT heatwaves
        meteo_list = np.array([]) #record the meteo criterion of the E-OBS heatwaves
        idx_scatt = np.array([],dtype=np.int32) #record the meteo criterion of the EM-DAT heatwaves
        nb_htw_scatt = np.array([],dtype=np.int32) #record the numbers of the EM-DAT heatwaves

        new_df=data[['Htw_ID',chosen_meteo,'extreme_bool',chosen_impact]]
        for htw in data.index :
            htw_id = data.loc[htw,'Htw_ID']
            meteo_list = np.append(meteo_list,data.loc[htw,chosen_meteo])
            extreme_htw_bool = np.append(extreme_htw_bool,data.loc[htw,'extreme_bool'])
            if data.loc[htw,'extreme_bool']==1:
                impact_list = np.append(impact_list,data.loc[htw,chosen_impact])
                idx_scatt = np.append(idx_scatt,data.loc[htw,chosen_meteo])
                nb_htw_scatt = np.append(nb_htw_scatt,htw_id)

        #-------------#
        # draw figure #
        #-------------#
        min_val = np.min(meteo_list)
        max_val = np.max(meteo_list)
        print(chosen_meteo,'min',np.min(meteo_list),'max',np.max(meteo_list))
        #fig = plt.figure(1,figsize=(24,16),facecolor='white')
        if bins_dico_func[chosen_meteo] == 'linear' :
            Y,bins_edges=np.histogram(meteo_list,bins=np.linspace(start=min_val*0.95, stop=max_val*1.05, num=30)) #histogram of the E-OBS heatwaves distribution
        elif bins_dico_func[chosen_meteo] == 'log':
            Y,bins_edges=np.histogram(meteo_list,bins=np.logspace(start=np.log10(min_val*0.95), stop=np.log10(max_val*1.05), num=30)) #histogram of the E-OBS heatwaves distribution
        X=[0]*len(Y)

        for k in range(len(Y)) :
           X[k]=(bins_edges[k+1]+bins_edges[k])/2
        Y=np.array(Y)
        Y2=signal.savgol_filter(Y, savgol_window_dico[chosen_meteo], 3) #smooth the histogram edges with a savitzky-golay filter
        if chosen_meteo in ['Duration','Global_mean','Max'] : 
           plt.plot(X,Y,'ko')
           plt.plot(X,Y2,'r-')
        else : #have to plot on semilog scale for these criteria
           plt.semilogx(X,Y,'ko')
           plt.semilogx(X,Y2,'r-')
        plt.plot(X,Y,'ko')
        plt.plot(X,Y2,'r-')
        plt.ylim([-2,50])
        plt.axvline(np.percentile(meteo_list,25),linewidth=2) #add 1st quartile of the meteo criterion list
        plt.axvline(np.median(meteo_list),linewidth=2) #add median of the meteo criterion list
        plt.axvline(np.percentile(meteo_list,75),linewidth=2) #add 3rd quartile of the meteo criterion list
        plt.grid()
        plt.xlabel(chosen_meteo,size=25)#+' '+units_dico[chosen_meteo])
        plt.ylabel('Frequency',size=25)
        plt.title('Heatwaves distribution over '+chosen_meteo+' criterion',size=25)# ('+criteria_dico[chosen_meteo]+')',y=1)
        if chosen_meteo == 'Multi_index_temp_NL':
            plt.xlim([15, 8e11])
        elif chosen_meteo == 'Global_mean':
            plt.xlim([2, 6.5])
        nb_htw_scatt=nb_htw_scatt[idx_scatt.argsort()] #sort the EM-DAT heatwaves lists in order to have a more readable figure, but have to keep matching impact with the given number and meteo criterion
        impact_list=impact_list[idx_scatt.argsort()]
        idx_scatt.sort()
        texts=[]
        if chosen_meteo == 'Duration' :
           for k in range(len(impact_list)):
               plt.annotate(em_dat_htw_ID_dico[the_variable][nb_htw_scatt[k]],(idx_scatt[k],1+3*(k%6)),size=13,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
               y_scatt=6
               mark_size=2e4
        elif chosen_meteo == 'Max_spatial' :
           for k in range(len(impact_list)):
               plt.annotate(em_dat_htw_ID_dico[the_variable][nb_htw_scatt[k]],(idx_scatt[k],1+2*(k%4)),size=13,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
               y_scatt=3
               mark_size=15e3
        else :
           for k in range(len(impact_list)):
               closest_x = min(range(len(X)), key=lambda i: abs(X[i]-idx_scatt[k]))
               plt.scatter(np.linspace(idx_scatt[k],idx_scatt[k],1000),np.linspace(0,Y2[closest_x],1000),c=[impact_list[k]]*1000,edgecolor=None, cmap = 'YlOrRd',norm=clrs_dico[chosen_impact],linewidths=4)
               #plt.annotate(em_dat_htw_ID_dico[the_variable][nb_htw_scatt[k]],(idx_scatt[k],1+4*(k%4)),size=14,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
               #plt.annotate(em_dat_htw_ID_dico[the_variable])
               texts.append(plt.annotate(nb_htw_scatt[k],(idx_scatt[k],Y2[closest_x]),size=15))
               y_scatt=7
               mark_size=240e3
        adjust_text(texts, only_move={'points':'y', 'texts':'y'}, arrowprops=dict(arrowstyle="->", color='k', lw=1))
        #CS1=plt.scatter(idx_scatt,[y_scatt]*len(idx_scatt),c=impact_list,s=[mark_size]*len(impact_list),cmap='YlOrRd',marker='|',norm=clrs_dico[chosen_impact],linewidths=4) #add the EM-DAT heatwaves along with their respective impact and numbers on the E-OBS heatwaves distribution
        cax = plt.axes([0.35, 0.02, 0.35, 0.02])
        plt.title('Impact of the extreme heatwaves ('+chosen_impact+')',y=1,size=25)
        #plt.colorbar(CS1,cax=cax,orientation='horizontal')
        plt.colorbar(cax=cax,orientation='horizontal')
        #plt.tight_layout()
        #plt.savefig("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/TEST_"+chosen_impact+"_"+chosen_meteo+".png")
        #plt.show()
        #break

        #fig.clear()

        emdat_htw[nb_impact,nb_meteo,:,0] = impact_list
        emdat_htw[nb_impact,nb_meteo,:,1] = idx_scatt
        emdat_htw[nb_impact,nb_meteo,:,2] = nb_htw_scatt


        #Rpearson = stats.pearsonr(np.log10(emdat_htw[nb_impact,nb_meteo,:,1]),np.log10(emdat_htw[nb_impact,nb_meteo,:,0]))
        #roc_auc_score_value = roc_auc_score(extreme_htw_bool,meteo_list)
    
        nb_meteo += 1
    #break
    nb_impact += 1
#plt.savefig("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/TEST_"+chosen_impact+"_best_and_worst_V2.png")
plt.savefig("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/TEST_"+chosen_impact+"_best_and_max_V2.png")
plt.show()
#%%


#%%
exit()

#Evaluate correlations between impact and meteo criteria for the EM-DAT heatwaves
print('Computing correlations ...')    

fig = plt.figure(2,figsize=(24,16))
plt.title('Correlation between meteo criteria and impact criteria for EM-DAT heatwaves')

for i in range(len(impact_criteria)) :
    for j in range(len(meteo_criteria)) :
        plt.subplot(len(impact_criteria),len(meteo_criteria),1+i*len(meteo_criteria)+j)
        #plt.subplot(4,9,1+i*len(meteo_criteria)+j)
        plt.grid()
        if meteo_criteria[j] in ['Duration','Global_mean','Max'] : #and impact_criteria[i] == 'Total_Affected' :
            plt.plot(emdat_htw[i,j,:,1],np.log10(emdat_htw[i,j,:,0]),'k+')
            (slope,intercept,rvalue,pvalue,stderr)=stats.linregress(emdat_htw[i,j,:,1],np.log10(emdat_htw[i,j,:,0]))
            X0 = np.min(emdat_htw[i,j,:,1])
            Y0 = slope*X0+intercept
            X1 = np.max(emdat_htw[i,j,:,1])
            Y1 = slope*X1+intercept
            print(rvalue)
            print(stats.pearsonr(emdat_htw[i,j,:,1],np.log10(emdat_htw[i,j,:,0])))
            plt.plot([X0,X1],[Y0,Y1], 'k-')
            plt.annotate('R='+str(round(rvalue,5)),((X0+X1)/2,(Y0+Y1/2)))
            plt.xlabel(meteo_criteria[j])
            plt.ylabel('Log('+impact_criteria[i]+')')
        #elif meteo_criteria[j] in ['Duration','Global_mean'] :
        #    plt.semilogy(emdat_htw[i,j,:,1],emdat_htw[i,j,:,0],'k+')
        #elif impact_criteria[i] in 'Total_Affected' :
        #    plt.semilogx(emdat_htw[i,j,:,1],emdat_htw[i,j,:,0],'k+')
        else :
            plt.plot(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0]),'k+')
            (slope,intercept,rvalue,pvalue,stderr)=stats.linregress(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0]))
            X0 = np.min(np.log10(emdat_htw[i,j,:,1]))
            Y0 = slope*X0+intercept
            X1 = np.max(np.log10(emdat_htw[i,j,:,1]))
            Y1 = slope*X1+intercept
            print('pearson :',stats.pearsonr(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))
            print('kendall :',stats.kendalltau(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))
            print('spearman :',stats.spearmanr(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))
            plt.plot([X0,X1],[Y0,Y1], 'k-')
            plt.annotate('R='+str(round(rvalue,5)),((X0+X1)/2,(Y0+Y1/2)))
            plt.xlabel('Log('+meteo_criteria[j]+') ')#+units_dico[meteo_criteria[j]])
            plt.ylabel('Log('+impact_criteria[i]+')')

plt.savefig("D:/Ubuntu/PFE/JUICCE/Output/Van_der_Wiel_graphs/"+the_variable+"/Heatwaves_distrib_correlations_V2.png")