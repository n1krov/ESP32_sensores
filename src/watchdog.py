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
    def __init__(self, wifi_manager, bot=None):
        self.wifi_manager = wifi_manager
        self.bot = bot
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

            # 3. Verificar reinicio programado
            try:
                await self.check_scheduled_reboot()
            except Exception as e:
                print(f"Watchdog: Error en verificacion de reinicio: {e}")

            await asyncio.sleep(config.WATCHDOG_CHECK_INTERVAL)

    async def check_scheduled_reboot(self):
        """Verifica si es necesario realizar un reinicio programado"""
        import ujson
        
        # 1. Verificar si la hora del RTC local es válida (NTP sincronizó exitosamente)
        current_tm = time.localtime()
        if current_tm[0] <= 2025:
            # Si el año sigue en 2000, la hora aún no se ha sincronizado por NTP
            return

        current_time = time.time()
        
        # 2. Obtener timestamp del último reinicio
        last_reboot = 0
        try:
            with open('last_reboot.json', 'r') as f:
                data = ujson.load(f)
                last_reboot = data.get("last_reboot_timestamp", 0)
        except Exception:
            # Si no existe el archivo o hay un error de lectura, es el primer ciclo.
            # Guardamos el tiempo actual para iniciar la cuenta desde ahora.
            try:
                with open('last_reboot.json', 'w') as f:
                    ujson.dump({"last_reboot_timestamp": current_time}, f)
                print("Watchdog: Archivo last_reboot.json inicializado con el tiempo actual.")
            except Exception as e:
                print(f"Watchdog: Error inicializando last_reboot.json: {e}")
            return

        # 3. Calcular tiempo transcurrido en segundos
        elapsed = current_time - last_reboot
        
        # Intervalo de reinicio en segundos (por defecto 3 días)
        reboot_interval_secs = getattr(config, 'REBOOT_INTERVAL_DAYS', 3) * 24 * 3600
        
        # Usamos un margen de tolerancia (ej: 4 horas antes) para asegurar que se
        # active perfectamente dentro de la ventana del tercer día sin desfases de minutos.
        threshold = reboot_interval_secs - 14400  # 14400 segundos = 4 horas
        
        if elapsed >= threshold:
            # Convertir a hora local para verificar la ventana horaria
            timezone_offset = getattr(config, 'TIMEZONE_OFFSET', -3)
            local_epoch = current_time + (timezone_offset * 3600)
            local_tm = time.localtime(local_epoch)
            local_hour = local_tm[3]
            
            start_hour = getattr(config, 'REBOOT_WINDOW_START_HOUR', 3)
            end_hour = getattr(config, 'REBOOT_WINDOW_END_HOUR', 5)
            
            # Verificar si la hora local está dentro del rango configurado (ej: de 3 a 5 AM inclusive)
            if start_hour <= local_hour <= end_hour:
                print(f"Watchdog: Iniciando reinicio programado de mantenimiento (Hora local: {local_hour:02d}hs)...")
                
                # Actualizar el archivo antes de reiniciar para evitar bucles de reinicio
                try:
                    with open('last_reboot.json', 'w') as f:
                        ujson.dump({"last_reboot_timestamp": current_time}, f)
                except Exception as e:
                    print(f"Watchdog: Error guardando last_reboot antes de reiniciar: {e}")
                
                # Enviar mensaje de alerta por Telegram
                if self.bot:
                    try:
                        mensaje = "Reinicio de Mantenimiento: El sistema se esta reiniciando de manera programada para optimizar el rendimiento."
                        await self.bot.send_message(config.CHAT_ID, mensaje)
                    except Exception as e:
                        print(f"Watchdog: Error enviando notificacion Telegram: {e}")
                    await asyncio.sleep(2) # Dar un pequeño margen para enviar el mensaje
                
                machine.reset()
