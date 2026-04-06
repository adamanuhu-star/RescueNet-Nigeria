import streamlit as st
import folium
from streamlit_folium import st_folium
import geocoder
import csv
import os
import pandas as pd
import speech_recognition as sr

# ---------------- PAGE ----------------
st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

# ---------------- LANGUAGE ----------------
language = st.sidebar.selectbox(
    "🌍 Language",
    ["English", "Pidgin", "Hausa", "Yoruba", "Igbo"]
)

def translate(text):
    translations = {
        "Report Incident": {
            "Pidgin": "Report Wahala",
            "Hausa": "Kai Rahoton Hadari",
            "Yoruba": "Jabo Iṣẹlẹ",
            "Igbo": "Kọwaa Ihe Mere"
        },
        "Describe situation": {
            "Pidgin": "Explain wetin happen",
            "Hausa": "Bayyana abinda ya faru",
            "Yoruba": "Ṣàlàyé ohun tó ṣẹlẹ̀",
            "Igbo": "Kọwaa ihe mere"
        }
    }
    return translations.get(text, {}).get(language, text)

# ---------------- TITLE ----------------
st.markdown("<h1 style='text-align: center;'>🚨 RescueNet Nigeria 🇳🇬</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Emergency Response System</p>", unsafe_allow_html=True)

st.divider()

# ---------------- VOICE FUNCTION ----------------
def voice_to_text(audio_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return text
    except:
        return ""

# ---------------- SAVE ----------------
def save_report(lat, lon, incident, agency, description):
    file_exists = os.path.isfile("reports.csv")

    with open("reports.csv", mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Latitude", "Longitude", "Incident", "Agency", "Description"])

        writer.writerow([lat, lon, incident, agency, description])

# ---------------- LOAD ----------------
def load_reports():
    if os.path.exists("reports.csv"):
        return pd.read_csv("reports.csv")
    return pd.DataFrame(columns=["Latitude", "Longitude", "Incident", "Agency", "Description"])

# ---------------- MENU ----------------
menu = st.sidebar.selectbox("Menu", ["Report Incident", "Dashboard"])

# ---------------- LOCATION ----------------
if "lat" not in st.session_state:
    try:
        g = geocoder.ip('me')
        if g.ok:
            st.session_state.lat = g.latlng[0]
            st.session_state.lon = g.latlng[1]
        else:
            st.session_state.lat = None
            st.session_state.lon = None
    except:
        st.session_state.lat = None
        st.session_state.lon = None

# ================= REPORT PAGE =================
if menu == "Report Incident":

    col1, col2 = st.columns([1, 1])

    # -------- MAP --------
    with col1:
        st.subheader("📍 Location")

        lat = st.session_state.lat or 9.0820
        lon = st.session_state.lon or 8.6753

        m = folium.Map(location=[lat, lon], zoom_start=10)
        map_data = st_folium(m, width=500, height=350)

        if map_data and map_data.get("last_clicked"):
            st.session_state.lat = map_data["last_clicked"]["lat"]
            st.session_state.lon = map_data["last_clicked"]["lng"]

        if st.session_state.lat:
            st.success(f"📍 {st.session_state.lat}, {st.session_state.lon}")
        else:
            st.warning("Select location")

    # -------- FORM --------
    with col2:
        st.subheader("🚨 " + translate("Report Incident"))

        incident = st.selectbox("Incident Type", [
            "Road Accident",
            "Fire Outbreak",
            "Flood",
            "Kidnapping",
            "Critical National Asset Vandalism"
        ])

        agency = ""
        number = ""

        if incident == "Road Accident":
            agency, number = "FRSC", "122"
        elif incident == "Fire Outbreak":
            agency, number = "Fire Service", "112"
        elif incident == "Flood":
            agency, number = "NEMA", "0800-ANEMA"
        elif incident == "Kidnapping":
            agency, number = "Police", "112"
        elif incident == "Critical National Asset Vandalism":
            agency, number = "NSCDC", "0800-NSCDC"

        st.info(f"{agency} | 📞 {number}")

        # 🎙️ VOICE INPUT
        audio = st.file_uploader("🎙️ Upload Voice Note (.wav only)", type=["wav"])

        if audio:
            st.audio(audio)
            voice_text = voice_to_text(audio)

            if voice_text:
                st.success("🧠 Voice converted to text")
                description = st.text_area("📝 " + translate("Describe situation"), value=voice_text)
            else:
                st.warning("Voice not clear, type manually")
                description = st.text_area("📝 " + translate("Describe situation"))
        else:
            description = st.text_area("📝 " + translate("Describe situation"))

        # 📷 IMAGE
        image = st.file_uploader("📷 Upload Image", type=["jpg", "png", "jpeg"])

        # 🎥 VIDEO
        video = st.file_uploader("🎥 Upload Video", type=["mp4", "mov"])

        if st.button("🚀 Report Incident"):
            if st.session_state.lat is not None:

                save_report(
                    st.session_state.lat,
                    st.session_state.lon,
                    incident,
                    agency,
                    description
                )

                st.success("✅ Report submitted successfully")

                if image:
                    st.image(image)

                if video:
                    st.video(video)

            else:
                st.error("⚠️ Please select location on map")

# ================= DASHBOARD =================
elif menu == "Dashboard":

    st.subheader("📊 Incident Dashboard")

    data = load_reports()

    if not data.empty:

        st.dataframe(data)

        csv_file = data.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Reports", csv_file, "reports.csv")

        st.divider()

        st.subheader("🗺️ Live Incident Map")

        m = folium.Map(location=[9.0820, 8.6753], zoom_start=6)

        for _, row in data.iterrows():
            folium.Marker(
                [row["Latitude"], row["Longitude"]],
                popup=f"{row['Incident']} - {row['Agency']}",
                icon=folium.Icon(color="red")
            ).add_to(m)

        st_folium(m, width=800, height=500)

    else:
        st.warning("No reports yet")

# ---------------- FOOTER ----------------
st.divider()
st.markdown("### 🚑 Emergency Contacts")

st.write("🚓 Police: 112")
st.write("🚧 FRSC: 122")
st.write("🚒 Fire: 112")
st.write("🌊 NEMA: 0800-ANEMA")
st.write("🛡️ NSCDC: 0800-NSCDC")
