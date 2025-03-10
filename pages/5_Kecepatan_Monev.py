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

st.set_page_config(page_title='Peta Focal Mechanism',  layout='wide', page_icon="🌍")

st.sidebar.header("Input Parameter :")
last1 = datetime.datetime.now() - datetime.timedelta(1)
last1 = last1.strftime('%Y-%m-%d')
last30 = datetime.datetime.now() - datetime.timedelta(30)
last30 = last30.strftime('%Y-%m-%d')

time_start=st.sidebar.text_input('Start DateTime:', '%s 00:00:00' %(last30))
time_end=st.sidebar.text_input('End DateTime:', '%s 23:59:59'%(last1))

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
#l_area=[]
#for i in range(len(area)):
#    a=area[i].split()
#    if len(area[i].split()) == 12:
#        remark=a[9]+' '+a[10]+' '+a[11]
#    if len(area[i].split()) == 11:
#        remark=a[9]+' '+a[10]
#    if len(area[i].split()) == 10:
#        remark=a[9]
#    l_area.append(remark)

df=pd.DataFrame({'eventid':eventid,'waktu':waktu,'lat':lat,'lon':lon,'mag':mag,
                 'depth':dep})
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

def fix_float(z):
    temp=[]
    for i in range(len(z)):
        b=float(z[i])
        temp.append(b)
    return temp
df['mag']=fix_float(df['mag'])

df['lon'] = pd.to_numeric(df['lon'],errors = 'coerce')
df['lat'] = pd.to_numeric(df['lat'],errors = 'coerce')

df_v=df[ df['mag'] >= 5]
df_v= df_v[(df_v['date_time'] > time_start) & (df_v['date_time'] < time_end)]
df_v= df_v[(df['lon'] > West) & (df_v['lon'] < East)]
df_v= df_v[(df['lat'] > South) & (df_v['lat'] < North)]

st.markdown(""" ### Grafik Kecepatan Prosesing Gempabumi M >=5 """)
st.scatter_chart(df_v, x="datetime", y="lapsetime (minutes)")

st.markdown("""### Data Parameter Gempa dan Kecepatan Prosesing Gempabumi""")
st.dataframe(df_v)
