import os,sys
from bs4 import BeautifulSoup
import requests
import pandas as pd



path = "C://Users//Asus//Documents//@2025//KANTOR//PROJECT_STREAMLIT//EQ_Analysis//pages//file_toast"
dir_list = os.listdir(path)

event_list = []
for i in range(len(dir_list)):
    temp=dir_list[i].split('.log')
    temp=temp[0]
    event_list.append(temp)

text_toast=[]
for i in range(len(dir_list)):
    curr=os.getcwd() 
    test=dir_list[i]
    with open(curr+'//file_toast//'+test) as f:
        lines = f.readlines()
        text_toast.append(lines)
print([len(text_toast),len(event_list)])

dttime_toast,remark_toast=[],[]
eventid_toast=[]
for i in range(len(text_toast)):    
    if event_list[i].startswith('bmg2024'):
        #print(event_list[i])
        t=text_toast[i][2].split()
        dttime=t[0]+' '+t[1]
        remark=t[2]
        #print([event_list[i],dttime,remark])
        dttime_toast.append(dttime)
        remark_toast.append(remark)
        eventid_toast.append(event_list[i])
    else:
        continue
    

df_toast= pd.DataFrame({'event_id':eventid_toast,'tstamp_toast':dttime_toast,'remark_toast':remark_toast})
df_toast['tstamp_toast'] = pd.to_datetime(df_toast['tstamp_toast'])

url='http://202.90.198.41/qc.txt'
page=requests.get(url)
url_pages=BeautifulSoup(page.text, 'html')

a=[]
for fo in url_pages.p:
    a.append(fo)
b=a[0].split('\n')
event_qc=[]
for i in range(len(b)):
    qc=b[i].split('|')
    event_qc.append(qc)

def get_qc(file,par):
    par=par
    data=[]
    for i in file[1:9000]:
        temp=i[par]
        data.append(temp)
    return data

event_id=get_qc(event_qc,0)
date_time=get_qc(event_qc,1)
mag=get_qc(event_qc,5)
lat=get_qc(event_qc,10)
lon=get_qc(event_qc,11)
depth=get_qc(event_qc,12)
remarks=get_qc(event_qc,14)

df = pd.DataFrame({'event_id':event_id,'date_time':date_time,'mag':mag,'lat':lat,
                   'lon':lon,'depth':depth,'remarks':remarks})

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

def fix_depth(z):
    z = z.strip()
    if z.endswith('km'):
        z = float(z.strip('km'))
    return z
    
def fix_float(z):
    temp=[]
    for i in range(len(z)):
        b=float(z[i])
        temp.append(b)
    return temp
def fix_split(a):
    a= a.strip()
    return a

df['event_id'] = df.event_id.apply(fix_split)

df['lat'] = df.lat.apply(fix_latitude)
df['lat'] = pd.to_numeric(df['lat'],errors = 'coerce')

df['lon'] = df.lon.apply(fix_longitude)
df['lon'] = pd.to_numeric(df['lon'],errors = 'coerce')

df['depth'] = df.depth.apply(fix_depth)
df['depth'] = pd.to_numeric(df['depth'],errors = 'coerce')

df['date_time'] = pd.to_datetime(df['date_time'])
df['date_time_wib'] = df['date_time'] + pd.Timedelta(hours=7)
df['mag'] = fix_float(df['mag'])
df= df[df['mag'] >=5]
df= df[(df['date_time'] > df_toast['tstamp_toast'][0] ) & (df['date_time'] < df_toast['tstamp_toast'][len(df_toast)-1])]
df_qc=df

result = pd.merge(df_qc, df_toast, on="event_id")
result['lapse_time_toast']=result['tstamp_toast']-result['date_time_wib']

st.dataframe(result)
