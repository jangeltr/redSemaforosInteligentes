import os
import sys
import time

# --- Bloque de configuración de SUMO ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")

import traci

# ------------------------------------------------------------------
# --- CONFIGURACIÓN DEL CONTROLADOR INTELIGENTE ---
# ------------------------------------------------------------------

SEMAFORO_A_CONTROLAR = "J15"
FASE_PRINCIPAL_VERDE = "GGgrrrGGgrrr"  # Verde para la vía principal
FASE_TRANSVERSAL_VERDE = "rrrGGgrrrGGg"  # Verde para la vía transversal

# NUEVO: Límite de coches. Si más de X coches esperan, cambiamos la luz.
UMBRAL_COCHES_ESPERANDO = 3

# ------------------------------------------------------------------
# --- SCRIPT PRINCIPAL ---
# ------------------------------------------------------------------

nombre_config_sumo = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start"]

print(f"Iniciando control INTELIGENTE para el semáforo '{SEMAFORO_A_CONTROLAR}'...")
traci.start(sumo_cmd)
print("Conexión establecida.")

# Obtenemos los carriles controlados por nuestro semáforo
carriles_controlados = traci.trafficlight.getControlledLanes(SEMAFORO_A_CONTROLAR)

# Identificamos cuáles carriles corresponden a la vía transversal (los que están en rojo en la fase principal)
# Usamos un truco: si la letra en el estado es 'r', ese carril es de la vía transversal.
carriles_transversales = []
for i, letra_estado in enumerate(FASE_PRINCIPAL_VERDE):
    if letra_estado == 'r':
        carriles_transversales.append(carriles_controlados[i])
print(f"Carriles transversales (rojos) detectados: {carriles_transversales}")

# El semáforo empieza en la fase principal
traci.trafficlight.setRedYellowGreenState(SEMAFORO_A_CONTROLAR, FASE_PRINCIPAL_VERDE)

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    # --- Lógica de Decisión INTELIGENTE ---

    # 1. Contamos cuántos coches están parados en la luz roja (vía transversal)
    coches_esperando = 0
    for carril in carriles_transversales:
        coches_esperando += traci.lane.getLastStepHaltingNumber(carril)
    
    print(f"Paso actual: Coches esperando en la luz roja de '{SEMAFORO_A_CONTROLAR}': {coches_esperando}")

    # 2. Comparamos con nuestro umbral para tomar una decisión
    estado_actual = traci.trafficlight.getRedYellowGreenState(SEMAFORO_A_CONTROLAR)

    # Si estamos en la fase principal Y hay suficientes coches esperando...
    if estado_actual == FASE_PRINCIPAL_VERDE and coches_esperando >= UMBRAL_COCHES_ESPERANDO:
        # ...cambiamos a la fase transversal para darles paso.
        print(f"¡CONGESTIÓN DETECTADA! -> Cambiando a fase transversal.")
        traci.trafficlight.setRedYellowGreenState(SEMAFORO_A_CONTROLAR, FASE_TRANSVERSAL_VERDE)
    
    # Si estamos en la fase transversal Y YA NO hay coches esperando...
    elif estado_actual == FASE_TRANSVERSAL_VERDE and coches_esperando == 0:
        # ...volvemos a la fase principal para no detener el tráfico principal innecesariamente.
        print(f"VÍA TRANSVERSAL DESPEJADA -> Volviendo a fase principal.")
        traci.trafficlight.setRedYellowGreenState(SEMAFORO_A_CONTROLAR, FASE_PRINCIPAL_VERDE)

    time.sleep(0.2) # Ralentizamos un poco para poder observar mejor

print("\nSimulación finalizada.")
traci.close()