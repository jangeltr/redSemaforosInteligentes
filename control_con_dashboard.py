# control_con_dashboard.py (Versión Mejorada para Dashboard)
import os
import sys
import time
import json

# --- Bloque de configuración de SUMO ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")
import traci

# --- CONFIGURACIÓN ---
# ... (Toda la configuración es igual que en el script anterior) ...
UMBRAL_COCHES_ESPERANDO = 3
TIEMPO_MINIMO_EN_FASE = 5
FASE_PRINCIPAL_VERDE = "GGgrrrGGgrrr"
FASE_TRANSVERSAL_VERDE = "rrrGGgrrrGGg"
VEHICULO_EMERGENCIA_ID = None
SEMAFOROS_EN_MODO_EMERGENCIA = set()
total_vehiculos_llegados = 0 # NUEVO: Contador de rendimiento

# --- SCRIPT PRINCIPAL ---
nombre_config_sumo = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start", "--quit-on-end"]

print("Iniciando control con Dashboard v2.0...")
traci.start(sumo_cmd)
print("Conexión establecida.")

# ... (Toda la inicialización de estado_semaforos es igual que antes) ...
lista_semaforos = traci.trafficlight.getIDList()
estado_semaforos = {}
for semaforo_id in lista_semaforos:
    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
    carriles_transversales = [carriles_controlados[i] for i, l in enumerate(FASE_PRINCIPAL_VERDE) if l == 'r']
    estado_semaforos[semaforo_id] = { "carriles_transversales": carriles_transversales, "tiempo_en_fase": 0 }
    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)

paso = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    paso += 1

    # NUEVO: Actualizar el contador de vehículos que han llegado
    llegados_ahora = traci.simulation.getArrivedIDList()
    total_vehiculos_llegados += len(llegados_ahora)

    # --- Lógica de emergencia y control de semáforos (exactamente igual que antes) ---
    # ... (Pega aquí toda la lógica desde 'if not VEHICULO_EMERGENCIA_ID...' hasta el final de la sección 'else') ...
    if not VEHICULO_EMERGENCIA_ID and os.path.exists("emergency_request.txt"):
        # ... (código de activar emergencia) ...
        pass
    if VEHICULO_EMERGENCIA_ID and VEHICULO_EMERGENCIA_ID in traci.vehicle.getIDList():
        # ... (código del corredor verde) ...
        pass
    else:
        # ... (código de control inteligente normal) ...
        pass

    # --- Escribir estado MEJORADO a JSON para el dashboard ---
    if paso % 5 == 0:
        lista_vehiculos = traci.vehicle.getIDList()
        vehiculos_parados_manual = 0
        tiempo_espera_total = 0
        for vehiculo_id in lista_vehiculos:
            velocidad = traci.vehicle.getSpeed(vehiculo_id)
            if velocidad < 0.1:
                vehiculos_parados_manual += 1
            tiempo_espera_total += traci.vehicle.getAccumulatedWaitingTime(vehiculo_id)
        
        tiempo_espera_promedio = tiempo_espera_total / len(lista_vehiculos) if lista_vehiculos else 0

        estado_actual_json = {
            "paso_simulacion": paso,
            "vehiculos_activos": len(lista_vehiculos),
            "vehiculos_parados": vehiculos_parados_manual,
            "emergencia_activa": VEHICULO_EMERGENCIA_ID is not None and VEHICULO_EMERGENCIA_ID in lista_vehiculos,
            "vehiculos_llegados_total": total_vehiculos_llegados,
            "tiempo_espera_promedio": round(tiempo_espera_promedio, 2)
        }
        with open("status.json", "w") as f:
            json.dump(estado_actual_json, f)

    time.sleep(0.1)

traci.close()