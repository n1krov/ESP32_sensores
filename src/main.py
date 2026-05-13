import uasyncio as asyncio
import config
from wifi_manager import WiFiManager
from sensor_manager import SensorManager
from mqtt_manager import MQTTManager
from telegram_bot import TelegramBot
from watchdog import Watchdog
import gc

async def sensor_mqtt_task(sensor_mgr, mqtt_mgr):
    """Tarea periódica de lectura de sensores y envío MQTT"""
    print("Tarea de Sensores/MQTT iniciada...")
    while True:
        try:
            datos = sensor_mgr.obtener_todo()
            print(f"Lectura: {datos['temperature']}C, {datos['fuel_percent']}%")
            
            await mqtt_mgr.publish_data(datos)
        except Exception as e:
            print(f"Error en tarea Sensores/MQTT: {e}")
            
        await asyncio.sleep(config.INTERVALO_LECTURA)

async def main():
    print("--- SISTEMA AZOTEA v2.0 (uasyncio) ---")
    
    # Inicializar componentes
    wifi = WiFiManager()
    sensors = SensorManager()
    mqtt = MQTTManager()
    bot = TelegramBot(sensors, wifi)
    health = Watchdog(wifi)

    # Conectar WiFi inicialmente
    if await wifi.connect():
        await mqtt.connect()
    
    # Crear tareas asincrónicas
    tasks = [
        asyncio.create_task(wifi.keep_connected()),   # Mantener WiFi vivo
        asyncio.create_task(bot.loop()),              # Bot de Telegram
        asyncio.create_task(sensor_mqtt_task(sensors, mqtt)), # Sensores y MQTT
        asyncio.create_task(health.run())             # Monitor de salud y GC
    ]

    print("Todas las tareas iniciadas.")
    
    # Mantener el bucle principal vivo
    while True:
        await asyncio.sleep(3600) # Dormir 1 hora (las tareas corren de fondo)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Sistema detenido por el usuario")
    except Exception as e:
        print(f"Error FATAL: {e}")
        import machine
        machine.reset()
