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
    
df=pd.DataFrame({'date':list_date,'time':list_time_rem,'timesent':list_timesent_rem})
df['datetime']=pd.to_datetime(df['date'] + ' ' + df['time'])
df['timesent']=pd.to_datetime(df['timesent'])
df['lapsetime']=df['timesent']-df['datetime']


st.markdown("""### Perbandingan Waktu Pengiriman dan Waktu Kejadian 30 Gempabumi terakhir)""")
st.table(df)
