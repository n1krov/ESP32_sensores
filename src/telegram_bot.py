import urequests
import ujson
import uasyncio as asyncio
import config
import machine

class TelegramBot:
    def __init__(self, sensor_manager, wifi_manager):
        self.sensor_manager = sensor_manager
        self.wifi_manager = wifi_manager
        self.last_update_id = 0
        self.url = f"https://api.telegram.org/bot{config.TOKEN}"

    async def send_message(self, chat_id, text):
        """Envía un mensaje a Telegram"""
        try:
            payload = {"chat_id": chat_id, "text": text}
            # urequests.post es bloqueante, pero con timeout debería volver pronto
            r = urequests.post(f"{self.url}/sendMessage", json=payload, timeout=config.NETWORK_TIMEOUT)
            r.close()
            return True
        except Exception as e:
            print(f"Error Telegram send: {e}")
            return False

    async def get_updates(self):
        """Consulta nuevos mensajes"""
        try:
            query = f"{self.url}/getUpdates?offset={self.last_update_id + 1}&timeout=5"
            r = urequests.get(query, timeout=config.NETWORK_TIMEOUT + 5)
            data = r.json()
            r.close()
            
            if data.get("ok"):
                return data.get("result", [])
            return []
        except Exception as e:
            print(f"Error Telegram getUpdates: {e}")
            return []

    async def procesar_comandos(self, updates):
        for update in updates:
            self.last_update_id = update["update_id"]
            if "message" not in update: continue
            
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").lower()
            
            print(f"Comando recibido: {text}")

            if text == "/start" or text == "/saludo":
                await self.send_message(chat_id, "Hola! Soy el Bot de Azotea v2.0 asincrónico.")
            
            elif text == "/estado":
                data = self.sensor_manager.obtener_todo()
                msg = "ESTADO ACTUAL\n"
                msg += f"Temp: {data['temperature']}C\n"
                msg += f"Hum: {data['humidity']}%\n"
                msg += f"Combustible: {data['fuel_percent']}%\n"
                msg += f"Voltaje: {data['voltage']}V\n"
                msg += f"WiFi: {self.wifi_manager.get_ip()}\n"
                
                # Obtener información del reinicio programado
                import time
                import ujson
                
                last_reboot = 0
                try:
                    with open('last_reboot.json', 'r') as f:
                        reboot_data = ujson.load(f)
                        last_reboot = reboot_data.get("last_reboot_timestamp", 0)
                except Exception:
                    pass
                
                current_tm = time.localtime()
                if current_tm[0] > 2025:
                    timezone_offset = getattr(config, 'TIMEZONE_OFFSET', -3)
                    if last_reboot > 0:
                        local_epoch = last_reboot + (timezone_offset * 3600)
                        tm = time.localtime(local_epoch)
                        fecha_str = "{:02d}/{:02d} {:02d}:{:02d}".format(tm[2], tm[1], tm[3], tm[4])
                        
                        proximo_epoch = last_reboot + (getattr(config, 'REBOOT_INTERVAL_DAYS', 3) * 24 * 3600)
                        local_proximo = proximo_epoch + (timezone_offset * 3600)
                        tm_p = time.localtime(local_proximo)
                        fecha_p_str = "{:02d}/{:02d} 03:00-05:00".format(tm_p[2], tm_p[1])
                        
                        msg += f"\nUltimo reinicio: {fecha_str}\nProx. reinicio: {fecha_p_str}"
                    else:
                        msg += "\nReinicio: Pendiente del primer ciclo"
                else:
                    msg += "\nReinicio: Esperando sinc. hora NTP"
                    
                await self.send_message(chat_id, msg)

            elif text == "/temp":
                temp, hum = self.sensor_manager.leer_dht()
                await self.send_message(chat_id, f"Temperatura: {temp}C\nHumedad: {hum}%")

            elif text == "/nivel":
                nivel, _ = self.sensor_manager.leer_combustible()
                await self.send_message(chat_id, f"Nivel de combustible: {nivel}%")

            elif text == "/mac":
                await self.send_message(chat_id, f"MAC: {self.wifi_manager.get_mac()}")

            elif text.startswith("/setbroker"):
                try:
                    new_broker = text.split(" ")[1]
                    if config.save_settings(broker=new_broker):
                        await self.send_message(chat_id, f"Broker actualizado: {new_broker}\nReiniciando para aplicar cambios...")
                        await asyncio.sleep(2)
                        machine.reset()
                    else:
                        await self.send_message(chat_id, "Error guardando la configuración.")
                except:
                    await self.send_message(chat_id, "Uso: /setbroker <url_del_broker>")

            elif text.startswith("/settopic"):
                try:
                    new_topic = text.split(" ")[1]
                    if config.save_settings(topic=new_topic):
                        await self.send_message(chat_id, f"Topico actualizado: {new_topic}\nReiniciando para aplicar cambios...")
                        await asyncio.sleep(2)
                        machine.reset()
                    else:
                        await self.send_message(chat_id, "Error guardando la configuración.")
                except:
                    await self.send_message(chat_id, "Uso: /settopic <nombre_del_topico>")

            elif text == "/help":
                msg = "COMANDOS:\n/estado - Resumen total\n/temp - Clima\n/nivel - Tanque\n/mac - ID Red\n/setbroker <url> - Cambiar MQTT\n/settopic <topic> - Cambiar Tópico\n/restart - Reiniciar"
                await self.send_message(chat_id, msg)

            elif text == "/restart":
                await self.send_message(chat_id, "Reiniciando equipo...")
                await asyncio.sleep(1)
                machine.reset()

    async def loop(self):
        """Tarea principal de polling del bot"""
        print("Bot de Telegram iniciado...")
        
        # Limpiar mensajes antiguos al arrancar para evitar bucles de reinicio
        try:
            print("Limpiando mensajes antiguos...")
            r = urequests.get(f"{self.url}/getUpdates?offset=-1", timeout=config.NETWORK_TIMEOUT)
            data = r.json()
            r.close()
            if data.get("ok") and data.get("result"):
                self.last_update_id = data["result"][0]["update_id"]
                print(f"Mensajes antiguos omitidos. ID actual: {self.last_update_id}")
        except Exception as e:
            print(f"Error limpiando mensajes: {e}")

        while True:
            if self.wifi_manager.is_connected():
                updates = await self.get_updates()
                if updates:
                    await self.procesar_comandos(updates)
            await asyncio.sleep(config.TELEGRAM_POLLING_INTERVAL)
