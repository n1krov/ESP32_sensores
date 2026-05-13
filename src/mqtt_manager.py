from umqtt.simple import MQTTClient
import ujson
import config
import uasyncio as asyncio

class MQTTManager:
    def __init__(self):
        self.client = None
        self.connected = False

    async def connect(self):
        try:
            self.client = MQTTClient(
                config.MQTT_CLIENT_ID,
                config.MQTT_BROKER,
                port=config.MQTT_PORT,
                user=config.MQTT_USER,
                password=config.MQTT_PASSWORD,
                keepalive=60
            )
            self.client.connect()
            self.connected = True
            print("Conectado a Broker MQTT")
            return True
        except Exception as e:
            print(f"Error conectando a MQTT: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.connected = False

    async def publish_data(self, data):
        if not self.connected:
            if not await self.connect():
                return False

        try:
            # Formatear según el protocolo previo
            payload = {
                "codigo_equipo": config.CODIGO_EQUIPO,
                "fecha_hora": int(data["timestamp"]),
                "tipo_evento": "TIEMPO",
                "modulos": []
            }

            if data["temperature"] is not None:
                payload["modulos"].append({
                    "codigo_modulo": config.CODIGO_MODULO_TEMPERATURA,
                    "valor": data["temperature"],
                    "codigo_sensor": config.CODIGO_SENSOR_DHT
                })
            
            if data["humidity"] is not None:
                payload["modulos"].append({
                    "codigo_modulo": config.CODIGO_MODULO_HUMEDAD,
                    "valor": data["humidity"],
                    "codigo_sensor": config.CODIGO_SENSOR_DHT
                })

            if data["fuel_percent"] is not None:
                payload["modulos"].append({
                    "codigo_modulo": config.CODIGO_MODULO_COMBUSTIBLE,
                    "valor": data["fuel_percent"],
                    "codigo_sensor": config.CODIGO_SENSOR_FLOTANTE
                })

            mensaje = ujson.dumps(payload)
            self.client.publish(config.MQTT_TOPIC, mensaje)
            print(f"MQTT Publicado en {config.MQTT_TOPIC}")
            return True
        except Exception as e:
            print(f"Error publicando MQTT: {e}")
            self.connected = False
            return False
