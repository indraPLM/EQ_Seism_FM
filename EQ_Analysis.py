import streamlit as st
from PIL import Image
import folium
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import timedelta,datetime
from streamlit_folium import st_folium
from obspy.geodetics import locations2degrees, degrees2kilometers

st.set_page_config(page_title="EQ Analyis", layout="wide", page_icon="🌏")

#st.write("# Earthquake Data Analysis 👨🏽‍💼")
#st.sidebar.success("EQ Analysis Menu")

now=datetime.today()+ timedelta(days=1)
now.strftime('%Y-%m-%d')

url='https://geofon.gfz.de/fdsnws/event/1/query?end=%s&limit=40&format=text' %(now)
page=requests.get(url)
url_pages=BeautifulSoup(page.text, 'html')

a=[]
for fo in url_pages.p:
    a.append(fo)

b=a[0].split('\n')
print(b[1])
event_qc=[]
for i in range(len(b)):
    qc=b[i].split('|')
    event_qc.append(qc)

def get_qc(file,par):
    par=par
    data=[]
    for i in file[1:len(file)-1]:
        temp=i[par]
        data.append(temp)
    return data

def fix_float(z):
    temp=[]
    for i in range(len(z)):
        b=float(z[i])
        temp.append(b)
    return temp

event_id=get_qc(event_qc,0)
date_time=get_qc(event_qc,1)
mag=get_qc(event_qc,10)
#mag = fix_float(mag)
typemag=get_qc(event_qc,9)
lat=get_qc(event_qc,2)
lat = fix_float(lat)
lon=get_qc(event_qc,3)
lon = fix_float(lon)
depth=get_qc(event_qc,4)
depth = fix_float(depth)
remarks=get_qc(event_qc,12)

df_gfz = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mag':mag,'typemag':typemag,'lat':lat,
                   'lon':lon,'depth':depth,'remarks':remarks})
df_gfz['mag_text']=df_gfz['mag']+' ' +df_gfz['typemag']
df_gfz['date_time']=pd.to_datetime(df_gfz['date_time'])

import geopandas
import datetime

url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
df_usgs = geopandas.read_file(url)

time_usgs=[]
for i in range(len(df_usgs['time'])):
    t=df_usgs['time'][i]
    t=datetime.datetime.fromtimestamp(t / 1000.0)
    time_usgs.append(t)
df_usgs['time_usgs']=time_usgs
df_usgs['time_usgs']=pd.to_datetime(df_usgs['time_usgs'])
#df_usgs['time_usgs']=df_usgs['time_usgs'] - pd.Timedelta(hours=7)
df_usgs['lon'] = df_usgs.geometry.x
df_usgs['lat'] = df_usgs.geometry.y
df_usgs['depth'] = df_usgs.geometry.z
#print(df_usgs)

url='https://bmkg-content-inatews.storage.googleapis.com/live30event.xml'
#url='https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.xml'
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
mag = fix_float(mag)
dep = soup.find_all('dalam')
dep = get_text(dep)
#area = soup.find_all('gempa')
#area = get_text(area)

#l_area=[]
#for i in range(len(area)):
#    a=area[i].split()
#    if len(area[i].split()) == 12:
#        text=a[9]+' '+a[10]+' '+a[11]
#    if len(area[i].split()) == 11:
#        text=a[9]+' '+a[10]
#    if len(area[i].split()) == 10:
#        text=a[9]
#    l_area.append(text)

df_bmkg=pd.DataFrame({'eventid':eventid,'waktu':waktu,'lat':lat,'lon':lon,'mag':mag,
                 'depth':dep})
df_bmkg['waktu']=pd.to_datetime(df_bmkg['waktu'])
df_bmkg= df_bmkg[df_bmkg['mag'] >=5]

x0=df_bmkg['lon'].to_list()[0]
y0=df_bmkg['lat'].to_list()[0]
m0=df_bmkg['mag'].to_list()[0]
d0=df_bmkg['depth'].to_list()[0]

temp=df_bmkg['waktu'].to_list()
a=temp[0]
x1,y1,m1,d1=[],[],[],[]
for i in range(len(df_gfz['date_time'])):
    b=df_gfz['date_time'][i]
    if abs(timedelta.total_seconds(a-b)) < 5:
        x=round(df_gfz['lon'][i],2)
        y=round(df_gfz['lat'][i],2)
        m=round(df_gfz['mag'][i],2)
        d=round(df_gfz['depth'][i],2)
        x1.append(x),y1.append(y),m1.append(m),d1.append(d)
    else:
        continue
#print(a)
#print(df_usgs['time_usgs'])
x2,y2,m2,d2=[],[],[],[]
for i in range(len(df_usgs['time_usgs'])):
    b=df_usgs['time_usgs'][i]
    print([a,b])
    if abs(timedelta.total_seconds(a-b)) < 5:
        x=round(df_usgs['lon'][i],2)
        y=round(df_usgs['lat'][i],2)
        m=round(df_usgs['mag'][i],2)
        d=round(df_usgs['depth'][i],2)
        x2.append(x),y2.append(y),m2.append(m),d2.append(d)
    else:
        continue
if len(m1)==0:
    del1= ' '
    del11= ' '
