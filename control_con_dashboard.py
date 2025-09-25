# control_con_dashboard.py (Versión Corregida y Completa)
import os
import sys
import time
import json

# --- Nos aseguramos de estar en el directorio correcto ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(SCRIPT_DIR)
except Exception as e:
    print(f"Error al cambiar el directorio de trabajo: {e}")
    sys.exit(1)

# --- Bloque de configuración de SUMO ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable de entorno 'SUMO_HOME'")
import traci

# ------------------------------------------------------------------
# --- CONFIGURACIÓN DE LA DEMO ---
# ------------------------------------------------------------------
UMBRAL_COCHES_ESPERANDO = 5
TIEMPO_MINIMO_EN_FASE = 8
TIEMPO_LUZ_AMARILLA = 3
FASE_PRINCIPAL_VERDE = "GGgrrrGGgrrr"
FASE_PRINCIPAL_AMARILLO = "yyyrrryyyrrr"
FASE_TRANSVERSAL_VERDE = "rrrGGgrrrGGg"
FASE_TRANSVERSAL_AMARILLO = "rrryyyrrryyy"

# --- Variables de estado del sistema ---
VEHICULO_EMERGENCIA_ID = None
SEMAFOROS_EN_MODO_EMERGENCIA = set()
total_vehiculos_llegados = 0
semaforos_en_transicion = {}

# --- CONFIGURACIÓN DE MISIÓN DE EMERGENCIA ---
# ¡¡¡IMPORTANTE!!! Asegúrate de que estos IDs de calles (edges) existen en tu mapa
CALLE_INICIO_EMERGENCIA = "-E21"
CALLE_FIN_EMERGENCIA = "E24"

# ------------------------------------------------------------------
# --- SCRIPT PRINCIPAL ---
# ------------------------------------------------------------------
SUMO_CONFIG_FILENAME = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG_FILENAME, "--start", "--quit-on-end"]

print("Iniciando control con Dashboard v2.1 (Corregido)...")
traci.start(sumo_cmd)
print("Conexión establecida.")

# --- Inicialización de la estructura de datos para todos los semáforos ---
lista_semaforos = traci.trafficlight.getIDList()
estado_semaforos = {}
for semaforo_id in lista_semaforos:
    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
    # Identificar carriles transversales para la lógica inteligente
    carriles_principales_indices = {i for i, l in enumerate(FASE_PRINCIPAL_VERDE) if l.lower() == 'g'}
    carriles_transversales_reales = [lane for i, lane in enumerate(carriles_controlados) if i not in carriles_principales_indices]
    
    estado_semaforos[semaforo_id] = {
        "carriles_transversales": carriles_transversales_reales,
        "tiempo_en_fase": 0,
        "fase_actual": "PRINCIPAL_VERDE"
    }
    traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_VERDE)

