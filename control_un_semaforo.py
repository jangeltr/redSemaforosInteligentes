
# Control del primer semaforo el J15
import os
import sys
import time

# --- Bloque de configuración de SUMO (igual que antes) ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")

import traci

# ------------------------------------------------------------------
# --- CONFIGURACIÓN DEL CONTROLADOR ---
# ------------------------------------------------------------------

# Elige el ID del semáforo que quieres controlar desde Python
SEMAFORO_A_CONTROLAR = "J5"  # <--- ¡ASEGÚRATE DE QUE ESTE ID EXISTA EN TU SIMULACIÓN!

# Definimos los estados (las fases) que queremos para nuestro semáforo.
# Basado en tu ejemplo, una fase permite el tráfico en una dirección y la otra en la dirección transversal.
FASE_A_ESTADO = "GGgrrrGGgrrr"  # Verde para la vía principal
FASE_B_ESTADO = "rrrGGgrrrGGg"  # Verde para la vía transversal (la 'g' minúscula es para el giro)

# Definimos cuánto tiempo (en segundos de simulación) durará cada fase
TIEMPO_FASE_A = 10
TIEMPO_FASE_B = 10

# ------------------------------------------------------------------
# --- SCRIPT PRINCIPAL ---
# ------------------------------------------------------------------

nombre_config_sumo = "calles.sumocfg" # <--- CAMBIA ESTO si tu archivo de config se llama diferente
sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start"]

print(f"Iniciando conexión para controlar el semáforo '{SEMAFORO_A_CONTROLAR}'...")
traci.start(sumo_cmd)
print("Conexión establecida.")

# Variables para llevar la cuenta de nuestro ciclo de control
fase_actual = "A"
tiempo_en_fase = 0

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    
    # Incrementamos el contador de tiempo en la fase actual
    tiempo_en_fase += 1

    # --- Lógica de Decisión (Nivel 1 de Inteligencia: Basada en Reglas) ---
    if fase_actual == "A" and tiempo_en_fase >= TIEMPO_FASE_A:
        # El tiempo de la Fase A ha terminado. Cambiamos a Fase B.
        traci.trafficlight.setRedYellowGreenState(SEMAFORO_A_CONTROLAR, FASE_B_ESTADO)
        fase_actual = "B"
        tiempo_en_fase = 0
        print(f"TIEMPO CUMPLIDO -> Cambiando a Fase B para '{SEMAFORO_A_CONTROLAR}'")

    elif fase_actual == "B" and tiempo_en_fase >= TIEMPO_FASE_B:
        # El tiempo de la Fase B ha terminado. Cambiamos de nuevo a Fase A.
        traci.trafficlight.setRedYellowGreenState(SEMAFORO_A_CONTROLAR, FASE_A_ESTADO)
        fase_actual = "A"
        tiempo_en_fase = 0
        print(f"TIEMPO CUMPLIDO -> Cambiando a Fase A para '{SEMAFORO_A_CONTROLAR}'")
    
    # La pausa para poder ver la simulación
    time.sleep(0.1)

print("\nSimulación finalizada.")
traci.close()