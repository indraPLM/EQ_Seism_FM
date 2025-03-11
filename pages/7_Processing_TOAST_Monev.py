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

st.set_page_config(page_title='Kecepatan Processing Tsunami TOAST',  layout='wide', page_icon="🌍")

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


path="./pages/filetoast/"
dir_list = os.listdir(path)

event_list = []
for i in range(len(dir_list)):
    temp=dir_list[i].split('.log')
    temp=temp[0]
    event_list.append(temp)

text_toast=[]
for i in range(len(dir_list)):
    curr=os.getcwd() 
    test=dir_list[i]
    with open(path+'/'+test) as f:
        lines = f.readlines()
        text_toast.append(lines)
print([len(text_toast),len(event_list)])

dttime_toast,remark_toast=[],[]
eventid_toast=[]
for i in range(len(text_toast)):    
    if event_list[i].startswith('bmg202'):        
        t=text_toast[i][2].split()
        dttime=t[0]+' '+t[1]
        remark=t[2]
        
        dttime_toast.append(dttime)
        remark_toast.append(remark)
        eventid_toast.append(event_list[i])
    else:
        continue
    

df_toast= pd.DataFrame({'event_id':eventid_toast,'tstamp_toast':dttime_toast,'remark_toast':remark_toast})
df_toast['tstamp_toast'] = pd.to_datetime(df_toast['tstamp_toast'])

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
mag=get_qc(event_qc,5)
lat=get_qc(event_qc,10)
lon=get_qc(event_qc,11)
depth=get_qc(event_qc,12)
remarks=get_qc(event_qc,14)

df = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mag':mag,'lat':lat,
                   'lon':lon,'depth':depth,'remarks':remarks})

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
def fix_split(a):
    a= a.strip()
    return a

df['event_id'] = df.event_id.apply(fix_split)

df['lat'] = df.lat.apply(fix_latitude)
df['lat'] = pd.to_numeric(df['lat'],errors = 'coerce')

df['lon'] = df.lon.apply(fix_longitude)
df['lon'] = pd.to_numeric(df['lon'],errors = 'coerce')

df['depth'] = df.depth.apply(fix_depth)
df['depth'] = pd.to_numeric(df['depth'],errors = 'coerce')

df['date_time'] = pd.to_datetime(df['date_time'])
df['date_time_wib'] = df['date_time'] + pd.Timedelta(hours=7)
df['mag'] = fix_float(df['mag'])
df= df[df['mag'] >=5]
df= df[(df['date_time'] > df_toast['tstamp_toast'][0] ) & (df['date_time'] < df_toast['tstamp_toast'][len(df_toast)-1])]
df_qc=df

result = pd.merge(df_qc, df_toast, on="event_id")
result['lapse_time_toast']=result['tstamp_toast']-result['date_time_wib']
result['lapse_time_toast'] = (result['lapse_time_toast'].dt.total_seconds()/60).round(2)
result= result[result['lapse_time_toast'] <= 60]

result= result[(result['date_time_wib'] > time_start) & (result['date_time_wib'] < time_end)]
result= result[(result['lon'] > West) & (result['lon'] < East)]
result= result[(result['lat'] > South) & (result['lat'] < North)]

st.markdown(""" ### Peta Lokasi Gempabumi Prosesing TOAST M >=5 """)
st.map(result, latitude="lat", longitude="lon", size=2000, zoom=4 )

st.markdown(""" ### Grafik Kecepatan Prosesing TOAST M >=5 """)
st.scatter_chart(result, x="date_time_wib", y="lapse_time_toast")

st.markdown("""### Data Parameter Gempa dan Kecepatan Prosesing TOAST""")
st.dataframe(result)
