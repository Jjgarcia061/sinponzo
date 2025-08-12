
#PARA INICIAR EL DASH DESPUES DE CORRER EL PROGRAMA EJECUTE EL SIGUIENTE COMANDO EN LA TERMINAL:
#streamlit run DASH_PONZO.py
import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import json
from streamlit_folium import st_folium
import plotly.express as px
import unicodedata

st.set_page_config(page_title="PONZOÑAS", layout="wide")
st.title("- Dashboard Epidemiológico -")


# --- Rutas de archivos de entrada ---
COORDS_CSV = r"C:\Users\jc698\OneDrive\Desktop\DASPONZO\COORDENADAS.csv"
GEOJSON_FILE = r"C:\Users\jc698\OneDrive\Desktop\DASPONZO\16l_michoacan.geojson"
CONSUMO_ANUAL_CSV = r"C:\Users\jc698\OneDrive\Desktop\DASPONZO\BASE1_2.csv"
CONSUMO_HIST_CSV = r"C:\Users\jc698\OneDrive\Desktop\DASPONZO\BASE1_2.csv"

# --- Tabs principales ---
tabs = st.tabs(["MAPA DE CALOR", "CONSUMO HISTORICO", "CASOS Y CONSUMO ANUAL", "HOSPITALES Y CENTROS DE SALUD"])

# --- Función de normalización de nombres ---
def normaliza_nombre(nombre):
    if pd.isna(nombre):
        return ''
    nombre = str(nombre).upper().strip()
    nombre = ''.join(c for c in unicodedata.normalize('NFD', nombre) if unicodedata.category(c) != 'Mn')
    nombre = nombre.replace(' LOCALIDAD', '').replace(' COLONIA', '').replace(' POBLADO', '')
    nombre = nombre.replace('.', '').replace(',', '').replace('  ', ' ')
    return nombre

# --- MAPA DE CALOR ---
with tabs[0]:
    st.header("MAPA DE CALOR")
    try:
        df = pd.read_csv(COORDS_CSV, encoding='utf-8', low_memory=False)
        if df.empty or len(df.columns) == 0:
            st.error("El archivo para el mapa está vacío o no tiene columnas válidas. Verifica el archivo.")
        else:
            # Usar LOC_RES(SINAVE) como localidad, y LAT_DECIMAL, LON_DECIMAL para el heatmap
            df = df.dropna(subset=['LOC_RES(SINAVE)', 'LAT_DECIMAL', 'LON_DECIMAL'])
            df['LOC_RES_NORM'] = df['LOC_RES(SINAVE)'].apply(normaliza_nombre)
            heat_data = df[['LAT_DECIMAL', 'LON_DECIMAL']].values.tolist()
            m = folium.Map(location=[19.1532, -101.8831], zoom_start=7, tiles='cartodbpositron')
            with open(GEOJSON_FILE, encoding='utf-8') as gjf:
                geojson_data = json.load(gjf)
            folium.GeoJson(geojson_data, name='Municipios').add_to(m)
            HeatMap(heat_data, radius=18, blur=15, min_opacity=0.3).add_to(m)
            st_folium(m, width=1000, height=600)
            st.success(f"Total de puntos en el mapa: {len(heat_data)}")
    except Exception as e:
        st.error(f"No se pudo procesar la base para el mapa de calor: {e}")

# --- CONSUMO HISTÓRICO ---
with tabs[1]:
    st.header("Consumo histórico de faboterápicos")
    try:
        df_hist = pd.read_csv(CONSUMO_HIST_CSV, encoding='utf-8')
        frasco_cols = [f'NUM_FRASCO_APL_{i}' for i in range(1, 11)]
        for col in frasco_cols:
            df_hist[col] = pd.to_numeric(df_hist[col], errors='coerce').fillna(0)
        df_hist['TOTAL_FRASCOS'] = df_hist[frasco_cols].sum(axis=1)
        JURISDICCIONES = {
            1: 'MORELIA', 2: 'ZAMORA', 3: 'ZITÁCUARO', 4: 'PÁTZCUARO',
            5: 'URUAPAN', 6: 'LA PIEDAD', 7: 'APATZINGÁN', 8: 'LÁZARO CÁRDENAS'
        }
        df_hist['JURISDICCION'] = df_hist['iID_Jurisdiccion'].map(JURISDICCIONES)
        df_hist['AÑO'] = pd.to_datetime(df_hist['Fecha de notificación'], dayfirst=True, errors='coerce').dt.year
        df_hist['MES'] = pd.to_datetime(df_hist['Fecha de notificación'], dayfirst=True, errors='coerce').dt.month
        df_hist = df_hist.dropna(subset=['Fecha de notificación', 'JURISDICCION'])
        df_grouped = df_hist.groupby(['AÑO', 'MES'])['TOTAL_FRASCOS'].sum().reset_index()
        df_grouped['PERIODO'] = pd.to_datetime(df_grouped['AÑO'].astype(str) + '-' + df_grouped['MES'].astype(str) + '-01')
        fig = px.line(df_grouped, x='PERIODO', y='TOTAL_FRASCOS', markers=True,
                      labels={'PERIODO':'Periodo', 'TOTAL_FRASCOS':'Consumo'},
                      title='Consumo histórico global de faboterápicos')
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"No se pudo cargar la base histórica local: {e}")

