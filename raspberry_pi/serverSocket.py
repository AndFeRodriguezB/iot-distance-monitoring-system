import socket
import json
from gpiozero import LED
from datetime import datetime
import time
import subprocess
import threading
import config

verde = LED(17)
amarillo = LED(27)
rojo = LED(22)

limite = float(input("Ingrese la distancia limite en cm: "))

advertencia = limite * 0.5
critico = limite

print("Zona advertencia:", advertencia,"cm")
print("Zona critica:",critico,"cm")


HOST = "0.0.0.0"
PORT = config.ESP_PORT

estado_critico = False
alarma_run = False

def alarma():
	global estado_critico, alarma_run
	
	alarma_run = True
	
	while estado_critico:
		proceso = subprocess.Popen(["aplay","siren.wav"])
		
		while estado_critico and proceso.poll() is None:
			time.sleep(0.1)
		
		if not estado_critico:
			proceso.terminate()
	alarma_run = False
		
pc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
pc.connect((config.PC_IP, config.PC_PORT ))    #IP del pc

buffer = ""

while True:
	try:
		print("\nEsperando conexin de ESP32...")
		
		server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		server.bind((HOST, PORT))
		server.listen(1)

		conn, addr = server.accept()
		print("ESP conectada:", addr)
		conn.settimeout(5)
		
		while True:
			data = conn.recv(1024)
			
			if not data:
				break
			
			buffer += data.decode()
			
			while "\n" in buffer:
				mensaje, buffer = buffer.split("\n",1)
				
				if mensaje == "":
					continue
					
				payload = json.loads(mensaje)
				packet = payload["pid"]
				ts = payload["ts"]
				distancia = payload["dist"]
				
				hora = datetime.fromtimestamp(ts)
				legible = hora.strftime("%Y-%m-%d %H:%M:%S")
				
				print(
					f"packetID: {packet} | "
					f"Hora: {legible} |"
					f"Distancia: {distancia:.2f}cm"
				)
				payload["limite"] = limite
				pc.send((json.dumps(payload) + "\n").encode())
				
				if distancia > critico:
					print("Estado NORMAL")
					
					estado_critico = False
					verde.on()
					amarillo.off()
					rojo.off()

					
				elif distancia > advertencia:
					print("Estado ADVERTENCIA")
					
					estado_critico = False
					verde.off()
					amarillo.blink(on_time=0.5, off_time=0.5)
					rojo.off()

				
				else:
					print("Estado CRITICO")
					verde.off()
					amarillo.off()
					rojo.blink(on_time=0.2, off_time=0.2)
					estado_critico = True
						
					if not alarma_run:
						threading.Thread(target=alarma, daemon=True).start()
	except Exception as e:
		print("\nConexin perdida con ESP32:", e)
		print("Cerrando sockets...")
		try:
			conn.close()
		except:
			pass
		try:
			server.close()
		except:
			pass
		print("Esperando reconexion en 3 segundos...")
		time.sleep(3)
