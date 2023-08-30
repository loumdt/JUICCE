#%%
import plotly.graph_objects as go
import numpy as np
import numpy.ma as ma
import netCDF4 as nc
import os
from tqdm import tqdm

from dash import Dash, dcc, html
from base64 import b64encode
import io
#%%
#PC or spirit server?
if os.name == 'nt' :
    datadir = "Data/"
else : 
    datadir = os.environ["DATADIR"]
#%%
#os.chdir("../../..")
#%%
f_label = nc.Dataset(os.path.join(datadir,"ERA5","t2m","Detection_Canicule","detected_heatwaves_tg_anomaly_JJA_1950_2021_threshold_95th_4days.nc"))
time_in = f_label.variables['time'][:]
lat_in = f_label.variables['lat'][:]
lon_in = f_label.variables['lon'][:]

f_land_sea_mask = nc.Dataset(os.path.join(datadir,"ERA5","Mask","land_sea_mask_ERA5_0.25deg.nc"))
topography = f_land_sea_mask.variables['land_density'][:].data

f_temp = nc.Dataset(os.path.join(datadir,"ERA5","t2m","Detection_Canicule","potential_heatwaves_tg_4days_before_scan_1950_2021_95th.nc"))
#%%
labels = f_label.variables['label'][92*0:92*1,:,:]
temp = f_temp.variables['t2m'][92*0:92*1,:,:]

id_label_list = []
for id in np.unique(labels) :
    try :
        id_label_list.append(int(id))
    except :
        pass
#%%
#heatwave = heatwave[:].data
#%%
# Create a grid of points based on longitude, latitude, and time
lon = lon_in.data[:]
lat = lat_in.data[:]
time = np.arange(0, 92, 1)

time_mesh, lat_mesh, lon_mesh = np.meshgrid(time, lat, lon, indexing='ij')

#%%
#fig = go.Figure(data=[go.Volume(x=lon_non_null.flatten(), y=lat_non_null.flatten(), z=time_non_null.flatten(), value=temp_non_null.flatten(), opacity=0.7, isomin=-15, isomax=15)])
#%%
fig = go.Figure()
for year in range(92):
    for id_label in tqdm(id_label_list[0:]) :
        heatwave=ma.masked_where(labels.data!=id_label,temp[:])
        heatwave[:]=ma.filled(heatwave[:],fill_value=-9999)
        heatwave = heatwave[:].data
        #if id_label==2:
        #    temp_non_null = heatwave[heatwave != -9999]
        #    time_non_null = time_mesh[heatwave != -9999]
        #    lat_non_null = lat_mesh[heatwave != -9999]
        #    lon_non_null = lon_mesh[heatwave != -9999]
        #    fig.add_trace(go.Volume(x=lon_non_null, y=lat_non_null, z=time_non_null, value=temp_non_null, opacity=0.5, isomin=-15, isomax=15,colorscale='RdBu_r'))
        #    break
        fig.add_trace(go.Volume(x=lon_mesh.flatten(), y=lat_mesh.flatten(), z=time_mesh.flatten(), value=heatwave.flatten(), opacity=0.5, isomin=-15, isomax=15,colorscale='RdBu_r',surface_count=25))
        break
    #fig.add_surface(z=topography.flatten(), x=lon_mesh[0,:,:].flatten(), y=lat_mesh[0,:,:].flatten())
    fig.update_layout(scene=dict(xaxis_title='Longitude', yaxis_title='Latitude', zaxis_title='Time'))
#fig.write_html("docs/heatwaves_3D_1950.html")
#fig.show(renderer="browser")

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)

#%%
#exit()
#%%
# fig = go.Figure(data=[go.Volume(x=lon_mesh.flatten(), y=lat_mesh.flatten(), z=time_mesh.flatten(), value=heatwave.flatten(), opacity=0.5, isomin=-15, isomax=15,colorscale='RdBu_r',surface_count=17)])
# fig.update_layout(scene=dict(xaxis_title='Longitude', yaxis_title='Latitude', zaxis_title='Time'))
# fig.show(renderer="browser") 