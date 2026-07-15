import geocoder
from geopy.distance import geodesic
import random
import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Ambulance Dashboard", layout="wide")
st.title("🚑 Ambulance Tracking Dashboard")

# Step 1: Get accident location (only once per session)
if "accident_location" not in st.session_state:
    g = geocoder.ip('me')
    st.session_state.accident_location = g.latlng

accident_location = st.session_state.accident_location
if not accident_location or accident_location == [None, None]:
    st.error("Could not detect accident location.")
    st.stop()

# Step 2: Simulate ambulances (only once per session)
def simulate_ambulances(center, count=5, radius_km=5):
    ambulances = []
    for i in range(count):
        delta_lat = random.uniform(-radius_km / 110, radius_km / 110)
        lon_divisor = 111 * abs(center[0]) if abs(center[0]) > 0.01 else 1
        delta_lon = random.uniform(-radius_km / lon_divisor, radius_km / lon_divisor)
        amb_lat = center[0] + delta_lat
        amb_lon = center[1] + delta_lon
        amb_location = (amb_lat, amb_lon)
        distance = geodesic(center, amb_location).km
        ambulances.append({
            "id": f"A{i+1}",
            "location": amb_location,
            "distance": distance
        })
    return ambulances

if "ambulances" not in st.session_state:
    st.session_state.ambulances = simulate_ambulances(st.session_state.accident_location)

ambulances = st.session_state.ambulances
for amb in ambulances:
    amb["distance"] = geodesic(accident_location, amb["location"]).km

nearest_ambulance = min(ambulances, key=lambda amb: amb["distance"])

# Step 3: Show accident location
st.subheader("📍 Accident Location")
st.write(f"**Latitude:** {accident_location[0]:.6f} &nbsp;&nbsp; **Longitude:** {accident_location[1]:.6f}")

# Step 4: List all ambulances and distances
st.subheader("🚑 Available Ambulances")
st.table([
    {"Ambulance": amb["id"], "Latitude": f"{amb['location'][0]:.6f}", "Longitude": f"{amb['location'][1]:.6f}", "Distance (km)": f"{amb['distance']:.2f}"}
    for amb in ambulances
])

# Step 5: Show nearest ambulance and its distance
st.subheader("🏥 Nearest Ambulance")
st.write(f"**{nearest_ambulance['id']}** is the nearest ambulance at a distance of **{nearest_ambulance['distance']:.2f} km**.")

# Step 6: Map with all ambulances (names and distances always visible)
m = folium.Map(location=accident_location, zoom_start=13)

# Accident location marker
folium.Marker(
    location=accident_location,
    popup="Accident Location",
    icon=folium.Icon(color='red')
).add_to(m)

# Ambulance markers with always-visible labels
for amb in ambulances:
    distance_label = f"{amb['id']} - {amb['distance']:.2f} km"
    icon_color = 'blue' if amb['id'] == nearest_ambulance['id'] else 'green'
    # Ambulance icon
    folium.Marker(
        location=amb["location"],
        icon=folium.Icon(color=icon_color, icon='ambulance', prefix='fa')
    ).add_to(m)
    # Always-visible label
    folium.map.Marker(
        amb["location"],
        icon=folium.DivIcon(html=f"""<div style="font-size:12px; color: black; text-align:center;"><b>{distance_label}</b></div>""")
    ).add_to(m)
    # Path from ambulance to accident
    folium.PolyLine([amb["location"], accident_location], color="gray", weight=2, opacity=0.5).add_to(m)

# Highlight path from nearest ambulance in blue with distance as popup
folium.PolyLine(
    [nearest_ambulance["location"], accident_location],
    color="blue",
    weight=5,
    popup=f"Distance: {nearest_ambulance['distance']:.2f} km"
).add_to(m)

# Step 7: Show map in dashboard
st.subheader("🗺️ Map View")
st_folium(m, width=900, height=600)

# Optional: Button to reset ambulance locations
if st.button("Reset Ambulance Locations"):
    st.session_state.ambulances = simulate_ambulances(st.session_state.accident_location)
    st.experimental_rerun()