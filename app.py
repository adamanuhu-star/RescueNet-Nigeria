import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

# LANGUAGE
language = st.selectbox("🌍 Language", ["English", "Pidgin"])

if language == "Pidgin":
    title = "🚨 RescueNet Nigeria"
    report_btn = "Send Report"
    success_msg = "✅ Report don send!"
else:
    title = "🚨 RescueNet Nigeria 🇳🇬"
    report_btn = "Report Incident"
    success_msg = "✅ Incident reported!"

st.title(title)

# MAP
st.subheader("📍 Select Incident Location")

m = folium.Map(location=[9.0820, 8.6753], zoom_start=6)  # Nigeria center

map_data = st_folium(m, width=700, height=400)

lat, lon = None, None

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"Selected Location: {lat}, {lon}")

# INCIDENT FORM
incident = st.selectbox("Incident Type", [
    "Road Accident",
    "Fire Outbreak",
    "Flood",
    "Kidnapping",
    "Vandalism"
])

description = st.text_area("Describe the situation")
uploaded_file = st.file_uploader("Upload Image/Video")

# REPORT
if st.button(report_btn):
    if lat and lon:
        st.success(success_msg)
        st.write(f"📍 Location: {lat}, {lon}")
    else:
        st.error("⚠️ Please select location on the map")

# CONTACTS
st.markdown("## 🚑 Emergency Contacts")
st.write("🚓 Police: 112")
st.write("🚒 Fire Service: 112")
st.write("🚧 FRSC: 122")
st.write("🌊 NEMA: 0800-ANEMA")
