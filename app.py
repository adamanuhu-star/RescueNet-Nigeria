import streamlit as st
import folium
from streamlit_folium import st_folium
import geocoder
import csv
import os
import pandas as pd
import whisper
import tempfile

# ---------------- PAGE ----------------
st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

# ---------------- TITLE ----------------
st.markdown("<h1 style='text-align: center;'>🚨 RescueNet Nigeria 🇳🇬</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Emergency Response System</p>", unsafe_allow_html=True)
st.divider()

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

# ---------------- WHISPER ----------------
@st.cache_resource
def load_model():
    return whisper.load_model("base")

def whisper_transcribe(audio_file):
    try:
        model = load_model()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name

        result = model.transcribe(tmp_path)
        return result["text"]

    except Exception:
        return "⚠️ Voice processing failed"

# ---------------- AI DETECTION ----------------
def detect_incident(text):
    text = text.lower()

    if "accident" in text or "crash" in text:
        return "Road Accident", "FRSC", "122"
    elif "fire" in text or "burn":
        return "Fire Outbreak", "Fire Service", "112"
    elif "flood" in text or "water":
        return "Flood", "NEMA", "0800-ANEMA"
    elif "kidnap" in text or "abduct":
        return "Kidnapping", "Police", "112"
    elif "vandal" in text or "pipeline":
        return "Critical National Asset Vandalism", "NSCDC", "0800-NSCDC"

    return None, None, None

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

# ================= REPORT =================
if menu == "Report Incident":

    col1, col2 = st.columns([1, 1])

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
            st.success(f"{st.session_state.lat}, {st.session_state.lon}")
        else:
            st.warning("Select location on map")

    with col2:
        st.subheader("🚨 " + translate("Report Incident"))

        incident = None
        agency = ""
        number = ""

        # VOICE
        audio = st.file_uploader("🎙️ Upload Voice", type=["wav", "mp3", "m4a", "ogg"])

        if audio:
            st.audio(audio)

            with st.spinner("Listening..."):
                voice_text = whisper_transcribe(audio)

            if "⚠️" in voice_text:
                st.error(voice_text)
                description = st.text_area("📝 " + translate("Describe situation"))
            else:
                st.success("Voice converted")
                description = st.text_area("📝 " + translate("Describe situation"), value=voice_text)
        else:
            description = st.text_area("📝 " + translate("Describe situation"))

        # AI detection
        if description:
            auto_incident, auto_agency, auto_number = detect_incident(description)

            if auto_incident:
                incident = auto_incident
                agency = auto_agency
                number = auto_number
                st.success(f"Detected: {incident}")

        # Manual fallback
        if not incident:
            incident = st.selectbox("Select Incident", [
                "Road Accident",
                "Fire Outbreak",
                "Flood",
                "Kidnapping",
                "Critical National Asset Vandalism"
            ])

            if incident == "Road Accident":
                agency, number = "FRSC", "122"
            elif incident == "Fire Outbreak":
                agency, number = "Fire Service", "112"
            elif incident == "Flood":
                agency, number = "NEMA", "0800-ANEMA"
            elif incident == "Kidnapping":
                agency, number = "Police", "112"
            else:
                agency, number = "NSCDC", "0800-NSCDC"

        st.info(f"{agency} | 📞 {number}")

        # Uploads
        image = st.file_uploader("📷 Image", type=["jpg", "png", "jpeg"])
        video = st.file_uploader("🎥 Video", type=["mp4", "mov"])

        if st.button("🚀 Submit Report"):
            if st.session_state.lat:
                save_report(
                    st.session_state.lat,
                    st.session_state.lon,
                    incident,
                    agency,
                    description
                )

                st.success("Report submitted")

                if image:
                    st.image(image)
                if video:
                    st.video(video)
            else:
                st.error("Select location first")

# ================= DASHBOARD =================
if menu == "Dashboard":

    st.subheader("📊 Dashboard")

    data = load_reports()

    if not data.empty:
        st.dataframe(data)

        st.download_button(
            "Download CSV",
            data.to_csv(index=False),
            "reports.csv"
        )

        st.subheader("🗺️ Live Map")

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
