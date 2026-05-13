import ujson
import os

# Valores por defecto
TOKEN = ""
WIFI_SSID = ""
WIFI_PASS = ""
MQTT_BROKER = "test.mosquitto.org"
MQTT_TOPIC = "equipo/default"

# Intentar cargar Secretos
try:
    with open('secrets.json', 'r') as f:
        secrets = ujson.load(f)
        TOKEN = secrets.get("telegram_token", TOKEN)
        WIFI_SSID = secrets.get("wifi_ssid", WIFI_SSID)
        WIFI_PASS = secrets.get("wifi_pass", WIFI_PASS)
except:
    print("Aviso: No se pudo cargar secrets.json")

# Intentar cargar Ajustes
try:
    with open('settings.json', 'r') as f:
        settings = ujson.load(f)
        MQTT_BROKER = settings.get("mqtt_broker", MQTT_BROKER)
        MQTT_TOPIC = settings.get("mqtt_topic", MQTT_TOPIC)
except:
    print("Aviso: No se pudo cargar settings.json")

def save_settings(broker=None, topic=None):
    """Guarda los ajustes de MQTT de forma persistente"""
    global MQTT_BROKER, MQTT_TOPIC
    
    if broker: MQTT_BROKER = broker
    if topic: MQTT_TOPIC = topic
    
    try:
        with open('settings.json', 'w') as f:
            ujson.dump({
                "mqtt_broker": MQTT_BROKER,
                "mqtt_topic": MQTT_TOPIC
            }, f)
        return True
    except Exception as e:
        print(f"Error guardando settings: {e}")
        return False

# --- OTRAS CONFIGURACIONES ---
CHAT_ID = "-1002979784867"
MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "bot_azotea_n1krov_001"

CODIGO_EQUIPO = "BOT-AZOTEA-n1krov-01"
CODIGO_SENSOR_DHT = "DHT01"
CODIGO_SENSOR_FLOTANTE = "FLOT01"
CODIGO_SENSOR_SISTEMA = "SYS01"

CODIGO_MODULO_TEMPERATURA = "TEMP01"
CODIGO_MODULO_HUMEDAD = "HUM01"
CODIGO_MODULO_COMBUSTIBLE = "COMB01"
CODIGO_MODULO_VOLTAJE = "VOLT01"

# --- HARDWARE ---
LED_PIN = 2
DHT_PIN = 15
ADC_PIN = 34
V_EMPTY = 2.2
V_FULL = 0.8

# --- TIEMPOS ---
INTERVALO_LECTURA = 60
TELEGRAM_POLLING_INTERVAL = 2
NETWORK_TIMEOUT = 10
WATCHDOG_CHECK_INTERVAL = 300
