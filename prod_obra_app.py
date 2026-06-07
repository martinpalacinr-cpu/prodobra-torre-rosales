#!/usr/bin/env python3
"""
ProdObra - Aplicación de Control de Productividad en Obras de Construcción
Desarrollado para Residentes de Obra y Capataces
Compatible con celulares (acceso vía navegador)
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import hashlib
import json
from io import BytesIO
import plotly.express as px

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="ProdObra | Control de Productividad",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para mejor experiencia móvil
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4A5568;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F7FAFC;
        border-radius: 12px;
        padding: 1rem;
        border-left: 5px solid #2B6CB0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    .big-button {
        font-size: 1.1rem !important;
        padding: 0.75rem 1.5rem !important;
        background-color: #2B6CB0 !important;
        color: white !important;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 5px solid #D69E2E;
        padding: 1rem;
        border-radius: 8px;
    }
    .success-box {
        background-color: #C6F6D5;
        border-left: 5px solid #38A169;
        padding: 1rem;
        border-radius: 8px;
    }
    @media (max-width: 768px) {
        .main-header { font-size: 1.6rem; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNCIONES DE BASE DE DATOS
# ============================================
DB_PATH = "productividad_obra.db"

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'capataz')),
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de actividades
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT NOT NULL,
            description TEXT,
            target_ratio REAL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de registros de productividad (logs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productivity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            user_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            start_datetime TEXT NOT NULL,
            end_datetime TEXT NOT NULL,
            duration_hours REAL NOT NULL,
            num_personal INTEGER NOT NULL,
            man_hours REAL NOT NULL,
            metrado REAL NOT NULL,
            ratio REAL,
            rendimiento REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (activity_id) REFERENCES activities(id)
        )
    """)
    
    conn.commit()
    
    # Insertar datos iniciales si no existen
    seed_initial_data(conn)

def seed_initial_data(conn):
    cursor = conn.cursor()
    
    # Verificar si ya hay usuarios
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        return  # Ya hay datos, no insertar de nuevo
    
    # Hash simple para contraseñas (demo)
    def hash_pw(pw):
        return hashlib.sha256((pw + "prodobra_salt_2026").encode()).hexdigest()
    
    # Usuarios iniciales
    users_data = [
        ("admin", hash_pw("admin123"), "Administrador General", "admin"),
        ("juan.perez", hash_pw("capataz123"), "Juan Pérez - Capataz Estructuras", "capataz"),
        ("carlos.lopez", hash_pw("capataz123"), "Carlos López - Capataz Acabados", "capataz"),
        ("maria.garcia", hash_pw("capataz123"), "María García - Capataz MEP", "capataz"),
    ]
    
    cursor.executemany(
        "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
        users_data
    )
    
    # Actividades iniciales (comunes en edificación Perú)
    activities_data = [
        ("Excavación manual", "m³", "Excavación de zanjas y suelos", 1.8),
        ("Encofrado metálico", "m²", "Instalación y desencofrado de encofrado metálico", 0.8),
        ("Armado de acero", "kg", "Colocación y amarre de refuerzo de acero", 0.025),
        ("Vaciado de concreto", "m³", "Colado de concreto en elementos estructurales", 2.5),
        ("Compactación de relleno", "m³", "Relleno y compactación de zanjas y bases", 1.2),
        ("Albañilería de bloques", "m²", "Levantamiento de muros con bloques de concreto", 0.9),
        ("Instalación tubería PVC", "ml", "Colocación de tuberías sanitarias y desagüe", 0.6),
        ("Pintura de paredes", "m²", "Aplicación de pintura en muros y cielos", 0.35),
        ("Colocación de cerámica", "m²", "Instalación de cerámica y porcelanato", 0.7),
        ("Montaje de andamios", "m²", "Armado y desarmado de andamios certificados", 1.5),
        ("Instalación Unistrut / soportes", "ml", "Colocación de rieles y soportes eléctricos", 0.5),
        ("Cableado eléctrico", "ml", "Tendido e instalación de cableado", 0.4),
    ]
    
    cursor.executemany(
        "INSERT INTO activities (name, unit, description, target_ratio) VALUES (?, ?, ?, ?)",
        activities_data
    )
    
    conn.commit()

def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND active = 1", (username,))
    row = cursor.fetchone()
    return dict(row) if row else None

def verify_password(username, password):
    user = get_user(username)
    if not user:
        return None
    hashed = hashlib.sha256((password + "prodobra_salt_2026").encode()).hexdigest()
    if hashed == user["password_hash"]:
        return user
    return None

