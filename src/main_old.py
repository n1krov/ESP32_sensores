"""
======================================================================
BOT DE TELEGRAM CON SENSORES Y MQTT PARA ESP32
======================================================================
Proyecto: Bot de Azotea - Sistema de monitoreo con sensores
Autores: Estefano, Lautaro y Rito
Fecha: 2025-10-13
Usuario: n1krov, estefanozappa

SOLO ELIMINADO: Sistema de logs JSON
======================================================================
"""

import urequests
import ujson
import network
import time
from machine import Pin, ADC, reset
import dht
from umqtt.simple import MQTTClient

# ======================================================================
# CONFIGURACIÓN GENERAL
# ======================================================================

# --- CONFIGURACIÓN DE TELEGRAM ---
TOKEN = "8388013031:AAHkvgzuAesR0qVa_K2ek0VvkS0G3rWbjio"
CHAT_ID = "-1002979784867"
WifiNetwork = "ECOMCHACO-LIBRE"
WifiPassword = ""

# para cuando este en Azotea
# WifiNetwork = "ECOM_WIFI"
# WifiPassword = "20Ecom24"

# --- CONFIGURACIÓN MQTT ---
MQTT_BROKER = "test.mosquitto.org"
# cuando este en azotea
# MQTT_BROKER = ""

MQTT_PORT = 1883
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "bot_azotea_n1krov_001"

# --- CÓDIGOS DE EQUIPO Y SENSORES ---
CODIGO_EQUIPO = "BOT-AZOTEA-n1krov-01"
CODIGO_SENSOR_DHT = "DHT01"
CODIGO_SENSOR_FLOTANTE = "FLOT01"
CODIGO_SENSOR_SISTEMA = "SYS01"

CODIGO_MODULO_TEMPERATURA = "TEMP01"
CODIGO_MODULO_HUMEDAD = "HUM01"
CODIGO_MODULO_COMBUSTIBLE = "COMB01"
CODIGO_MODULO_VOLTAJE = "VOLT01"
CODIGO_MODULO_MAC = "MAC01"

MQTT_TOPIC = f"equipo/{CODIGO_EQUIPO}"

# --- CONFIGURACIÓN DE SENSORES ---
LED_PIN = 2
DHT_PIN = 15
ADC_PIN = 34
R_PULLUP = 66
V_EMPTY = 2.2
V_FULL = 0.8
# ELIMINADO: LOG_FILE = "sensor_log.json"

# --- CONFIGURACIÓN DE TEMPORIZACIÓN ---
PERIODO = 10
SLEEP_TIME = 2

# ======================================================================
# INICIALIZACIÓN DE HARDWARE
# ======================================================================

led = Pin(LED_PIN, Pin.OUT)
adc = ADC(Pin(ADC_PIN))
adc.atten(ADC.ATTN_11DB)

try:
    dht_sensor = dht.DHT22(Pin(DHT_PIN))
    DHT_AVAILABLE = True
    print("DHT22 inicializado correctamente en pin", DHT_PIN)
except Exception as e:
    print(f"Error inicializando DHT22: {e}")
    DHT_AVAILABLE = False

mqtt_client = None

# ======================================================================
# FUNCIONES DE CONECTIVIDAD
# ======================================================================

def conexion_wifi():
    """Establece conexión WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        print(f'Conectando a red: {WifiNetwork}')
        
        if WifiPassword:
            wlan.connect(WifiNetwork, WifiPassword)
        else:
            wlan.connect(WifiNetwork)
        
        while not wlan.isconnected():
            time.sleep(1)
            print(".", end="")
    
    print(f'\nConectado. IP asignada: {wlan.ifconfig()[0]}')
    mostrar_mac()

def mostrar_mac():
    """Obtiene y muestra la dirección MAC del ESP32"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    mac = wlan.config('mac')
    mac_str = ':'.join('%02x' % b for b in mac) 
    
    print(f"MAC del ESP32: {mac_str}")
    return mac_str

