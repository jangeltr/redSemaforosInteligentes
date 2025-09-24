import sys
import os

print("--- DIAGNÓSTICO DE ENTORNO PYTHON ---")

# 1. ¿Qué ejecutable de Python estamos usando?
print(f"Ruta del ejecutable de Python: {sys.executable}")

# 2. ¿Cuál es la versión de Python?
print(f"Versión de Python: {sys.version}")

# 3. ¿Dónde está buscando Python los módulos ANTES de hacer nada?
print("\n--- sys.path ANTES de modificar ---")
for path in sys.path:
    print(path)

# 4. Intentamos añadir la ruta de SUMO_HOME/tools
sumo_home_path = os.environ.get('SUMO_HOME')
print(f"\nValor de SUMO_HOME encontrado: {sumo_home_path}")

if sumo_home_path:
    tools_path = os.path.join(sumo_home_path, 'tools')
    print(f"Ruta de 'tools' a añadir: {tools_path}")
    
    # Comprobamos si la ruta existe de verdad
    if os.path.isdir(tools_path):
        print("La ruta de 'tools' SÍ existe.")
        sys.path.append(tools_path)
    else:
        print("¡ERROR! La ruta de 'tools' NO existe.")
else:
    print("¡ERROR! La variable de entorno SUMO_HOME no fue encontrada por Python.")


# 5. ¿Dónde está buscando Python los módulos DESPUÉS de nuestro intento?
print("\n--- sys.path DESPUÉS de modificar ---")
for path in sys.path:
    print(path)

print("\n--- FIN DEL DIAGNÓSTICO ---")

# 6. Ahora intentamos la importación (descomenta la siguiente línea para probar)
# import traci
# print("\n¡ÉXITO! El módulo 'traci' se importó correctamente.")