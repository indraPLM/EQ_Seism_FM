from bs4 import BeautifulSoup
import requests
import pandas as pd
import streamlit as st


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

url='https://rtsp.bmkg.go.id/publicbull.php'
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

def split_list(lst, chunk_size):
    chunks = []
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        chunks.append(chunk)
    return chunks

chunk_size = 9
chunks = split_list(tsp_table, chunk_size)

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

date_time,mag,depth,lat,lon,typ,num_bull,evt_group=[],[],[],[],[],[],[],[]
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

df=pd.DataFrame({'date_time':date_time,'mag':mag,'depth':depth,'lat':lat,'lon':lon,'typ':typ,'num_bull':num_bull,'evt_group':evt_group})
df['date_time']=pd.to_datetime(df['date_time'])
df['fixedLat'] = df.lat.apply(fix_latitude)
df['fixedLon'] = df.lon.apply(fix_longitude)
df['sizemag']=1000*df['mag']

#st.markdown(""" ### Peta Lokasi Gempabumi berdasarkan Diseminasi RTSP """)
#st.map(df, latitude="fixedLat", longitude="fixedLon")

st.markdown(""" ### Tabel RTSP BMKG """)
st.dataframe(df)
