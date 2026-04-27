import streamlit as st
import sqlite3
import pandas as pd
import pydeck as pdk
import math
import time
import json
import streamlit.components.v1 as components

# -------------------------
# DATABASE
# -------------------------
conn = sqlite3.connect("rescue.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident TEXT,
    lat REAL,
    lon REAL,
    status TEXT,
    priority INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    lat REAL,
    lon REAL,
    status TEXT,
    report_id INTEGER
)
""")

conn.commit()

# -------------------------
# FUNCTIONS
# -------------------------
def get_priority(incident):
    return {
        "Kidnapping": 5,
        "Fire Outbreak": 5,
        "Road Accident": 4,
        "Flood": 3,
        "Critical National asset Vandalism": 4
    }.get(incident, 2)

def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def move(current, target, step=0.01):
    if current < target:
        current += step
    elif current > target:
        current -= step
    return current

def calculate_eta(lat1, lon1, lat2, lon2):
    return round(distance(lat1, lon1, lat2, lon2) / 0.02, 2)

def auto_assign(report_id, lat, lon):
    agents = pd.read_sql("SELECT * FROM agents WHERE status='Available'", conn)

    if agents.empty:
        return []

    agents["dist"] = agents.apply(
        lambda x: distance(lat, lon, x["lat"], x["lon"]), axis=1
    )

    nearest = agents.sort_values("dist").head(2)

    assigned = []

    for _, a in nearest.iterrows():
        c.execute("""
            UPDATE agents SET status='Responding', report_id=?
            WHERE id=?
        """, (report_id, a["id"]))
        assigned.append(a["name"])

    conn.commit()
    return assigned

# -------------------------
# GOOGLE MAP ROUTE
# -------------------------
def google_route(lat1, lon1, lat2, lon2, key):
    return f"""
    <iframe
        width="100%"
        height="400"
        style="border:0"
        loading="lazy"
        allowfullscreen
        src="https://www.google.com/maps/embed/v1/directions?key={key}
        &origin={lat1},{lon1}
        &destination={lat2},{lon2}
        &mode=driving&departure_time=now">
    </iframe>
    """

# -------------------------
# UI CONFIG
# -------------------------
st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

st.title("🚨 RescueNet Nigeria 🇳🇬")
st.markdown("### Smart Emergency & Dispatch System")

menu = st.sidebar.selectbox("Menu", ["Report Incident", "Add Agent", "Dashboard"])

api_key = st.sidebar.text_input("Google Maps API Key (optional)", type="password")

# -------------------------
# REPORT INCIDENT
# -------------------------
if menu == "Report Incident":

    st.subheader("📍 Location Detection")

    if st.button("📡 Get My Location"):
        components.html(
            """
            <script>
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const coords = {
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude
                    };
                    window.parent.postMessage(JSON.stringify(coords), "*");
                },
                (err) => {
                    window.parent.postMessage(JSON.stringify({error: err.message}), "*");
                }
            );
            </script>
            """,
            height=0,
        )

    location_data = st.text_input("GPS Data", key="gps")

    components.html(
        """
        <script>
        window.addEventListener("message", (event) => {
            const input = window.parent.document.querySelector('input[aria-label="GPS Data"]');
            if (input) {
                input.value = event.data;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        </script>
        """,
        height=0,
    )

    lat, lon = None, None

    try:
        if location_data:
            coords = json.loads(location_data)
            lat = coords.get("lat")
            lon = coords.get("lon")
    except:
        pass

    if lat and lon:
        st.success(f"📍 Location: {lat}, {lon}")
    else:
        st.warning("⚠ GPS not detected — enter manually")
        lat = st.number_input("Latitude", value=9.0820)
        lon = st.number_input("Longitude", value=8.6753)

    incident = st.selectbox("Incident Type", [
        "Road Accident",
        "Fire Outbreak",
        "Flood",
        "Kidnapping",
        "Critical National asset Vandalism"
    ])

    if st.button("🚨 Submit Report"):

        if lat is None or lon is None:
            st.error("❌ Location required")
        else:
            priority = get_priority(incident)

            c.execute("""
                INSERT INTO reports (incident, lat, lon, status, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (incident, lat, lon, "Pending", priority))

            report_id = c.lastrowid
            conn.commit()

            assigned = auto_assign(report_id, lat, lon)

            st.success("✅ Incident Reported")

            if assigned:
                st.success(f"🚓 Assigned: {', '.join(assigned)}")
            else:
                st.warning("⚠ No available agents")

# -------------------------
# ADD AGENT
# -------------------------
elif menu == "Add Agent":

    st.subheader("Add Agent")

    name = st.text_input("Agent Name")
    lat = st.number_input("Latitude", value=9.0820)
    lon = st.number_input("Longitude", value=8.6753)

    if st.button("Add Agent"):
        c.execute("""
            INSERT INTO agents (name, lat, lon, status, report_id)
            VALUES (?, ?, ?, 'Available', NULL)
        """, (name, lat, lon))
        conn.commit()
        st.success("✅ Agent Added")

# -------------------------
# DASHBOARD
# -------------------------
elif menu == "Dashboard":

    st.subheader("📡 Live Dispatch Dashboard")

    placeholder = st.empty()

    for _ in range(30):

        reports = pd.read_sql("SELECT * FROM reports", conn)
        agents = pd.read_sql("SELECT * FROM agents", conn)

        points = []
        lines = []

        # MOVE AGENTS
        for _, a in agents.iterrows():

            if a["report_id"]:
                r = reports[reports["id"] == a["report_id"]]

                if not r.empty:
                    target_lat = r.iloc[0]["lat"]
                    target_lon = r.iloc[0]["lon"]

                    new_lat = move(a["lat"], target_lat)
                    new_lon = move(a["lon"], target_lon)

                    c.execute("""
                        UPDATE agents SET lat=?, lon=? WHERE id=?
                    """, (new_lat, new_lon, a["id"]))

                    eta = calculate_eta(new_lat, new_lon, target_lat, target_lon)

                    points.append({
                        "lat": new_lat,
                        "lon": new_lon,
                        "color": [0, 0, 255],
                        "label": f"{a['name']} (ETA: {eta}m)"
                    })

                    lines.append({
                        "start": [new_lon, new_lat],
                        "end": [target_lon, target_lat]
                    })

        conn.commit()

        # INCIDENT POINTS
        for _, r in reports.iterrows():

            color = [255, 0, 0]
            if r["status"] == "Resolved":
                color = [0, 200, 0]

            points.append({
                "lat": r["lat"],
                "lon": r["lon"],
                "color": color,
                "label": f"{r['incident']} (P{r['priority']})"
            })

        # MAP
        df = pd.DataFrame(points)

        scatter = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=200,
            pickable=True,
        )

        line_layer = pdk.Layer(
            "LineLayer",
            data=lines,
            get_source_position="start",
            get_target_position="end",
            get_color=[0, 0, 0],
            get_width=2,
        )

        view = pdk.ViewState(latitude=9.0820, longitude=8.6753, zoom=6)

        with placeholder.container():
            st.pydeck_chart(pdk.Deck(
                layers=[scatter, line_layer],
                initial_view_state=view,
                tooltip={"text": "{label}"}
            ))

        # GOOGLE MAP ROUTE (REAL)
        if api_key and len(agents) > 0 and len(reports) > 0:
            a = agents.iloc[0]
            r = reports.iloc[0]

            st.markdown("### 🗺 Real Route (Google Maps)")
            route_html = google_route(
                a["lat"], a["lon"],
                r["lat"], r["lon"],
                api_key
            )
            components.html(route_html, height=400)

        time.sleep(2)
