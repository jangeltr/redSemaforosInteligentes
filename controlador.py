# Abre y ejecuta el modelo hecho por tu compañero
# 1. Importaciones de librerías estándar de Python
import os
import sys
import time # NUEVA LÍNEA: Importamos la librería para manejar el tiempo

# 2. Manipulación del sistema: Asegurarnos de que Python conozca la ruta de SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")

# 3. Ahora que la ruta es conocida, importamos la librería de SUMO
import traci

# ------------------------------------------------------------------
# EL SCRIPT PRINCIPAL
# ------------------------------------------------------------------

sumo_cmd = ["sumo-gui", "-c", "calles.sumocfg", "--start"]

print("Iniciando la conexión con SUMO...")
traci.start(sumo_cmd)
print("Conexión establecida.")

paso = 0

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    
    # NUEVA LÍNEA: Hacemos una pausa de 0.05 segundos en el mundo real
    time.sleep(0.05) 

    lista_vehiculos = traci.vehicle.getIDList()
    
    print(f"--- Paso de Simulación: {paso} ---")
    print(f"Vehículos activos: {lista_vehiculos}")

    for coche_id in lista_vehiculos:
        posicion = traci.vehicle.getPosition(coche_id)
        velocidad = traci.vehicle.getSpeed(coche_id)
        print(f"  -> Vehículo '{coche_id}': Posición={posicion}, Velocidad={round(velocidad * 3.6, 2)} km/h")
        
    paso += 1

print("\nSimulación finalizada. No hay más vehículos.")
traci.close()