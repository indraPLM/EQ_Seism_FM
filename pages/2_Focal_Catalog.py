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
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests
from matplotlib.pyplot import figure
import geopandas
from obspy.imaging.beachball import beachball
from obspy.imaging.beachball import beach
import cartopy.crs as ccrs
import cartopy

st.set_page_config(page_title='Peta Focal Mechanism',  layout='wide', page_icon="🌍")

st.sidebar.header("FOCAL BMKG :")
time_start=st.sidebar.text_input('Start Time:', '2024-09-01 00:00:00')
time_end=st.sidebar.text_input('End Time:', '2025-01-31 23:59:59')

layout2 = st.sidebar.columns(2)
with layout2[0]: 
    North = st.text_input('North:', '6.0') 
    North = float(North)
with layout2[-1]: 
    South = st.text_input('South:', '-13.0')
    South = float(South)
 
layout3 = st.sidebar.columns(2)
with layout3[0]: 
    West = st.text_input('West:', '90.0')
    West = float(West)
with layout3[-1]: 
    East = st.text_input('East:', '142.0')
    East = float(East)

st.sidebar.header("Global CMT :")
time_start1=st.sidebar.text_input('Start Time:', '2000-01-01 00:00')
time_end1=st.sidebar.text_input('End Time:', '2020-12-31 23:59')

st.markdown( """ ### Peta Focal Mechanism BMKG (sumber : http://202.90.198.41/qc_focal.txt) """)

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
    for i in file[1:len(file)-2]:
        temp=i[par]
        data.append(temp)
    return data

event_id=get_fc(event_fc,0)
date_time=get_fc(event_fc,1)
date_create=get_fc(event_fc,2)
mode=get_fc(event_fc,3)
status=get_fc(event_fc,4)
mag=get_fc(event_fc,5)
type_mag= get_fc(event_fc,6)
latitude=get_fc(event_fc,7)
longitude=get_fc(event_fc,8)
depth=get_fc(event_fc,9)
S1=get_fc(event_fc,10)
D1=get_fc(event_fc,11)
R1=get_fc(event_fc,12)
S2=get_fc(event_fc,13)
D2=get_fc(event_fc,14)
R2=get_fc(event_fc,15)


df = pd.DataFrame({'event_id':event_id,'date_time':date_time,'date_create':date_create,'mode':mode,
                   'status':status,'mag':mag,'type_mag':type_mag,'lat':latitude,'lon':longitude,
                   'depth':depth,'S1':S1,'D1':D1,'R1':R1,'S2':S2,'D2':D2,'R2':R2})

def fix_longitude(x):
    x = x.strip()
    if x.endswith('W'):
        x = -float(x.strip('W'))
    else:        
        x = x.strip('E')        
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
                                       

cmt=df[['event_id','date_time','fixedLon','fixedLat','mag',
                  'depth','S1','D1','R1','S2','D2','R2']]

projection = ccrs.PlateCarree(central_longitude=120.0)

fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((West, East, South-2, North+2))
ax.add_feature(cartopy.feature.BORDERS, linestyle='-', linewidth=0.5,alpha=0.5)
ax.coastlines(resolution='10m', color='black', linestyle='-',linewidth=0.5,alpha=0.5)

cmt=df[['event_id','date_time','fixedLon','fixedLat','mag',
                  'depth','S1','D1','R1','S2','D2','R2']]
x0=list(cmt.fixedLon)
y0=list(cmt.fixedLat)
z0=list(cmt.depth)
a=list(cmt.S1)
b=list(cmt.D1)
c=list(cmt.R1)
fm_list=[]
xy_list=[]
for i in range(len(a)):
    x, y = projection.transform_point(x=x0[i], y=y0[i],src_crs=ccrs.Geodetic())
    focmecs=[a[i],b[i],c[i]]
    fm_list.append(focmecs)
    xy_list.append((x,y))

dist_lon=East-West
if dist_lon >55:
    w=1.5
if 40 < dist_lon <= 55:
    w=1.25
if 30 < dist_lon <= 40:
    w=1.0
if 15 < dist_lon <= 30:
    w=0.75
if 10 < dist_lon <= 15 :
    w=0.5
if 5 < dist_lon <= 10 :
    w=0.40
if dist_lon <= 5:
    w=0.30


for i in range(len(fm_list)):
    if z0[i] < 60:
        b = beach(fm_list[i], xy=xy_list[i],width=w, linewidth=0.5, alpha=0.65, zorder=10,facecolor='r')
        ax.add_collection(b)
    if 60 < z0[i] < 300:
        b = beach(fm_list[i], xy=xy_list[i],width=w, linewidth=0.5, alpha=0.65, zorder=10,facecolor='y')
        ax.add_collection(b)
    if z0[i] >= 300:
        b = beach(fm_list[i], xy=xy_list[i],width=w, linewidth=0.5, alpha=0.65, zorder=10,facecolor='g')
        ax.add_collection(b)

st.pyplot(fig)

st.dataframe(cmt)

## GLOBAL CMT

st.markdown( """ ### Peta Global CMT Harvard (sumber : https://www.globalcmt.org) """)

url='https://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/jan76_dec20.ndk' 
print(url)
page=requests.get(url)
url_pages=BeautifulSoup(page.text, 'html')

cmt=[]
for data in url_pages.find_all("p"): 
    a=data.get_text()
    cmt.append(a)
cmt_line=cmt[0].split('\n')

