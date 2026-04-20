import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
import random

# -----------------------------
# DATABASE
# -----------------------------
conn = sqlite3.connect("rescuenet.db", check_same_thread=False)
c = conn.cursor()

# USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    verified INTEGER DEFAULT 1
)
""")

# REPORTS
c.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident TEXT,
    agency TEXT,
    description TEXT,
    lat REAL,
    lon REAL,
    user TEXT,
    time TEXT
)
""")

# OTP TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS otp_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT,
    code TEXT,
    expires TEXT
)
""")

conn.commit()

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="RescueNet Nigeria 🇳🇬", layout="wide")
st.title("🚨 RescueNet Nigeria 🇳🇬")

# -----------------------------
# HELPERS
# -----------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    try:
        c.execute(
            "INSERT INTO users (username, password, role, verified) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), "user", 1)
        )
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return c.fetchone()

# -----------------------------
# OTP SYSTEM (SMART)
# -----------------------------
def send_otp(phone):
    code = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)

    c.execute(
        "INSERT INTO otp_codes (phone, code, expires) VALUES (?, ?, ?)",
        (phone, code, expiry.strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()

    try:
        import requests
        api_key = st.secrets.get("TERMI_API_KEY", "")

        if api_key:
            url = "https://api.ng.termii.com/api/sms/send"

            payload = {
                "to": phone,
                "from": "RescueNet",
                "sms": f"Your OTP is {code}",
                "type": "plain",
                "api_key": api_key
            }

            requests.post(url, json=payload)
            st.success("📩 OTP sent via SMS")
        else:
            raise Exception("No API key")

    except:
        st.warning("⚠️ SMS failed — use OTP below")
        st.code(code)

    return True

def verify_otp(phone, code):
    c.execute(
        "SELECT code, expires FROM otp_codes WHERE phone=? ORDER BY id DESC LIMIT 1",
        (phone,)
    )
    result = c.fetchone()

    if result:
        db_code, expires = result

        if datetime.now() > datetime.strptime(expires, "%Y-%m-%d %H:%M"):
            return False

        return db_code == code

    return False

# -----------------------------
# AGENCY ROUTING
# -----------------------------
def route_agency(incident):
    mapping = {
        "Road Accident": "FRSC",
        "Fire": "Fire Service",
        "Flood": "NSCDC",
        "Kidnapping": "Police",
        "Vandalism": "NSCDC"
    }
    return mapping.get(incident, "Police")

# -----------------------------
# ALERT SYSTEM
# -----------------------------
def send_alert(agency, message):
    try:
        import requests
        api_key = st.secrets.get("TERMI_API_KEY", "")

        contacts = {
            "Police": "+2348011111111",
            "FRSC": "+2348022222222",
            "NSCDC": "+2348033333333",
            "Fire Service": "+2348044444444"
        }

        phone = contacts.get(agency)

        if api_key and phone:
            url = "https://api.ng.termii.com/api/sms/send"

            payload = {
                "to": phone,
                "from": "RescueNet",
                "sms": message,
                "type": "plain",
                "api_key": api_key
            }

            requests.post(url, json=payload)
            return "SMS sent"
        else:
            st.info(f"🚨 {agency}: {message}")
            return "Displayed (no SMS)"

    except:
        st.warning("⚠️ Alert fallback")
        st.info(f"🚨 {agency}: {message}")
        return "Fallback used"

# -----------------------------
# SESSION
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------
# AUTH
# -----------------------------
if not st.session_state.user:

    menu = st.sidebar.selectbox("Menu", ["Login", "Signup"])

    # SIGNUP
    if menu == "Signup":
        st.subheader("Create Account")

        user = st.text_input("Username")
        phone = st.text_input("Phone (+234...)")
        pwd = st.text_input("Password", type="password")

        if st.button("Send OTP"):
            if phone:
                send_otp(phone)
                st.session_state.phone = phone
            else:
                st.warning("Enter phone")

        otp = st.text_input("Enter OTP")

        if st.button("Verify & Create Account"):
            if verify_otp(phone, otp):
                if create_user(user, pwd):
                    st.success("🎉 Account created successfully!")
                else:
                    st.error("Username exists")
            else:
                st.error("Invalid or expired OTP")

    # LOGIN
    elif menu == "Login":
        st.subheader("Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            result = login_user(user, pwd)

            if result:
                st.session_state.user = result
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

# -----------------------------
# MAIN APP
# -----------------------------
else:

    username = st.session_state.user[1]

    st.sidebar.write(f"👤 {username}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    menu = st.sidebar.selectbox("Menu", ["Report Incident", "Dashboard"])

    # REPORT
    if menu == "Report Incident":
        st.subheader("📍 Report Emergency")

        incident = st.selectbox("Incident", [
            "Road Accident", "Fire", "Flood",
            "Kidnapping", "Vandalism"
        ])

        desc = st.text_area("Description")
        lat = st.number_input("Latitude", value=9.0820)
        lon = st.number_input("Longitude", value=8.6753)

        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

        if st.button("Submit Report"):
            if desc:
                agency = route_agency(incident)

                c.execute("""
                    INSERT INTO reports 
                    (incident, agency, description, lat, lon, user, time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident,
                    agency,
                    desc,
                    lat,
                    lon,
                    username,
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ))
                conn.commit()

                message = f"{incident} at ({lat},{lon}) by {username}"
                status = send_alert(agency, message)

                st.success(f"✅ Sent to {agency}")
                st.info(f"Alert: {status}")
            else:
                st.warning("Enter description")

    # DASHBOARD
    elif menu == "Dashboard":
        df = pd.read_sql("SELECT * FROM reports", conn)
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.map(df)