else:
    del1=round((float(m1[0]) - float(m0)),2)
    del1=str(del1)
    del11=round((float(d1[0]) - float(d0)),2)
    del11=str(del11)
    j1=locations2degrees(float(x0), float(y0), float(x1[0]), float(y1[0]))
    del111=round(degrees2kilometers(j1),2)

if len(m2)==0:
    del2 = ' '
    del22 = ' '
else:
    del2=round((float(m2[0]) - float(m0)),2)
    del2=str(del2)
    del22=round((float(d2[0]) - float(d0)),2)
    del22=str(del22)
    j2=locations2degrees(float(x0), float(y0), float(x2[0]), float(y2[0]))
    del222=round(degrees2kilometers(j2),2)

import folium
tiles='https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
m= folium.Map(( y0,x0),tiles=tiles, attr='ESRI', zoom_start=8)
geo_json_data = requests.get("https://bmkg-content-inatews.storage.googleapis.com/indo_faults_lines.geojson").json()
folium.GeoJson(geo_json_data, style_function=lambda feature: {"color": "orange","weight": 1.0,},).add_to(m)

#html1 = """ <p> Mag: %s </p> <p> Kedalaman : %s </p> """ %(m0, d0)
if (len(x1)== 0 and len(x2) ==0):
    folium.Marker(location=[y0,x0], icon=folium.Icon(icon="1",prefix='fa', color='red'),).add_to(m)

if (len(x1)== 1 and len(x2)==1):
    x1=str(x1[0])
    y1=str(y1[0])
    x2=str(x2[0])
    y2=str(y2[0])
    folium.Marker(location=[ y0,x0], icon=folium.Icon(icon="1",prefix='fa',color='red'),).add_to(m)
    folium.Marker(location=[y1,x1], icon=folium.Icon(icon="2",prefix='fa',color='blue'),).add_to(m)
    folium.Marker(location=[y2,x2], icon=folium.Icon(icon="3",prefix='fa',color='green'),).add_to(m)

if (len(x1)==1 and len(x2)==0):
    x1=str(x1[0])
    y1=str(y1[0])
    folium.Marker(location=[y0,x0], icon=folium.Icon(icon="1",prefix='fa',color='red'),).add_to(m)
    folium.Marker(location=[y1,x1], icon=folium.Icon(icon="2",prefix='fa',color='blue'),).add_to(m)

if (len(x1)==0 and len(x2) ==1):
    x2=str(x2[0])
    y2=str(y2[0])
    folium.Marker(location =[y0,x0], icon=folium.Icon(icon="1",prefix='fa',color='red'),).add_to(m)
    folium.Marker(location =[y2,x2], icon=folium.Icon(icon="3",prefix='fa', color='green'),).add_to(m)


col1,col2 =st.columns(2)
with col1:
    st.markdown(""" ## Magnitude""")
               
with col2:
    st.markdown(""" ## Depth """)

col1, col2, col3, col4,col5,col6 = st.columns(6)
with col1:
    m0=str(m0)
    st.metric(label="1.BMKG", value="%s" %(m0), delta=" ")
with col2:
    if len(m1) == 0:
        st.metric(label= "2.GFZ", value = " ")
    else:
        m1=str(m1[0])
        st.metric(label="2.GFZ", value="%s" %(m1), delta=" %s" %(del1))
with col3:
    if len(m2) == 0:
        st.metric(label="3.USGS", value= " ")
    else:
        m2=str(m2[0])
        st.metric(label="3.USGS", value="%s" %(m2), delta=" %s" %(del2))
with col4:
    d0=str(d0)
    st.metric(label="1.BMKG", value="%s" %(d0), delta= " " )
with col5:
    if len(d1) == 0:
        st.metric(label="2.GFZ", value=" ")
    else:
        d1=str(d1[0])
        st.metric(label="2.GFZ", value= "%s" %(d1), delta= "%s" %(del11))
with col6:
    if len(d2) == 0:
        st.metric (label = "3.USGS", value=" ")
    else:
        d2=str(d2[0])
        st.metric(label="3.USGS", value="%s" %(d2), delta= "%s " %(del22))

st.markdown(""" ## Longitude/Latitude""")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="1.BMKG", value="%s ; %s" %(x0,y0), delta=" ")
with col2:
    if len(x1)==0:
        st.metric(label="2.GFZ", value=" ", delta=" ")
    else:
        st.metric(label="2.GFZ", value="%s ; %s" %(x1,y1), delta="%s Km" %(del111))
with col3:
    if len(x2)==0:        
        st.metric(label="3.USGS", value=" ", delta=" ")
    else:
        st.metric(label="3.USGS", value="%s ; %s" %(x2,y2), delta="%s Km" %(del222))
    
st_data = st_folium(m, width=1000)

st.markdown(""" ### 15 Data Gempabumi Terkini""")
st.table(df_bmkg)

st.markdown(
    """ 
    ### Link Website 
    -  BMKG [Badan Meteorologi Klimatologi dan Geofisika](https://www.bmkg.go.id/)
    -  InaTEWS [Indonesia Tsunami Early Warning System](https://inatews.bmkg.go.id/)
    -  Webdc BMKG [Access to BMKG Data Archive](https://geof.bmkg.go.id/webdc3/)
"""
)
