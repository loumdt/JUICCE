"""This script draws the distribution of the heatwaves found in E-OBS temperature data and the impact of those also found in EM-DAT, regarding several meteo and impact criteria"""

import time 
start_time=time.time()

import netCDF4 as nc
import numpy as np
import csv
import numpy.ma as ma
import matplotlib.pyplot as plt
import matplotlib.colors as clrs
from scipy import signal
from scipy import stats

cr = csv.reader(open("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_heatwaves.csv","r")) #csv file containing the heatwaves from EM-DAT
liste_lignes = list(cr)

nc_file = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_TWICE_tg_anomaly_threshold_95th_scan_size35_10.0%.nc" #netcdf file containing the heatwaves from E-OBS

f = nc.Dataset(nc_file,mode='r')
lon_in = f.variables['lon'][:]
lat_in = f.variables['lat'][:]

Russo_file = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/Russo_index_summer_only_1950_2020.nc"
f_Russo = nc.Dataset(Russo_file,mode='r')

heatwaves_idx = np.load("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_4days_V3.npy",allow_pickle = True) #numpy file containing the days of the E-OBS heatwaves
heatwaves_idx_2 = np.load("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_2_4days_V3.npy",allow_pickle = True) #numpy file containing the days of the E-OBS heatwaves
heatwaves_dates = np.load("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/heatwaves_dates_4days_V3.npy",allow_pickle = True) #numpy file containing the dates of the E-OBS heatwaves

#--------------------------
# Define dictonaries to avoid an illegible code full of 'if'/'elif' :

csv_dico = {"Total_Deaths": 36, "Total_Affected": 40, "Total_Damages": 43, "Stefanon : détectée ?": 46, "Si oui, quel fichier": 47} #columns of the csv files

bins_dico = {"Global_mean": 30, "Spatial_extent": np.logspace(start=np.log10(214), stop=np.log10(779e3), num=30), 
"Duration": np.linspace(start=3.5,stop=21.5,num=19), "multi_index": np.logspace(start=np.log10(1300), stop=np.log10(5800e3), num=30),
'pseudo_Russo': np.logspace(start=np.log10(903), stop=np.log10(2691700), num=30), 
'pseudo_Russo_area': np.logspace(start=np.log10(406), stop=np.log10(1756000), num=30), 'max_spatial' : np.logspace(start=np.log10(1500), stop=np.log10(10.7e6), num=30), 'max': 30,
"Global_mean_pop": np.logspace(start=np.log10(0.1), stop=np.log10(1e3), num=30), "Spatial_extent_pop": np.logspace(start=np.log10(5), stop=np.log10(26e6), num=30), 
"Duration_pop": np.logspace(start=np.log10(0.01), stop=np.log10(1.9e3), num=30), "multi_index_pop": np.logspace(start=np.log10(32), stop=np.log10(184300000), num=30),
'pseudo_Russo_pop': np.logspace(start=np.log10(23), stop=np.log10(82500000), num=30), 
'pseudo_Russo_area_pop': np.logspace(start=np.log10(9), stop=np.log10(57.8e6), num=30), 'max_spatial_pop' : np.logspace(start=np.log10(37), stop=np.log10(353500000), num=30), 
'max_pop': np.logspace(start=np.log10(0.1), stop=np.log10(1.7e3), num=30), 'multi_index_pop_mean': np.logspace(start=np.log10(13), stop=np.log10(127400000), num=30), 
'pseudo_Russo_area_pop_NL': np.logspace(start=np.log10(9), stop=np.log10(121629357900), num=30)} #bins of the histogram

savgol_window_dico = {"Global_mean": 15, "Spatial_extent": 9, "Duration": 7, "multi_index":7,'pseudo_Russo': 7, 'pseudo_Russo_area': 7, 'max_spatial': 9, 'max': 7,
"Global_mean_pop": 15, "Spatial_extent_pop": 9, "Duration_pop": 7, "multi_index_pop":7,'pseudo_Russo_pop': 7, 'pseudo_Russo_area_pop': 7, 'max_spatial_pop': 9, 'max_pop': 7,
'multi_index_pop_mean': 9, 'pseudo_Russo_area_pop_NL': 7} #window of the savitzky-golay filter for the histogram smoothing

