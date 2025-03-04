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
#df_rtsp.query('%s <= date_time <= %s' %(t0,t1))

st.markdown(""" ### Peta Lokasi Gempabumi berdasarkan Diseminasi RTSP """)
st.map(df_rtsp, latitude="fixedLat", longitude="fixedLon", size="sizemag")

st.markdown(""" ### Tabel RTSP BMKG """)
st.dataframe(df_rtsp)

usgs_url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-01-01&endtime=2025-03-02&minmagnitude=6.0'
df_usgs = pd.read_csv(usgs_url)

df_usgs['DATEUSGS']=pd.to_datetime(df_usgs['time'])
df_usgs['date_usgs_local'] = df_usgs['DATEUSGS']
df_usgs['noniso_dateusgs'] = df_usgs['date_usgs_local'].dt.strftime('%d-%m-%Y %H:%M:%S')
df_usgs['fix_dateusgs']=pd.to_datetime(df_usgs['noniso_dateusgs'])
#print(df_usgs['fix_dateusgs'])

#df_usgs.query('%s <= fix_dateusgs <= %s' %(t0,t1))

st.markdown(""" ### Peta Lokasi Gempabumi M > 6 Katalog USGS """)
st.map(df_usgs, latitude="latitude", longitude="longitude")

st.markdown(""" ### Tabel USGS EQ Significant """)
st.dataframe(df_usgs)

tsp_data=[]
for i in range(len(df_rtsp['date_time'])):
    for j in range(len(df_usgs['time'])):
        dt1=df_rtsp['date_time'][i]
        dt2=df_usgs['fix_dateusgs'][j]
        laps=date_diff_in_Seconds(dt1,dt2)
        #lapse.append(laps)
        if laps <= 20 :
            #print(laps,df_rtsp['date_time'][i],df_usgs['time'][j])
            date_bmkg = df_rtsp['date_time'][i]
            date_usgs = df_usgs['time'][j]
            loc_bmkg =df_usgs['place'][j]
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

df_tsp_new= df_tsp[(df_tsp['date_bmkg'] > time_start) & (df_tsp['date_bmkg'] < time_end)]

st.markdown(""" ### Grafik Selisih Magnitudo USGS - BMKG (RTSP) """)
st.line_chart(df_tsp_new, x="date_bmkg", y="mag_diff")

st.markdown(""" ### Grafik Selisih Kedalaman USGS - BMKG (RTSP) """)
st.line_chart(df_tsp_new, x="date_bmkg", y="depth_diff")

st.markdown(""" ### Grafik Selisih Jarak USGS - BMKG (RTSP) """)
st.line_chart(df_tsp_new, x="date_bmkg", y="distance_diff_km")

st.markdown(""" ### Tabel Perbandingan Parameter Gempa USGS - BMKG(RTSP) """)
st.dataframe(df_tsp_new)

def get_rtsp_time_Diss(url):
    page=requests.get(url)
    url_pages=BeautifulSoup(page.text, 'html')

    table=url_pages.find('table')
    rows=table.find_all("td",{"class":"txt12pxarialb"})
    diss_table=[]
    for row in rows:
        cells = row.find_all('div')
        for cell in cells:
            #data=cell.text
            diss_table.append(cell.text)
    return diss_table
a=list(df_tsp_new['event_group'])
OT_Diss=[]

for i in a:
    temp=get_rtsp_time_Diss('https://rtsp.bmkg.go.id/timelinepub.php?id=&session_id=&grup=%s' % (i))
    
    OT_temp=temp[0].split()
    Diss_temp=temp[1].split()
    OT_date=OT_temp[1]
    OT_time=OT_temp[2]
    OT_datetime='%s %s' %(OT_date,OT_time)
    
    Diss_date=Diss_temp[0]
    Diss_time=Diss_temp[1]
    Diss_datetime='%s %s' %(Diss_date,Diss_time)
    OT_Diss.append([OT_datetime,Diss_datetime])
    
df_ot_diss=pd.DataFrame(OT_Diss, columns=['OT_datetime','Diss_datetime'])

dt1=pd.to_datetime(df_ot_diss['OT_datetime'])
dt2=pd.to_datetime(df_ot_diss['Diss_datetime'])
laps=dt2-dt1

df_ot_diss['Lapse_Time']=laps
#print(df_ot_diss)
st.markdown(""" ### Tabel Perbandingan Waktu Kirim OT dan Diseminasi BMKG(RTSP) """)
st.dataframe(df_ot_diss)


