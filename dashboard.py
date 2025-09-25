# dashboard.py (Versión 3.0 - Demo Profesional)
import streamlit as st
import json
import os
import time
import pandas as pd
import altair as alt # Usaremos Altair para un mejor control del gráfico

st.set_page_config(
    page_title="Dashboard de Control de Tráfico - SYNCRONÍA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar el estado de la sesión
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=[
        'Paso', 
        'Vehículos Detenidos', 
        'Espera Promedio por Vehículo ⏱️'
    ])

# --- LAYOUT PRINCIPAL (definimos los espacios una sola vez) ---

st.title("🚦 Centro de Mando de Tráfico - SYNCRONÍA 🚦")
st.markdown("Panel de control en tiempo real para la gestión de la red de semáforos inteligentes.")

# Columnas para los elementos principales
col1, col2 = st.columns([1, 2.5]) # La columna del gráfico es 2.5 veces más ancha

with col1:
    st.subheader("Estado del Sistema")
    status_placeholder = st.empty()
    
    st.subheader("Controles")
    if st.button("🚨 LANZAR EMERGENCIA 🚨", type="primary", use_container_width=True):
        with open("emergency_request.txt", "w") as f:
            f.write("start")
        st.success("¡Petición de emergencia enviada!")
    
    st.subheader("Indicadores Clave (KPIs)")
    kpi1_placeholder = st.empty()
    kpi2_placeholder = st.empty()
    kpi3_placeholder = st.empty()

with col2:
    st.subheader("Evolución de la Red en Tiempo Real")
    chart_placeholder = st.empty()

# --- BUCLE DE ACTUALIZACIÓN ---

while True:
    try:
        with open("status.json", "r") as f:
            data = json.load(f)

            # Extraemos los datos con .get() para seguridad
            paso = data.get("paso_simulacion", 0)
            activos = data.get("vehiculos_activos", 0)
            llegados = data.get("vehiculos_llegados_total", 0)
            espera = data.get("tiempo_espera_promedio", 0.0)
            parados = data.get("vehiculos_parados", 0)
            emergencia = data.get("emergencia_activa", False)

            # --- Actualizar los placeholders ---

            # 1. Actualizar el indicador de estado
            with status_placeholder.container():
                if emergencia:
                    st.warning("⚠️ MODO EMERGENCIA ACTIVADO ⚠️", icon="🚑")
                else:
                    st.info("✅ Operación Normal ✅", icon="🚦")

            # 2. Actualizar los KPIs
            with kpi1_placeholder.container():
                st.metric(label="Tiempo de Simulación 🕒", value=f"{paso} s")
            with kpi2_placeholder.container():
                st.metric(label="Rendimiento (Vehículos Llegados) 🏁", value=llegados)
            with kpi3_placeholder.container():
                st.metric(label="Vehículos Activos 🚗 / Detenidos 🛑", value=f"{activos} / {parados}")

            # 3. Actualizar el historial de datos para el gráfico
            nuevo_dato = pd.DataFrame([{
                "Paso": paso, 
                "Vehículos Detenidos": parados, 
                "Espera Promedio por Vehículo ⏱️": espera
            }])
            st.session_state.history = pd.concat([st.session_state.history, nuevo_dato], ignore_index=True)
            st.session_state.history = st.session_state.history.tail(100) # Mantenemos solo los últimos 100 puntos
            
            # 4. Crear y mostrar el gráfico actualizado usando Altair
            with chart_placeholder.container():
                
                # Preparamos los datos para Altair
                df_melted = st.session_state.history.melt(
                    id_vars=['Paso'], 
                    value_vars=['Vehículos Detenidos', 'Espera Promedio por Vehículo ⏱️'],
                    var_name='Métrica',
                    value_name='Valor'
                )

                chart = alt.Chart(df_melted).mark_line(interpolate='basis').encode(
                    x=alt.X('Paso', axis=alt.Axis(title='Tiempo de Simulación (s)')),
                    y=alt.Y('Valor', axis=alt.Axis(title='Valor de la Métrica')),
                    color=alt.Color('Métrica', scale=alt.Scale(
                        domain=['Vehículos Detenidos', 'Espera Promedio por Vehículo ⏱️'],
                        range=['#FF4B4B', '#1E90FF'] # Colores: Rojo para parados, Azul para espera
                    )),
                    tooltip=['Paso', 'Métrica', 'Valor']
                ).properties(
                    title="Métricas Clave de la Red"
                ).interactive()

                st.altair_chart(chart, use_container_width=True)

    except (FileNotFoundError, json.JSONDecodeError):
        with status_placeholder.container():
            st.info("Esperando datos de la simulación...")
        time.sleep(1)
    
    time.sleep(1)