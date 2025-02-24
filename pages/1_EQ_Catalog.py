# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 05:05:03 2023

@author: Indra Gunawan
"""
import streamlit as st
from PIL import Image
import numpy as np
#import pydeck as pdk
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os,sys
import geopandas as gpd
#from shapely.geometry import Point
import matplotlib.pyplot as plt
#import pygmt
from matplotlib.pyplot import figure


st.set_page_config(page_title='Earthquake Catalog, Statistik & Plotting',  layout='centered', page_icon="🌍")
#st.title('Seismisitas dan Statistik Kegempaan')

st.sidebar.header("Input Parameter :")
 
time_start=st.sidebar.text_input('Start Time:', '2025-01-01 00:00:00')
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

   
### -----------------------Earthquake Catalog ----------------------
st.markdown(
    """
    ### Peta Seismisitas dan Statistik Kegempaaan
    """)

url='http://202.90.198.41/qc.txt'
page=requests.get(url)
url_pages=BeautifulSoup(page.text, 'html')

a=[]
for fo in url_pages.p:
    a.append(fo)
b=a[0].split('\n')
event_qc=[]
for i in range(len(b)):
    qc=b[i].split('|')
    event_qc.append(qc)

def get_qc(file,par):
    par=par
    data=[]
    for i in file[1:9000]:
        temp=i[par]
        data.append(temp)
    return data

event_id=get_qc(event_qc,0)
date_time=get_qc(event_qc,1)
mode=get_qc(event_qc,2)
status=get_qc(event_qc,3)
phase=get_qc(event_qc,4)
mag=get_qc(event_qc,5)
type_mag= get_qc(event_qc,6)
n_mag=get_qc(event_qc,7)
azimuth=get_qc(event_qc,8)
rms=get_qc(event_qc,9)
latitude=get_qc(event_qc,10)
longitude=get_qc(event_qc,11)
depth=get_qc(event_qc,12)
type_event=get_qc(event_qc,13)
remarks=get_qc(event_qc,14)

df = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mode':mode,
                   'status':status,'phase':phase,'mag':mag,'type_mag':type_mag,
                   'n_mag':n_mag,'azimuth':azimuth,'rms':rms,'lat':latitude,
                   'lon':longitude,'depth':depth,'type_event':type_event,'remarks':remarks})

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

def fix_depth(z):
    z = z.strip()
    if z.endswith('km'):
        z = float(z.strip('km'))
    return z
    
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

df['fixedDepth'] = df.depth.apply(fix_depth)
df['fixedDepth'] = pd.to_numeric(df['fixedDepth'],errors = 'coerce')

df['date_time'] = pd.to_datetime(df['date_time'])
df['mag'] = fix_float(df['mag'])

df= df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df= df[(df['fixedLon'] > West) & (df['fixedLon'] < East)]
df= df[(df['fixedLat'] > South) & (df['fixedLat'] < North)]

#region=[West,East,South-1,North+1]
                                       
#fig = pygmt.Figure()
#fig.basemap(region=region, projection="M40", frame=True)
#fig.coast(land="grey", water="lightblue",borders="1/1p,black",shorelines=True)
#pygmt.makecpt(cmap="viridis", series=[df.fixedDepth.min(), df.fixedDepth.max()])
#fig.plot(
#    x=df.fixedLon,
#    y=df.fixedLat,
#    size=0.02* 2**df.mag,
#   fill=df.fixedDepth,
#    cmap=True,
#    style="cc",
#    pen="black",
#)
#fig.colorbar(frame="xaf+lDepth (km)")
#fig.savefig('seismisitas.png')

#image = Image.open('seismisitas.png')
#st.image(image, caption='Peta Seismisitas')

st.map(df, latitude=df['fixedLat'], longitude=df['fixedLon'], size=0.02*2**df['mag'])

unique_values = df['remarks'].unique()
count_region=[]
for i in unique_values:
    count=df['remarks'].apply(lambda x: x == i).sum()
    count_region.append(count)

df_region = pd.DataFrame({'region':unique_values,'count':count_region})

ax = df_region.plot.bar(x='region', y='count', rot=20,
                       figsize=(25, 15), legend=True, fontsize=14)
ax.set_xlabel("Region", fontsize=20)
ax.set_ylabel("Jumlah Gempa", fontsize=20)
plt.savefig('grafik_stat_eq.png')

image = Image.open('grafik_stat_eq.png')
st.image(image, caption='Grafik Frekuensi Gempa berdasarkan Area Flin Engdhal')

st.markdown(""" ### Tabel Seismisitas dan Statistik Gempa """)
st.dataframe(df)
st.dataframe(df_region)
