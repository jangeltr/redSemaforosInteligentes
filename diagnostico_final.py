# diagnostico_final.py
import subprocess
import os
import time

# --- Aseguramos estar en el directorio correcto ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
try:
    os.chdir(SCRIPT_DIR)
    print(f"Directorio de trabajo: {os.getcwd()}")
except Exception as e:
    print(f"Error cambiando directorio: {e}")
    exit()

# --- El comando exacto que intentamos ejecutar ---
SUMO_CONFIG_FILENAME = "calles.sumocfg"
sumo_cmd = ["sumo-gui", "-c", SUMO_CONFIG_FILENAME, "--start", "--quit-on-end"]

print(f"\nIntentando lanzar SUMO con el siguiente comando:")
print(" ".join(sumo_cmd))
print("\n--- SALIDA DE SUMO ---")

# --- Lanzamos SUMO como un subproceso y capturamos su salida ---
# Esta es la parte importante. Leemos lo que SUMO imprime en su consola.
process = subprocess.Popen(
    sumo_cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Esperamos a que el proceso termine y obtenemos su salida
stdout, stderr = process.communicate()

# Decodificamos la salida para poder leerla
stdout_decoded = stdout.decode('utf-8')
stderr_decoded = stderr.decode('utf-8')

print("\n--- Salida Estándar (stdout) ---")
if stdout_decoded:
    print(stdout_decoded)
else:
    print("(Vacía)")

print("\n--- Salida de Error (stderr) ---")
if stderr_decoded:
    print(stderr_decoded)
else:
    print("(Vacía)")

print("\n--- FIN DEL DIAGNÓSTICO ---")

if process.returncode != 0:
    print(f"\n¡SUMO terminó con un código de error: {process.returncode}!")
    print("El problema está en la 'Salida de Error (stderr)' de arriba.")
else:
    print("\nSUMO terminó correctamente (código 0), lo cual es inesperado.")