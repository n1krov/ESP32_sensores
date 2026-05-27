import network
import uasyncio as asyncio
import time
from machine import Pin
import config

class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.led = Pin(config.LED_PIN, Pin.OUT)

    async def connect(self):
        """Establece conexión WiFi de forma asincrónica"""
        if self.wlan.isconnected():
            return True

        print(f"Conectando a WiFi: {config.WIFI_SSID}...")
        self.wlan.connect(config.WIFI_SSID, config.WIFI_PASS)
        
        # Esperar hasta 20 segundos
        for _ in range(20):
            if self.wlan.isconnected():
                print(f"WiFi Conectado! IP: {self.wlan.ifconfig()[0]}")
                # Lanzar tarea de sincronización de hora en segundo plano
                asyncio.create_task(self.sync_time_background())
                return True
            self.led.value(not self.led.value()) # Blink mientras conecta
            await asyncio.sleep(1)
            
        print("Fallo la conexión WiFi")
        self.led.value(0)
        return False

    async def sync_time_background(self):
        """Intenta sincronizar la hora por NTP con reintentos"""
        import ntptime
        
        # Esperar 2 segundos para asegurar la estabilidad de la red y resolución de DNS
        await asyncio.sleep(2)
        
        for intento in range(3):
            try:
                print(f"WiFiManager: Sincronizando hora con NTP (intento {intento+1})...")
                ntptime.settime()
                print("WiFiManager: Sincronizacion NTP exitosa. Hora actual (UTC):", time.localtime())
                return True
            except Exception as e:
                print(f"WiFiManager: Error en sincronizacion NTP (intento {intento+1}): {e}")
                await asyncio.sleep(5)
        return False

    def is_connected(self):
        return self.wlan.isconnected()

    def get_ip(self):
        if self.is_connected():
            return self.wlan.ifconfig()[0]
        return "No IP"

    def get_mac(self):
        mac = self.wlan.config('mac')
        return ':'.join('%02x' % b for b in mac)

    async def keep_connected(self):
        """Tarea de fondo para asegurar que el WiFi siga vivo"""
        while True:
            if not self.is_connected():
                print("WiFi perdido. Reintentando conexión...")
                await self.connect()
            await asyncio.sleep(30)
