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
from bs4 import BeautifulSoup
import requests
import pandas as pd
import os,sys
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import cartopy.crs as ccrs
import cartopy
from cartopy.io.shapereader import Reader

st.set_page_config(page_title='Earthquake Catalog, Statistik & Plotting',  layout='wide', page_icon="🌍")
#st.title('Seismisitas dan Statistik Kegempaan')

st.sidebar.header("Input Parameter :")
 
time_start=st.sidebar.text_input('Start Time:', '2025-01-01 00:00:00')
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

   
### -----------------------Earthquake Catalog ----------------------
st.markdown(
    """
    ### Peta Seismisitas dan Statistik Kegempaaan (sumber : http://202.90.198.41/qc.txt)
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
print(len(event_qc))
def get_qc(file,par):
    par=par
    data=[]
    for i in file[1:len(file)-1]:
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


st.map(df, latitude="fixedLat", longitude="fixedLon", size="sizemag", zoom=3 )


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

def get_eq(name):
    eq_pulau=gpd.read_file('%s_Area.shp' %(name))
    temp_clip=gpd_seis.clip(eq_pulau)
    a=np.array(list(temp_clip.fixedLon))
    b=np.array(list(temp_clip.fixedLat))
    x, y ,_= projection.transform_points(ccrs.Geodetic(), a, b).T
    return x,y

list_pulau=['Sumatra','Jawa','Bali-A','Nustra','Kalimantan','Sulawesi','Maluku','Papua']
list_color=['r','g','b','y','c','m','purple','orange']
#region=[West,East,South-1,North+1]
projection = ccrs.PlateCarree(central_longitude=120.0)

fig = plt.figure(dpi=300)
ax = fig.add_subplot(111, projection=projection)
ax.set_extent((85, 145, -15, 10))

for i in range(len(list_pulau)):
    eq_x,eq_y=get_eq(list_pulau[i])
    ax.scatter(eq_x,eq_y, 1, color=list_color[i], marker="o", zorder=3)
    shp_name='%s_Area.shp' %(list_pulau[i])
    ax.add_geometries(Reader(shp_name).geometries(),ccrs.PlateCarree(),
                      facecolor="white", edgecolor=list_color[i],linewidth=0.25)
    ax.add_feature(cartopy.feature.BORDERS, linestyle='-', linewidth=0.5,alpha=0.5)
    ax.coastlines(resolution='10m', color='black', linestyle='-',linewidth=0.5,alpha=0.5)

st.markdown(""" ### Seismisitas Berdasakan Pulau """)
st.pyplot(fig)

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
    sedang = df[(df['mag'] >= 4) & (df['mag'] < 5 )]
    num_sedang=sedang['event_id'].count()
    besar = df[(df['mag'] >= 5 )]
    num_besar=besar['event_id'].count()
    #dibawah5 = df[(df['mag'] < 5 )]
    #num_dibawah5=dibawah5['event_id'].count()
    
    return (num,[num_dangkal,num_menengah,num_dalam,num_kecil,num_sedang,num_besar])
sumatra = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Sumatra_Area.zip')
jawa = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Jawa_Area.zip')
bali = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Bali-A_Area.zip')
nustra = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Nustra_Area.zip')
kalimantan = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Kalimantan_Area.zip')
sulawesi = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Sulawesi_Area.zip')
maluku = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Maluku_Area.zip')
papua = gpd.read_file('https://raw.githubusercontent.com/indraPLM/EQ_Seism_FM/main/Papua_Area.zip')

sumatra_clipped = gpd_seis.clip(sumatra)
jawa_clipped = gpd_seis.clip(jawa)
bali_clipped = gpd_seis.clip(bali)
nustra_clipped = gpd_seis.clip(nustra)
kalimantan_clipped = gpd_seis.clip(kalimantan)
sulawesi_clipped = gpd_seis.clip(sulawesi)
maluku_clipped = gpd_seis.clip(maluku)
papua_clipped = gpd_seis.clip(papua)

pulau=[sumatra_clipped,jawa_clipped,bali_clipped,nustra_clipped,
       kalimantan_clipped,sulawesi_clipped,maluku_clipped,papua_clipped]
stat_gempa=[]
for x in pulau:
    a=stat_eq(x)
    data=a[1]
    data.insert(len(pulau),a[0])
    stat_gempa.append(data)
header=['Dangkal < 60','Menengah (60-300)','Dalam > 300','Kecil <4','Menengah 4-5','Besar >= 5','Total']
df_clip = pd.DataFrame(stat_gempa,columns=header)

total=[]
for y in header:
    tot=df_clip[y].sum()
    total.append(tot)
df_clip.loc[len(df)] = total

nama_pulau = ['SUMATRA', 'JAWA', 'BALI', 'NUSA TENGGARA','KALIMANTAN','SULAWESI','MALUKU','PAPUA','INDONESIA']
df_clip['Wilayah'] = nama_pulau

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
