import numpy as np
from tqdm import tqdm
import sys

the_variable = str(sys.argv[1])

heatwaves_idx = np.load("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_idx_4days_"+the_variable+"_V3.npy",allow_pickle=True)

file_txt=open("D:/Ubuntu/PFE/Data/E-OBS/Detection_Canicule/heatwaves_days_"+the_variable+"_Theo.txt",'w')
for htw in tqdm(heatwaves_idx) :
    file_txt.write(str(htw[0])+" "+str(htw[1])+" "+str(htw[1]-htw[0]+1) + '\n')

file_txt.close()