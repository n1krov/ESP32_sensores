"""
Watchdog

se encarga de gestionar revisando los tiempos de espera de reconexion
"""
import uasyncio as asyncio
import machine
import gc
import config
import time

class Watchdog:
    def __init__(self, wifi_manager):
        self.wifi_manager = wifi_manager
        self.last_internet_time = time.time()

    async def run(self):
        print("Watchdog de salud iniciado...")
        while True:
            # 1. Gestión de memoria
            before = gc.mem_free()
            gc.collect()
            after = gc.mem_free()
            print(f"Watchdog: RAM Liberada: {after - before} bytes | Libre: {after}")

            # 2. Verificar conectividad
            if self.wifi_manager.is_connected():
                self.last_internet_time = time.time()
            else:
                elapsed = time.time() - self.last_internet_time
                print(f"Watchdog: Sin WiFi hace {elapsed}s")
                
                # Si pasaron más de 10 minutos sin WiFi, intentamos reiniciar
                if elapsed > 600:
                    print("Watchdog: Demasiado tiempo sin red. Reiniciando equipo...")
                    machine.reset()

            await asyncio.sleep(config.WATCHDOG_CHECK_INTERVAL)
