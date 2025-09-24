import os
import sys
import time

# --- Bloque de configuración de SUMO ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")
# ... (igual que antes) ...
import traci

# ------------------------------------------------------------------
# --- CONFIGURACIÓN DEL CONTROLADOR DE RED ---
# ------------------------------------------------------------------
UMBRAL_COCHES_ESPERANDO = 3
TIEMPO_MINIMO_EN_FASE = 5 # Nuevo: Evita que el semáforo cambie demasiado rápido

# Definimos los estados de las fases. Asumimos que todos los semáforos tienen una estructura similar.
FASE_PRINCIPAL_VERDE = "GGgrrrGGgrrr"
FASE_TRANSVERSAL_VERDE = "rrrGGgrrrGGg"

# ------------------------------------------------------------------
# --- SCRIPT PRINCIPAL ---
# ------------------------------------------------------------------
nombre_config_sumo = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start"]

print("Iniciando control INTELIGENTE para TODOS los semáforos...")
traci.start(sumo_cmd)
print("Conexión establecida.")

lista_semaforos = traci.trafficlight.getIDList()
print(f"Semáforos a controlar: {lista_semaforos}")

# --- ESTRUCTURA DE DATOS PARA GESTIONAR TODOS LOS SEMÁFOROS ---
estado_semaforos = {}
for semaforo_id in lista_semaforos:
    # Obtenemos los carriles que corresponden a la vía transversal para este semáforo
    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
    carriles_transversales = []
    for i, letra_estado in enumerate(FASE_PRINCIPAL_VERDE):
        if letra_estado == 'r':
            carriles_transversales.append(carriles_controlados[i])
    
    # Inicializamos el estado para cada semáforo
    estado_semaforos[semaforo_id] = {
        "carriles_transversales": carriles_transversales,
        "tiempo_en_fase": 0
    }
    # Ponemos todos los semáforos en la fase principal al inicio
    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)

# --- BUCLE PRINCIPAL DE SIMULACIÓN ---
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    # --- LÓGICA DE DECISIÓN PARA CADA SEMÁFORO ---
    for semaforo_id in lista_semaforos:
        
        # Incrementamos el tiempo que lleva este semáforo en su fase actual
        estado_semaforos[semaforo_id]["tiempo_en_fase"] += 1

        # Contamos los coches esperando en la vía transversal de ESTE semáforo
        coches_esperando = 0
        for carril in estado_semaforos[semaforo_id]["carriles_transversales"]:
            coches_esperando += traci.lane.getLastStepHaltingNumber(carril)

        # Obtenemos el estado actual de ESTE semáforo
        estado_actual = traci.trafficlight.getRedYellowGreenState(semaforo_id)

        # Aplicamos la lógica de decisión
        # Si está en fase principal, hay suficientes coches esperando Y ha pasado un tiempo mínimo...
        if (estado_actual == FASE_PRINCIPAL_VERDE and 
            coches_esperando >= UMBRAL_COCHES_ESPERANDO and
            estado_semaforos[semaforo_id]["tiempo_en_fase"] >= TIEMPO_MINIMO_EN_FASE):
            
            traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_TRANSVERSAL_VERDE)
            estado_semaforos[semaforo_id]["tiempo_en_fase"] = 0 # Reiniciamos el contador
            print(f"SEMAFORO '{semaforo_id}': Congestión detectada. Cambiando a fase transversal.")

        # Si está en fase transversal, no hay coches esperando Y ha pasado un tiempo mínimo...
        elif (estado_actual == FASE_TRANSVERSAL_VERDE and 
              coches_esperando == 0 and
              estado_semaforos[semaforo_id]["tiempo_en_fase"] >= TIEMPO_MINIMO_EN_FASE):
            
            traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)
            estado_semaforos[semaforo_id]["tiempo_en_fase"] = 0 # Reiniciamos el contador
            print(f"SEMAFORO '{semaforo_id}': Vía despejada. Volviendo a fase principal.")

    time.sleep(0.1)

print("\nSimulación finalizada.")
traci.close()