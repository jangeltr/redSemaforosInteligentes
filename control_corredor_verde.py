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
# --- CONFIGURACIÓN DEL CONTROLADOR DE RED Y EMERGENCIA ---
# ------------------------------------------------------------------
UMBRAL_COCHES_ESPERANDO = 3
TIEMPO_MINIMO_EN_FASE = 5
FASE_PRINCIPAL_VERDE = "GGgrrrGGgrrr"
FASE_TRANSVERSAL_VERDE = "rrrGGgrrrGGg"

# --- NUEVA CONFIGURACIÓN DE EMERGENCIA ---
PASO_INICIO_EMERGENCIA = 50 # ¿En qué segundo de la simulación aparecerá la ambulancia?
VEHICULO_EMERGENCIA_ID = None # Usaremos esta variable para saber quién es la ambulancia
SEMAFOROS_EN_MODO_EMERGENCIA = set() # Un conjunto para saber qué semáforos estamos controlando

# ------------------------------------------------------------------
# --- SCRIPT PRINCIPAL ---
# ------------------------------------------------------------------
nombre_config_sumo = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", nombre_config_sumo, "--start", "--quit-on-end"]

print("Iniciando control con capacidad de respuesta a emergencias...")
traci.start(sumo_cmd)
print("Conexión establecida.")

lista_semaforos = traci.trafficlight.getIDList()
estado_semaforos = {} # Inicializamos la estructura de datos (igual que antes)
# ... (código de inicialización de estado_semaforos igual que en el script anterior) ...
for semaforo_id in lista_semaforos:
    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
    carriles_transversales = []
    for i, letra_estado in enumerate(FASE_PRINCIPAL_VERDE):
        if letra_estado == 'r':
            carriles_transversales.append(carriles_controlados[i])
    estado_semaforos[semaforo_id] = {
        "carriles_transversales": carriles_transversales, "tiempo_en_fase": 0
    }
    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)


paso = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    paso += 1

    # --- ETAPA 1: INICIAR LA EMERGENCIA ---
    if paso == PASO_INICIO_EMERGENCIA:
        # Elegimos un vehículo al azar para que sea nuestra ambulancia
        lista_vehiculos_activos = traci.vehicle.getIDList()
        if lista_vehiculos_activos:
            VEHICULO_EMERGENCIA_ID = lista_vehiculos_activos[0]
            print(f"\n¡¡¡ EMERGENCIA INICIADA !!! Vehículo '{VEHICULO_EMERGENCIA_ID}' es ahora la ambulancia.")
            traci.vehicle.setColor(VEHICULO_EMERGENCIA_ID, (255, 0, 0, 255)) # Color Rojo
            traci.vehicle.setVehicleClass(VEHICULO_EMERGENCIA_ID, "emergency")
            traci.vehicle.setSpeedMode(VEHICULO_EMERGENCIA_ID, 0) # Ignora límites de velocidad
            traci.vehicle.setLaneChangeMode(VEHICULO_EMERGENCIA_ID, 0) # Puede cambiar de carril libremente

    # --- LÓGICA PRINCIPAL: Decidimos si operamos en modo normal o de emergencia ---
    if VEHICULO_EMERGENCIA_ID and VEHICULO_EMERGENCIA_ID in traci.vehicle.getIDList():
        # --- ETAPA 2: MANTENER EL CORREDOR VERDE ---
        
        # Obtenemos la ruta de la ambulancia
        ruta_ambulancia = traci.vehicle.getRoute(VEHICULO_EMERGENCIA_ID)
        calle_actual_ambulancia = traci.vehicle.getRoadID(VEHICULO_EMERGENCIA_ID)
        
        # Encontramos el índice de la calle actual en la ruta
        try:
            indice_calle_actual = ruta_ambulancia.index(calle_actual_ambulancia)
        except ValueError:
            continue # Si la ambulancia está en una transición, puede no estar en la lista, saltamos este paso

        # Miramos 2 intersecciones hacia adelante
        for i in range(indice_calle_actual, min(indice_calle_actual + 3, len(ruta_ambulancia))):
            calle = ruta_ambulancia[i]
            # La intersección (y el semáforo) está al final de la calle
            # nodo_semaforo = traci.edge.getToNode(calle)
            id_nodo_semaforo = traci.edge.getParameter(calle, "to")
            
            # Comprobamos si el nodo es un semáforo
            #if nodo_semaforo.getID() in lista_semaforos:
            if id_nodo_semaforo in lista_semaforos:
                semaforo_id = id_nodo_semaforo
                carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
                estado_seguro = list("r" * len(carriles_controlados)) # Todo en rojo por defecto

                # Ponemos en verde SOLO los carriles que la ambulancia usará en esa intersección
                links = traci.lane.getLinks(calle + "_0") # Asumimos que la ambulancia va por el carril 0
                for link in links:
                    carril_siguiente = link[0]
                    if carril_siguiente in carriles_controlados:
                        indice_luz = carriles_controlados.index(carril_siguiente)
                        estado_seguro[indice_luz] = "G"

                # Aplicamos el estado de emergencia y lo recordamos
                traci.trafficlight.setRedYellowGreenState(semaforo_id, "".join(estado_seguro))
                SEMAFOROS_EN_MODO_EMERGENCIA.add(semaforo_id)

        # --- ETAPA 3: RESTAURAR LA NORMALIDAD ---
        # Restauramos semáforos que ya no están en la ruta cercana de la ambulancia
        semaforos_a_restaurar = SEMAFOROS_EN_MODO_EMERGENCIA.copy()
        for semaforo_id in semaforos_a_restaurar:
             # Si un semáforo ya no está en la ruta inmediata, lo liberamos
             if semaforo_id not in [traci.edge.getToNode(ruta_ambulancia[i]).getID() for i in range(indice_calle_actual, min(indice_calle_actual + 3, len(ruta_ambulancia)))]:
                 SEMAFOROS_EN_MODO_EMERGENCIA.remove(semaforo_id)


    else:
        # --- MODO NORMAL DE OPERACIÓN ---
        # La lógica de control inteligente para todos los semáforos que NO están en modo emergencia
        for semaforo_id in lista_semaforos:
            if semaforo_id not in SEMAFOROS_EN_MODO_EMERGENCIA:
                # ... (Aquí va exactamente la misma lógica de tu script anterior `control_inteligente_todos.py`) ...
                estado_semaforos[semaforo_id]["tiempo_en_fase"] += 1
                coches_esperando = sum(traci.lane.getLastStepHaltingNumber(carril) for carril in estado_semaforos[semaforo_id]["carriles_transversales"])
                estado_actual = traci.trafficlight.getRedYellowGreenState(semaforo_id)
                if (estado_actual == FASE_PRINCIPAL_VERDE and coches_esperando >= UMBRAL_COCHES_ESPERANDO and estado_semaforos[semaforo_id]["tiempo_en_fase"] >= TIEMPO_MINIMO_EN_FASE):
                    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_TRANSVERSAL_VERDE)
                    estado_semaforos[semaforo_id]["tiempo_en_fase"] = 0
                elif (estado_actual == FASE_TRANSVERSAL_VERDE and coches_esperando == 0 and estado_semaforos[semaforo_id]["tiempo_en_fase"] >= TIEMPO_MINIMO_EN_FASE):
                    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)
                    estado_semaforos[semaforo_id]["tiempo_en_fase"] = 0
    
    time.sleep(0.1)

print("\nSimulación finalizada.")
traci.close()