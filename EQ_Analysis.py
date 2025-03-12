import streamlit as st
from PIL import Image
import folium
from bs4 import BeautifulSoup
import requests
import pandas as pd
from streamlit_folium import st_folium

st.set_page_config(page_title="EQ Analyis", layout="wide", page_icon="🌏")

#st.write("# Earthquake Data Analysis 👨🏽‍💼")
#st.sidebar.success("EQ Analysis Menu")

url='https://geofon.gfz.de/fdsnws/event/1/query?end=2025-03-13&limit=40&format=text'
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

event_id=get_qc(event_qc,0)
date_time=get_qc(event_qc,1)
mag=get_qc(event_qc,10)
typemag=get_qc(event_qc,9)
lat=get_qc(event_qc,2)
lon=get_qc(event_qc,3)
depth=get_qc(event_qc,4)
remarks=get_qc(event_qc,12)

df_gfz = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mag':mag,'typemag':typemag,'lat':lat,
                   'lon':lon,'depth':depth,'remarks':remarks})
df_gfz['mag_text']=df_gfz['mag']+' ' +df_gfz['typemag']
df_gfz['date_time']=pd.to_datetime(df_gfz['date_time'])

from datetime import datetime,timedelta
now=datetime.today().strftime('%Y-%m-%d')
p4days=(datetime.today() - timedelta(days=4)).strftime('%Y-%m-%d')

usgs_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=%s&endtime=%s&minmagnitude=4.0' %(p4days,now)
df_usgs = pd.read_csv(usgs_url)

df_usgs['DATEUSGS']=pd.to_datetime(df_usgs['time'])
df_usgs['date_usgs_local'] = df_usgs['DATEUSGS']
df_usgs['noniso_dateusgs'] = df_usgs['date_usgs_local'].dt.strftime('%d-%m-%Y %H:%M:%S')
df_usgs['fix_dateusgs']=pd.to_datetime(df_usgs['noniso_dateusgs'])

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

def fix_float(z):
    temp=[]
    for i in range(len(z)):
        b=float(z[i])
        temp.append(b)
    return temp

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

df_bmkg=pd.DataFrame({'eventid':eventid,'waktu':waktu,'lat':lat,'lon':lon,'mag':mag,
                 'depth':dep,'area':l_area})
df_bmkg['waktu']=pd.to_datetime(df_bmkg['waktu'])
df_bmkg= df_bmkg[df_bmkg['mag'] >=5]

x0=df_bmkg['lon'].to_list()[3]
y0=df_bmkg['lat'].to_list()[3]
m0=df_bmkg['mag'].to_list()[3]
z0=df_bmkg['depth'].to_list()[3]

temp=df_bmkg['waktu'].to_list()
a=temp[3]
x1,y1,m1,d1=[],[],[],[]
for i in range(len(df_gfz['date_time'])):
    b=df_gfz['date_time'][i]
    if abs(timedelta.total_seconds(a-b)) < 5:
        x=df_gfz['lon'][i]
        y=df_gfz['lat'][i]
        m=df_gfz['mag'][i]
        d=df_gfz['depth'][i]
        x1.append(x),y1.append(y),m1.append(m),d1.append(d)
    else:
        continue

x2,y2,m2,d2=[],[],[],[]
for i in range(len(df_usgs['fix_dateusgs'])):
    b=df_usgs['fix_dateusgs'][i]
    if abs(timedelta.total_seconds(a-b)) < 5:
        x=df_usgs['longitude'][i]
        y=df_usgs['latitude'][i]
        m=df_usgs['mag'][i]
        d=df_usgs['depth'][i]
        x2.append(x),y2.append(y),m2.append(m),d2.append(d)
    else:
        continue


import folium
tiles='https://services.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
m= folium.Map(( y0,x0),tiles=tiles, attr='ESRI', zoom_start=7)

#html1 = """ <p> Mag: %s </p> <p> Kedalaman : %s </p> """ %(m0, d0)
x1=str(x1[0])
y1=str(y1[0])
#x2=str(x2[0])
#y2=str(y2[0])
folium.Marker(location=[ y0,x0], icon=folium.Icon(icon_shape='circle-dot'),).add_to(m)
folium.Marker(location=[y1,x1], icon=folium.Icon(icon_shape='circle-dot'),).add_to(m)
#folium.Marker(location=[y2,x2], icon=folium.Icon(icon_shape='circle-dot'),).add_to(m)



#st.markdown(""" ### Gempa Terkini BMKG - USGS - GFZ """)
col1, col2, col3 = st.columns(3)
with col1:
    m0=str(m0)
    st.metric(label="BMKG", value="%s" %(m0), delta=" ")
with col2:
    m1=str(m1)
    dm=str(abs(m0-m1))
    st.metric(label="USGS", value="%s" %(m1), delta="%s"(dm))
#with col3:
#    st.metric(label="USGS", value="%s" %(m2), delta="%s"(abs(m0-m2)))
    
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
