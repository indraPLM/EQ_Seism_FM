# -*- coding: utf-8 -*-
"""
Created on Wed Mar  8 05:05:03 2023

@author: Indra Gunawan
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
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


st.set_page_config(page_title='Earthquake Catalog, Statistik & Plotting',  layout='wide', page_icon="🌍")
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
df['sizemag']=1000*df['mag']

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

#st.map(df, latitude="fixedLat", longitude="fixedLon", size="sizemag" )

m = folium.Map(location=(0, 120), zoom_start=4)

# go through each quake in set, make circle, and add to map.
for i in range(len(df)):
    folium.Circle(
        location=[df.iloc[i]['fixedLat'], df.iloc[i]['fixedLon']],
        radius=10,
    ).add_to(m)

# Same as before, we save it to file
st_data = st_folium(m, width=725)

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
st.table(df_region)

gpd_seis = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.fixedLon, df.fixedLat), crs="EPSG:4326")

# Loading Data SHP dan Clipped data gempa per-Pulau
sumatra = gpd.read_file('Sumatra_Area.shp')
jawa = gpd.read_file('Jawa_Area.shp')
bali = gpd.read_file('Bali-A_Area.shp')
nustra = gpd.read_file('Nustra_Area.shp')
kalimantan = gpd.read_file('Kalimantan_Area.shp')
sulawesi = gpd.read_file('Sulawesi_Area.shp')
maluku = gpd.read_file('Maluku_Area.shp')
papua = gpd.read_file('Papua_Area.shp')
provinsi = gpd.read_file('Batas Provinsi.shp')

sumatra_clipped = gpd_seis.clip(sumatra)
jawa_clipped = gpd_seis.clip(jawa)
bali_clipped = gpd_seis.clip(bali)
nustra_clipped = gpd_seis.clip(nustra)
kalimantan_clipped = gpd_seis.clip(kalimantan)
sulawesi_clipped = gpd_seis.clip(sulawesi)
maluku_clipped = gpd_seis.clip(maluku)
papua_clipped = gpd_seis.clip(papua)

# Plot the clipped data
fig, ax = plt.subplots(figsize=(30, 20))
provinsi.boundary.plot(ax=ax, color='black')
sumatra_clipped.plot(ax=ax, color="purple")
sumatra.boundary.plot(ax=ax, color="green")
jawa_clipped.plot(ax=ax, color="purple")
jawa.boundary.plot(ax=ax, color="green")
bali_clipped.plot(ax=ax, color="purple")
bali.boundary.plot(ax=ax, color="green")
nustra_clipped.plot(ax=ax, color="purple")
nustra.boundary.plot(ax=ax, color="green")
kalimantan_clipped.plot(ax=ax, color="purple")
kalimantan.boundary.plot(ax=ax, color="green")
sulawesi_clipped.plot(ax=ax, color="purple")
sulawesi.boundary.plot(ax=ax, color="green")
maluku_clipped.plot(ax=ax, color="purple")
maluku.boundary.plot(ax=ax, color="green")
papua_clipped.plot(ax=ax, color="purple")
papua.boundary.plot(ax=ax, color="green")

ax.set_title("Plot Clipped Data Gempa Per-Pulau", fontsize=20)
ax.set_axis_off()
plt.savefig('seismisitas_per_pulau.png')

image = Image.open('seismisitas_per_pulau.png')
st.image(image, caption='Peta Seismisitas Berdasarkan Pulau-Pulau')

def stat_eq(df):
    num = df['event_id'].count()
    dangkal = df[(df['fixedDepth'] < 60 )]
    num_dangkal=dangkal['event_id'].count()
    menengah = df[(df['fixedDepth'] >= 60) & (df['fixedDepth'] <= 300 )]
    num_menengah=menengah['event_id'].count()
    dalam = df[(df['fixedDepth'] > 300 )]
    num_dalam=dalam['event_id'].count()
    
    num = df['event_id'].count()
    kecil = df[(df['mag'] < 4 )]
    num_kecil=kecil['event_id'].count()
    sedang = df[(df['mag'] >= 4) & (df['mag'] <= 5 )]
    num_sedang=sedang['event_id'].count()
    besar = df[(df['mag'] > 5 )]
    num_besar=besar['event_id'].count()
    
    return (num,[num_dangkal,num_menengah,num_dalam,num_kecil,num_sedang,num_besar])

pulau=[sumatra_clipped,jawa_clipped,bali_clipped,nustra_clipped,
       kalimantan_clipped,sulawesi_clipped,maluku_clipped,papua_clipped]
stat_gempa=[]
for x in pulau:
    a=stat_eq(x)
    data=a[1]
    data.insert(len(pulau),a[0])
    stat_gempa.append(data)
header=['Dangkal < 60','Menengah (60-300)','Dalam > 300','Kecil <4','Menengah 4-5','Besar > 5','Total']
df_clip = pd.DataFrame(stat_gempa,columns=header)

total=[]
for y in header:
    tot=df_clip[y].sum()
    total.append(tot)
df_clip.loc[len(df)] = total

nama_pulau = ['SUMATRA', 'JAWA', 'BALI', 'NUSA TENGGARA','KALIMANTAN','SULAWESI','MALUKU','PAPUA','INDONESIA']
df_clip['Wilayah'] = nama_pulau
file_name = 'Statistik_PerPulau.xlsx'
df_clip.to_excel(file_name)

df_new = df_clip.drop('Total', axis=1)
idx = [8]
df_new = df_new.query("index != @idx")
df_new.set_index('Wilayah',inplace=True)
df_new1=df_new.drop(['INDONESIA'])

df_new1.plot.bar(rot=6,figsize=(15, 10))

plt.savefig('grafik_eq_clip_per_pulau.png')

image = Image.open('grafik_eq_clip_per_pulau.png')
st.image(image, caption='Grafik Frekuensi Gempa berdasarkan Pulau-Pulau Utama')

st.markdown(""" ### Tabel Statistik Gempabumi Per Pulau """)
#st.dataframe(df_clip)
st.table(df_new)
#st.dataframe(df_new1)