paso = 0
try:
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        paso += 1

        llegados_ahora = traci.simulation.getArrivedIDList()
        total_vehiculos_llegados += len(llegados_ahora)

        # --- Lógica de activación de emergencia desde el Dashboard ---
        if not VEHICULO_EMERGENCIA_ID and os.path.exists("emergency_request.txt"):
            os.remove("emergency_request.txt")
            
            id_ambulancia = f"ambulancia_{paso}"
            id_ruta = f"ruta_ambulancia_{paso}"
            
            try:
                # Asegúrate de que la ruta entre inicio y fin es válida
                traci.route.add(id_ruta, [CALLE_INICIO_EMERGENCIA, CALLE_FIN_EMERGENCIA])
                traci.vehicle.add(id_ambulancia, id_ruta, typeID="AMBULANCIA")
                # Establecer modos para que ignore semáforos y cambie de carril libremente
                traci.vehicle.setSpeedMode(id_ambulancia, 31) # Ignora límites de velocidad y semáforos
                traci.vehicle.setLaneChangeMode(id_ambulancia, 512) # Permite cambios de carril estratégicos
                
                VEHICULO_EMERGENCIA_ID = id_ambulancia
                print(f"\n¡¡¡ MISIÓN DE EMERGENCIA CREADA !!! Despachando ambulancia '{VEHICULO_EMERGENCIA_ID}'.")
                
            except traci.TraCIException as e:
                print(f"Error al crear la misión de emergencia: {e}. ¿Son correctas las calles de inicio/fin?")
                VEHICULO_EMERGENCIA_ID = None

        # --- Lógica de Control Principal ---
        if VEHICULO_EMERGENCIA_ID and VEHICULO_EMERGENCIA_ID in traci.vehicle.getIDList():
            # --- MODO EMERGENCIA: CORREDOR VERDE ---
            # (Esta sección es la del script funcional y ahora está integrada)
            ruta_ambulancia = traci.vehicle.getRoute(VEHICULO_EMERGENCIA_ID)
            calle_actual_ambulancia = traci.vehicle.getRoadID(VEHICULO_EMERGENCIA_ID)
            try:
                indice_calle_actual = ruta_ambulancia.index(calle_actual_ambulancia)
            except ValueError:
                continue
            semaforos_en_ruta_cercana = set()
            for i in range(indice_calle_actual, min(indice_calle_actual + 3, len(ruta_ambulancia))):
                calle = ruta_ambulancia[i]
                id_nodo_semaforo = traci.edge.getParameter(calle, "to")
                if id_nodo_semaforo in lista_semaforos:
                    semaforo_id = id_nodo_semaforo
                    semaforos_en_ruta_cercana.add(semaforo_id)
                    carriles_controlados = traci.trafficlight.getControlledLanes(semaforo_id)
                    estado_seguro = list("r" * len(carriles_controlados))
                    try:
                        links = traci.lane.getLinks(calle + "_0")
                        for link in links:
                            carril_siguiente = link[0]
                            if carril_siguiente in carriles_controlados:
                                indice_luz = carriles_controlados.index(carril_siguiente)
                                estado_seguro[indice_luz] = "G"
                    except traci.TraCIException:
                        pass
                    traci.trafficlight.setRedYellowGreenState(semaforo_id, "".join(estado_seguro))
                    SEMAFOROS_EN_MODO_EMERGENCIA.add(semaforo_id)
            semaforos_a_restaurar = SEMAFOROS_EN_MODO_EMERGENCIA - semaforos_en_ruta_cercana
            for semaforo_id in semaforos_a_restaurar:
                SEMAFOROS_EN_MODO_EMERGENCIA.remove(semaforo_id)
                print(f"SEMAFORO '{semaforo_id}': Emergencia finalizada. Volviendo a control inteligente.")
                traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_AMARILLO)
                semaforos_en_transicion[semaforo_id] = {'tiempo': TIEMPO_LUZ_AMARILLA, 'siguiente_fase': FASE_PRINCIPAL_VERDE, 'siguiente_fase_nombre': 'PRINCIPAL_VERDE'}
        else:
            # --- MODO NORMAL: CONTROL INTELIGENTE DESCENTRALIZADO ---
            if VEHICULO_EMERGENCIA_ID:
                print(f"\n¡MISIÓN CUMPLIDA! Ambulancia '{VEHICULO_EMERGENCIA_ID}' ha llegado al destino.")
                VEHICULO_EMERGENCIA_ID = None
            for semaforo_id in lista_semaforos:
                if semaforo_id in SEMAFOROS_EN_MODO_EMERGENCIA:
                    continue
                if semaforo_id in semaforos_en_transicion:
                    semaforos_en_transicion[semaforo_id]['tiempo'] -= 1
                    if semaforos_en_transicion[semaforo_id]['tiempo'] <= 0:
                        traci.trafficlight.setRedYellowGreenState(semaforo_id, semaforos_en_transicion[semaforo_id]['siguiente_fase'])
                        estado_semaforos[semaforo_id]['fase_actual'] = semaforos_en_transicion[semaforo_id]['siguiente_fase_nombre']
                        estado_semaforos[semaforo_id]['tiempo_en_fase'] = 0
                        del semaforos_en_transicion[semaforo_id]
                    continue
                info_semaforo = estado_semaforos[semaforo_id]
                info_semaforo["tiempo_en_fase"] += 1
                if info_semaforo["fase_actual"] == "PRINCIPAL_VERDE" and info_semaforo["tiempo_en_fase"] > TIEMPO_MINIMO_EN_FASE:
                    coches_esperando = sum(traci.lane.getLastStepHaltingNumber(c) for c in info_semaforo["carriles_transversales"])
                    if coches_esperando >= UMBRAL_COCHES_ESPERANDO:
                        traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_PRINCIPAL_AMARILLO)
                        semaforos_en_transicion[semaforo_id] = {'tiempo': TIEMPO_LUZ_AMARILLA, 'siguiente_fase': FASE_TRANSVERSAL_VERDE, 'siguiente_fase_nombre': 'TRANSVERSAL_VERDE'}
                elif info_semaforo["fase_actual"] == "TRANSVERSAL_VERDE" and info_semaforo["tiempo_en_fase"] > TIEMPO_MINIMO_EN_FASE:
                    coches_esperando_principales = sum(traci.lane.getLastStepHaltingNumber(c) for c in traci.trafficlight.getControlledLanes(semaforo_id) if c not in info_semaforo["carriles_transversales"])
                    if coches_esperando_principales >= UMBRAL_COCHES_ESPERANDO or info_semaforo["tiempo_en_fase"] > 30: # Condición de tiempo máximo
                         traci.trafficlight.setRedYellowGreenState(semaforo_id, FASE_TRANSVERSAL_AMARILLO)
                         semaforos_en_transicion[semaforo_id] = {'tiempo': TIEMPO_LUZ_AMARILLA, 'siguiente_fase': FASE_PRINCIPAL_VERDE, 'siguiente_fase_nombre': 'PRINCIPAL_VERDE'}
        
        # --- Actualización del archivo JSON para el dashboard ---
        if paso % 5 == 0:
            lista_vehiculos = traci.vehicle.getIDList()
            vehiculos_parados_manual = 0
            tiempo_espera_total = 0
            for vehiculo_id in lista_vehiculos:
                if traci.vehicle.getSpeed(vehiculo_id) < 0.1:
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

        time.sleep(0.05) # Puedes reducir el sleep para una simulación más fluida

except traci.TraCIException:
    print("\nConexión con SUMO cerrada (la simulación ha terminado).")

finally:
    if traci.isLoaded():
        traci.close()
        print("Script finalizado correctamente.")