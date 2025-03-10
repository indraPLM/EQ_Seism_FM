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

df['latitude'] = df.lat.apply(fix_latitude)
df['latitude'] = pd.to_numeric(df['latitude'],errors = 'coerce')

df['longitude'] = df.lon.apply(fix_longitude)
df['longitude'] = pd.to_numeric(df['longitude'],errors = 'coerce')

df['date_time'] = pd.to_datetime(df['date_time'])
df['mag'] = fix_float(df['mag'])
df['depth'] = fix_float(df['depth'])

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
for i in range(len(df['event_id'])):
    a,b=get_processtime(df['event_id'][i])
    #print([df['event_id'][i],a,b])
    t_stamp.append(a)
    t_proc.append(b)
df['tstamp_proc']=t_stamp
df['time_proc']=t_proc
