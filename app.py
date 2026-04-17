import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="RescueNet Nigeria 🇳🇬", layout="wide")

st.title("🚨 RescueNet Nigeria 🇳🇬")

# -----------------------------
# INCIDENT → AGENCY MAP
# -----------------------------
AGENCY_MAP = {
    "Road Accident": "FRSC",
    "Fire Outbreak": "Fire Service",
    "Flood": "NEMA",
    "Kidnapping": "Police",
    "Critical Asset Vandalism": "NSCDC"
}

# -----------------------------
# AGENCY PHONE NUMBERS
# -----------------------------
AGENCY_PHONES = {
    "FRSC": "+2340000000000",
    "Fire Service": "+2340000000000",
    "NEMA": "+2340000000000",
    "Police": "+2340000000000",
    "NSCDC": "+2340000000000"
}

def get_agency_phone(agency):
    return AGENCY_PHONES.get(agency)

# -----------------------------
# WHATSAPP + CALL SYSTEM
# -----------------------------
def send_alert(incident, agency, desc, lat, lon):

    try:
        to_number = get_agency_phone(agency)

        if not to_number:
            return "No number available"

        message = f"""🚨 RescueNet Nigeria 🇳🇬
Incident: {incident}
Agency: {agency}
Location: {lat}, {lon}

Details:
{desc}
"""

        encoded = urllib.parse.quote(message)

        whatsapp_link = f"https://wa.me/{to_number.replace('+','')}?text={encoded}"
        call_link = f"tel:{to_number}"

        return {
            "whatsapp": whatsapp_link,
            "call": call_link
        }

    except Exception as e:
        return str(e)

# -----------------------------
# SESSION STORAGE
# -----------------------------
if "reports" not in st.session_state:
    st.session_state.reports = []

# -----------------------------
# MENU
# -----------------------------
menu = st.sidebar.selectbox("Menu", ["Report Incident", "Dashboard"])

# =============================
# REPORT PAGE
# =============================
if menu == "Report Incident":

    st.subheader("📍 Report Emergency")

    col1, col2 = st.columns(2)

    with col1:
        incident = st.selectbox("Select Incident", list(AGENCY_MAP.keys()))
        agency = AGENCY_MAP[incident]

        st.info(f"🚑 Assigned Agency: {agency}")

        desc = st.text_area("Describe incident")

        file = st.file_uploader("Upload Image/Video", type=["jpg", "png", "mp4"])

    with col2:
        st.markdown("### 📌 Select Location")

        lat = st.number_input("Latitude", value=9.0820)
        lon = st.number_input("Longitude", value=8.6753)

        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=6)

    if st.button("🚨 Submit Report"):

        if not desc:
            st.warning("Please describe the incident")
        else:
            report = {
                "incident": incident,
                "agency": agency,
                "desc": desc,
                "lat": lat,
                "lon": lon,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            st.session_state.reports.append(report)

            result = send_alert(incident, agency, desc, lat, lon)

            st.success("✅ Report saved successfully!")

            if isinstance(result, dict):

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"[📲 Send via WhatsApp]({result['whatsapp']})")

                with col2:
                    st.markdown(f"[📞 Call Agency Now]({result['call']})")

            else:
                st.warning(result)

# =============================
# DASHBOARD
# =============================
elif menu == "Dashboard":

    st.subheader("📊 Live Incident Dashboard")

    if len(st.session_state.reports) == 0:
        st.info("No reports yet")
    else:
        df = pd.DataFrame(st.session_state.reports)

        st.dataframe(df, use_container_width=True)

        st.map(df)
