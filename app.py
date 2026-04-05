import streamlit as st
import folium
from streamlit_folium import st_folium
import geocoder

# ---------------- PAGE ----------------
st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

# ---------------- TITLE ----------------
st.markdown("<h1 style='text-align: center;'>🚨 RescueNet Nigeria 🇳🇬</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>AI-Powered Emergency Response System</p>", unsafe_allow_html=True)

st.divider()

# ---------------- AUTO LOCATION ----------------
if "lat" not in st.session_state:
    g = geocoder.ip('me')
    if g.ok:
        st.session_state.lat = g.latlng[0]
        st.session_state.lon = g.latlng[1]
    else:
        st.session_state.lat = None
        st.session_state.lon = None

# ---------------- LAYOUT ----------------
col1, col2 = st.columns([1, 1])

# -------- LEFT: MAP --------
with col1:
    st.subheader("📍 Location")

    default_lat = 9.0820
    default_lon = 8.6753

    lat = st.session_state.lat if st.session_state.lat else default_lat
    lon = st.session_state.lon if st.session_state.lon else default_lon

    m = folium.Map(location=[lat, lon], zoom_start=10)

    map_data = st_folium(
        m,
        width=500,
        height=350,
        key="map"
    )

    # Save click
    if map_data and map_data.get("last_clicked"):
        st.session_state.lat = map_data["last_clicked"]["lat"]
        st.session_state.lon = map_data["last_clicked"]["lng"]

    # Show location
    if st.session_state.lat:
        st.success(f"
