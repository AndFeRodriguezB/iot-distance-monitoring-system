import network
import config
import time
import ntptime
import socket
import machine
import json


trig = machine.Pin(5, machine.Pin.OUT)
echo = machine.Pin(18, machine.Pin.IN)

def conectar_rasp():
    while True:
        try:
            print("Intentando conectar con Raspberry...")
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((config.RASP_IP, config.ESP_PORT))
            
            print("Conectado al servidor")
            return s
        except Exception as e:
            print("No se pudo conectar:",e )
            print("Reintentando en 5 segundos...")
            time.sleep(5)
    
def readSen():
    trig.value(0)
    time.sleep_us(2)
    
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    timout = 30000
    st_wait = time.ticks_us()
    
    while echo.value() == 0:
        start = time.ticks_us()
        if time.ticks_diff(time.ticks_us(), st_wait) > timout:
            return None
    st_wait2 = time.ticks_us()
    
    while echo.value() == 1:
        end = time.ticks_us()
        if time.ticks_diff(time.ticks_us(), st_wait2) > timout:
            return None
    
    duration = time.ticks_diff(end, start)
    
    d = (duration * 0.0343) / 2
    
    return d

wf = network.WLAN(network.STA_IF)
wf.active(True)
print("Conectando a Wifi...")
wf.connect(config.WIFI_SSIDI, config.WIFI_PASSWORD)  # Red Wifi

for i in range(20):
    if wf.isconnected():
        break
    time.sleep(1)
    
print("Conectado a:", wf.ifconfig())

print("Sincronizando hora...")

try:
    ntptime.settime()
    print("Hora sincronizada correctamente")
except:
    print("Error sincronizando hora")

print("Conectando al servidor...")

s  = conectar_rasp()
    
pid = 0
    
while True:
    d = readSen()
    
    if d is None:
        print("Error leyendo Sensor")
        
    if d is not None:
        payload = {
            "pid": pid,
            "ts" : int(time.time()) + 946684800,
            "dist": round(d,2)
        }
            
        message = json.dumps(payload) + "\n"
            
        try:
            s.send(message.encode())
            print("Enviado:", message.strip())
            pid += 1
            
        except Exception as e:
            print("Conexión perdida con Raspberry:", e)
            try:
                s.close()
            except:
                pass
            print("Intentando reconectar...")
            s=conectar_rasp()
        
    time.sleep(1)


    