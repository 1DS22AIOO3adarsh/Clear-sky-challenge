

# 🍃 Low-Pollution Route Optimizer

A full-stack web application that helps users find the cleanest, least polluted route for their journey. This app provides a side-by-side comparison of the "Fastest Route" and the "Cleanest Route" by using a predictive pollution model based on real-world sensor data.

  
<img width="2048" height="2048" alt="FLOW" src="https://github.com/user-attachments/assets/b8d4236f-19c2-434e-b642-bc39dd9f691f" />


## ✨ Key Features

  * **Predictive Pollution Modeling**: A custom engine uses interpolation to estimate PM₂.₅ levels anywhere on the map, even between sensors.
  * **Fastest vs. Cleanest Route Comparison**: The core feature displays two routes side-by-side: one optimized for time, the other for minimum pollution exposure.
  * **Interactive Map Visualization**: The frontend provides a map-based view of both route options, color-coded for easy interpretation.
  * **Guided Location Selection**: Users choose from a dropdown of valid locations, ensuring all route requests are within the model's trained geographic area.

## 🛠️ Tech Stack

  * **Backend**: Flask, Pandas, NumPy, SciPy
  * **Frontend**: Streamlit, Folium
  * **APIs & Data**: OpenRouteService, Air Quality Open Data

## 🗺️ Architecture Overview

The application uses a client-server architecture. The Streamlit frontend handles user interaction, while the Flask backend performs the heavy lifting of route calculation and pollution scoring.

  
*\<-- Replace with a link to your architecture diagram --\>*

## 🚀 Getting Started

Follow these instructions to get the project running on your local machine.

### Prerequisites

  * Python 3.8+
  * pip package manager

### Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/low-pollution-route-optimizer.git
    cd low-pollution-route-optimizer
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies from `requirements.txt`:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Add Required Files (Crucial Step):**
    This repository does not include data files or API keys. You must provide them yourself.

      * **Create an API Key File**:
        Create a file named `.env` in the root of the project directory and add your OpenRouteService API key in the following format:

        ```
        ORS_API_KEY="your_actual_api_key_goes_here"
        ```

      * **Add the Data File**:
        Download the necessary air quality dataset and place it in the root of the project directory. The application expects this file to be named:
        `Air View+ Clear Skies Hourly Dataset.csv`

### How to Run the Application

You need to run the backend and frontend servers simultaneously in two separate terminals. Make sure your virtual environment is activated in both.

1.  **Run the Backend Server (Terminal 1):**

    ```bash
    python app.py
    ```

    You should see output indicating that the Flask server is running on `http://127.0.0.1:5000`.

2.  **Run the Frontend App (Terminal 2):**

    ```bash
    streamlit run frontend.py
    ```

    This will automatically open a new tab in your web browser with the application's UI.

You can now use the application to select locations and find the cleanest routes\!

