from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from scipy.interpolate import Rbf
import openrouteservice
from shapely.geometry import LineString, Point
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Data Loading and Model Classes ---

def load_and_prepare_data(air_quality_path):
    print("Loading dataset...")
    df = pd.read_csv(air_quality_path)
    df['local_time'] = pd.to_datetime(df['local_time'], dayfirst=True)
    print("Finding the latest reading for each station...")
    latest_df = df.sort_values('local_time').drop_duplicates('station_name', keep='last')
    latest_df.rename(columns={'PM2_5': 'PM2.5_corrected'}, inplace=True)
    latest_df.dropna(subset=['PM2.5_corrected', 'latitude', 'longitude'], inplace=True)
    print("Data preparation complete.")
    return latest_df

class PollutionModel:
    def __init__(self, sensor_data):
        if sensor_data.empty:
            raise ValueError("Sensor data cannot be empty.")
        self.points = sensor_data[['latitude', 'longitude']].values
        self.values = sensor_data['PM2.5_corrected'].values
        self.interpolator = Rbf(self.points[:, 0], self.points[:, 1], self.values, function='inverse_multiquadric', epsilon=0.1)
        print("Pollution prediction model trained.")
    def predict(self, lat, lon):
        return self.interpolator(lat, lon)

# --- Helper function ---

def sample_route(route_geometry, interval_meters=100):
    line = LineString(route_geometry)
    sampled_points = []
    num_samples = int(line.length / 0.001)
    for i in range(num_samples + 1):
        point = line.interpolate(float(i) / num_samples, normalized=True)
        sampled_points.append((point.y, point.x))
    return sampled_points

# --- Flask App Setup ---
app = Flask(__name__)

# --- Initialization ---
print("Initializing model...")
AIR_QUALITY_FILE = "Air View+ Clear Skies Hourly Dataset.csv"
sensor_data = load_and_prepare_data(AIR_QUALITY_FILE)
sensor_data.drop_duplicates(subset=['latitude', 'longitude'], keep='first', inplace=True)
pollution_model = PollutionModel(sensor_data)
print("Model initialized. Server is ready.")


# --- API Endpoints ---

@app.route('/')
def index():
    return "Low-Pollution Route Optimizer API is running!"

@app.route('/predict', methods=['GET'])
def predict_pollution():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify({'error': 'Please provide both lat and lon parameters.'}), 400
    predicted_pm25 = pollution_model.predict(lat, lon)
    return jsonify({'latitude': lat, 'longitude': lon, 'predicted_pm2.5': round(predicted_pm25, 2)})

@app.route('/routes', methods=['GET'])
def get_routes():
    ors_api_key = os.getenv('ORS_API_KEY')
    if not ors_api_key:
        return jsonify({'error': 'API key for OpenRouteService not found in .env file.'}), 500

    start_lon = request.args.get('start_lon', type=float)
    start_lat = request.args.get('start_lat', type=float)
    end_lon = request.args.get('end_lon', type=float)
    end_lat = request.args.get('end_lat', type=float)

    if not all([start_lon, start_lat, end_lon, end_lat]):
        return jsonify({'error': 'Missing start/end coordinates.'}), 400

    client = openrouteservice.Client(key=ors_api_key)

    try:
        # --- FIX is here: Changed 'alternatives=True' to the new format ---
        routes_response = client.directions(
            coordinates=[[start_lon, start_lat], [end_lon, end_lat]],
            profile='driving-car',
            format='geojson',
            alternative_routes={'target_count': 3} # Requesting up to 3 alternative routes
        )
    except Exception as e:
        return jsonify({'error': f'Error fetching routes from ORS: {str(e)}'}), 500

    scored_routes = []
    for i, route in enumerate(routes_response['features']):
        geometry = route['geometry']['coordinates']
        sampled_points = sample_route(geometry)
        pollution_scores = [pollution_model.predict(lat, lon) for lat, lon in sampled_points]
        avg_pollution = np.mean(pollution_scores) if pollution_scores else 0

        scored_routes.append({
            'id': i,
            'distance_km': round(route['properties']['summary']['distance'] / 1000, 2),
            'duration_min': round(route['properties']['summary']['duration'] / 60, 2),
            'avg_pm2.5': round(avg_pollution, 2),
            'geometry': geometry
        })
    
    if not scored_routes:
        return jsonify({'error': 'No routes found between the specified points.'}), 404
        
    fastest_route = min(scored_routes, key=lambda x: x['duration_min'])
    cleanest_route = min(scored_routes, key=lambda x: x['avg_pm2.5'])

    return jsonify({
        'fastest_route': fastest_route,
        'cleanest_route': cleanest_route,
        'all_alternatives': scored_routes
    })


if __name__ == '__main__':
    app.run(debug=True)