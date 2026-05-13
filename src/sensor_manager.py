import machine
import dht
import time
import config

class SensorManager:
    def __init__(self):
        # Inicializar DHT22
        try:
            self.dht_sensor = dht.DHT22(machine.Pin(config.DHT_PIN))
            self.dht_available = True
        except Exception as e:
            print(f"Error inicializando DHT22: {e}")
            self.dht_available = False

        # Inicializar ADC para combustible
        self.adc = machine.ADC(machine.Pin(config.ADC_PIN))
        self.adc.atten(machine.ADC.ATTN_11DB)

    def leer_dht(self):
        if not self.dht_available:
            return None, None
        
        try:
            self.dht_sensor.measure()
            # Un pequeño delay es recomendado después de measure() en algunos casos
            time.sleep_ms(100) 
            return self.dht_sensor.temperature(), self.dht_sensor.humidity()
        except Exception as e:
            print(f"Error leyendo DHT: {e}")
            return None, None

    def leer_combustible(self):
        try:
            raw = self.adc.read()
            voltage = (raw / 4095) * 3.3
            
            # Cálculo de porcentaje basado en los límites configurados
            # Inverso: V_EMPTY (alto voltaje) es 0%, V_FULL (bajo voltaje) es 100%
            nivel = (config.V_EMPTY - voltage) / (config.V_EMPTY - config.V_FULL) * 100
            nivel = max(0.0, min(100.0, nivel))
            
            return round(nivel, 1), round(voltage, 2)
        except Exception as e:
            print(f"Error leyendo ADC: {e}")
            return None, None

    def obtener_todo(self):
        temp, hum = self.leer_dht()
        nivel, volt = self.leer_combustible()
        
        return {
            "temperature": temp,
            "humidity": hum,
            "fuel_percent": nivel,
            "voltage": volt,
            "timestamp": time.time()
        }
