import pandas as pd
import numpy as np
from scipy.interpolate import Rbf

# --- 1. DATA INGESTION & PREPARATION ---

def load_and_prepare_data(air_quality_path):
    """
    Loads air quality data, handles the day-first date format, and returns
    the latest reading for each unique station.

    Args:
        air_quality_path (str): The file path for the hourly air quality CSV.

    Returns:
        pandas.DataFrame: A cleaned DataFrame with the latest AQI reading per station.
    """
    print("Loading dataset...")
    df = pd.read_csv(air_quality_path)

    # Use dayfirst=True to parse dates like "13/11/2024"
    df['local_time'] = pd.to_datetime(df['local_time'], dayfirst=True)

    # Get the most recent reading for each station
    print("Finding the latest reading for each station...")
    latest_df = df.sort_values('local_time').drop_duplicates('station_name', keep='last')

    # Rename the PM2.5 column for consistency
    latest_df.rename(columns={'PM2_5': 'PM2.5_corrected'}, inplace=True)
    
    # Remove any rows that are missing crucial data for the model
    latest_df.dropna(subset=['PM2.5_corrected', 'latitude', 'longitude'], inplace=True)
    
    print("Data preparation complete.")
    return latest_df

# --- 2. POLLUTION ESTIMATION MODEL (Inverse Distance Weighting) ---

class PollutionModel:
    """
    A model to predict PM2.5 values at any geographic coordinate using
    Inverse Distance Weighting (IDW) via Radial Basis Function interpolation.
    """
    def __init__(self, sensor_data):
        if sensor_data.empty:
            raise ValueError("Sensor data cannot be empty.")
            
        self.points = sensor_data[['latitude', 'longitude']].values
        self.values = sensor_data['PM2.5_corrected'].values
        
        self.interpolator = Rbf(self.points[:, 0], self.points[:, 1], self.values, function='inverse_multiquadric', epsilon=0.1)
        print("Pollution prediction model trained.")

    def predict(self, lat, lon):
        return self.interpolator(lat, lon)

# --- 3. EXECUTION & EXAMPLE USAGE ---

if __name__ == '__main__':
    AIR_QUALITY_FILE = "Air View+ Clear Skies Hourly Dataset.csv"

    try:
        # Step 1: Prepare the data
        sensor_data_df = load_and_prepare_data(AIR_QUALITY_FILE)

        # --- FIX for 'Matrix is singular' error ---
        # Before training, remove any stations that have the exact same coordinates.
        print("Removing duplicate sensor locations...")
        sensor_data_df.drop_duplicates(subset=['latitude', 'longitude'], keep='first', inplace=True)

        print("\nLatest Sensor Data (Sample):")
        print(sensor_data_df[['station_name', 'local_time', 'PM2.5_corrected', 'latitude', 'longitude']].head())

        # Step 2: Initialize the pollution model
        pollution_model = PollutionModel(sensor_data_df)

        # Step 3: Example Prediction
        sample_lat, sample_lon = 28.4595, 77.0266
        predicted_pm25 = pollution_model.predict(sample_lat, sample_lon)
        
        print(f"\n--- Example Prediction ---")
        print(f"Predicted PM2.5 at ({sample_lat}, {sample_lon}): {predicted_pm25:.2f}")

    except FileNotFoundError as e:
        print(f"Error: {e}. Please make sure the CSV file is in the correct directory.")
    except Exception as e:
        # Changed the exception message to be more general
        print(f"An error occurred: {e}")