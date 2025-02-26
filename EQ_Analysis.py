# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 12:02:47 2022

@author: Asus
"""

import streamlit as st
from PIL import Image
import folium
from bs4 import BeautifulSoup
import requests
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(page_title="EQ Analyis", layout="wide", page_icon="🌏")

st.write("# Earthquake Data Analysis 👨🏽‍💼")

st.sidebar.success("EQ Analysis Menu")

url='https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml'
page=requests.get(url)
url_pages=BeautifulSoup(page.text, 'html')

# Parsing data xml file

def par_xml(params):
    data=url_pages.find(params)
    data=data.get_text()

    return data

def fix_latitude(x):
    x = x.strip()
    if x.endswith('LS'):
        x = -float(x.strip('LS'))
    else:
        x = x.strip('LU')
    return x

def fix_longitude(y):
    y = y.strip()
    if y.endswith('BB'):
        y = -float(y.strip('BB'))
    else:
        y = y.strip('BT')
    return y

lat_a=par_xml('lintang')
lat=fix_latitude(lat_a)

lon_a=par_xml('bujur')
lon=fix_longitude(lon_a)

mag=par_xml('magnitude')
dep=par_xml('kedalaman')
tanggal=par_xml('tanggal')
waktu=par_xml('jam')
datetime=par_xml('datetime')

m= folium.Map((lat, lon),zoom_start=4)

html = """
    <h2> Gempa Terkini</h2>
    <p> Tanggal %s %s </p>
    <p> Mag: %s </p>
    <p> Kedalaman : %s </p>
    """ %(tanggal,waktu, mag,dep)

folium.Marker(
    location=[lat, lon],
    tooltip="Click me!",
    popup=html,
    icon=folium.Icon(icon_shape='circle-dot'),
).add_to(m)

st_data = st_folium(m, width=800)

url_m5='https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml'
page_m5=requests.get(url_m5)
url_pages_m5=BeautifulSoup(page_m5.text, 'html')

data=url_pages_m5.find_all('tanggal')
print(data[0])
print(len(data))
def par_xml_m5(params):
    data=url_pages_m5.find_all(params)
    content=[]
    for x in data:
        par=x.get_text()
        content.append(par)
    return content

def fix_latitude_m5(a):
    for x in a:
        x = x.strip()
        if x.endswith('LS'):
            x = -float(x.strip('LS'))
        else:
            x = x.strip('LU')
    return x

def fix_longitude_m5(b):
    for y in b:
        y = y.strip()
        if y.endswith('BB'):
            y = -float(y.strip('BB'))
        else:
            y = y.strip('BT')
    return y

a=par_xml_m5('tanggal')
b=par_xml_m5('jam')
c=par_xml_m5('datetime')

d=par_xml_m5('lintang')
d1=fix_latitude_m5(d)
e=par_xml('bujur')
e1=fix_longitude_m5(e)

f=par_xml_m5('magnitude')
g=par_xml_m5('kedalaman')
h=par_xml_m5('wilayah')
i=par_xml_m5('potensi')

df=pd.DataFrame({'tanggal':a,'waktu':b,'date_time':c,'lat':d1,'lon':e1,'mag':f,'depth':g,
                 'region':h,'status':i})
st.markdown(""" 15 Data Gempabumi Terkini""")
st.table(df)

st.markdown(
    """ 
    ### Link Website 
    -  BMKG [Badan Meteorologi Klimatologi dan Geofisika](https://www.bmkg.go.id/)
    -  InaTEWS [Indonesia Tsunami Early Warning System](https://inatews.bmkg.go.id/)
    -  Webdc BMKG [Access to BMKG Data Archive](https://geof.bmkg.go.id/webdc3/)
"""
)
