# MQTT Data Collection and Visualization System

## Project Overview
This project implements a complete IoT data collection system using MQTT protocol, with data storage and real-time visualization capabilities. The system collects sensor data from ESP32 devices, stores it in both SQL and CSV formats, and provides a real-time dashboard for monitoring.

## System Architecture

### Components
1. MQTT Broker (Mosquitto)
2. Python MQTT Client
3. SQLite Database
4. CSV Storage
5. Streamlit Dashboard

## Installation and Setup

### 1. MQTT Broker Setup
```bash
# Install Mosquitto
sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients

# Configure Mosquitto
sudo nano /etc/mosquitto/mosquitto.conf
```

Add the following configuration:
```
# Network settings
listener 1883 0.0.0.0
allow_anonymous false
password_file /etc/mosquitto/passwd

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all

# Persistence
persistence true
persistence_location /var/lib/mosquitto/
```

Create user and password:
```bash
sudo mosquitto_passwd -c /etc/mosquitto/passwd admin
# Enter password when prompted
```

### 2. Python Environment Setup
```bash
# Create virtual environment
python -m venv py_mqtt
source py_mqtt/bin/activate

# Install required packages
pip install paho-mqtt pandas sqlite3 streamlit plotly
```

## Code Implementation

### 1. MQTT Data Logger (`mqtt_logger.py`)
```python
import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import pandas as pd
import json
import os

# MQTT Settings
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "mqtt123"
MQTT_TOPIC = "#"

# Database initialization and message handling code...
```

### 2. Streamlit Dashboard (`mqtt_dashboard.py`)
```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json

# Dashboard implementation code...
```

## Database Schema

### SQLite Table Structure
```sql
CREATE TABLE mqtt_messages (
    timestamp TEXT,
    topic TEXT,
    message TEXT
);
```

## Data Format

### MQTT Message Format (JSON)
```json
{
    "device": "ESP32_e7f9d108",
    "humidity": 45,
    "temperature": 39.2,
    "conductivity": 1475,
    "ph": 11.4,
    "nitrogen": 220,
    "phosphorus": 22,
    "potassium": 348,
    "wifi_strength": -68,
    "timestamp": 415011
}
```

## Running the System

### 1. Start MQTT Broker
```bash
sudo systemctl start mosquitto
sudo systemctl status mosquitto
```

### 2. Run Data Logger
```bash
python mqtt_logger.py
```

### 3. Launch Dashboard
```bash
streamlit run mqtt_dashboard.py
```

## Dashboard Features

1. Real-time Data Display
   - Latest sensor values
   - Message distribution
   - Historical trends

2. Data Visualization
   - Time series plots
   - Pie charts
   - Basic statistics

3. Data Management
   - CSV download
   - Time range filtering
   - Auto-refresh capability

## Security Considerations

1. MQTT Security
   - Username/password authentication
   - TLS/SSL encryption (optional)
   - IP restriction

2. Data Security
   - SQL injection prevention
   - Regular backups
   - Access control

## Troubleshooting

### Common Issues and Solutions

1. MQTT Connection Issues
   ```bash
   sudo systemctl status mosquitto
   tail -f /var/log/mosquitto/mosquitto.log
   ```

2. Database Issues
   ```bash
   sqlite3 mqtt_data.db
   .tables
   .schema mqtt_messages
   ```

## Future Enhancements

1. Additional Features
   - Email/SMS alerts
   - Data export in multiple formats
   - Advanced analytics

2. Performance Improvements
   - Data aggregation
   - Caching
   - Query optimization

## Resources

- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Paho-MQTT Documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)

## License
MIT License

## Contributors
[Your Name]

## Version History
- v1.0.0 - Initial Release
  - Basic MQTT functionality
  - SQLite and CSV storage
  - Streamlit dashboard

---

*Last Updated: 12-12-24*
