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

st.sidebar.header("Input Parameter :")
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

st.markdown( """ ### Peta Seismisitas Terkini (BMKG) """)
url='https://bmkg-content-inatews.storage.googleapis.com/live30event.xml'
page=requests.get(url)
soup=BeautifulSoup(page.text, 'html')

def get_text(file):
    list_text=[]
    for name in file:
        temp= name.text
        list_text.append(temp)
    return list_text

eventid = soup.find_all('eventid')
eventid = get_text(eventid)

waktu = soup.find_all('waktu')
waktu = get_text(waktu)

lon = soup.find_all('bujur')
lon = get_text(lon)

lat = soup.find_all('lintang')
lat = get_text(lat)

mag = soup.find_all('mag')
mag = get_text(mag)

dep = soup.find_all('dalam')
dep = get_text(dep)

area = soup.find_all('gempa')
area = get_text(area)
l_area=[]
for i in range(len(area)):
    a=area[i].split()
    if len(area[i].split()) == 12:
        text=a[9]+' '+a[10]+' '+a[11]
    if len(area[i].split()) == 11:
        text=a[9]+' '+a[10]
    if len(area[i].split()) == 10:
        text=a[9]
    l_area.append(text)

df=pd.DataFrame({'eventid':eventid,'waktu':waktu,'lat':lat,'lon':lon,'mag':mag,
                 'depth':dep,'area':l_area})
df['waktu']=pd.to_datetime(df['waktu'])

def get_processtime(eventid):
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

    lapsetime=get_qc(lapse,1)
    lapsetime=fix_float(lapsetime)
    
    return(lapsetime[0])

t_proc=[]
for i in range(len(df['eventid'])):
    t=get_processtime(df['eventid'][i])
    #print([df['eventid'][i],t])
    t_proc.append(t)
#print(t_proc)
df['time_proc']=t_proc
st.dataframe(df)
