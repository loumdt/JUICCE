""" This script is used to download and extract GHS-POP data to the given resolution"""

import sys,os
import requests
import zipfile
import io


try : 
    coord_sys = sys.argv[1] #'Mollweide' or 'WGS84'
except :
    coord_sys = 'Mollweide' #'Mollweide' or 'WGS84'
    
try : 
    resolution = str(sys.argv[2]) #'Mollweide' or 'WGS84'
except :
    resolution = '1000' #'1000' or '100' meters in 'Mollweide', '3SS' or '30SS' for 'WGS84'

print('coord_sys :', coord_sys)
print('resolution :', resolution)

coord_sys_dict = {'Mollweide':'54009','WGS84':'4326'}

download_dir = "Data/Pop/GHS_POP"
extract_dir = download_dir

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

if not os.path.exists(extract_dir):
    os.makedirs(extract_dir)

def download_data(year, resolution, coord_sys):
    year = str(year)
    
    url = f"https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2022A/GHS_POP_E{year}_GLOBE_R2022A_{coord_sys_dict[coord_sys]}_{resolution}/V1-0/GHS_POP_E{year}_GLOBE_R2022A_{coord_sys_dict[coord_sys]}_{resolution}_V1_0.zip"

    filename = f"GHS_POP_E{year}_GLOBE_R2022A_{coord_sys_dict[coord_sys]}_{resolution}_V1_0.zip"
    download_path = os.path.join(download_dir, filename)
    response = requests.get(url)
    if response.status_code == 200:
        with open(download_path, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(download_path) as z:
            z.extractall(extract_dir)
            print(f"Data downloaded and extracted successfully for year {year} at resolution {resolution}.")
    else:
        print(f"Failed to download data for year {year} at resolution {resolution}")


years = [1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020]
for year in years:
    download_data(year, resolution, coord_sys)