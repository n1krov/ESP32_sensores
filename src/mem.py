"""
======================================================================
LIMPIADOR DE MEMORIA SIMPLE PARA ESP32
======================================================================
Usuario: n1krov
Fecha: 2025-10-15

Script básico para limpiar memoria sin dependencias externas
======================================================================
"""

import gc
import time
from machine import Pin

# LED para indicar actividad (opcional)
try:
    led = Pin(2, Pin.OUT)
    LED_AVAILABLE = True
except:
    LED_AVAILABLE = False

def blink(times=1):
    """Parpadeo simple para indicar actividad"""
    if LED_AVAILABLE:
        for _ in range(times):
            led.value(1)
            time.sleep(0.1)
            led.value(0)
            time.sleep(0.1)

def show_memory():
    """Muestra estado actual de memoria"""
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    mem_total = mem_free + mem_alloc
    usage_percent = (mem_alloc / mem_total) * 100
    
    print(f"Memoria libre: {mem_free:,} bytes")
    print(f"Memoria usada: {mem_alloc:,} bytes ({usage_percent:.1f}%)")
    print(f"Memoria total: {mem_total:,} bytes")
    
    return mem_free, mem_alloc

def clean_memory():
    """Limpia memoria y muestra resultado"""
    print("\n--- ANTES DE LIMPIAR ---")
    before_free, before_used = show_memory()
    
    print("\nLimpiando memoria...")
    blink(2)
    
    # Ejecutar garbage collection múltiples veces
    for i in range(3):
        gc.collect()
        time.sleep(0.1)
    
    print("\n--- DESPUÉS DE LIMPIAR ---")
    after_free, after_used = show_memory()
    
    # Calcular mejora
    freed_bytes = after_free - before_free
    
    print(f"\nRESULTADO:")
    print(f"Memoria liberada: {freed_bytes:,} bytes")
    
    if freed_bytes > 0:
        print("✓ Limpieza exitosa")
        blink(1)
    else:
        print("- No se liberó memoria adicional")
    
    return freed_bytes

def memory_status():
    """Devuelve estado simple de memoria"""
    mem_free = gc.mem_free()
    
    if mem_free < 5000:
        return "CRITICA"
    elif mem_free < 15000:
        return "BAJA"
    elif mem_free < 30000:
        return "NORMAL"
    else:
        return "ALTA"

def quick_clean():
    """Limpieza rápida sin prints detallados"""
    before = gc.mem_free()
    gc.collect()
    after = gc.mem_free()
    freed = after - before
    
    print(f"Limpieza: +{freed} bytes (total: {after:,})")
    return freed

def emergency_clean():
    """Limpieza agresiva de emergencia"""
    print("🚨 LIMPIEZA DE EMERGENCIA")
    
    for i in range(10):
        gc.collect()
        time.sleep(0.05)
        if i % 2 == 0:
            blink(1)
    
    mem_free = gc.mem_free()
    print(f"Memoria después de emergencia: {mem_free:,} bytes")
    
    return mem_free

def auto_clean_if_needed():
    """Limpia automáticamente si memoria está baja"""
    status = memory_status()
    mem_free = gc.mem_free()
    
    if status == "CRITICA":
        print(f"⚠️  MEMORIA CRITICA: {mem_free:,} bytes")
        emergency_clean()
        return True
    elif status == "BAJA":
        print(f"⚠️  MEMORIA BAJA: {mem_free:,} bytes")
        quick_clean()
        return True
    else:
        return False

def main():
    """Función principal para testing"""
    print("=" * 40)
    print("LIMPIADOR DE MEMORIA ESP32")
    print("=" * 40)
    
    # Mostrar estado inicial
    print("ESTADO INICIAL:")
    show_memory()
    print(f"Estado: {memory_status()}")
    
    # Limpiar memoria
    freed = clean_memory()
    
    # Mostrar estado final
    print(f"\nESTADO FINAL: {memory_status()}")
    print("=" * 40)

# Funciones de una línea para uso rápido
def m():
    """Mostrar memoria - función corta"""
    free = gc.mem_free()
    used = gc.mem_alloc()
    print(f"Libre: {free:,} | Usado: {used:,}")

def c():
    """Limpiar memoria - función corta"""
    before = gc.mem_free()
    gc.collect()
    after = gc.mem_free()
    print(f"Liberados: {after - before:+} bytes")

def s():
    """Estado de memoria - función corta"""
    print(f"Estado: {memory_status()} ({gc.mem_free():,} bytes)")

if __name__ == "__main__":
    main()