from bs4 import BeautifulSoup
import requests
import pandas as pd
import streamlit as st
import numpy as np

st.set_page_config(page_title='TSP Monitoring dan Evaluasi',  layout='wide', page_icon="🌍")
#st.title('Seismisitas dan Statistik Kegempaan')

st.sidebar.header("Input Parameter :")
 
time_start=st.sidebar.text_input('Start DateTime:', '2024-11-01 00:00:00')
time_end=st.sidebar.text_input('End DateTime:', '2025-01-31 23:59:59')

url='https://bmkg-content-inatews.storage.googleapis.com/last30event.xml'
page=requests.get(url)
soup=BeautifulSoup(page.text, 'html')

def get_text(file):
    list_text=[]
    for name in file:
        temp= name.text
        list_text.append(temp)
    return list_text

def remove_wib(temp):
    x = temp.strip()
    if x.endswith('WIB'):
        x = x.strip('WIB')
    else:
        x = x.strip('UTC')
    return x

def fix_longitude(x):
    x = x.strip()
    if x.endswith(' BB'):
        x = -float(x.strip(' BB'))        
    else:        
        x = x.strip(' BT')        
    return x

def fix_latitude(y):
    y = y.strip()
    if y.endswith(' LS'):
        y = -float(y.strip(' LS'))
    else:
        y = y.strip(' LU')
    return y
 
l_date = soup.find_all('date')
list_date=get_text(l_date)

l_time = soup.find_all('time')
list_time=get_text(l_time)
list_time_rem=[]
for x in list_time:
    temp=remove_wib(x)
    list_time_rem.append(temp)
    
l_timesent= soup.find_all('timesent')
list_timesent=get_text(l_timesent)
list_timesent_rem=[]
for x in list_timesent:
    temp=remove_wib(x)
    list_timesent_rem.append(temp)

l_lat= soup.find_all('latitude')
list_lat=get_text(l_lat)
list_lat_rem=[]
for x in list_timesent:
    temp=fix_latitude(x)
    list_lat_rem.append(temp)

l_lon= soup.find_all('longitude')
list_lon=get_text(l_lon)
list_lon_rem=[]
for x in list_timesent:
    temp=fix_longitude(x)
    list_lon_rem.append(temp)

l_mag= soup.find_all('magnitude')
list_mag=get_text(l_mag)

l_dep= soup.find_all('depth')
list_dep=get_text(l_dep)

l_area= soup.find_all('potential')
list_area=get_text(l_area)
df=pd.DataFrame({'date':list_date,'time':list_time_rem,'timesent':list_timesent_rem })
df['datetime']=pd.to_datetime(df['date'] + ' ' + df['time'])
df['timesent']=pd.to_datetime(df['timesent'])
df['lapsetime']=df['timesent']-df['datetime']

df_display=df.drop(['date', 'time'], axis=1)
df_display['lon']=list_lon_rem
df_display['lat']=list_lat_rem
df_display['mag']=list_mag
df_display['depth']=list_dep
df_display['location']=list_area
st.markdown("""### Perbandingan Waktu Pengiriman dan Waktu Kejadian 30 Gempabumi terakhir""")
st.table(df_display)
