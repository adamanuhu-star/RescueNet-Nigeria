import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
import urllib.parse
import sqlite3

# -----------------------------
# DATABASE
# -----------------------------
conn = sqlite3.connect("rescuenet.db", check_same_thread=False)
c = conn.cursor()

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="RescueNet Nigeria 🇳🇬", layout="wide")

st.title("🚨 RescueNet Nigeria 🇳🇬")

# -----------------------------
# HASH PASSWORD
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -----------------------------
# AUTH FUNCTIONS
# -----------------------------
def create_user(username, password, role="user"):
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
              (username, hash_password(password), role))
    conn.commit()

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    return c.fetchone()

# -----------------------------
# INCIDENT MAP
# -----------------------------
AGENCY_MAP = {
    "Road Accident": "FRSC",
    "Fire Outbreak": "Fire Service",
    "Flood": "NEMA",
    "Kidnapping": "Police",
    "Critical Asset Vandalism": "NSCDC"
}

AGENCY_PHONES = {
    "FRSC": "+2340000000000",
    "Fire Service": "+2340000000000",
    "NEMA": "+2340000000000",
    "Police": "+2340000000000",
    "NSCDC": "+2340000000000"
}

def send_alert(incident, agency, desc, lat, lon):
    to_number = AGENCY_PHONES.get(agency)

    message = f"""🚨 RescueNet Nigeria 🇳🇬
Incident: {incident}
Agency: {agency}
Location: {lat}, {lon}

Details:
{desc}
"""

    encoded = urllib.parse.quote(message)

    return {
        "whatsapp": f"https://wa.me/{to_number.replace('+','')}?text={encoded}",
        "call": f"tel:{to_number}"
    }

# -----------------------------
# SESSION STATE
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------
# AUTH UI
# -----------------------------
if not st.session_state.user:

    menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])

    if menu == "Signup":
        st.subheader("Create Account")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Sign Up"):
            create_user(user, pwd)
            st.success("Account created! Login now")

    elif menu == "Login":
        st.subheader("Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            result = login_user(user, pwd)

            if result:
                st.session_state.user = result
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

# -----------------------------
# MAIN APP
# -----------------------------
else:

    username = st.session_state.user[1]
    role = st.session_state.user[3]

    st.sidebar.write(f"👤 {username} ({role})")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    menu = st.sidebar.selectbox("Menu", ["Report Incident", "Dashboard"])

    if menu == "Report Incident":

        st.subheader("📍 Report Emergency")

        incident = st.selectbox("Select Incident", list(AGENCY_MAP.keys()))
        agency = AGENCY_MAP[incident]

        desc = st.text_area("Describe incident")

        lat = st.number_input("Latitude", value=9.0820)
        lon = st.number_input("Longitude", value=8.6753)

        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

        if st.button("Submit Report"):

            c.execute("""
            INSERT INTO reports (incident, agency, description, lat, lon, user, time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (incident, agency, desc, lat, lon, username,
                  datetime.now().strftime("%Y-%m-%d %H:%M")))

            conn.commit()

            links = send_alert(incident, agency, desc, lat, lon)

            st.success("Report submitted!")

            st.markdown(f"[📲 WhatsApp Alert]({links['whatsapp']})")
            st.markdown(f"[📞 Call Agency]({links['call']})")

    elif menu == "Dashboard":

        st.subheader("📊 Dashboard")

        if role == "admin":
            df = pd.read_sql("SELECT * FROM reports", conn)
        else:
            df = pd.read_sql(f"SELECT * FROM reports WHERE user='{username}'", conn)

        st.dataframe(df)

        if not df.empty:
            st.map(df.rename(columns={"lat": "lat", "lon": "lon"}))