clrs_dico = {"Total_Deaths": clrs.LogNorm(vmin=1, vmax=72210), "Total_Affected": clrs.Normalize(vmin=0, vmax=500), "Total_Damages": clrs.LogNorm(vmin=1, vmax=12120000) , "Impact_fct_1": clrs.LogNorm(vmin=1e4, vmax=157e6)} #colormap depending on the selected criterion

criteria_dico = {"Global_mean": 'Global Mean temperature anomaly (°C) of the heatwave', "Spatial_extent": 'Cumulative area (km²) of the heatwave', 
"Duration": 'Duration of the heatwaves in days', "multi_index": 'Temperature anomaly multiplied by the normalized cell area',
'pseudo_Russo': 'Sum of the Russo index over the heatwave', 'pseudo_Russo_area': 'Sum of the Russo index over the heatwave multiplied by the normalized cell area for each point', 
'max_spatial': 'Cumulative normalized area multiplied by the maximum temperature anomaly of the heatwave','max' : 'maximum temperature anomaly of the heatwave'} #Title depending on the chosen impact criterion

units_dico = {"Global_mean": '(°C)', "Spatial_extent": '(km²)', "Duration": '(days)', "multi_index": '(°C)', 'pseudo_Russo': '(dimensionless)', 'pseudo_Russo_area': '(dimensionless)','max_spatial': '(°C)', 'max': '(°C)'} #units of the chosen meteo criterion

pop_file = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/Pop/WorldPop/World_pop_2000_e-obs_grid.nc"
f_pop = nc.Dataset(pop_file,mode='r')

impact_criteria = ['Total_Deaths', 'Impact_fct_1'] #'Total_Affected', 'Total_Damages',
meteo_criteria = ['Global_mean','Spatial_extent','Duration','multi_index','pseudo_Russo','pseudo_Russo_area','max_spatial','max','Global_mean_pop','Duration_pop',
'Spatial_extent_pop','multi_index_pop','pseudo_Russo_pop','pseudo_Russo_area_pop','max_spatial_pop','max_pop','multi_index_pop_mean']

stefanon_htw = np.array([],dtype=np.int32)
stefanon_htw_dico={}

for i in range(len(liste_lignes)) : 
    if liste_lignes[i][csv_dico["Stefanon : détectée ?"]]=='Oui' :
        stefanon_htw = np.append(stefanon_htw,int(liste_lignes[i][csv_dico["Si oui, quel fichier"]][21:24])) #record the numbers of the heatwaves that were both found in E-OBS and EM-DAT
        if stefanon_htw[-1]!=171 :
            stefanon_htw_dico[stefanon_htw[-1]] = i  #link between heatwave number and corresponding line in EM-DAT csv file

stefanon_htw = np.unique(stefanon_htw)
not_computed_htw = np.array([212,213,219,238,239],dtype=np.int32) #all of these heatwaves are merged with other ones, so we must not count them twice
careful_htw = np.array([209,217,237],dtype=np.int32) #the heatwaves with which the previous ones are merged

#--------------------------

cell_area = np.array([6371**2*np.cos(np.pi*lat_in/180)*0.1*0.1]*705).T # the area in km² of each cell, depending on the latitude

chosen_meteo = 'pseudo_Russo_area_pop_NL'
chosen_impact = 'Total_Deaths'
power_NL_list=range(2,5)
threshold_NL_list=[300]

pop_file_worlpop = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/Pop/WorldPop/World_pop_all_2000-2020_e-obs_grid.nc"
f_pop_WP = nc.Dataset(pop_file_worlpop,mode='r')
pop_file_GHS= "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/Pop/GHS_pop/GHS_pop_all_e-obs_grid.nc"
f_pop_GHS = nc.Dataset(pop_file_GHS,mode='r')
pop_table = ma.array(np.zeros((23,len(lat_in),len(lon_in))))
pop_table[0:2,:,:] = ma.array([f_pop_GHS.variables['pop_density'][:]])
pop_table[2:,:,:] = ma.array([f_pop_WP.variables['pop_density'][:]])

file_txt=open("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/try_NL/criteria_distrib_correlations_try_NL.txt",'w')

pearsonR_table=np.zeros((len(threshold_NL_list),len(power_NL_list)))
class_perf_table=np.zeros((len(threshold_NL_list),len(power_NL_list)))

emdat_htw = np.zeros((len(threshold_NL_list),len(power_NL_list),len(stefanon_htw),3)) #impact,meteo,htw (htw_impact,htw_meteo,htw_number) in order to evalujate correlations at the end

