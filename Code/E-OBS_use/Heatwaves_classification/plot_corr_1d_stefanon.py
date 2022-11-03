import netCDF4 as nc
import numpy as np
import csv
import numpy.ma as ma
import matplotlib.pyplot as plt

cr = csv.reader(open("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/EM-DAT/emdat_Europe_1950-2021_heatwaves.csv","r"))
liste_lignes = list(cr)

nc_file = "/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/compress_heatwaves_4days_scan_2nd_step_TWICE_tg_anomaly_threshold_95th_scan_size35_10.0%.nc"

f = nc.Dataset(nc_file,mode='r')
lon_in = f.variables['lon'][:]
lat_in = f.variables['lat'][:]

csv_dico = {"Total_Deaths": 36, "Total_Affected": 40, "Total_Damages": 43, "Stefanon : détectée ?": 46, "Si oui, quel fichier": 47}

heatwaves_idx_2 = np.load("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_2_4days_V3.npy",allow_pickle = True)
heatwaves_dates = np.load("/home/theom/Bureau/Ubuntu_SSD/PFE/Data/E-OBS/Detection_Canicule/heatwaves_dates_4days_V3.npy",allow_pickle = True)

impact_criteria = ['Total_Deaths', 'Total_Affected', 'Total_Damages']
meteo_criteria = ['Global_mean','Spatial_extent','Duration']

cell_area = np.array([6371**2*np.cos(np.pi*lat_in/180)*0.1*0.1]*705).T # the area in km² of each cell, depending on the latitude

stefanon_htw=np.array([])
 
count_fig = 1
for chosen_impact in impact_criteria:
    for chosen_meteo in meteo_criteria :

        impact_list = np.array([])
        meteo_list = np.array([])

        for i in range(len(heatwaves_idx_2)) :
            if i not in not_computed_htw and i not in careful_htw: 
                nb_htw = int(liste_lignes[i][csv_dico["Si oui, quel fichier"]][21:24])
                #print(nb_htw)
                idx_htw = heatwaves_idx_2[nb_htw]
                #print(idx_htw)
                temp = f.variables['temp'][idx_htw[0]:idx_htw[0]+idx_htw[1],:,:]
                temp = ma.masked_where(temp==0,temp)
                if chosen_meteo == 'Global_mean' :
                    meteo_list = np.append(meteo_list,np.mean(temp))
                elif chosen_meteo == 'Spatial_extent' :
                    cell_area_3d = np.array([cell_area]*idx_htw[1])
                    meteo_list = np.append(meteo_list, np.sum(cell_area_3d*temp>0)) #area of the considered heatwave in km²
                elif chosen_meteo == 'Duration' :
                    meteo_list = np.append(meteo_list,idx_htw[1]) #duration in days