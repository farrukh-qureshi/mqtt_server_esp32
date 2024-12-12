import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
from collections import deque
import sqlite3
import os

# Page config
st.set_page_config(
    page_title="Soil Monitoring System",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
def init_db():
    conn = sqlite3.connect('soil_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS soil_readings
                 (timestamp TEXT PRIMARY KEY,
                  humidity REAL,
                  temperature REAL,
                  conductivity REAL,
                  ph REAL,
                  nitrogen REAL,
                  phosphorus REAL,
                  potassium REAL)''')
    conn.commit()
    return conn

# Initialize data storage
MAX_DATA_POINTS = 100
data_buffer = {
    'timestamp': deque(maxlen=MAX_DATA_POINTS),
    'humidity': deque(maxlen=MAX_DATA_POINTS),
    'temperature': deque(maxlen=MAX_DATA_POINTS),
    'conductivity': deque(maxlen=MAX_DATA_POINTS),
    'ph': deque(maxlen=MAX_DATA_POINTS),
    'nitrogen': deque(maxlen=MAX_DATA_POINTS),
    'phosphorus': deque(maxlen=MAX_DATA_POINTS),
    'potassium': deque(maxlen=MAX_DATA_POINTS)
}

# MQTT Settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "soil/data"
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "mqtt123"

# Initialize session state
if 'mqtt_connected' not in st.session_state:
    st.session_state['mqtt_connected'] = False

# Callback when connecting to the MQTT broker
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        st.session_state['mqtt_connected'] = True
        client.subscribe(MQTT_TOPIC)
    else:
        st.session_state['mqtt_connected'] = False

# Callback when receiving a message
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Store in database
        conn = init_db()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO soil_readings VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (current_time, 
                      payload.get('humidity', 0), 
                      payload.get('temperature', 0),
                      payload.get('conductivity', 0), 
                      payload.get('ph', 0), 
                      payload.get('nitrogen', 0),
                      payload.get('phosphorus', 0), 
                      payload.get('potassium', 0)))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Skip duplicate timestamps
        finally:
            conn.close()
            
    except Exception as e:
        print(f"Error processing message: {e}")

def get_historical_data(days=1):
    conn = init_db()
    query = f"""
    SELECT * FROM soil_readings 
    WHERE timestamp >= datetime('now', '-{days} days')
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def create_plots(df):
    if df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=4, cols=2,
        subplot_titles=('Humidity (%)', 'Temperature (°C)', 
                       'Conductivity (µS/cm)', 'pH',
                       'Nitrogen (mg/kg)', 'Phosphorus (mg/kg)',
                       'Potassium (mg/kg)', ''),
        vertical_spacing=0.1
    )
    
    # Add traces
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['humidity'], 
                            name='Humidity', line=dict(color='blue')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], 
                            name='Temperature', line=dict(color='red')), row=1, col=2)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['conductivity'], 
                            name='Conductivity', line=dict(color='green')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ph'], 
                            name='pH', line=dict(color='purple')), row=2, col=2)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['nitrogen'], 
                            name='Nitrogen', line=dict(color='orange')), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['phosphorus'], 
                            name='Phosphorus', line=dict(color='brown')), row=3, col=2)
    fig.add_trace(go.Scatter(x=df['timestamp'], y=df['potassium'], 
                            name='Potassium', line=dict(color='pink')), row=4, col=1)
    
    fig.update_layout(
        height=1200,
        showlegend=False,
        title_text="Soil Parameters Over Time",
        title_x=0.5
    )
    
    return fig

def main():
    # Initialize MQTT client
    client = mqtt.Client(client_id=f'streamlit_client_{time.time()}', protocol=mqtt.MQTTv5)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to MQTT broker
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        st.error(f"Failed to connect to MQTT broker: {e}")

    st.title("🌱 Soil Monitoring Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        days_to_show = st.slider("Days of data to display", 1, 30, 1)
        
        st.header("Alert Thresholds")
        temp_threshold = st.slider("Temperature Alert (°C)", 0, 50, 30)
        humidity_threshold = st.slider("Humidity Alert (%)", 0, 100, 80)
        ph_threshold_low = st.slider("pH Alert (Low)", 0.0, 14.0, 6.0)
        ph_threshold_high = st.slider("pH Alert (High)", 0.0, 14.0, 8.0)

    # Main content
    if st.session_state['mqtt_connected']:
        st.success("Connected to MQTT broker")
    else:
        st.error("Disconnected from MQTT broker")

    # Get data
    df = get_historical_data(days=days_to_show)

    # Display current metrics
    if not df.empty:
        latest = df.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperature", f"{latest['temperature']:.1f}°C")
        col2.metric("Humidity", f"{latest['humidity']:.1f}%")
        col3.metric("pH", f"{latest['ph']:.1f}")
        col4.metric("Conductivity", f"{latest['conductivity']:.0f}")

        # Display alerts
        if latest['temperature'] > temp_threshold:
            st.warning(f"⚠️ High Temperature Alert: {latest['temperature']:.1f}°C")
        if latest['humidity'] > humidity_threshold:
            st.warning(f"⚠️ High Humidity Alert: {latest['humidity']:.1f}%")
        if latest['ph'] < ph_threshold_low or latest['ph'] > ph_threshold_high:
            st.warning(f"⚠️ pH Out of Range Alert: {latest['ph']:.1f}")

    # Display plots
    st.plotly_chart(create_plots(df), use_container_width=True)

    # Data export section
    st.subheader("Data Export")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV File",
                data=csv,
                file_name=f'soil_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv'
            )
    
    with col2:
        conn = init_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM soil_readings")
        total_records = c.fetchone()[0]
        conn.close()
        st.info(f"Total records in database: {total_records}")

    # Add a refresh button
    if st.button("Refresh Data"):
        st.stop()

    # Sleep briefly to prevent too frequent updates
    time.sleep(1)

if __name__ == "__main__":
    main()
