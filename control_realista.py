import os
import sys
import time

# --- Bloque de configuración de SUMO ---
# ... (igual que en los scripts anteriores) ...
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")
import traci

# ------------------------------------------------------------------
# --- CONFIGURACIÓN DEL CONTROLADOR REALISTA ---
# ------------------------------------------------------------------
UMBRAL_COCHES_ESPERANDO = 3
TIEMPO_MINIMO_EN_FASE = 10 # Aumentamos para ver mejor el efecto
TIEMPO_LUZ_AMARILLA = 3 # Duración de la fase de transición

# Definimos los 4 estados posibles para un semáforo
FASE_PRINCIPAL_VERDE = "GGgrrrGGgrrr"
FASE_PRINCIPAL_AMARILLO = "yyyrrryyyrrr" # Amarillo para la vía principal
FASE_TRANSVERSAL_VERDE = "rrrGGgrrrGGg"
FASE_TRANSVERSAL_AMARILLO = "rrryyyrrryyy" # Amarillo para la vía transversal

# ------------------------------------------------------------------
# --- SCRIPT PRINCIPAL ---
# ------------------------------------------------------------------
nombre_config_sumo = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start"]

print("Iniciando control REALISTA para TODOS los semáforos...")
traci.start(sumo_cmd)
print("Conexión establecida.")

lista_semaforos = traci.trafficlight.getIDList()

estado_semaforos = {}
for semaforo_id in lista_semaforos:
    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
    carriles_transversales = [carriles_controlados[i] for i, l in enumerate(FASE_PRINCIPAL_VERDE) if l == 'r']
    
    estado_semaforos[semaforo_id] = {
        "carriles_transversales": carriles_transversales,
        "tiempo_en_fase": 0,
        "fase_actual": "PRINCIPAL_VERDE" # Nuevo: un estado más explícito
    }
    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    for semaforo_id in lista_semaforos:
        info_semaforo = estado_semaforos[semaforo_id]
        info_semaforo["tiempo_en_fase"] += 1
        
        # --- Lógica de la Máquina de Estados ---
        
        # 1. Si está en VERDE PRINCIPAL, revisamos si debemos cambiar
        if info_semaforo["fase_actual"] == "PRINCIPAL_VERDE" and info_semaforo["tiempo_en_fase"] > TIEMPO_MINIMO_EN_FASE:
            coches_esperando = sum(traci.lane.getLastStepHaltingNumber(c) for c in info_semaforo["carriles_transversales"])
            if coches_esperando >= UMBRAL_COCHES_ESPERANDO:
                traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_AMARILLO)
                info_semaforo["fase_actual"] = "PRINCIPAL_AMARILLO"
                info_semaforo["tiempo_en_fase"] = 0
                print(f"SEMAFORO '{semaforo_id}': Congestión detectada. Transición a AMARILLO.")

        # 2. Si está en AMARILLO (viniendo de principal), esperamos y cambiamos a verde transversal
        elif info_semaforo["fase_actual"] == "PRINCIPAL_AMARILLO" and info_semaforo["tiempo_en_fase"] >= TIEMPO_LUZ_AMARILLA:
            traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_TRANSVERSAL_VERDE)
            info_semaforo["fase_actual"] = "TRANSVERSAL_VERDE"
            info_semaforo["tiempo_en_fase"] = 0

        # 3. Si está en VERDE TRANSVERSAL, revisamos si debemos volver
        elif info_semaforo["fase_actual"] == "TRANSVERSAL_VERDE" and info_semaforo["tiempo_en_fase"] > TIEMPO_MINIMO_EN_FASE:
            coches_esperando = sum(traci.lane.getLastStepHaltingNumber(c) for c in info_semaforo["carriles_transversales"])
            if coches_esperando == 0:
                traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_TRANSVERSAL_AMARILLO)
                info_semaforo["fase_actual"] = "TRANSVERSAL_AMARILLO"
                info_semaforo["tiempo_en_fase"] = 0
                print(f"SEMAFORO '{semaforo_id}': Vía despejada. Transición a AMARILLO.")
        
        # 4. Si está en AMARILLO (viniendo de transversal), esperamos y volvemos a verde principal
        elif info_semaforo["fase_actual"] == "TRANSVERSAL_AMARILLO" and info_semaforo["tiempo_en_fase"] >= TIEMPO_LUZ_AMARILLA:
            traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)
            info_semaforo["fase_actual"] = "PRINCIPAL_VERDE"
            info_semaforo["tiempo_en_fase"] = 0
            
    time.sleep(0.1)

traci.close()