def conexion_mqtt():
    """Establece conexión con el broker MQTT"""
    global mqtt_client
    
    try:
        print(f"Conectando a broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        
        mqtt_client = MQTTClient(
            MQTT_CLIENT_ID,
            MQTT_BROKER,
            MQTT_PORT
        )
        
        mqtt_client.connect()
        print(f"Conectado a MQTT broker")
        print(f"Topico de publicacion: {MQTT_TOPIC}")
        
        return True
        
    except Exception as e:
        print(f"Error conectando a MQTT: {e}")
        mqtt_client = None
        return False

# ======================================================================
# FUNCIONES DE LECTURA DE SENSORES
# ======================================================================

def leer_dht():
    """Lee temperatura y humedad del sensor DHT22"""
    if not DHT_AVAILABLE:
        print("DHT22 no disponible")
        return None, None
    
    for intento in range(3):
        try:
            print(f"Leyendo DHT22... intento {intento + 1}/3")
            
            dht_sensor.measure()
            time.sleep(1)
            
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
            
            print(f"DHT22 OK: Temp={temp}°C, Hum={hum}%")
            return temp, hum
            
        except Exception as e:
            print(f"Error DHT22 intento {intento + 1}: {e}")
            
            if intento < 2:
                time.sleep(2)
            continue
    
    print("DHT22 fallo despues de 3 intentos")
    return None, None

def leer_adc_raw():
    """Lee el valor crudo del ADC"""
    try:
        print("Leyendo ADC...")
        raw = adc.read()
        print(f"ADC raw: {raw} (0-4095)")
        return raw
    except Exception as e:
        print(f"Error ADC: {e}")
        return None

def raw_a_voltaje(raw):
    """Convierte valor crudo del ADC a voltaje"""
    if raw is None:
        return None
    
    voltage = raw / 4095 * 3.3
    print(f"Voltaje calculado: {voltage:.2f}V")
    return voltage

def calcular_nivel(voltage):
    """Calcula el porcentaje de combustible basado en el voltaje"""
    if voltage is None:
        return None
    
    nivel = (V_EMPTY - voltage) / (V_EMPTY - V_FULL) * 100
    nivel = max(0.0, min(100.0, nivel))
    print(f"Nivel calculado: {nivel:.1f}%")
    
    return round(nivel, 2)

def leer_sensores():
    """Lee todos los sensores disponibles"""
    print("=" * 40)
    print("INICIANDO LECTURA DE SENSORES")
    print("=" * 40)
    
    temp, hum = leer_dht()
    raw = leer_adc_raw()
    voltage = raw_a_voltaje(raw) if raw is not None else None
    nivel = calcular_nivel(voltage)
    
    payload = {
        "timestamp": time.time(),
        "temperature": temp,
        "humidity": hum,
        "adc_raw": raw,
        "voltage": round(voltage, 1) if voltage is not None else None,
        "fuel_level_percent": nivel
    }
    
    print(f"Payload generado: {payload}")
    # ELIMINADO: guardar_log(payload)
    
    print("=" * 40)
    return payload

def crear_json_mqtt(datos_sensores):
    """Convierte los datos de sensores al formato JSON MQTT"""
    modulos = []
    
    if datos_sensores["temperature"] is not None:
        modulos.append({
            "codigo_modulo": CODIGO_MODULO_TEMPERATURA,
            "valor": datos_sensores["temperature"],
            "codigo_sensor": CODIGO_SENSOR_DHT
        })
    
    if datos_sensores["humidity"] is not None:
        modulos.append({
            "codigo_modulo": CODIGO_MODULO_HUMEDAD,
            "valor": datos_sensores["humidity"], 
            "codigo_sensor": CODIGO_SENSOR_DHT
        })
    
    if datos_sensores["fuel_level_percent"] is not None:
        modulos.append({
            "codigo_modulo": CODIGO_MODULO_COMBUSTIBLE,
            "valor": datos_sensores["fuel_level_percent"],
            "codigo_sensor": CODIGO_SENSOR_FLOTANTE
        })
    
    if datos_sensores["voltage"] is not None:
        modulos.append({
            "codigo_modulo": CODIGO_MODULO_VOLTAJE,
            "valor": datos_sensores["voltage"],
            "codigo_sensor": CODIGO_SENSOR_SISTEMA
        })
    
    json_mqtt = {
        "codigo_equipo": CODIGO_EQUIPO,
        "fecha_hora": int(datos_sensores["timestamp"]),
        "tipo_evento": "TIEMPO",
        "modulos": modulos
    }
    
    return json_mqtt

# ======================================================================
# FUNCIONES MQTT
# ======================================================================

def enviar_mqtt(datos_sensores):
    """Envía los datos de sensores por MQTT"""
    global mqtt_client
    
    if mqtt_client is None:
        print("Cliente MQTT no conectado")
        return False
    
    try:
        json_mqtt = crear_json_mqtt(datos_sensores)
        mensaje_json = ujson.dumps(json_mqtt)
        
        print(f"\nENVIANDO POR MQTT")
        print(f"Topico: {MQTT_TOPIC}")
        print(f"JSON: {mensaje_json}")
        
        mqtt_client.publish(MQTT_TOPIC, mensaje_json)
        
        print(f"Mensaje MQTT enviado correctamente\n")
        return True
        
    except Exception as e:
        print(f"Error enviando MQTT: {e}")
        
        print("Intentando reconectar MQTT...")
        if conexion_mqtt():
            print("Reconexion MQTT exitosa")
            try:
                mqtt_client.publish(MQTT_TOPIC, mensaje_json)
                print("Reenvio exitoso")
                return True
            except:
                print("Reenvio fallo")
        else:
            print("Reconexion MQTT fallo")
            
        return False

# ======================================================================
# FUNCIONES DE UTILIDAD
# ======================================================================

# ELIMINADO: def guardar_log(data)

def blink(times=2, delay=0.15):
    """Hace parpadear el LED integrado"""
    for i in range(times):
        led.value(1)
        time.sleep(delay)
        led.value(0)
        time.sleep(delay)

def sensar_y_mostrar():
    """Lee sensores y los muestra por consola (no duplica lectura)"""
    datos = leer_sensores()
    
    mensaje = "=" * 20 + " SENSORES " + "=" * 20
    
    if datos["temperature"] is not None:
        mensaje += f"\nTemperatura: {datos['temperature']}°C"
    else:
        mensaje += "\nTemperatura: Error"
    
    if datos["humidity"] is not None:
        mensaje += f"\nHumedad: {datos['humidity']}%"
    else:
        mensaje += "\nHumedad: Error"
    
    if datos["fuel_level_percent"] is not None:
        mensaje += f"\nCombustible: {datos['fuel_level_percent']}%"
    else:
        mensaje += "\nCombustible: Error"
    
    if datos["voltage"] is not None:
        mensaje += f"\nVoltaje: {datos['voltage']}V"
    
    mensaje += f"\nTimestamp: {int(datos['timestamp'])}"
    mensaje += "\n" + "=" * 47
    
    print(mensaje)
    return datos  # Retornar datos para usar en MQTT

# ======================================================================
# FUNCIONES DE TELEGRAM (SIMPLIFICADAS)
# ======================================================================

def send_message(msg, chat_id=CHAT_ID):
    """Envía un mensaje a través del bot de Telegram (simplificado)"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": str(chat_id), "text": str(msg)}
        
        r = urequests.post(url, json=payload)
        
        if r.status_code == 200:
            response_data = ujson.loads(r.text)
            r.close()
            return response_data.get("ok", False)
        else:
            print(f"Error HTTP Telegram: {r.status_code}")
            r.close()
            return False
            
    except Exception as e:
        print(f'Error enviando mensaje Telegram: {e}')
        return False

def get_updates(offset=None):
    """Obtiene los últimos mensajes del bot (simplificado)"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        if offset:
            url += f"?offset={offset}"
        
        r = urequests.get(url)
        
        if r.status_code == 200:
            data = ujson.loads(r.text)
            r.close()
            return data
        else:
            print(f"Error HTTP getUpdates: {r.status_code}")
            r.close()
            return None
            
    except Exception as e:
        print(f'Error obteniendo updates: {e}')
        return None

# ======================================================================
# PROCESAMIENTO DE COMANDOS (SIMPLIFICADO)
# ======================================================================

def procesar_comando(text, chat_id):
    """Procesa los comandos del bot de Telegram"""
    command = text.strip().lower()
    print(f"Procesando comando: '{command}'")
    
    if command == "/saludo":
        send_message("Hola, Soy el bot de Azotea (Hecho por Estefano, Lautaro y Rito)", chat_id)
    
    elif command == "/mac":
        mac = mostrar_mac()
        send_message(f"Direccion MAC del ESP32: {mac}", chat_id)
    
    elif command == "/nivel":
        blink(1)
        datos = leer_sensores()
        if datos["fuel_level_percent"] is not None:
            send_message(f"Nivel de combustible: {datos['fuel_level_percent']}%", chat_id)
        else:
            send_message("Error leyendo el sensor de combustible", chat_id)
    
    elif command == "/temp":
        blink(1)
        datos = leer_sensores()
        if datos["temperature"] is not None:
            temp_msg = f"Temperatura: {datos['temperature']}°C"
            if datos["humidity"] is not None:
                temp_msg += f"\nHumedad: {datos['humidity']}%"
            send_message(temp_msg, chat_id)
        else:
            send_message("Error leyendo el sensor DHT", chat_id)
    
    elif command == "/estado":
        blink(2)
        datos = leer_sensores()
        
        mensaje = "Estado de Sensores\n\n"
        mensaje += f"Temperatura: {datos['temperature'] if datos['temperature'] is not None else 'Error'}°C\n"
        mensaje += f"Humedad: {datos['humidity'] if datos['humidity'] is not None else 'Error'}%\n"
        mensaje += f"Combustible: {datos['fuel_level_percent'] if datos['fuel_level_percent'] is not None else 'Error'}%\n"
        mensaje += f"Voltaje: {datos['voltage'] if datos['voltage'] is not None else 'Error'}V\n"
        mensaje += f"Equipo: {CODIGO_EQUIPO}"
        
        send_message(mensaje, chat_id)
    
    # === COMANDO: /help ===
    elif command == "/help":
        print("Ejecutando comando /ayuda")
        
        # Mensaje sin caracteres especiales problemáticos
        mensaje = "COMANDOS DISPONIBLES:\n\n"
        mensaje += "Informacion:\n"
        mensaje += "- /saludo - Informacion del bot\n"
        mensaje += "- /mac - Direccion MAC del ESP32\n"
        mensaje += "- /help - Mostrar esta ayuda\n\n"
        mensaje += "Sensores:\n"
        mensaje += "- /nivel - Solo nivel de combustible\n"
        mensaje += "- /temp - Temperatura y humedad\n"
        mensaje += "- /mqtt - Enviar datos por MQTT manualmente\n"
        mensaje += "- /estado - Todos los datos de sensores\n\n"
        mensaje += "- /restart - Reiniciar ESP32\n\n"  
        mensaje += "Ejemplo: Envia /todo para ver el estado completo"
        
        print(f"Enviando ayuda a chat {chat_id}")
        resultado = send_message(mensaje, chat_id)
        
        if resultado:
            print("Mensaje de ayuda enviado correctamente")
        else:
            print("Error enviando mensaje de ayuda")
    
    elif command == "/mqtt":
        print("Comando /mqtt - Enviando datos por MQTT manualmente")
        datos = leer_sensores()
        if mqtt_client is not None:
            exito = enviar_mqtt(datos)
            if exito:
                send_message(f"Mensaje MQTT enviado a {MQTT_TOPIC}", chat_id)
            else:
                send_message("Error enviando mensaje MQTT", chat_id)
        else:
            send_message("MQTT no conectado", chat_id)
    
    elif command == "turip":
        send_message("ip ip", chat_id)
    
    elif command == "ip ip ip":
        send_message("turip", chat_id)
    
    elif command == "/restart":
        print("Ejecutando comando /restart")
        send_message("Reiniciando ESP32 en 3 segundos...", chat_id)
        time.sleep(3)
        reiniciar_esp32()
    else:
        print(f'[{command}] NO es Un comando configurado')

def reiniciar_esp32():
    """Reinicia el ESP32 de forma controlada"""
    print("Preparando reinicio del ESP32...")
    
    # Cerrar conexion MQTT si existe
    global mqtt_client
    if mqtt_client:
        try:
            mqtt_client.disconnect()
            print("Conexion MQTT cerrada")
        except:
            pass
    
    # Parpadeo para indicar reinicio
    for i in range(5):
        led.value(1)
        time.sleep(0.2)
        led.value(0)
        time.sleep(0.2)
    
    print("Reiniciando ESP32...")
    time.sleep(1)
    
    # Importar reset si no está importado
    try:
        reset()
    except:
        from machine import reset
        reset()


# ======================================================================
# FUNCIÓN PRINCIPAL (SIMPLIFICADA)
# ======================================================================

def main():
    """Función principal del bot"""
    print("=" * 60)
    print("INICIANDO BOT DE TELEGRAM CON SENSORES Y MQTT")
    print("=" * 60)
    print(f"Codigo Equipo: {CODIGO_EQUIPO}")
    print(f"Topico MQTT: {MQTT_TOPIC}")
    print("=" * 60)
    
    conexion_wifi()
    
    mqtt_conectado = conexion_mqtt()
    if not mqtt_conectado:
        print("Continuando sin MQTT (solo Telegram)")
    
    print("Bot listo")
    blink(3, 0.1)
    
    last_update_id = None
    sensor_counter = 0
    loop_count = 0
    telegram_error_count = 0
    
    while True:
        try:
#             loop_count += 1
#             print(f'\n[+] ITERACION Numero -> #{loop_count}')
            # ======================================================================
            # ENVÍO PERIÓDICO POR MQTT
            # ======================================================================
            sensor_counter += 1
            if sensor_counter >= PERIODO:
                print(f"\nENVIO PERIODICO MQTT #{loop_count//PERIODO}")
                print("=" * 40)
                
                datos = sensar_y_mostrar()  # Leer y mostrar sensores
                
                if mqtt_client is not None:
                    envio_exitoso = enviar_mqtt(datos)
                    if envio_exitoso:
                        blink(2, 0.1)
                    else:
                        blink(5, 0.05)
                else:
                    print("MQTT no conectado")
                
                sensor_counter = 0
                print("=" * 40)
            
            # ======================================================================
            # PROCESAR MENSAJES DE TELEGRAM
            # ======================================================================
            #print(".", end="")  # Mostrar actividad
            
            updates = get_updates(last_update_id)
            
            if updates and "result" in updates and len(updates["result"]) > 0:
                print(f"\nRecibidos {len(updates['result'])} mensajes")
                telegram_error_count = 0  # Reset counter en éxito
                
                for item in updates["result"]:
                    update_id = item["update_id"]
                    message = item.get("message")
                    
                    if message:
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")
                        
                        user = message.get("from", {})
                        first_name = user.get("first_name", "Usuario")
                        
                        print(f"Mensaje de {first_name}: '{text}'")
                        
                        if text:
                            procesar_comando(text, chat_id)
                    
                    last_update_id = update_id + 1
            
            elif updates is None:
                telegram_error_count += 1
                print(f"\nError Telegram #{telegram_error_count}")
                
                if telegram_error_count >= 5:
                    print("Demasiados errores de Telegram, continuando solo con MQTT")
                    telegram_error_count = 0
                    time.sleep(10)
                
        except Exception as e:
            print(f"\nError en bucle principal: {e}")
            time.sleep(5)
        
        #time.sleep(SLEEP_TIME)

# ======================================================================
# PUNTO DE ENTRADA
# ======================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError critico: {e}")
        time.sleep(10)