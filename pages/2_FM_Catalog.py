# -*- coding: utf-8 -*-
"""
Created on Mon Jul  4 17:58:06 2022

@author: Asus
"""

import streamlit as st
from PIL import Image
from urllib.error import URLError
import pandas as pd
import os,sys
import geopandas as gpd
#from geodatasets import get_path
#from shapely.geometry import Point
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
#import pygmt
from matplotlib.pyplot import figure
import geopandas
from obspy.imaging.beachball import beachball
#from IPython.core.display import display,HTML

st.set_page_config(page_title='Peta Focal Mechanism',  layout='wide', page_icon="🌍")
#st.title('Peta Focal Mechanism')

st.sidebar.header("Input Parameter :")
time_start=st.sidebar.text_input('Start Time:', '2024-09-01 00:00:00')
time_end=st.sidebar.text_input('End Time:', '2025-01-31 23:59:59')

layout2 = st.sidebar.columns(2)
with layout2[0]: 
    North = st.number_input('North:', 6.0) 
with layout2[-1]: 
    South = st.number_input('South:', -13.0)
 
layout3 = st.sidebar.columns(2)
with layout3[0]: 
    West = st.number_input('West:', 90.0)
with layout3[-1]: 
    East = st.number_input('East:', 142.0)

### ----------------------- Obtaining Waveform & Plotting  ----------------------
st.markdown( """ ### Peta Focal Mechanism """)

url='http://202.90.198.41/qc_focal.txt'
page=requests.get(url)
url_pages=BeautifulSoup(page.text, 'html')
a=[]
for fo in url_pages.p:
    a.append(fo)
b=a[0].split('\n')
event_fc=[]
for i in range(len(b)):
    fc=b[i].split('|')
    event_fc.append(fc)

def get_fc(file,par):
    par=par
    data=[]
    for i in file[1:600]:
        temp=i[par]
        data.append(temp)
    return data

event_id=get_fc(event_fc,0)
date_time=get_fc(event_fc,1)
mode=get_fc(event_fc,2)
status=get_fc(event_fc,3)
phase=get_fc(event_fc,4)
mag=get_fc(event_fc,5)
type_mag= get_fc(event_fc,6)
n_mag=get_fc(event_fc,7)
azimuth=get_fc(event_fc,8)
rms=get_fc(event_fc,9)
latitude=get_fc(event_fc,10)
longitude=get_fc(event_fc,11)
depth=get_fc(event_fc,13)
S1=get_fc(event_fc,14)
D1=get_fc(event_fc,15)
R1=get_fc(event_fc,16)
S2=get_fc(event_fc,17)
D2=get_fc(event_fc,18)
R2=get_fc(event_fc,19)
type_event=get_fc(event_fc,20)
remarks=get_fc(event_fc,21)

df = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mode':mode,'status':status,
                  'phase':phase,'mag':mag,'type_mag':type_mag,'n_mag':n_mag,'azimuth':azimuth,
                 'rms':rms,'lat':latitude,'lon':longitude,'depth':depth,'S1':S1,'D1':D1,'R1':R1,
                  'S2':S2,'D2':D2,'R2':R2,'type_event':type_event,'remarks':remarks})

def fix_longitude(x):
    x = x.strip()
    if x.endswith('W'):
        x = -float(x.strip('W'))
        #print(x)
    else:
        #print(x)
        x = x.strip('E')
        #print(x)
    return x

def fix_latitude(y):
    y = y.strip()
    if y.endswith('S'):
        y = -float(y.strip('S'))
    else:
        y = y.strip('N')
    return y

def fix_float(z):
    temp=[]
    for i in range(len(z)):
        b=float(z[i])
        temp.append(b)
    return temp

df['fixedLat'] = df.lat.apply(fix_latitude)
df['fixedLat'] = pd.to_numeric(df['fixedLat'],errors = 'coerce')

df['fixedLon'] = df.lon.apply(fix_longitude)
df['fixedLon'] = pd.to_numeric(df['fixedLon'],errors = 'coerce')

df['date_time'] = pd.to_datetime(df['date_time'])
df['mag'] = fix_float(df['mag'])
df['depth'] = fix_float(df['depth'])

df['S1'] = fix_float(df['S1'])
df['D1'] = fix_float(df['D1'])
df['R1'] = fix_float(df['R1'])

df['S2'] = fix_float(df['S2'])
df['D2'] = fix_float(df['D1'])
df['R2'] = fix_float(df['R1'])

df= df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df= df[(df['fixedLon'] > West) & (df['fixedLon'] < East)]
df= df[(df['fixedLat'] > South) & (df['fixedLat'] < North)]

region=[West,East,South-1,North+1]
                                       
#fig = pygmt.Figure()
#fig.basemap(region=region, projection="M40", frame=True)
#fig.coast(land="grey", water="lightblue",borders="1/1p,black",shorelines=True)
#pygmt.makecpt(cmap="viridis", series=[df.depth.min(), df.depth.max()])
#fig.plot(
#    x=df.fixedLon,
#    y=df.fixedLat,
#    size=0.02 * 2**df.mag,
#    fill=df.depth,
#    cmap=True,
#    style="cc",
#    pen="black",
#)
#fig.colorbar(frame="xaf+lDepth (km)")
#fig.savefig('fc_eq_map.png')

#image = Image.open('fc_eq_map.png')
#st.image(image, caption='Peta Seismisitas Focal Mechanism')

#focal_mechanism=dict(strike=df['S1'].tolist(),dip=df['D1'].tolist(),
#                     rake=df['R1'].tolist(),magnitude=df['mag'].tolist(),)

#fig = pygmt.Figure()
#fig.coast(region=region,projection="M40", land="grey",water="lightblue",
#          borders="1/1p,black",shorelines=True,frame="a",)
#fig.meca(spec=focal_mechanism, scale="1c", longitude=df['fixedLon'].tolist(),
#         latitude=df['fixedLat'].tolist(), depth=df['depth'].tolist(),)
#fig.show()
#fig.savefig('fc_map.png')

#image = Image.open('fc_map.png')
#st.image(image, caption='Peta Focal Mechanism')

#st.markdown( """ ### Tabel Data Focal Mechanism """)
cmt=df[['event_id','date_time','fixedLon','fixedLat','mag',
                  'depth','S1','D1','R1','S2','D2','R2']]

st.dataframe(cmt)

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from obspy.imaging.beachball import beach

#region=[West,East,South-1,North+1]
projection = ccrs.PlateCarree(central_longitude=120.0)

fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((85, 145, -15, 10))
ax.coastlines()
ax.gridlines()

x1, y1 = projection.transform_point(x=115, y=-13,src_crs=ccrs.Geodetic())
x2, y2 = projection.transform_point(x=95, y=-1,src_crs=ccrs.Geodetic())
#focmecs = [0.136, -0.591, 0.455, -0.396, 0.046, -0.615]
focmecs1 = [280, 10, 90]
focmecs2 = [330, 10, 80]

ax = plt.gca()
b1 = beach(focmecs1, xy=(x1, y1), width=2, linewidth=1, alpha=0.85)
b2 = beach(focmecs2, xy=(x2, y2), width=2, linewidth=1, alpha=0.85)
b1.set_zorder(2)
ax.add_collection(b1)
b2.set_zorder(2)
ax.add_collection(b2)

st.pyplot(fig)
#plt.show()
