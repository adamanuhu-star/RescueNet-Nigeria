import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import sqlite3
import secrets

# -----------------------------
# DATABASE
# -----------------------------
conn = sqlite3.connect("rescuenet.db", check_same_thread=False)
c = conn.cursor()

# USERS TABLE
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# Ensure verified column exists
try:
    c.execute("ALTER TABLE users ADD COLUMN verified INTEGER DEFAULT 0")
    conn.commit()
except:
    pass

# REPORTS TABLE
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

# RESET TOKENS
c.execute("""
CREATE TABLE IF NOT EXISTS reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    token TEXT,
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

def create_user(username, password, role="user"):
    try:
        c.execute(
            "INSERT INTO users (username, password, role, verified) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), role, 0)
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

def create_reset_token(username):
    token = secrets.token_urlsafe(16)
    expiry = datetime.now() + timedelta(minutes=15)

    c.execute(
        "INSERT INTO reset_tokens (username, token, expires) VALUES (?, ?, ?)",
        (username, token, expiry.strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    return token

def verify_token(token):
    c.execute("SELECT username, expires FROM reset_tokens WHERE token=?", (token,))
    result = c.fetchone()

    if result:
        username, expires = result
        if datetime.now() < datetime.strptime(expires, "%Y-%m-%d %H:%M"):
            return username
    return None

def update_password(username, new_password):
    c.execute(
        "UPDATE users SET password=? WHERE username=?",
        (hash_password(new_password), username)
    )
    conn.commit()

# -----------------------------
# SESSION
# -----------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------
# RESET PASSWORD LINK HANDLER
# -----------------------------
query_params = st.query_params

if "reset_token" in query_params:
    token = query_params["reset_token"]
    username = verify_token(token)

    if username:
        st.subheader("🔑 Set New Password")
        new_pwd = st.text_input("New Password", type="password")

        if st.button("Update Password"):
            update_password(username, new_pwd)
            st.success("✅ Password updated! Go to login")
    else:
        st.error("❌ Invalid or expired token")

    st.stop()

# -----------------------------
# AUTH SECTION
# -----------------------------
if not st.session_state.user:

    menu = st.sidebar.selectbox("Menu", ["Login", "Signup", "Forgot Password"])

    # ---------------- SIGNUP ----------------
    if menu == "Signup":
        st.subheader("Create Account")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Sign Up"):
            if create_user(user, pwd):
                st.success("✅ Account created! Please login to verify")
            else:
                st.error("Username already exists")

    # ---------------- LOGIN ----------------
    elif menu == "Login":
        st.subheader("Login")

        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")

        if st.button("Login"):
            result = login_user(user, pwd)

            if result:
                verified = result[4] if len(result) > 4 else 1

                if verified == 0:
                    st.warning("⚠️ Account not verified")

                    if st.button("Verify Account"):
                        c.execute(
                            "UPDATE users SET verified=1 WHERE username=?",
                            (user,)
                        )
                        conn.commit()
                        st.success("✅ Account verified! Now login again")

                else:
                    st.session_state.user = result
                    st.success("✅ Login successful")
                    st.rerun()
            else:
                st.error("Invalid credentials")

    # ---------------- FORGOT PASSWORD ----------------
    elif menu == "Forgot Password":
        st.subheader("🔐 Reset Password")

        user = st.text_input("Enter your username")

        if st.button("Generate Reset Link"):
            token = create_reset_token(user)
            reset_link = f"?reset_token={token}"

            st.success("✅ Copy this link (valid 15 mins)")
            st.code(reset_link)

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

    # -------- REPORT INCIDENT --------
    if menu == "Report Incident":

        st.subheader("📍 Report Emergency")

        incident = st.selectbox("Incident", [
            "Road Accident", "Fire Outbreak", "Flood",
            "Kidnapping", "Vandalism"
        ])

        desc = st.text_area("Describe incident")

        lat = st.number_input("Latitude", value=9.0820)
        lon = st.number_input("Longitude", value=8.6753)

        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

        if st.button("Submit Report"):
            if desc:
                c.execute("""
                    INSERT INTO reports 
                    (incident, agency, description, lat, lon, user, time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident, incident, desc, lat, lon,
                    username,
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ))

                conn.commit()
                st.success("✅ Report submitted")
            else:
                st.warning("Please describe the incident")

    # -------- DASHBOARD --------
    elif menu == "Dashboard":

        if role == "admin":

            tab1, tab2 = st.tabs(["Reports", "Users"])

            # REPORTS
            with tab1:
                df = pd.read_sql("SELECT * FROM reports", conn)
                st.dataframe(df, use_container_width=True)

                if not df.empty:
                    st.map(df)

                rid = st.number_input("Report ID to delete", step=1)

                if st.button("Delete Report"):
                    c.execute("DELETE FROM reports WHERE id=?", (rid,))
                    conn.commit()
                    st.success("Deleted")
                    st.rerun()

            # USERS
            with tab2:
                users = pd.read_sql("SELECT id, username, role FROM users", conn)
                st.dataframe(users, use_container_width=True)

                uid = st.number_input("User ID to delete", step=1)

                if uid != st.session_state.user[0]:
                    if st.button("Delete User"):
                        c.execute("DELETE FROM users WHERE id=?", (uid,))
                        conn.commit()
                        st.success("User deleted")
                        st.rerun()
                else:
                    st.warning("You cannot delete yourself")

        else:
            df = pd.read_sql(
                f"SELECT * FROM reports WHERE user='{username}'",
                conn
            )
            st.dataframe(df, use_container_width=True)

            if not df.empty:
                st.map(df)