def get_all_capataces():
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, username, full_name FROM users WHERE role = 'capataz' AND active = 1 ORDER BY full_name",
        conn
    )
    return df

def get_all_activities(active_only=True):
    conn = get_connection()
    query = "SELECT id, name, unit, description, target_ratio FROM activities"
    if active_only:
        query += " WHERE active = 1"
    query += " ORDER BY name"
    df = pd.read_sql_query(query, conn)
    return df

def add_activity(name, unit, description="", target_ratio=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO activities (name, unit, description, target_ratio) VALUES (?, ?, ?, ?)",
        (name, unit, description, target_ratio)
    )
    conn.commit()
    return cursor.lastrowid

def add_productivity_log(fecha, user_id, activity_id, start_dt, end_dt, num_personal, metrado, notes=""):
    duration = (end_dt - start_dt).total_seconds() / 3600.0
    if duration < 0:
        duration = 0.0  # Evitar negativos
    
    man_hours = round(duration * num_personal, 2)
    ratio = round(man_hours / metrado, 4) if metrado > 0 else None
    rendimiento = round(metrado / man_hours, 4) if man_hours > 0 else None
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO productivity_logs 
        (fecha, user_id, activity_id, start_datetime, end_datetime, duration_hours, 
         num_personal, man_hours, metrado, ratio, rendimiento, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fecha.isoformat(),
        user_id,
        activity_id,
        start_dt.isoformat(sep=' '),
        end_dt.isoformat(sep=' '),
        round(duration, 2),
        num_personal,
        man_hours,
        metrado,
        ratio,
        rendimiento,
        notes
    ))
    conn.commit()
    return cursor.lastrowid

def get_logs_dataframe(user_id=None, start_date=None, end_date=None, activity_id=None):
    conn = get_connection()
    
    query = """
        SELECT 
            pl.id,
            pl.fecha,
            u.full_name as capataz,
            a.name as actividad,
            a.unit as unidad,
            pl.start_datetime,
            pl.end_datetime,
            pl.duration_hours as horas,
            pl.num_personal as personal,
            pl.man_hours as horas_hombre,
            pl.metrado,
            pl.ratio,
            pl.rendimiento,
            pl.notes
        FROM productivity_logs pl
        JOIN users u ON pl.user_id = u.id
        JOIN activities a ON pl.activity_id = a.id
        WHERE 1=1
    """
    params = []
    
    if user_id:
        query += " AND pl.user_id = ?"
        params.append(user_id)
    if start_date:
        query += " AND pl.fecha >= ?"
        params.append(start_date.isoformat())
    if end_date:
        query += " AND pl.fecha <= ?"
        params.append(end_date.isoformat())
    if activity_id:
        query += " AND pl.activity_id = ?"
        params.append(activity_id)
    
    query += " ORDER BY pl.fecha DESC, pl.start_datetime DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    return df

