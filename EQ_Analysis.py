# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 12:02:47 2022

@author: Asus
"""

import streamlit as st
from PIL import Image

st.set_page_config(page_title="EQ Analyis", page_icon="🌏")

st.write("# Earthquake Data Analysis 👨🏽‍💼")

st.sidebar.success("EQ Analysis Menu")

st.markdown(
    """
    ### Seismisitas dan Mekanisme Sumber (Focal Mechanism)
       
"""
)

image = Image.open('EQ_Catalog.png')
st.image(image, caption='Peta Seismisitas Indonesia')

image = Image.open('FM_Catalog.png')
st.image(image, caption='Katalog Mekanisme Sumber')

st.markdown(
    """ 
    ### Link Website 
    -  BMKG [Badan Meteorologi Klimatologi dan Geofisika](https://www.bmkg.go.id/)
    -  InaTEWS [Indonesia Tsunami Early Warning System](https://inatews.bmkg.go.id/)
    -  Webdc BMKG [Access to BMKG Data Archive](https://geof.bmkg.go.id/webdc3/)
"""
)