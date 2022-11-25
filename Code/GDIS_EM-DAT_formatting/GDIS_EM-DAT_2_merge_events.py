"""This script is used to merge events that have the same 'disasterno': 
a single event is initially registered several times, one for each affected 
country/administrative region, and we sum damages and merge affected 
territories into one single event."""
#%%
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
import shapely

#%%
#Merge events in EM-DAT excel file

df_emdat = pd.read_excel('D:/Ubuntu/These/Data/GDIS_EM-DAT/EMDAT_Europe-1950-2022-heatwaves.xlsx',header=0,index_col=0,dtype={'Start Year': str,'End Year': str,'Start Month': str,'End Month': str,'Start Day': str,'End Day': str,'Adm Level': str,'Admin1 Code': str,'Admin2 Code': str})

df_emdat.insert(32,'Start Date (DD-MM-YYYY)',df_emdat.loc[:,'Start Day']+'-'+df_emdat.loc[:,'Start Month']+'-'+df_emdat.loc[:,'Start Year']) #insert a Start date
df_emdat.insert(36,'End Date (DD-MM-YYYY)',df_emdat.loc[:,'End Day']+'-'+df_emdat.loc[:,'End Month']+'-'+df_emdat.loc[:,'End Year']) #insert an End date
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
output_df.to_excel('D:/Ubuntu/These/Data/GDIS_EM-DAT/EMDAT_Europe-1950-2022-heatwaves_merged.xlsx')

#%%
#Merge events in GDIS GeoPackage file
df_gdis = gpd.read_file('D:/Ubuntu/These/Data/GDIS_EM-DAT/GDIS_Europe-1960-2018-heatwaves.gpkg',header=0,index_col=0,dtype={'disasterno': str,'geometry':shapely.geometry.multipolygon.MultiPolygon})
output_df_gdis = gpd.GeoDataFrame(columns=df_gdis.columns.values)

idx=1
for code in np.unique(df_gdis.loc[:,'disasterno'].values):
    output_df_gdis.loc[idx,:]=df_gdis[df_gdis['disasterno']==code].iloc[0,:]
    for item in ['id','country','iso3','gwno','geo_id','geolocation','level','adm1','adm2','adm3','location','historical','hist_country']:
        output_df_gdis.loc[idx,item]=''
        for line in df_gdis[df_gdis['disasterno']==code].index.values :
            output_df_gdis.loc[idx,item] += str(df_gdis.loc[line,item]) + ' ; '
        output_df_gdis.loc[idx,item] = output_df_gdis.loc[idx,item][:-3]
    
    new_geom=[unary_union(df_gdis[df_gdis['disasterno']==code].loc[:,'geometry'].values)]
    output_df_gdis.loc[[idx], 'geometry'] = gpd.GeoDataFrame(geometry=new_geom).geometry.values

    idx+=1

#Export Geopackage file
output_df_gdis.to_file('D:/Ubuntu/These/Data/GDIS_EM-DAT/GDIS_Europe-1960-2018-heatwaves_merged.gpkg',driver ='GPKG')