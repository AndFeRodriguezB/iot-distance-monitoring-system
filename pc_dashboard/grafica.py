import socket
import json
from datetime import datetime
import matplotlib.pyplot as plt
import time
import config

HOST = "0.0.0.0"
PORT = config.PC_PORT

distancias = []
plt.ion()
fig, ax = plt.subplots()

while True:
    try:
        print("Esperando datos desde Raspberry...")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(1)

        conn, addr = server.accept()
        print("Raspberry conectada:", addr)
        
        while True:
            data = conn.recv(1024)
            if not data:
                raise Exception("Conexión cerrada")
            
            mensajes = data.decode().split("\n")
            for mensaje in mensajes:
                if mensaje == "":
                    continue
                
                payload = json.loads(mensaje)
                packet = payload["pid"]
                ts = payload["ts"]
                distancia = payload["dist"]
                limite = payload["limite"]
                distancias.append(distancia)
                
                hora = datetime.fromtimestamp(ts)
                legible = hora.strftime("%Y-%m-%d %H:%M:%S")
                
                advertencia = limite * 0.5
                critico = limite
                
                print(
                    f"PacketID: {packet} |"
                    f"Hora: {legible} |"
                    f"Distancia: {distancia:f} cm"
                )
                if len(distancias) > 50:
                    distancias.pop(0)
                ax.clear()
                ax.plot(distancias)
                
                ax.axhspan(critico, 100, color="green", alpha=0.2)
                ax.axhspan(advertencia, critico, color="yellow", alpha=0.2)
                ax.axhspan(0, advertencia, color="red", alpha=0.2)
                ax.axhline(advertencia, linestyle="--")
                ax.axhline(critico, linestyle="--")
                
                ax.set_title("Distancia sensor en tiempo real")
                ax.set_ylabel("Distancia (cm)")
                ax.set_xlabel("Tiempo")
                
                plt.pause(0.01)
    except Exception as e:
        print("Conexión perdida con Raspberry:", e)
        try:
            conn.close()
        except:
            pass
        try:
            server.close()
        except:
            pass
        print("Esperando reconexión...")
        time.sleep(3)