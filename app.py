import streamlit as st

st.set_page_config(page_title="RescueNet Nigeria", layout="wide")

st.title("🚨 RescueNet Nigeria 🇳🇬")
st.write("AI-powered Emergency Reporting System")

incident = st.selectbox("Select Incident Type", [
    "Road Accident",
    "Fire Outbreak",
    "Flood",
    "Kidnapping",
    "Vandalism"
])

location = st.text_input("Enter Location")

description = st.text_area("Describe the incident")

uploaded_file = st.file_uploader("Upload Image/Video Evidence")

if st.button("Report Incident"):
    st.success("✅ Incident reported successfully!")
