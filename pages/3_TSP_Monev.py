from bs4 import BeautifulSoup
import requests
import pandas as pd
import streamlit as st
import numpy as np

st.set_page_config(page_title='TSP Monitoring dan Evaluasi',  layout='wide', page_icon="🌍")
#st.title('Seismisitas dan Statistik Kegempaan')

st.sidebar.header("Input Parameter :")
 
time_start=st.sidebar.text_input('Start Time:', '2025-01-01 00:00:00')
time_end=st.sidebar.text_input('End Time:', '2025-01-31 23:59:59')

layout2 = st.sidebar.columns(2)
with layout2[0]: 
    North = st.number_input('North:', 6.0) 
with layout2[-1]: 
    South = st.number_input('South:', -13.0)
 
layout3 = st.sidebar.columns(2)
with layout3[0]: 
    West = st.number_input('West:', 90.0)
with layout3[-1]: 
    East = st.number_input('East:', 142.0)

def split_list(lst, chunk_size):
    chunks = []
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        chunks.append(chunk)
    return chunks

def fix_latitude(x):
    if x.endswith('S'):
        x = -float(x.strip('S'))
    else:
        x = x.strip('N')
    return x

def fix_longitude(y):
    if y.endswith('W'):
        y = -float(y.strip('W'))
    else:
        y = y.strip('E')
    return y

def date_diff_in_Seconds(dt1, dt2):
    # Calculate the time difference between dt2 and dt1
    timedelta = abs(dt1 - dt2)
    # Return the total time difference in seconds
    return timedelta.days * 24 * 3600 + timedelta.seconds

def get_rtsp(url):
    page=requests.get(url)
    url_pages=BeautifulSoup(page.text, 'html')

    table=url_pages.find('table')
    rows=table.find_all("td",{"class":"txt11pxarialb"})
    tsp_table=[]
    for row in rows:
        cells = row.find_all('div')
        for cell in cells:
            #data=cell.text
            tsp_table.append(cell.text)
    chunk_size = 9
    chunks = split_list(tsp_table, chunk_size)
    
    date_time,mag,depth,lat,lon=[],[],[],[],[]
    typ,num_bull,evt_group=[],[],[]
    for lst in chunks:
        a='%s %s' %(lst[0],lst[1])
        date_time.append(a)
        b=float(lst[2])
        mag.append(b)
        c=float(lst[3])
        depth.append(c)
        d=lst[4]
        lat.append(d)
        e=lst[5]
        lon.append(e)
        f=lst[6]
        typ.append(f)
        g=lst[7]
        num_bull.append(g)
        h=lst[8]
        evt_group.append(h)

    df=pd.DataFrame({'date_time':date_time,'mag':mag,'depth':depth,
                     'lat':lat,'lon':lon,'typ':typ,'num_bull':num_bull,
                     'evt_group':evt_group})
    
    df['date_time']=pd.to_datetime(df['date_time'])
    df['fixedLat'] = df.lat.apply(fix_latitude)
    df['fixedLat'] = pd.to_numeric(df['fixedLat'],errors = 'coerce')

    df['fixedLon'] = df.lon.apply(fix_longitude)
    df['fixedLon'] = pd.to_numeric(df['fixedLon'],errors = 'coerce')
    df['sizemag']=1000*df['mag']
    
    return df
# RTSP halaman awal
df_awal=get_rtsp('https://rtsp.bmkg.go.id/publicbull.php')
# RTSP halaman selanjutnya
pages=14
a=np.arange(2,pages+1,1)
df=[]
for i in a:
    temp=get_rtsp('https://rtsp.bmkg.go.id/publicbull.php?halaman=%s' % (i))
    df.append(temp)
df_rtsp=pd.concat([df_awal,df[0],df[1],df[2],df[3],df[4],df[5],df[6],df[7],
                  df[8],df[9],df[10],df[11],df[12]], ignore_index=True)
print(df_rtsp)

st.markdown(""" ### Peta Lokasi Gempabumi berdasarkan Diseminasi RTSP """)
st.map(df_rtsp, latitude="fixedLat", longitude="fixedLon", size="sizemag")

st.markdown(""" ### Tabel RTSP BMKG """)
st.dataframe(df_rtsp)

usgs_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-01-01&endtime=2025-01-02&minmagnitude=6.0'
df_usgs = pd.read_csv(usgs_url)

st.markdown(""" ### Peta Lokasi Gempabumi M > 6 Katalog USGS """)
st.map(df_usgs, latitude="latitude", longitude="longitude")

st.markdown(""" ### Tabel USGS EQ Significant """)
st.dataframe(df_usgs)

tsp_data=[]
for i in range(len(df_rtsp['date_time'])):
    for j in range(len(df_usgs['time'])):
        laps=date_diff_in_Seconds(df_rtsp['date_time'][i],df_usgs['time'][j].tz_convert(None))
        #lapse.append(laps)
        if laps <= 20 :
            #print(laps,df_rtsp['date_time'][i],df_usgs['time'][j])
            date_bmkg = df_rtsp['date_time'][i]
            date_usgs = df_usgs['time'][j]
            #loc_bmkg =df_usgs['place'][j]
            lon_bmkg = float(df_rtsp['fixedLon'][i])
            lat_bmkg = float(df_rtsp['fixedLat'][i])
            lon_usgs = df_usgs['longitude'][j]
            lat_usgs = df_usgs['latitude'][j]
            mag_bmkg =df_rtsp['mag'][i]
            mag_usgs =df_usgs['mag'][j]
            depth_bmkg =df_rtsp['depth'][i]
            depth_usgs =df_usgs['depth'][j]
            tsp_data.append([date_bmkg,date_usgs,laps,loc_bmkg,lon_bmkg,lon_usgs,
                             lat_bmkg,lat_usgs,mag_bmkg,mag_usgs,depth_bmkg,depth_usgs])
            

df_tsp = pd.DataFrame(tsp_data, columns=['date_bmkg','date_usgs','lapse_time(s)','loc_bmkg','lon_bmkg','lon_usgs',
                 'lat_bmkg','lat_usgs','mag_bmkg','mag_usgs','depth_bmkg','depth_usgs'])

from obspy.geodetics import degrees2kilometers
import numpy as np

df_tsp['lon_diff'] = df_tsp.apply(lambda x: abs(x['lon_bmkg'] - x['lon_usgs']), axis=1)
df_tsp['lon_diff_km']=degrees2kilometers(df_tsp.lon_diff)
df_tsp['lat_diff'] = df_tsp.apply(lambda x: abs(x['lat_bmkg'] - x['lat_usgs']), axis=1)
df_tsp['lat_diff_km']=degrees2kilometers(df_tsp.lat_diff)

df_tsp['mag_diff'] = df_tsp.apply(lambda x: abs(x['mag_bmkg'] - x['mag_usgs']), axis=1)
df_tsp['depth_diff'] = df_tsp.apply(lambda x: abs(x['depth_bmkg'] - x['depth_usgs']), axis=1)
df_tsp['distance_diff_km']=(np.sqrt(df_tsp[['lon_diff_km', 'lat_diff_km']].sum(axis=1)))**2

st.pyplot(df_tsp.plot( 'date_bmkg' , 'mag_diff',figsize=(20, 15)))
st.pyplot(df_tsp.plot( 'date_bmkg' , 'depth_diff',figsize=(20, 15))) 
st.pyplot(df_tsp.plot( 'date_bmkg' , 'distance_diff_km',figsize=(20, 15))) 