date_cmt,time_cmt,lat_cmt,lon_cmt,depth_cmt,mb_cmt,Ms_cmt,loc_cmt=[],[],[],[],[],[],[],[]
S1_cmt,D1_cmt,R1_cmt,S2_cmt,D2_cmt,R2_cmt=[],[],[],[],[],[]
datetime_cmt=[]
for i in range(int(len(cmt_line)/5)-1):
    date=cmt_line[(i*5)+0][5:15]
    time=cmt_line[(i*5)+0][16:21]
    lat=cmt_line[(i*5)+0][26:33]
    lon=cmt_line[(i*5)+0][35:41]
    depth=cmt_line[(i*5)+0][43:47]
    mb=cmt_line[(i*5)+0][47:51]
    Ms=cmt_line[(i*5)+0][52:55]
    loc=cmt_line[(i*5)+0][56:80]
    datetime=date+' '+time
    date_cmt.append(date)
    time_cmt.append(time)
    lat_cmt.append(lat)
    lon_cmt.append(lon)
    depth_cmt.append(depth)
    mb_cmt.append(mb)
    Ms_cmt.append(Ms)
    loc_cmt.append(loc)
    datetime_cmt.append(datetime)
   
    S1=cmt_line[(i*5)+4][56:60]
    D1=cmt_line[(i*5)+4][61:64]
    R1=cmt_line[(i*5)+4][65:69]
    S2=cmt_line[(i*5)+4][69:72]
    D2=cmt_line[(i*5)+4][73:76]
    R2=cmt_line[(i*5)+4][77:80]
    S1_cmt.append(S1)
    D1_cmt.append(D1)
    R1_cmt.append(R1)
    S2_cmt.append(S2)
    D2_cmt.append(D2)
    R2_cmt.append(R2)

df = pd.DataFrame({'Datetime':datetime_cmt,'Mag_mb':mb_cmt,'Mag_Ms':Ms_cmt,'Lat':lat_cmt,'Lon':lon_cmt,
                       'Depth':depth_cmt,'S1':S1_cmt,'D1':D1_cmt,'R1':R1_cmt,
                       'S2':S2_cmt,'D2':D2_cmt,'R2':R2_cmt,'Location':loc_cmt})
def fix_float(z):
    temp=[]
    for i in range(len(z)):
        b=float(z[i])
        temp.append(b)
    return temp

df['Datetime'] = pd.to_datetime(df['Datetime'])
df['Lon'] = pd.to_numeric(df['Lon'],errors = 'coerce')
df['Lat'] = pd.to_numeric(df['Lat'],errors = 'coerce')

df['Mag_mb'] = fix_float(df['Mag_mb'])
df['Mag_Ms'] = fix_float(df['Mag_Ms'])
df['Depth'] = fix_float(df['Depth'])

df['S1'] = fix_float(df['S1'])
df['D1'] = fix_float(df['D1'])
df['R1'] = fix_float(df['R1'])

df['S2'] = fix_float(df['S2'])
df['D2'] = fix_float(df['D2'])
df['R2'] = fix_float(df['R2'])

df= df[(df['Datetime'] > time_start1) & (df['Datetime'] < time_end1)]
df= df[(df['Lon'] > West) & (df['Lon'] < East)]
df= df[(df['Lat'] > South) & (df['Lat'] < North)]

region=[West,East,South-1,North+1]

projection = ccrs.PlateCarree(central_longitude=120.0)

fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((West1, East1, South1-2, North1+2))
ax.add_feature(cartopy.feature.BORDERS, linestyle='-', linewidth=0.5,alpha=0.5)
ax.coastlines(resolution='10m', color='black', linestyle='-',linewidth=0.5,alpha=0.5)

cmt=df[['Datetime','Lon','Lat','Mag_mb','Mag_Ms',
                  'Depth','S1','D1','R1','S2','D2','R2']]
x0=list(cmt.Lon)
y0=list(cmt.Lat)
z0=list(cmt.Depth)
a=list(cmt.S1)
b=list(cmt.D1)
c=list(cmt.R1)
fm_list=[]
xy_list=[]
for i in range(len(a)):
    x, y = projection.transform_point(x=x0[i], y=y0[i],src_crs=ccrs.Geodetic())
    focmecs=[a[i],b[i],c[i]]
    fm_list.append(focmecs)
    xy_list.append((x,y))

dist_lon=East-West
if dist_lon >55:
    w=1.5
if 40 < dist_lon <= 55:
    w=1.25
if 30 < dist_lon <= 40:
    w=1.0
if 15 < dist_lon <= 30:
    w=0.75
if 10 < dist_lon <= 15 :
    w=0.5
if 5 < dist_lon <= 10 :
    w=0.40
if dist_lon <= 5:
    w=0.30


for i in range(len(fm_list)):
    if z0[i] < 60:
        b = beach(fm_list[i], xy=xy_list[i],width=w, linewidth=0.5, alpha=0.65, zorder=10,facecolor='r')
        ax.add_collection(b)
    if 60 < z0[i] < 300:
        b = beach(fm_list[i], xy=xy_list[i],width=w, linewidth=0.5, alpha=0.65, zorder=10,facecolor='y')
        ax.add_collection(b)
    if z0[i] >= 300:
        b = beach(fm_list[i], xy=xy_list[i],width=w, linewidth=0.5, alpha=0.65, zorder=10,facecolor='g')
        ax.add_collection(b)

st.pyplot(fig)

st.dataframe(cmt)