nb_threshold = 0
for threshold_NL in threshold_NL_list :
    nb_power = 0
    for power_NL in  power_NL_list :
        #threshold_NL = 2500
        #power_NL = 2
        print('threshold_NL',threshold_NL, 'power_NL', power_NL)

        #print('Computing '+chosen_impact+' and '+chosen_meteo+' ...')

        impact_list = np.array([]) #record the impact of the EM-DAT heatwaves
        meteo_list = np.array([]) #record the meteo criterion of the E-OBS heatwaves
        idx_scatt = np.array([],dtype=np.int32) #record the meteo criterion of the EM-DAT heatwaves
        nb_htw_scatt = np.array([],dtype=np.int32) #record the numbers of the EM-DAT heatwaves

        for i in range(len(heatwaves_idx_2)) : #each heatwave has a number, ranging from 0 to 305 in my case
            #print(i)
            if i not in not_computed_htw and i not in careful_htw:
                temp = f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:]
                temp = ma.masked_where(temp==0,temp) #mask where heatwave is not happening
                pop = ma.array([f_pop.variables['pop_density'][:]]*np.shape(temp)[0])
                russo_idx_map = f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:]
                russo_idx_map = ma.masked_where(temp==0,russo_idx_map)
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                pop_unique = ma.masked_where(temp==0,pop)
                pop_unique = np.nanmean(pop_unique,axis=0)
                russo_idx_map = np.nansum(russo_idx_map,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*russo_idx_map*pop_unique*np.nanmax(temp*cell_area)*(pop_unique>threshold_NL))**power_NL + ((pop_unique<=threshold_NL)*cell_area**2*russo_idx_map*pop_unique*np.nanmax(temp*cell_area))))

            elif i in careful_htw :
                if i == 209 : #three heatwaves to merge
                    temp1 = f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:]
                    temp2 = f.variables['temp'][heatwaves_idx_2[212,0]:heatwaves_idx_2[212,0]+heatwaves_idx_2[212,1],:,:]
                    temp3 = f.variables['temp'][heatwaves_idx_2[213,0]:heatwaves_idx_2[213,0]+heatwaves_idx_2[213,1],:,:]

                    temp = ma.concatenate((temp1,temp2,temp3),axis=0)
                    del temp1
                    del temp2
                    del temp3
                    temp = ma.masked_where(temp==0,temp)

                    russo_idx_map1 = f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:]
                    russo_idx_map2 = f_Russo.variables['Russo_index'][heatwaves_idx[212,0]:heatwaves_idx[212,0]+heatwaves_idx_2[212,1],:,:]
                    russo_idx_map3 = f_Russo.variables['Russo_index'][heatwaves_idx[213,0]:heatwaves_idx[213,0]+heatwaves_idx_2[213,1],:,:]

                    russo_idx_map = ma.concatenate((russo_idx_map1,russo_idx_map2,russo_idx_map3),axis=0)
                    del russo_idx_map1
                    del russo_idx_map2
                    del russo_idx_map3
                    russo_idx_map = ma.masked_where(temp==0,russo_idx_map)

                elif i == 217 : #two heatwaves to merge
                    temp1 = f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:]
                    temp2 = f.variables['temp'][heatwaves_idx_2[219,0]:heatwaves_idx_2[219,0]+heatwaves_idx_2[219,1],:,:]
                    temp = ma.concatenate((temp1,temp2),axis=0)
                    del temp1
                    del temp2
                    temp = ma.masked_where(temp==0,temp)

                    russo_idx_map1 = f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:]
                    russo_idx_map2 = f_Russo.variables['Russo_index'][heatwaves_idx[219,0]:heatwaves_idx[219,0]+heatwaves_idx_2[219,1],:,:]

                    russo_idx_map = ma.concatenate((russo_idx_map1,russo_idx_map2),axis=0)
                    del russo_idx_map1
                    del russo_idx_map2
                    russo_idx_map = ma.masked_where(temp==0,russo_idx_map)

                elif i ==237 : #three heatwaves to merge
                    temp1 = f.variables['temp'][heatwaves_idx_2[i,0]:heatwaves_idx_2[i,0]+heatwaves_idx_2[i,1],:,:]
                    temp2 = f.variables['temp'][heatwaves_idx_2[238,0]:heatwaves_idx_2[238,0]+heatwaves_idx_2[238,1],:,:]
                    temp3 = f.variables['temp'][heatwaves_idx_2[239,0]:heatwaves_idx_2[239,0]+heatwaves_idx_2[239,1],:,:]
                    temp = ma.concatenate((temp1,temp2,temp3),axis=0)
                    del temp1
                    del temp2
                    del temp3                  
                    temp = ma.masked_where(temp==0,temp)

                    russo_idx_map1 = f_Russo.variables['Russo_index'][heatwaves_idx[i,0]:heatwaves_idx[i,0]+heatwaves_idx_2[i,1],:,:]
                    russo_idx_map2 = f_Russo.variables['Russo_index'][heatwaves_idx[238,0]:heatwaves_idx[238,0]+heatwaves_idx_2[238,1],:,:]
                    russo_idx_map3 = f_Russo.variables['Russo_index'][heatwaves_idx[239,0]:heatwaves_idx[239,0]+heatwaves_idx_2[239,1],:,:]

                    russo_idx_map = ma.concatenate((russo_idx_map1,russo_idx_map2,russo_idx_map3),axis=0)
                    del russo_idx_map1
                    del russo_idx_map2
                    del russo_idx_map3
                    russo_idx_map = ma.masked_where(temp==0,russo_idx_map)                    
                pop = ma.array([f_pop.variables['pop_density'][:]]*np.shape(temp)[0]) #Sum of Russo index over the heatwave (time and space), multiplied by the normalized cell area
                russo_idx_map = ma.masked_where(temp==0,russo_idx_map)
                max_area = np.max(cell_area)
                cell_area = cell_area/max_area
                pop_unique = ma.masked_where(temp==0,pop)
                pop_unique = np.nanmean(pop_unique,axis=0)
                russo_idx_map = np.nansum(russo_idx_map,axis=0)
                meteo_list=np.append(meteo_list,np.sum((cell_area**2*russo_idx_map*pop_unique**power_NL*np.nanmax(temp*cell_area)*(pop_unique>threshold_NL)) + ((pop_unique<=threshold_NL)*cell_area**2*russo_idx_map*pop_unique*np.nanmax(temp*cell_area))))

            if i in stefanon_htw and i not in not_computed_htw and i != 171:
                if chosen_impact != 'Impact_fct_1' :
                    impact_list = np.append(impact_list, int(liste_lignes[stefanon_htw_dico[i]][csv_dico[chosen_impact]])) #find selected impact in the csv file
                else : #Impact_fct_1 = Total_Damages + Total_Deaths*2e6 USD + Total_Affected * 50k USD
                    impact_list = np.append(impact_list, int(liste_lignes[stefanon_htw_dico[i]][csv_dico['Total_Deaths']])*2e3 + 
                    int(liste_lignes[stefanon_htw_dico[i]][csv_dico['Total_Affected']])*50 + 
                    int(liste_lignes[stefanon_htw_dico[i]][csv_dico['Total_Damages']])) #find selected impact in the csv file
                idx_scatt = np.append(idx_scatt,meteo_list[-1]) 
                nb_htw_scatt = np.append(nb_htw_scatt,i)
            elif i ==171 :
                impact_171=0
                for line in [14,15,16,17]:
                    if chosen_impact != 'Impact_fct_1' :
                        impact_171 += int(liste_lignes[line][csv_dico[chosen_impact]]) #find selected impact in the csv file
                    else :
                        impact_171 += (int(liste_lignes[line][csv_dico['Total_Deaths']])*2e3 + 
                        int(liste_lignes[line][csv_dico['Total_Affected']])*50 + 
                        int(liste_lignes[line][csv_dico['Total_Damages']])) #find selected impact in the csv file
                impact_list = np.append(impact_list,impact_171)
                idx_scatt = np.append(idx_scatt,meteo_list[-1])
                nb_htw_scatt = np.append(nb_htw_scatt,i)

        #-------------#
        # draw figure #
        #-------------#
        min_val = np.min(meteo_list)
        max_val = np.max(meteo_list)
        print(chosen_meteo,'min',np.min(meteo_list),'max',np.max(meteo_list))

        fig = plt.figure(1,figsize=(24,16))

        count_misplaced = 0
        for val in idx_scatt :
            for val2 in meteo_list :
                if val2 not in idx_scatt and val2>val :
                    count_misplaced += 1
                    plt.scatter([val2],[-1],s=4,c='b',marker='s')
        print('count_misplaced',count_misplaced)
        class_perf = 1/(1+count_misplaced)
        class_perf_table[nb_threshold,nb_power] = class_perf
        
        Y,bins_edges=np.histogram(meteo_list,bins=np.logspace(start=np.log10(0.97*min_val), stop=np.log10(1.03*max_val), num=30)) #histogram of the E-OBS heatwaves distribution
        X=[0]*len(Y)

        for k in range(len(Y)) :
           X[k]=(bins_edges[k+1]+bins_edges[k])/2
        Y=np.array(Y)
        Y2=signal.savgol_filter(Y, 7, 3) #smooth the histogram edges with a savitzky-golay filter
        if chosen_meteo in ['Duration','Global_mean','max'] : #have to plot on semilog scale for these criteria
           plt.plot(X,Y,'ko')
           plt.plot(X,Y2,'r-')
        else :
           plt.semilogx(X,Y,'ko')
           plt.semilogx(X,Y2,'r-')
        plt.axvline(np.median(meteo_list),linewidth=1) #add median of the meteo criterion list
        plt.grid()
        plt.xlabel(chosen_meteo)#+' '+units_dico[chosen_meteo])
        plt.ylabel('Frequency')
        plt.title('Heatwaves distribution over '+chosen_meteo+' criterion')# ('+criteria_dico[chosen_meteo]+')',y=1)
        nb_htw_scatt=nb_htw_scatt[idx_scatt.argsort()] #sort the EM-DAT heatwaves lists in order to have a more readable figure, but have to keep matching impact with the given number and meteo criterion
        impact_list=impact_list[idx_scatt.argsort()]
        idx_scatt.sort()
        if chosen_meteo == 'Duration' :
           for k in range(len(impact_list)):
               plt.annotate(str(nb_htw_scatt[k]),(idx_scatt[k],1+3*(k%6)),size=10,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
               y_scatt=6
               mark_size=2e4
        elif chosen_meteo == 'max_spatial' :
           for k in range(len(impact_list)):
               plt.annotate(str(nb_htw_scatt[k]),(idx_scatt[k],1+2*(k%4)),size=10,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
               y_scatt=3
               mark_size=15e3
        else :
           for k in range(len(impact_list)):
               plt.annotate(str(nb_htw_scatt[k]),(idx_scatt[k],1+(k%4)),size=10,rotation=45) #modulo to avoid superposition of the number annotation when same meteo criterion
               y_scatt=3
               mark_size=15e3

        CS1=plt.scatter(idx_scatt,[y_scatt]*len(idx_scatt),c=impact_list,s=[mark_size]*len(impact_list),cmap='YlOrRd',marker='|',norm=clrs_dico[chosen_impact],linewidths=4) #add the EM-DAT heatwaves along with their respective impact and numbers on the E-OBS heatwaves distribution
        cax = plt.axes([0.35, 0.04, 0.35, 0.01])
        plt.title('Impact of the extreme heatwaves '+chosen_impact,y=0.8)
        plt.colorbar(CS1,cax=cax,orientation='horizontal')

        plt.savefig("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/try_NL/Heatwaves_distrib_"+chosen_impact+"_"+chosen_meteo+"pow"+str(power_NL)+"thresh"+str(threshold_NL)+".png")
        #plt.show()
        #break

        fig.clear()

        emdat_htw[nb_threshold,nb_power,:,0] = impact_list
        emdat_htw[nb_threshold,nb_power,:,1] = idx_scatt
        emdat_htw[nb_threshold,nb_power,:,2] = nb_htw_scatt

        plt.plot(np.log10(idx_scatt),np.log10(impact_list),'k+')
        (slope,intercept,rvalue,pvalue,stderr)=stats.linregress(np.log10(idx_scatt),np.log10(impact_list))
        pearsonR_table[nb_threshold,nb_power] = rvalue
        X0 = np.min(np.log10(idx_scatt))
        Y0 = slope*X0+intercept
        X1 = np.max(np.log10(idx_scatt))
        Y1 = slope*X1+intercept
        print('pearson :',stats.pearsonr(np.log10(idx_scatt),np.log10(impact_list)))
        print('kendall :',stats.kendalltau(np.log10(idx_scatt),np.log10(impact_list)))
        print('spearman :',stats.spearmanr(np.log10(idx_scatt),np.log10(impact_list)))
        print('class_perf :',class_perf)
        print('class_perf x Rpearson :', class_perf*stats.pearsonr(np.log10(emdat_htw[nb_threshold,nb_power,:,1]),np.log10(emdat_htw[nb_threshold,nb_power,:,0]))[0])
        file_txt.write("power "+str(power_NL)+" thresh "+str(threshold_NL)+' : pearson R :'+str(stats.pearsonr(np.log10(idx_scatt),np.log10(impact_list)))+" "+
        'kendall tau :'+str(stats.kendalltau(np.log10(idx_scatt),np.log10(impact_list)))+" "+
        'spearman R :'+str(stats.spearmanr(np.log10(idx_scatt),np.log10(impact_list)))+'class_perf :' + str(class_perf) + 
        'class_perf x Rpearson :'+ str(class_perf*stats.pearsonr(np.log10(emdat_htw[nb_threshold,nb_power,:,1]),np.log10(emdat_htw[nb_threshold,nb_power,:,0]))[0]) + '\n')
        plt.plot([X0,X1],[Y0,Y1], 'k-')
        plt.annotate('R='+str(round(rvalue,5)),((X0+X1)/2,(Y0+Y1/2)))
        plt.grid()
        plt.ylabel('Log(Total_Deaths)')#+units_dico[meteo_criteria[j]])
        plt.xlabel('Log(pRusso_area_pop_NL) pow'+str(power_NL)+'thresh'+str(threshold_NL))

        plt.savefig("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/try_NL/correlations_try_NL_pow"+str(power_NL)+"thresh"+str(threshold_NL)+".png")
        fig.clear()
        nb_power += 1
    #break
    nb_threshold += 1
    print("Temps d'exécution : %f secondes" %(time.time()-start_time))

f_Russo.close()
f.close()
f_pop.close()
file_txt.close()

print("Temps d'exécution : %f secondes" %(time.time()-start_time))

print('max pearson :',np.max(pearsonR_table), 'min pearson :',np.min(pearsonR_table), 'argmax pearson :',np.argmax(pearsonR_table))
print('max class_perf :',np.max(class_perf_table), 'min class_perf :',np.min(class_perf_table), 'argmax class_perf :',np.argmax(class_perf_table))
print('max produit:',np.max(class_perf_table*pearsonR_table), 'min produit :',np.min(class_perf_table*pearsonR_table), 'argmax produit :',np.argmax(class_perf_table*pearsonR_table))

exit()

#Evaluate correlations between impact and meteo criteria for the EM-DAT heatwaves
print('Computing correlations ...')    

fig = plt.figure(2,figsize=(24,16))
plt.title('Correlation between meteo criteria and impact criteria for EM-DAT heatwaves')

for i in range(len(impact_criteria)) :
    for j in range(len(meteo_criteria)) :
        #plt.subplot(len(impact_criteria),len(meteo_criteria),1+i*len(meteo_criteria)+j)
        plt.subplot(4,9,1+i*len(meteo_criteria)+j)
        plt.grid()
        if meteo_criteria[j] in ['Duration','Global_mean','max'] : #and impact_criteria[i] == 'Total_Affected' :
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
            file_txt.write(meteo_criteria[j]+' : pearson R :'+str(stats.pearsonr(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))+" "+'kendall tau :'+str(stats.kendalltau(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))+" "+'spearman R :'+str(stats.spearmanr(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))+ '\n')
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
            file_txt.write(meteo_criteria[j]+' : pearson R :'+str(stats.pearsonr(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))+" "+'kendall tau :'+str(stats.kendalltau(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))+" "+'spearman R :'+str(stats.spearmanr(np.log10(emdat_htw[i,j,:,1]),np.log10(emdat_htw[i,j,:,0])))+ '\n')
            plt.plot([X0,X1],[Y0,Y1], 'k-')
            plt.annotate('R='+str(round(rvalue,5)),((X0+X1)/2,(Y0+Y1/2)))
            plt.xlabel('Log('+meteo_criteria[j]+') ')#+units_dico[meteo_criteria[j]])
            plt.ylabel('Log('+impact_criteria[i]+')')

plt.savefig("/home/theom/Bureau/Ubuntu_SSD/PFE/Code/Van_der_Wiel_graphs/try_NL/Heatwaves_distrib_correlations_try_NL.png")

f_Russo.close()
f.close()
f_pop.close()
file_txt.close()

print("Temps d'exécution : %f secondes" %(time.time()-start_time))