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
import datetime
from streamlit_folium import st_folium

st.set_page_config(page_title='Kecepatan Processing Gempabumi',  layout='wide', page_icon="🌍")

st.sidebar.header("Input Parameter :")
time_start=st.sidebar.text_input('Start DateTime:', '2025-02-01 00:00:00' )
time_end=st.sidebar.text_input('End DateTime:', '2025-02-28 23:59:59')

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
    for i in file[1:700]:
        temp=i[par]
        data.append(temp)
    return data

event_id=get_fc(event_fc,0)
date_time=get_fc(event_fc,1)
mag=get_fc(event_fc,5)
latitude=get_fc(event_fc,10)
longitude=get_fc(event_fc,11)
depth=get_fc(event_fc,13)
remarks=get_fc(event_fc,21)

df = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mag':mag,'lat':latitude,
                   'lon':longitude,'depth':depth,'remarks':remarks})

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

def fix_strip(a):
    a= a.strip()
    return a

df['event_id'] = df.event_id.apply(fix_strip)

df['latitude'] = df.lat.apply(fix_latitude)
df['latitude'] = pd.to_numeric(df['latitude'],errors = 'coerce')

df['longitude'] = df.lon.apply(fix_longitude)
df['longitude'] = pd.to_numeric(df['longitude'],errors = 'coerce')

df['date_time'] = pd.to_datetime(df['date_time'])
df['mag'] = fix_float(df['mag'])
df['depth'] = fix_float(df['depth'])

df= df[df['mag'] >= 5]
#time_start= '2025-02-08 00:00:00'
#time_end= '2025-03-09 23:59:59'
West,East,North,South=90.0,145.0,10, -15
df= df[(df['date_time'] > time_start) & (df['date_time'] < time_end)]
df= df[(df['longitude'] > West) & (df['longitude'] < East)]
df= df[(df['latitude'] > South) & (df['latitude'] < North)]

list_date=df['date_time'].to_list()
list_mag=df['mag'].to_list()
list_dep=df['depth'].to_list()
list_title=[]
for i in range(len(list_mag)):
    title='Tanggal: %s , Mag: %s, Depth:%s'%(list_date[i],list_mag[i],list_dep[i])
    list_title.append(title)
df['title']=list_title

def get_processtime(eventid):
    def get_qc(file,par):
        par=par
        data=[]
        for i in file[1:2]:
            temp=i[par]
            data.append(temp)
        return data
    
    def fix_float(z):
        temp=[]
        for i in range(len(z)):
            b=float(z[i])
            temp.append(b)
        return temp
        
    try:
        eventid=eventid.split()
        eventid=eventid[0]
        url='https://bmkg-content-inatews.storage.googleapis.com/history.%s.txt' %(eventid)
        page=requests.get(url)
        url_pages=BeautifulSoup(page.text, 'html')
        a=[]
        for fo in url_pages.p:
            a.append(fo)
        b=a[0].split('\n')
        
        lapse=[]
        for i in range(len(b)):
            t=b[i].split('|')
            lapse.append(t)
        
        timestamp=get_qc(lapse,0)
        lapsetime=get_qc(lapse,1)
        #print(lapsetime)
        lapsetime=fix_float(lapsetime)
        
        return timestamp[0],lapsetime[0]
    
    except:
        timestamp =' '
        lapsetime =' '
        return timestamp,lapsetime

t_stamp,t_proc=[],[]
list_id=df['event_id'].to_list()
for i in range(len(list_id)):
    a,b=get_processtime(list_id[i])
    #print([df['event_id'][i],a,b])
    t_stamp.append(a)
    t_proc.append(b)
df['tstamp_proc']=t_stamp
df['time_proc (minutes)']=t_proc
df['time_proc (minutes)']= fix_float(df['time_proc (minutes)'],)

df_display=df[['event_id','date_time','tstamp_proc','time_proc (minutes)',
                  'longitude','latitude','mag','depth','remarks']]

import folium
x=df_display['longitude'].values.tolist()
y=df_display['latitude'].values.tolist()
text=df['title'].values.tolist()
tiles='https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
m = folium.Map([-4, 120], tiles=tiles, attr='ESRI', zoom_start=5)

for i in range(len(x)):
    folium.Marker(location=[y[i], x[i]],popup=text[i],
                  icon=folium.Icon(color="red"),).add_to(m)

st.markdown("""### Peta Seismisitas Gempabumi M >=5 (BMKG)""")
st_data = st_folium(m, width=1000)

st.markdown(""" ### Grafik Kecepatan Prosesing Gempabumi M >=5 """)
st.scatter_chart(df_display, x="date_time", y="time_proc (minutes)")

st.markdown("""### Data Parameter Gempa dan Kecepatan Prosesing Gempabumi""")
st.dataframe(df_display)
