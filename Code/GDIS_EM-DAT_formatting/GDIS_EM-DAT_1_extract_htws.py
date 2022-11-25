"""Extract European heatwave events from GDIS and EM-DAT databases (Excel file and geopackage)."""
#%%
import pandas as pd
import geopandas as gpd
#%%
#Extract only European heatwaves from EM-DAT Europe extreme events (1950-2022):
#EM-DAT data can be downloaded at https://public.emdat.be/
df_emdat = pd.read_excel('D:/Ubuntu/These/Data/GDIS_EM-DAT/emdat_public_2022_11_10_Europe.xlsx',header=6,dtype={'Seq': str,'Year': str})
#Add disasterno feature to be able to 'joint' easily with GDIS
df_emdat.insert(3,'disasterno',df_emdat.loc[:,'Year']+'-'+df_emdat.loc[:,'Seq'])
df_emdat=df_emdat[df_emdat['Disaster Subtype']=='Heat wave']
df_emdat.to_excel('D:/Ubuntu/These/Data/GDIS_EM-DAT/EMDAT_Europe-1950-2022-heatwaves.xlsx')
#%%
#Extract European heatwaves from GDIS, using newly created EM-DAT database
df_htw = pd.read_excel('D:/Ubuntu/These/Data/GDIS_EM-DAT/pend-gdis-1960-2018-disasterlocations.xlsx',header=0)
df_htw.replace({'extreme temperature ': 'extreme temperature'}, regex=True,inplace=True) #suppress text space at the end, to avoid future mistakes
df_htw = df_htw[df_htw['disasterno'].isin(df_emdat.loc[:,'disasterno'].values)]
df_htw.to_excel('D:/Ubuntu/These/Data/GDIS_EM-DAT/GDIS_Europe-1960-2018-heatwaves.xlsx')

#GeoPackage file :
df_htw = gpd.read_file('D:/Ubuntu/These/Data/GDIS_EM-DAT/pend-gdis-1960-2018-disasterlocations.gpkg')
df_htw.replace({'extreme temperature ': 'extreme temperature'}, regex=True,inplace=True) #suppress text space at the end, to avoid future mistakes
df_htw = df_htw[df_htw['disasterno'].isin(df_emdat.loc[:,'disasterno'].values)]
df_htw.to_file('D:/Ubuntu/These/Data/GDIS_EM-DAT/GDIS_Europe-1960-2018-heatwaves.gpkg')