# Muestra una lista de semaforos al inicio de la simulación
import os
import sys
import time

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")

import traci

# ------------------------------------------------------------------
# EL SCRIPT PRINCIPAL
# ------------------------------------------------------------------

# Asegúrate de que este nombre coincide con el archivo de tu compañero
nombre_config_sumo = "calles.sumocfg" # <--- CAMBIA ESTO SI ES NECESARIO

sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start"]

print("Iniciando la conexión con SUMO...")
traci.start(sumo_cmd)
print("Conexión establecida.")



lista_semaforos = traci.trafficlight.getIDList()
print(f"Semáforos detectados en la simulación: {lista_semaforos}")

# NUEVO: Imprimir el mapeo de carriles para el primer semáforo de la lista
if len(lista_semaforos) > 0:
    semaforo_ejemplo_id = lista_semaforos[0]
    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_ejemplo_id)
    print(f"\n--- Mapeo de Carriles para el Semáforo '{semaforo_ejemplo_id}' ---")
    for i, carril_id in enumerate(carriles_controlados):
        print(f"  Índice {i} -> Letra en la posición {i+1} -> Corresponde al Carril: {carril_id}")
    print("--------------------------------------------------")



# NUEVO: Obtener la lista de todos los semáforos UNA SOLA VEZ al principio
lista_semaforos = traci.trafficlight.getIDList()
print(f"Semáforos detectados en la simulación: {lista_semaforos}")

paso = 0

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    time.sleep(0.05) 
    
    print(f"\n--- Paso de Simulación: {paso} ---")

    # ----- INFORMACIÓN DE VEHÍCULOS (como antes) -----
    lista_vehiculos = traci.vehicle.getIDList()
    print(f"Vehículos activos: {len(lista_vehiculos)}")

    # ----- NUEVO: INFORMACIÓN DE SEMÁFOROS -----
    print("--- Estado de los Semáforos ---")
    for semaforo_id in lista_semaforos:
        # Para cada semáforo, obtenemos su estado actual
        estado = traci.trafficlight.getRedYellowGreenState(semaforo_id)
        print(f"  -> Semáforo '{semaforo_id}': Estado = {estado}")
        
    paso += 1

print("\nSimulación finalizada. No hay más vehículos.")
traci.close()