def delete_log(log_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productivity_logs WHERE id = ?", (log_id,))
    conn.commit()

# ============================================
# FUNCIONES DE UI / HELPERS
# ============================================
def format_ratio(r):
    if pd.isna(r) or r is None:
        return "—"
    return f"{r:.2f}"

def calculate_summary_stats(df):
    if df.empty:
        return {
            "total_registros": 0,
            "total_horas_hombre": 0,
            "total_metrado": 0,
            "ratio_promedio": None
        }
    
    total_hh = df["horas_hombre"].sum()
    total_m = df["metrado"].sum()
    
    return {
        "total_registros": len(df),
        "total_horas_hombre": round(total_hh, 1),
        "total_metrado": round(total_m, 1),
        "ratio_promedio": round(total_hh / total_m, 3) if total_m > 0 else None
    }

# ============================================
# PÁGINA DE LOGIN
# ============================================
def login_page():
    st.markdown('<h1 class="main-header">🏗️ ProdObra</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Control de Productividad en Obras de Construcción • Torre Rosales</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("### 🔐 Iniciar Sesión")
        
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="admin o juan.perez")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Ingresar al Sistema", use_container_width=True, type="primary")
            
            if submitted:
                user = verify_password(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos. Intente nuevamente.")
        
        st.markdown("---")
        with st.expander("ℹ️ Credenciales de prueba (demo)"):
            st.markdown("""
            **Administrador:**  
            Usuario: `admin` | Contraseña: `admin123`
            
            **Capataces:**  
            Usuario: `juan.perez` | Contraseña: `capataz123`  
            Usuario: `carlos.lopez` | Contraseña: `capataz123`
            """)

# ============================================
# DASHBOARD CAPATAZ
# ============================================
def capataz_dashboard(user):
    st.sidebar.markdown(f"### 👷 {user['full_name']}")
    st.sidebar.caption("Capataz de Obra")
    
    menu_options = [
        "📊 Mi Dashboard",
        "⏱️ Registrar Actividad",
        "📋 Mis Registros",
        "📈 Mi Productividad"
    ]
    menu = st.sidebar.radio("Menú", menu_options, label_visibility="collapsed")
    
    # Cerrar sesión
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown(f'<h1 class="main-header">🏗️ ProdObra - {user["full_name"].split(" - ")[0]}</h1>', unsafe_allow_html=True)
    st.caption(f"Proyecto: Torre Rosales | Fecha actual: {date.today().strftime('%d/%m/%Y')}")
    
    # ==========================================
    # PESTAÑA: DASHBOARD
    # ==========================================
    if menu == "📊 Mi Dashboard":
        st.subheader("Resumen de tu jornada")
        
        today = date.today()
        df_today = get_logs_dataframe(user_id=user["id"], start_date=today, end_date=today)
        stats = calculate_summary_stats(df_today)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Registros hoy", stats["total_registros"])
        col2.metric("Horas-Hombre", stats["total_horas_hombre"])
        col3.metric("Metrado Total", stats["total_metrado"])
        ratio_str = f"{stats['ratio_promedio']:.2f}" if stats["ratio_promedio"] else "—"
        col4.metric("Ratio Promedio (hh/unidad)", ratio_str)
        
        st.markdown("---")
        
        if not df_today.empty:
            st.subheader("Actividad del día")
            display_df = df_today[["actividad", "unidad", "horas", "personal", "horas_hombre", "metrado", "ratio"]].copy()
            display_df["ratio"] = display_df["ratio"].apply(format_ratio)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no tienes registros para hoy. ¡Comienza a registrar tus actividades!")
    
    # ==========================================
    # PESTAÑA: REGISTRAR ACTIVIDAD
    # ==========================================
    elif menu == "⏱️ Registrar Actividad":
        st.subheader("📝 Registrar Nueva Actividad")
        
        activities_df = get_all_activities()
        if activities_df.empty:
            st.warning("No hay actividades configuradas. Contacta al administrador.")
            return
        
        activity_options = {row["name"]: row["id"] for _, row in activities_df.iterrows()}
        
        with st.form("register_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_activity_name = st.selectbox(
                    "Actividad realizada *",
                    options=list(activity_options.keys()),
                    help="Selecciona la actividad ejecutada"
                )
                activity_id = activity_options[selected_activity_name]
                activity_row = activities_df[activities_df["id"] == activity_id].iloc[0]
                st.caption(f"Unidad de medida: **{activity_row['unit']}**")
            
            with col2:
                num_personal = st.number_input(
                    "Cantidad de Personal (Obreros) *",
                    min_value=1, max_value=50, value=4, step=1,
                    help="Número de trabajadores asignados a esta actividad"
                )
            
            col_fecha, col_inicio, col_fin = st.columns(3)
            
            with col_fecha:
                fecha = st.date_input("Fecha *", value=date.today())
            
            with col_inicio:
                hora_inicio = st.time_input("Hora de Inicio *", value=datetime.now().time().replace(second=0, microsecond=0))
            
            with col_fin:
                hora_fin = st.time_input("Hora de Fin *", value=(datetime.now() + timedelta(hours=1, minutes=30)).time().replace(second=0, microsecond=0))
            
            metrado = st.number_input(
                f"Metrado Ejecutado ({activity_row['unit']}) *",
                min_value=0.01, max_value=100000.0, value=10.0, step=0.5,
                format="%.2f"
            )
            
            notes = st.text_area("Notas / Observaciones (opcional)", placeholder="Ej: Sector A, nivel 2, problemas de acceso...")
            
            submitted = st.form_submit_button("💾 GUARDAR REGISTRO", use_container_width=True, type="primary")
            
            if submitted:
                start_dt = datetime.combine(fecha, hora_inicio)
                end_dt = datetime.combine(fecha, hora_fin)
                
                if end_dt <= start_dt:
                    st.error("❌ La hora de fin debe ser posterior a la hora de inicio.")
                elif metrado <= 0:
                    st.error("❌ El metrado debe ser mayor a cero.")
                else:
                    log_id = add_productivity_log(
                        fecha=fecha,
                        user_id=user["id"],
                        activity_id=activity_id,
                        start_dt=start_dt,
                        end_dt=end_dt,
                        num_personal=num_personal,
                        metrado=metrado,
                        notes=notes
                    )
                    st.success(f"✅ Registro guardado correctamente. Ratio calculado: **{ (num_personal * ((end_dt - start_dt).total_seconds()/3600)) / metrado :.2f}** hh/{activity_row['unit']}")
                    st.balloons()
    
    # ==========================================
    # PESTAÑA: MIS REGISTROS
    # ==========================================
    elif menu == "📋 Mis Registros":
        st.subheader("📋 Historial de Registros")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            start_date = st.date_input("Desde", value=date.today() - timedelta(days=7))
        with col_f2:
            end_date = st.date_input("Hasta", value=date.today())
        
        df = get_logs_dataframe(user_id=user["id"], start_date=start_date, end_date=end_date)
        
        if df.empty:
            st.info("No hay registros en el rango seleccionado.")
        else:
            st.caption(f"Mostrando {len(df)} registros")
            
            # Mostrar tabla bonita
            display_cols = ["fecha", "actividad", "unidad", "horas", "personal", "horas_hombre", "metrado", "ratio", "rendimiento"]
            display_df = df[display_cols].copy()
            display_df["ratio"] = display_df["ratio"].apply(format_ratio)
            display_df["rendimiento"] = display_df["rendimiento"].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "—")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "fecha": st.column_config.DateColumn("Fecha"),
                    "horas": st.column_config.NumberColumn("Horas", format="%.2f"),
                    "personal": st.column_config.NumberColumn("Personal", format="%d"),
                    "horas_hombre": st.column_config.NumberColumn("Horas-Hombre", format="%.1f"),
                    "metrado": st.column_config.NumberColumn("Metrado", format="%.2f"),
                }
            )
            
            # Eliminar registro
            with st.expander("🗑️ Eliminar un registro"):
                log_to_delete = st.selectbox(
                    "Selecciona el registro a eliminar",
                    options=df["id"].tolist(),
                    format_func=lambda x: f"ID {x} - {df[df['id']==x]['actividad'].values[0]} ({df[df['id']==x]['fecha'].values[0]})"
                )
                if st.button("Eliminar registro seleccionado", type="secondary"):
                    delete_log(log_to_delete)
                    st.success("Registro eliminado.")
                    st.rerun()
    
    # ==========================================
    # PESTAÑA: MI PRODUCTIVIDAD
    # ==========================================
    elif menu == "📈 Mi Productividad":
        st.subheader("📈 Análisis de tu Productividad")
        
        df = get_logs_dataframe(user_id=user["id"])
        
        if df.empty:
            st.info("Aún no tienes suficientes datos para generar análisis.")
            return
        
        # Resumen general
        stats = calculate_summary_stats(df)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", stats["total_registros"])
        col2.metric("Total Horas-Hombre", stats["total_horas_hombre"])
        col3.metric("Ratio Global (hh/unidad)", f"{stats['ratio_promedio']:.3f}" if stats["ratio_promedio"] else "—")
        
        st.markdown("---")
        
        # Tabla resumen por actividad
        st.subheader("Resumen por Actividad")
        summary = df.groupby(["actividad", "unidad"]).agg({
            "metrado": "sum",
            "horas_hombre": "sum",
            "id": "count"
        }).reset_index()
        summary.columns = ["Actividad", "Unidad", "Metrado Total", "Horas-Hombre", "N° Veces"]
        summary["Ratio Promedio (hh/unidad)"] = (summary["Horas-Hombre"] / summary["Metrado Total"]).round(3)
        summary["Rendimiento (unidad/hh)"] = (summary["Metrado Total"] / summary["Horas-Hombre"]).round(3)
        
        st.dataframe(summary, use_container_width=True, hide_index=True)
        
        # Gráfico de ratios
        if len(summary) > 1:
            fig = px.bar(
                summary,
                x="Actividad",
                y="Ratio Promedio (hh/unidad)",
                color="Actividad",
                title="Ratio por Actividad (menor = más productivo)",
                labels={"Ratio Promedio (hh/unidad)": "Horas-Hombre por Unidad"}
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

# ============================================
# DASHBOARD ADMINISTRADOR
# ============================================
def admin_dashboard(user):
    st.sidebar.markdown(f"### 👨‍💼 {user['full_name']}")
    st.sidebar.caption("Administrador del Sistema")
    
    menu_options = [
        "📊 Dashboard General",
        "👥 Gestión de Usuarios",
        "🛠️ Catálogo de Actividades",
        "📈 Reportes y Análisis"
    ]
    menu = st.sidebar.radio("Menú", menu_options, label_visibility="collapsed")
    
    if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown('<h1 class="main-header">🏗️ ProdObra - Panel de Administración</h1>', unsafe_allow_html=True)
    st.caption("Proyecto Torre Rosales | Consorcio CTR")
    
    # ==========================================
    # DASHBOARD GENERAL
    # ==========================================
    if menu == "📊 Dashboard General":
        st.subheader("Resumen General de Productividad")
        
        df_all = get_logs_dataframe()
        stats = calculate_summary_stats(df_all)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Registros", stats["total_registros"])
        col2.metric("Horas-Hombre Totales", stats["total_horas_hombre"])
        col3.metric("Metrado Acumulado", stats["total_metrado"])
        col4.metric("Ratio Global", f"{stats['ratio_promedio']:.3f}" if stats["ratio_promedio"] else "—")
        
        if not df_all.empty:
            st.subheader("Últimos 10 registros del proyecto")
            recent = df_all.head(10)
            display = recent[["fecha", "capataz", "actividad", "horas_hombre", "metrado", "ratio"]].copy()
            display["ratio"] = display["ratio"].apply(format_ratio)
            st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay registros en el sistema.")
    
    # ==========================================
    # GESTIÓN DE USUARIOS
    # ==========================================
    elif menu == "👥 Gestión de Usuarios":
        st.subheader("👥 Gestión de Capataces y Usuarios")
        
        # Listar usuarios actuales
        conn = get_connection()
        users_df = pd.read_sql_query(
            "SELECT id, username, full_name, role, active FROM users ORDER BY role, full_name",
            conn
        )
        st.dataframe(users_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("➕ Agregar Nuevo Capataz")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Nombre de usuario (sin espacios)")
            new_fullname = st.text_input("Nombre completo y cargo", placeholder="Ej: Roberto Sánchez - Capataz de Acabados")
            new_password = st.text_input("Contraseña inicial", type="password")
            
            if st.form_submit_button("Crear Capataz"):
                if new_username and new_fullname and new_password:
                    try:
                        hashed = hashlib.sha256((new_password + "prodobra_salt_2026").encode()).hexdigest()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, 'capataz')",
                            (new_username, hashed, new_fullname)
                        )
                        conn.commit()
                        st.success(f"✅ Capataz '{new_fullname}' creado exitosamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ El nombre de usuario ya existe.")
                else:
                    st.error("Todos los campos son obligatorios.")

        # ==========================================
        # EDITAR USUARIO EXISTENTE
        # ==========================================
        st.markdown("---")
        st.subheader("✏️ Editar Usuario Existente")

        if not users_df.empty:
            user_options = {row['full_name']: row['id'] for _, row in users_df.iterrows()}
            selected_name = st.selectbox(
                "Selecciona el usuario que quieres editar",
                options=list(user_options.keys())
            )
            selected_id = user_options[selected_name]
            selected_row = users_df[users_df['id'] == selected_id].iloc[0]

            with st.form("edit_user_form"):
                new_username = st.text_input("Nombre de usuario (sin espacios)", value=selected_row['username'])
                new_full_name = st.text_input("Nombre completo y cargo", value=selected_row['full_name'])
                
                col1, col2 = st.columns(2)
                with col1:
                    reset_pass = st.checkbox("Resetear contraseña a '123456'")
                with col2:
                    is_active = st.checkbox("Usuario Activo", value=bool(selected_row['active']))

                submitted = st.form_submit_button("💾 Guardar Cambios")

                if submitted:
                    cursor = conn.cursor()
                    try:
                        # Actualizar username, nombre y estado
                        cursor.execute(
                            "UPDATE users SET username = ?, full_name = ?, active = ? WHERE id = ?",
                            (new_username, new_full_name, 1 if is_active else 0, selected_id)
                        )
                        
                        # Resetear contraseña si está marcado
                        if reset_pass:
                            new_hash = hashlib.sha256(("123456" + "prodobra_salt_2026").encode()).hexdigest()
                            cursor.execute(
                                "UPDATE users SET password_hash = ? WHERE id = ?",
                                (new_hash, selected_id)
                            )
                        
                        conn.commit()
                        st.success(f"✅ Usuario actualizado correctamente.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ Ese nombre de usuario ya está en uso por otra persona.")
        else:
            st.info("No hay usuarios para editar.")
    
    # ==========================================
    # CATÁLOGO DE ACTIVIDADES
    # ==========================================
    elif menu == "🛠️ Catálogo de Actividades":
        st.subheader("🛠️ Catálogo de Actividades")
        
        activities_df = get_all_activities(active_only=False)
        st.dataframe(activities_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("➕ Agregar Nueva Actividad")
        
        with st.form("add_activity_form"):
            col1, col2 = st.columns(2)
            with col1:
                act_name = st.text_input("Nombre de la actividad *")
            with col2:
                act_unit = st.text_input("Unidad de medida *", placeholder="m², m³, ml, kg, und...")
            
            act_desc = st.text_area("Descripción (opcional)")
            act_target = st.number_input("Ratio objetivo (hh/unidad) - opcional", min_value=0.0, value=0.0, step=0.1)
            
            if st.form_submit_button("Agregar Actividad"):
                if act_name and act_unit:
                    add_activity(act_name, act_unit, act_desc, act_target if act_target > 0 else None)
                    st.success(f"✅ Actividad '{act_name}' agregada.")
                    st.rerun()
                else:
                    st.error("Nombre y unidad son obligatorios.")
    
    # ==========================================
    # REPORTES Y ANÁLISIS
    # ==========================================
    elif menu == "📈 Reportes y Análisis":
        st.subheader("📈 Reportes Avanzados de Productividad")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            rep_start = st.date_input("Fecha inicio", value=date.today() - timedelta(days=30))
        with col_f2:
            rep_end = st.date_input("Fecha fin", value=date.today())
        with col_f3:
            capataz_filter = st.selectbox(
                "Filtrar por Capataz",
                options=["Todos"] + get_all_capataces()["full_name"].tolist()
            )
        
        # Aplicar filtros
        user_id_filter = None
        if capataz_filter != "Todos":
            cap_df = get_all_capataces()
            user_id_filter = int(cap_df[cap_df["full_name"] == capataz_filter]["id"].values[0])
        
        df_filtered = get_logs_dataframe(
            user_id=user_id_filter,
            start_date=rep_start,
            end_date=rep_end
        )
        
        if df_filtered.empty:
            st.warning("No hay datos para los filtros seleccionados.")
            return
        
        # KPIs
        stats = calculate_summary_stats(df_filtered)
        k1, k2, k3 = st.columns(3)
        k1.metric("Registros", stats["total_registros"])
        k2.metric("Horas-Hombre", stats["total_horas_hombre"])
        k3.metric("Ratio Promedio", f"{stats['ratio_promedio']:.3f}" if stats["ratio_promedio"] else "—")
        
        st.markdown("---")
        
        # Tabla resumen por actividad
        st.subheader("Productividad por Actividad")
        act_summary = df_filtered.groupby(["actividad", "unidad"]).agg({
            "metrado": "sum",
            "horas_hombre": "sum",
            "ratio": "mean"
        }).reset_index()
        act_summary.columns = ["Actividad", "Unidad", "Metrado Total", "Horas-Hombre Total", "Ratio Promedio"]
        act_summary["Ratio Promedio"] = act_summary["Ratio Promedio"].round(3)
        act_summary = act_summary.sort_values("Ratio Promedio")
        
        st.dataframe(act_summary, use_container_width=True, hide_index=True)
        
        # Gráfico
        if len(act_summary) >= 2:
            fig = px.bar(
                act_summary,
                x="Actividad",
                y="Ratio Promedio",
                title="Comparativa de Ratios por Actividad (menor es mejor)",
                color="Ratio Promedio",
                color_continuous_scale="RdYlGn_r"
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
        
        # Exportar
        st.markdown("---")
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar datos filtrados (CSV)",
            data=csv,
            file_name=f"productividad_{rep_start}_{rep_end}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ============================================
# MAIN
# ============================================
def main():
    init_database()
    
    # Inicializar estado de sesión
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        login_page()
    else:
        user = st.session_state.user
        if user["role"] == "admin":
            admin_dashboard(user)
        else:
            capataz_dashboard(user)

if __name__ == "__main__":
    main()
