#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// Configuration
const char* ssid = "Namal-Net";
const char* password = "namal123";
const char* mqtt_server = "65.0.176.163";
const int mqtt_port = 1883;
const char* mqtt_username = "admin";
const char* mqtt_password = "mqtt123";

// Constants
const unsigned long WIFI_TIMEOUT = 10000;  // 10 seconds timeout for WiFi connection
const unsigned long MQTT_RECONNECT_DELAY = 5000;  // 5 seconds between MQTT reconnection attempts
const unsigned long SENSOR_PUBLISH_INTERVAL = 10000;  // 10 second between sensor readings

// Global variables
WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
unsigned long lastWifiCheck = 0;
bool firstConnection = true;
int reconnectCount = 0;
String deviceID;

// Status LED pins (if available on your board)
#define WIFI_LED 2    // Built-in LED
#define MQTT_LED 4    // External LED for MQTT status

// Function to generate random sensor values within realistic ranges
struct SensorData {
    float humidity;      // 0-100 %
    float temperature;   // 0-50 °C
    float conductivity;  // 0-2000 µS/cm
    float ph;           // 0-14
    float nitrogen;     // 0-1000 mg/kg
    float phosphorus;   // 0-100 mg/kg
    float potassium;    // 0-1000 mg/kg
    bool valid;         // Indicates if readings are valid
};

// Generate unique device ID
String generateDeviceID() {
    uint64_t chipid = ESP.getEfuseMac();
    return "ESP32_" + String((uint32_t)chipid, HEX);
}

// WiFi event handler
void WiFiEvent(WiFiEvent_t event) {
    Serial.printf("[WiFi] Event: %d\n", event);
    switch(event) {
        case ARDUINO_EVENT_WIFI_STA_GOT_IP:
            Serial.println("WiFi connected");
            Serial.println("IP address: " + WiFi.localIP().toString());
            digitalWrite(WIFI_LED, HIGH);
            break;
        case ARDUINO_EVENT_WIFI_STA_DISCONNECTED:
            Serial.println("WiFi lost connection");
            digitalWrite(WIFI_LED, LOW);
            break;
        default:
            break;
    }
}

// Setup WiFi connection
bool setup_wifi() {
    Serial.println("\nConnecting to WiFi...");
    digitalWrite(WIFI_LED, LOW);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);

    unsigned long startAttemptTime = millis();

    while (WiFi.status() != WL_CONNECTED && 
           millis() - startAttemptTime < WIFI_TIMEOUT) {
        delay(100);
        Serial.print(".");
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\nFailed to connect to WiFi");
        return false;
    }

    Serial.println("\nWiFi connected successfully");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(WIFI_LED, HIGH);
    return true;
}

// MQTT connection handling
bool mqtt_connect() {
    digitalWrite(MQTT_LED, LOW);
    Serial.println("Attempting MQTT connection...");
    
    if (client.connect(deviceID.c_str(), mqtt_username, mqtt_password)) {
        Serial.println("MQTT Connected");
        digitalWrite(MQTT_LED, HIGH);
        
        // Publish connection message
        StaticJsonDocument<200> statusDoc;
        statusDoc["device"] = deviceID;
        statusDoc["status"] = "connected";
        statusDoc["reconnects"] = reconnectCount;
        
        String statusPayload;
        serializeJson(statusDoc, statusPayload);
        client.publish("soil/status", statusPayload.c_str());
        
        return true;
    } else {
        Serial.print("MQTT Connection failed, rc=");
        Serial.println(client.state());
        return false;
    }
}

SensorData readSensorData() {
    SensorData data;
    
    // Simulate sensor readings with random values
    // In real application, replace with actual sensor readings
    data.humidity = random(30, 90);
    data.temperature = 20 + ((float)random(0, 200) / 10);
    data.conductivity = random(500, 1500);
    data.ph = 4 + ((float)random(0, 100) / 10);
    data.nitrogen = random(100, 800);
    data.phosphorus = random(10, 80);
    data.potassium = random(100, 800);
    
    // Print readings to Serial
    Serial.println("\nCurrent Sensor Readings:");
    Serial.println("Humidity: " + String(data.humidity) + " %");
    Serial.println("Temperature: " + String(data.temperature) + " °C");
    Serial.println("Conductivity: " + String(data.conductivity) + " µS/cm");
    Serial.println("pH: " + String(data.ph));
    Serial.println("Nitrogen: " + String(data.nitrogen) + " mg/kg");
    Serial.println("Phosphorus: " + String(data.phosphorus) + " mg/kg");
    Serial.println("Potassium: " + String(data.potassium) + " mg/kg");
    
    data.valid = true;
    return data;
}

void publishSensorData(const SensorData& data) {
    if (!data.valid) {
        Serial.println("Invalid sensor data - skipping publish");
        return;
    }

    StaticJsonDocument<512> doc;
    doc["device"] = deviceID;
    doc["humidity"] = data.humidity;
    doc["temperature"] = data.temperature;
    doc["conductivity"] = data.conductivity;
    doc["ph"] = data.ph;
    doc["nitrogen"] = data.nitrogen;
    doc["phosphorus"] = data.phosphorus;
    doc["potassium"] = data.potassium;
    doc["wifi_strength"] = WiFi.RSSI();
    doc["timestamp"] = millis();

    String payload;
    serializeJson(doc, payload);

    if (client.publish("soil/data", payload.c_str())) {
        Serial.println("Data published successfully");
    } else {
        Serial.println("Failed to publish data");
    }
}

void setup() {
    // Initialize serial and pins
    Serial.begin(115200);
    pinMode(WIFI_LED, OUTPUT);
    pinMode(MQTT_LED, OUTPUT);
    
    // Generate unique device ID
    deviceID = generateDeviceID();
    Serial.println("Device ID: " + deviceID);

    // Setup WiFi event handling
    WiFi.onEvent(WiFiEvent);

    // Initialize WiFi
    setup_wifi();

    // Configure MQTT
    client.setServer(mqtt_server, mqtt_port);
    
    // Initialize random seed
    randomSeed(analogRead(0));
}

void loop() {
    unsigned long currentMillis = millis();

    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi connection lost. Reconnecting...");
        setup_wifi();
    }

    // Handle MQTT connection
    if (!client.connected()) {
        digitalWrite(MQTT_LED, LOW);
        if (currentMillis - lastMsg >= MQTT_RECONNECT_DELAY) {
            reconnectCount++;
            if (mqtt_connect()) {
                lastMsg = currentMillis;
            }
        }
    }

    // Publish sensor data at regular intervals
    if (client.connected() && (currentMillis - lastMsg >= SENSOR_PUBLISH_INTERVAL)) {
        SensorData data = readSensorData();
        publishSensorData(data);
        lastMsg = currentMillis;
    }

    // Maintain MQTT connection
    client.loop();
}
