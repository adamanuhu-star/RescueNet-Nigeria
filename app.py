import streamlit as st
import folium
from streamlit_folium import st_folium

st.title("🚨 RescueNet Nigeria - Map Test")

# Center map on Nigeria
m = folium.Map(location=[9.0820, 8.6753], zoom_start=6)

# Show map in Streamlit
st_data = st_folium(m, width=700, height=400)

if st_data.get("last_clicked"):
    lat = st_data["last_clicked"]["lat"]
    lon = st_data["last_clicked"]["lng"]
    st.write(f"📍 You clicked: {lat}, {lon}")
