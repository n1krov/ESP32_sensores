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
                return True
            self.led.value(not self.led.value()) # Blink mientras conecta
            await asyncio.sleep(1)
            
        print("Fallo la conexión WiFi")
        self.led.value(0)
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
