"""Extract European heatwave events from GDIS and EM-DAT databases (Excel file and geopackage).
This script is also used to merge events that have the same 'disasterno': 
a single event is initially registered several times, one for each affected 
country/administrative region, and we sum damages and merge affected 
territories into one single event."""
#%%
import pandas as pd
import numpy as np
#%%
#Extract only European heatwaves from EM-DAT Europe extreme events (1950-2022):
#EM-DAT data can be downloaded at https://public.emdat.be/
df_emdat = pd.read_excel('Data/GDIS_EM-DAT/emdat_public_2023_07_04_Europe&Turkey.xlsx',header=6,dtype={'Seq': str,'Year': str})
#Add disasterno feature to be able to 'joint' easily with GDIS
df_emdat.insert(3,'disasterno',df_emdat.loc[:,'Year']+'-'+df_emdat.loc[:,'Seq'])
df_emdat=df_emdat[df_emdat['Disaster Subtype']=='Heat wave']
df_emdat.to_excel('Data/GDIS_EM-DAT/EMDAT_Europe-1950-2022-heatwaves.xlsx')

#%%
#Merge events in EM-DAT excel file
df_emdat.insert(32,'Start Date (DD-MM-YYYY)',f"{df_emdat.loc[:,'Start Day']}-{df_emdat.loc[:,'Start Month']}-{df_emdat.loc[:,'Start Year']}") #insert a Start date
df_emdat.insert(36,'End Date (DD-MM-YYYY)',f"{df_emdat.loc[:,'End Day']}-{df_emdat.loc[:,'End Month']}-{df_emdat.loc[:,'End Year']}") #insert a End date
output_df = pd.DataFrame(columns=df_emdat.columns.values)

idx=1
for code in np.unique(df_emdat.loc[:,'disasterno'].values):
    try :
        output_df.loc[idx,:]=df_emdat[df_emdat['disasterno']==code].iloc[0,:]
    except :
        output_df.loc[idx,:]=df_emdat[df_emdat['disasterno']==code]
    for item in ["AID Contribution ('000 US$)",'Total Deaths','No Injured','No Affected','No Homeless','Total Affected',"Reconstruction Costs ('000 US$)","Reconstruction Costs, Adjusted ('000 US$)","Insured Damages ('000 US$)","Insured Damages, Adjusted ('000 US$)","Total Damages ('000 US$)","Total Damages, Adjusted ('000 US$)"]:#damages items that are summed
        output_df.loc[idx,item] = df_emdat[df_emdat['disasterno']==code].loc[:,item].sum()
    for item in ['Dis No','Country','ISO','Region','Location','Origin','Associated Dis','Associated Dis2','OFDA Response','Appeal','Declaration','Dis Mag Value','Dis Mag Scale','Latitude','Longitude','Local Time','River Basin','Start Year','Start Month','Start Day','Start Date (DD-MM-YYYY)','End Year','End Month','End Day','End Date (DD-MM-YYYY)','Adm Level','Admin1 Code','Admin2 Code','Geo Locations']:#text items that are concatenated
        output_df.loc[idx,item]=''
        for line in df_emdat[df_emdat['disasterno']==code].index.values :
            output_df.loc[idx,item] += str(df_emdat.loc[line,item]) + ' ; '
        output_df.loc[idx,item] = output_df.loc[idx,item][:-3]
    idx+=1

#Export Excel file
output_df.to_excel('Data/GDIS_EM-DAT/EMDAT_Europe-1950-2022-heatwaves_merged.xlsx')