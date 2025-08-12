import streamlit as st
import folium
import requests
import pandas as pd
from streamlit_folium import st_folium

# --- Page Configuration ---
st.set_page_config(
    page_title="Low-Pollution Route Optimizer",
    page_icon="🍃",
    layout="wide"
)

st.title("🍃 Low-Pollution Route Optimizer")
st.markdown("Find the fastest or the cleanest route for your journey within the Gurugram region.")

# --- Data Loading and Caching ---
@st.cache_data
def load_location_data():
    """Loads and caches the location data to populate the dropdowns."""
    try:
        df = pd.read_csv("Air View+ Clear Skies Hourly Dataset.csv")
        # Get unique station names and their coordinates
        locations = df[['station_name', 'latitude', 'longitude']].drop_duplicates('station_name').reset_index(drop=True)
        return locations
    except FileNotFoundError:
        st.error("Air View+ Clear Skies Hourly Dataset.csv not found. Please make sure it's in the same directory.")
        return pd.DataFrame()

locations_df = load_location_data()
location_names = locations_df['station_name'].tolist()

# --- Initialize session state ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None

# --- Helper Function ---
def get_routes_from_api(start_lat, start_lon, end_lat, end_lon):
    """Calls the backend API to get route data."""
    api_url = f"http://127.0.0.1:5000/routes?start_lat={start_lat}&start_lon={start_lon}&end_lat={end_lat}&end_lon={end_lon}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the backend API: {e}")
        return None

# --- User Inputs ---
with st.sidebar:
    st.header("Select Your Journey")
    if not location_names:
        st.warning("No locations to display. Check data file.")
    else:
        # Use a dropdown menu (selectbox) instead of text input
        start_location_name = st.selectbox("Start Location", options=location_names, index=0)
        end_location_name = st.selectbox("End Location", options=location_names, index=10)

        if st.button("Find Routes", type="primary"):
            # Get coordinates for selected locations from the dataframe
            start_loc = locations_df[locations_df['station_name'] == start_location_name].iloc[0]
            end_loc = locations_df[locations_df['station_name'] == end_location_name].iloc[0]

            start_coords = (start_loc['latitude'], start_loc['longitude'])
            end_coords = (end_loc['latitude'], end_loc['longitude'])

            with st.spinner("Calculating cleanest routes..."):
                st.session_state.route_data = get_routes_from_api(
                    start_coords[0], start_coords[1],
                    end_coords[0], end_coords[1]
                )

# --- Map and Route Display ---
if st.session_state.route_data:
    route_data = st.session_state.route_data

    if 'fastest_route' in route_data:
        fastest_route = route_data['fastest_route']
        cleanest_route = route_data['cleanest_route']
        
        # Get start/end coordinates from the returned route data for accuracy
        start_lon, start_lat = fastest_route['geometry'][0]
        end_lon, end_lat = fastest_route['geometry'][-1]
        
        m = folium.Map(location=[start_lat, start_lon], zoom_start=12)
        
        # --- Smart Display Logic ---
        if fastest_route['id'] == cleanest_route['id']:
            # Display a single, unified result
            st.success("The Fastest Route is also the Cleanest available!")
            geom_swapped = [(point[1], point[0]) for point in fastest_route['geometry']]
            folium.PolyLine(locations=geom_swapped, color='purple', weight=6, opacity=0.9, tooltip='Optimal Route').add_to(m)
            
            st.header("Optimal Route Details")
            st.metric("Duration", f"{fastest_route['duration_min']} min")
            st.metric("Distance", f"{fastest_route['distance_km']} km")
            st.metric("Avg. PM₂.₅", f"{fastest_route['avg_pm2.5']} µg/m³")

        else:
            # Display the two-column comparison
            folium.PolyLine(locations=[(p[1], p[0]) for p in fastest_route['geometry']], color='blue', weight=5, opacity=0.8, tooltip='Fastest Route').add_to(m)
            folium.PolyLine(locations=[(p[1], p[0]) for p in cleanest_route['geometry']], color='green', weight=5, opacity=0.8, tooltip='Cleanest Route').add_to(m)
            
            st.header("Route Comparison")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🔵 Fastest Route")
                st.metric("Duration", f"{fastest_route['duration_min']} min")
                st.metric("Distance", f"{fastest_route['distance_km']} km")
                st.metric("Avg. PM₂.₅", f"{fastest_route['avg_pm2.5']} µg/m³")
            with col2:
                st.subheader("🟢 Cleanest Route")
                st.metric("Duration", f"{cleanest_route['duration_min']} min")
                st.metric("Distance", f"{cleanest_route['distance_km']} km")
                st.metric("Avg. PM₂.₅", f"{cleanest_route['avg_pm2.5']} µg/m³", delta=f"{round(cleanest_route['avg_pm2.5'] - fastest_route['avg_pm2.5'], 2)}", delta_color="inverse")

        # Add markers for start and end points
        folium.Marker([start_lat, start_lon], popup=f"Start", icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker([end_lat, end_lon], popup=f"End", icon=folium.Icon(color='red')).add_to(m)

        st_folium(m, width=1200, height=600)

    elif 'error' in route_data:
        st.error(f"Error from API: {route_data['error']}")
else:
    st.info("Please select your start and end locations and click 'Find Routes'.")