# --- CONSUMO ANUAL INTERACTIVO ---
with tabs[2]:
    st.header(":bar_chart: Consumo anual interactivo de faboterápicos")
    JURISDICCIONES = {
        1: 'MORELIA', 2: 'ZAMORA', 3: 'ZITÁCUARO', 4: 'PÁTZCUARO',
        5: 'URUAPAN', 6: 'LA PIEDAD', 7: 'APATZINGÁN', 8: 'LÁZARO CÁRDENAS'
    }
    COLORES_JURIS = {
        'MORELIA': '#E41A1C', 'ZAMORA': '#377EB8', 'ZITÁCUARO': "#00eeff", 'PÁTZCUARO': '#FF7F00',
        'URUAPAN': '#984EA3', 'LA PIEDAD': '#FFFF33', 'APATZINGÁN': '#A65628', 'LÁZARO CÁRDENAS': '#F781BF'
    }
    MESES_ES = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    try:
        df = pd.read_csv(CONSUMO_ANUAL_CSV, encoding='utf-8')
        frasco_cols = [f'NUM_FRASCO_APL_{i}' for i in range(1, 11)]
        for col in frasco_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        df['TOTAL_FRASCOS'] = df[frasco_cols].sum(axis=1)
        df['JURISDICCION'] = df['iID_Jurisdiccion'].map(JURISDICCIONES)
        df['AÑO'] = pd.to_datetime(df['Fecha de notificación'], dayfirst=True, errors='coerce').dt.year
        df['MES'] = pd.to_datetime(df['Fecha de notificación'], dayfirst=True, errors='coerce').dt.month
        df = df.dropna(subset=['Fecha de notificación', 'JURISDICCION'])
        anios_disponibles = sorted(df['AÑO'].dropna().unique(), reverse=True)
        anio = st.selectbox("Selecciona el año a analizar", anios_disponibles, index=0, key="anio_interactivo")
        jurisdicciones_disponibles = ['TODAS'] + list(JURISDICCIONES.values())
        jurisdiccion_sel = st.selectbox("Selecciona la jurisdicción (o TODAS)", jurisdicciones_disponibles, index=0, key="juris_interactivo")
        import plotly.graph_objects as go
        if jurisdiccion_sel == 'TODAS':
            df_anio = df[df['AÑO'] == anio]
            df_grouped = df_anio.groupby(['MES', 'JURISDICCION'])['TOTAL_FRASCOS'].sum().reset_index()
            st.subheader(f"Polígono de frecuencia anual combinado - {anio}")
            fig = go.Figure()
            for jurisdiccion in JURISDICCIONES.values():
                data = df_grouped[df_grouped['JURISDICCION'] == jurisdiccion]
                if data.empty:
                    continue
                color = COLORES_JURIS.get(jurisdiccion, None)
                fig.add_trace(go.Scatter(
                    x=[MESES_ES[m-1] for m in data['MES']],
                    y=data['TOTAL_FRASCOS'],
                    mode='lines+markers',
                    name=jurisdiccion,
                    line=dict(color=color, width=3),
                    marker=dict(size=9, color=color, line=dict(width=1, color='#fff')),
                    hovertemplate='<b>%{x}</b><br>Consumo: %{y}<extra>'+jurisdiccion+'</extra>'
                ))
            total_global = int(df_anio['TOTAL_FRASCOS'].sum())
            fig.update_layout(
                title=f'Polígono de Frecuencia Anual - Consumo de Faboterápicos ({anio})<br><sup>Total consumido "ALACRAMYN": {total_global:,} | Todas las Jurisdicciones Sanitarias de Michoacán</sup>',
                xaxis_title='Mes',
                yaxis_title='Consumo de Faboterápicos',
                legend_title='Jurisdicción',
                template='plotly_white',
                hovermode='x unified',
                margin=dict(l=30, r=30, t=80, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Mostrar todas las series de años para la jurisdicción seleccionada
            df_juris = df[df['JURISDICCION'] == jurisdiccion_sel]
            anios_juris = sorted(df_juris['AÑO'].dropna().unique())
            st.subheader(f"Polígono de frecuencia anual combinado - {jurisdiccion_sel}")
            fig = go.Figure()
            import plotly.colors as pc
            palette = pc.qualitative.Plotly
            # Orden epidemiológico: OCTUBRE (10) a SEPTIEMBRE (9)
            orden_epidemiologico = [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            meses_epidemiologicos = [MESES_ES[m-1] for m in orden_epidemiologico]
            for idx, anio_j in enumerate(anios_juris):
                data = df_juris[df_juris['AÑO'] == anio_j].groupby('MES')['TOTAL_FRASCOS'].sum().reset_index()
                # Filtrar meses válidos y reordenar según ciclo epidemiológico
                data = data[(data['MES'] >= 1) & (data['MES'] <= 12)]
                data['MES'] = data['MES'].astype(int)
                data = data.set_index('MES').reindex(orden_epidemiologico).reset_index()
                if data['TOTAL_FRASCOS'].isnull().all():
                    continue
                color = palette[idx % len(palette)]
                fig.add_trace(go.Scatter(
                    x=meses_epidemiologicos,
                    y=data['TOTAL_FRASCOS'],
                    mode='lines+markers',
                    name=f"{jurisdiccion_sel} - {anio_j}",
                    line=dict(color=color, width=3),
                    marker=dict(size=10, color=color, line=dict(width=1, color='#fff')),
                    hovertemplate=f'<b>%{{x}}</b><br>Consumo: %{{y}}<extra>{jurisdiccion_sel} - {anio_j}</extra>'
                ))
            total_juris = int(df_juris['TOTAL_FRASCOS'].sum())
            fig.update_layout(
                title=f'Polígono de Frecuencia Anual - {jurisdiccion_sel}<br><sup>Total consumido "ALACRAMYN": {total_juris:,} | Todos los años disponibles</sup>',
                xaxis_title='Mes',
                yaxis_title='Consumo de Faboterápicos',
                legend_title='Año',
                template='plotly_white',
                hovermode='x unified',
                margin=dict(l=30, r=30, t=80, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)
        if jurisdiccion_sel != 'TODAS':
            st.markdown("---")
            st.subheader(f"Polígono de frecuencia individual - {jurisdiccion_sel}")
            # Filtrar datos por año y jurisdicción seleccionados
            df_filt = df[(df['AÑO'] == anio) & (df['JURISDICCION'] == jurisdiccion_sel)]
            # Consumo mensual
            data = df_filt.groupby('MES')['TOTAL_FRASCOS'].sum().reset_index()
            # Casos mensuales (conteo de FOL_Plat)
            casos = df_filt.groupby('MES')['FOL_Plat'].count().reset_index().rename(columns={'FOL_Plat': 'CASOS'})
            # Reordenar meses según ciclo epidemiológico
            data = data[(data['MES'] >= 1) & (data['MES'] <= 12)]
            data['MES'] = data['MES'].astype(int)
            data = data.set_index('MES').reindex(orden_epidemiologico).reset_index()
            casos = casos[(casos['MES'] >= 1) & (casos['MES'] <= 12)]
            casos['MES'] = casos['MES'].astype(int)
            casos = casos.set_index('MES').reindex(orden_epidemiologico).reset_index()
            if data['TOTAL_FRASCOS'].notnull().any():
                color = COLORES_JURIS.get(jurisdiccion_sel, None)
                import plotly.graph_objects as go
                fig2 = go.Figure()
                # Línea de consumo
                fig2.add_trace(go.Scatter(
                    x=meses_epidemiologicos,
                    y=data['TOTAL_FRASCOS'],
                    mode='lines+markers+text',
                    name='Consumo',
                    line=dict(color=color, width=3),
                    marker=dict(size=10, color=color, line=dict(width=1, color='#fff')),
                    text=[str(int(y)) if pd.notnull(y) else '' for y in data['TOTAL_FRASCOS']],
                    textposition='top center',
                    hovertemplate='<b>%{x}</b><br>Consumo: %{y}<extra>Consumo</extra>',
                    yaxis='y1'
                ))
                # Picos máximos de consumo
                if data['TOTAL_FRASCOS'].notnull().any():
                    idx_max = data['TOTAL_FRASCOS'].idxmax()
                    x_max = data.loc[idx_max, 'MES']
                    y_max = data.loc[idx_max, 'TOTAL_FRASCOS']
                    if pd.notnull(y_max):
                        fig2.add_trace(go.Scatter(
                            x=[MESES_ES[int(x_max)-1]],
                            y=[y_max],
                            mode='markers+text',
                            marker=dict(color='#D7263D', size=12, line=dict(width=2, color='#fff')),
                            name='Pico máximo consumo',
                            text=[f"{int(y_max)}"],
                            textposition='top center',
                            hovertemplate=f'<b>{MESES_ES[int(x_max)-1]}</b><br>Pico: {y_max}<extra>Pico máximo</extra>',
                            yaxis='y1'
                        ))
                # Línea de casos
                fig2.add_trace(go.Scatter(
                    x=meses_epidemiologicos,
                    y=casos['CASOS'],
                    mode='lines+markers+text',
                    name='Casos',
                    line=dict(color='green', width=3, dash='dot'),
                    marker=dict(size=10, color='green', line=dict(width=1, color='#fff')),
                    text=[str(int(y)) if pd.notnull(y) else '' for y in casos['CASOS']],
                    textposition='bottom center',
                    hovertemplate='<b>%{x}</b><br>Casos: %{y}<extra>Casos</extra>',
                    yaxis='y2'
                ))
                total_juris = int(data['TOTAL_FRASCOS'].sum(skipna=True))
                fig2.update_layout(
                    title=f'Consumo de Faboterápicos y Casos - {jurisdiccion_sel} ({anio})<br><sup>Total consumido "ALACRAMYN": {total_juris:,}</sup>',
                    xaxis_title='Mes',
                    #MODIFICAR EJE DE LA GRAFICA
                    yaxis=dict(title='Consumo de Faboterápicos', side='left', range=[0, None]),
                    yaxis2=dict(title='Casos', overlaying='y', side='right', showgrid=False, range=[0, None]),
                    template='plotly_white',
                    margin=dict(l=30, r=30, t=70, b=40),
                    legend=dict(x=0.01, y=0.99)
                )
                st.plotly_chart(fig2, use_container_width=True)

            # --- NUEVAS GRÁFICAS: RANGO DE EDADES Y CASOS POR GÉNERO ---
            st.markdown("---")
            # Grupos de edad personalizados
            bins = [0, 4, 9, 14, 19, 24, 44, 49, 59, 64, 150]
            labels = [
                "0-4", "5-9", "10-14", "15-19", "20-24", "25-44",
                "45-49", "50-59", "60-64", "65 y más"
            ]
            df_filt['GRUPO_EDAD'] = pd.cut(df_filt['IDE_EDAD_AÑOS'], bins=bins, labels=labels, right=True, include_lowest=True)
            edad_counts = df_filt['GRUPO_EDAD'].value_counts().sort_index()
            fig_edad = px.bar(x=edad_counts.index, y=edad_counts.values, labels={'x': 'Rango de edad', 'y': 'Casos'},
                              title='RANGO DE EDADES', color_discrete_sequence=['#636EFA'])
            st.plotly_chart(fig_edad, use_container_width=True)

            # Gráfica de género
            genero_counts = df_filt['IDE_SEX'].value_counts()
            fig_genero = px.bar(x=genero_counts.index, y=genero_counts.values, labels={'x': 'Género', 'y': 'Casos'},
                                title='CASOS POR GENERO', color_discrete_sequence=['#EF553B'])
            st.plotly_chart(fig_genero, use_container_width=True)
    except Exception as e:
        st.error(f"No se pudo cargar la base anual de consumo: {e}")
# --- HOSPITALES Y CENTROS DE SALUD ---
with tabs[3]:
    st.header("HOSPITALES Y CENTROS DE SALUD")
    JURISDICCIONES = {
        1: 'MORELIA', 2: 'ZAMORA', 3: 'ZITÁCUARO', 4: 'PÁTZCUARO',
        5: 'URUAPAN', 6: 'LA PIEDAD', 7: 'APATZINGÁN', 8: 'LÁZARO CÁRDENAS'
    }
    juris_nombres = list(JURISDICCIONES.values())
    juris_sel = st.selectbox("Selecciona una jurisdicción", options=juris_nombres)
    df_hosp = df.copy() if 'df' in locals() else pd.read_csv(CONSUMO_ANUAL_CSV, encoding='utf-8')
    df_hosp = df_hosp[df_hosp['JURISDICCION'] == juris_sel]
    frasco_cols = [f'NUM_FRASCO_APL_{i}' for i in range(1, 11)]
    df_hosp['CONSUMO_TOTAL_FRASCOS'] = df_hosp[frasco_cols].sum(axis=1)
    lote_cols = [f'LOT_{i}' for i in range(1, 11)]
    cols_mostrar = ['Fecha de notificación', 'FOL_Plat', 'UNI_MED_TRA', 'CLUES_TRATA', 'CONSUMO_TOTAL_FRASCOS'] + lote_cols
    cols_existentes = [col for col in cols_mostrar if col in df_hosp.columns]
    st.subheader(f"Casos y consumo en {juris_sel}")
    tabla = df_hosp[cols_existentes].reset_index(drop=True).copy()
    tabla.index = tabla.index + 1
    for col in lote_cols:
        if col in tabla.columns:
            tabla[col] = tabla[col].fillna('-').replace('None', '-')
    st.dataframe(tabla)
