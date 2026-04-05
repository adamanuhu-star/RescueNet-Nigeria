import streamlit as st
import folium
from streamlit_folium import st_folium

# PAGE CONFIG
st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

# TITLE
st.title("🚨 RescueNet Nigeria 🇳🇬")
st.write("AI-Powered Emergency Response System")

# ---------------- MAP ----------------
st.subheader("📍 Select Incident Location")

# Nigeria center
m = folium.Map(location=[9.0820, 8.6753], zoom_start=6)

map_data = st_folium(m, width=700, height=400)

lat, lon = None, None

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📍 Selected Location: {lat}, {lon}")

# ---------------- INCIDENT ----------------
incident = st.selectbox("🚨 Incident Type", [
    "Road Accident",
    "Fire Outbreak",
    "Flood",
    "Kidnapping",
    "Critical National Asset Vandalism"
])

# SMART ROUTING
agency = ""
agency_number = ""

if incident == "Road Accident":
    agency = "🚧 FRSC"
    agency_number = "122"

elif incident == "Fire Outbreak":
    agency = "🚒 Fire Service"
    agency_number = "112"

elif incident == "Flood":
    agency = "🌊 NEMA"
    agency_number = "0800-ANEMA"

elif incident == "Kidnapping":
    agency = "🚓 Police"
    agency_number = "112"

elif incident == "Critical National Asset Vandalism":
    agency = "🛡️ NSCDC"
    agency_number = "0800-NSCDC"

# SHOW ROUTING
st.info(f"📡 Assigned Agency: {agency} | 📞 {agency_number}")

# ---------------- DETAILS ----------------
description = st.text_area("📝 Describe the situation")
uploaded_file = st.file_uploader("📸 Upload Image/Video Evidence")

# ---------------- REPORT ----------------
if st.button("🚀 Report Incident"):
    if lat and lon:
        st.success("✅ Incident reported successfully!")
        st.write(f"📍 Location: {lat}, {lon}")
        st.write(f"🚨 Agency: {agency}")
        st.write(f"📞 Contact: {agency_number}")
    else:
        st.error("⚠️ Please select location on the map")

# ---------------- CONTACTS ----------------
st.markdown("## 🚑 Emergency Contacts")

st.write("🚓 Police: 112")
st.write("🚒 Fire Service: 112")
st.write("🚧 FRSC: 122")
st.write("🌊 NEMA: 0800-ANEMA")
st.write("🛡️ NSCDC: 0800-NSCDC")
