import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import time

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Dashboard Café Latte", layout="wide")
st.title("📊 Dashboard Café Latte (Tiempo Real)")

# ==============================
# LOGIN ESTABLE
# ==============================
import streamlit_authenticator as stauth

if "authenticator" not in st.session_state:

    credentials = {
        "usernames": {
            "admin": {
                "name": "Admin",
                "password": "1234"
            }
        }
    }

    st.session_state["authenticator"] = stauth.Authenticate(
        credentials,
        "dashboard_cookie",
        "clave_secreta",
        cookie_expiry_days=1,
        auto_hash=True
    )

authenticator = st.session_state["authenticator"]

authenticator.login()

if st.session_state.get("authentication_status") is False:
    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

if st.session_state.get("authentication_status") is None:
    st.warning("⚠️ Ingrese sus credenciales")
    st.stop()

st.success(f"✅ Bienvenido {st.session_state.get('name')}")

# ==============================
# CARGA DE DATOS DESDE SHAREPOINT
# ==============================

@st.cache_data(ttl=30)
def load_data():
    try:
        url = "https://supercentrohn-my.sharepoint.com/:x:/g/personal/hmartinez_centro_hn/IQCVqyoZtIpJTZ2pyvHhhHSYAbgX98ZQN8_SvSyT2LxqfZo?e=DPgqDY"  # ⚠️ CAMBIA ESTO

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            st.error(f"Error HTTP: {response.status_code}")
            return pd.DataFrame()

        file = BytesIO(response.content)

        df = pd.read_excel(file, engine="openpyxl")

        return df

    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        return pd.DataFrame()

df = load_data()

# ==============================
# VALIDAR DATA
# ==============================

if df.empty:
    st.error("❌ No se pudo cargar el Excel o está vacío")
    st.stop()

# ==============================
# LIMPIEZA ROBUSTA
# ==============================

# limpiar nombres
df.columns = [str(col).strip() for col in df.columns]

# eliminar columnas basura
df = df.loc[:, ~pd.Series(df.columns).str.contains("Unnamed", case=False)]

# DEBUG
st.write("Columnas detectadas:", df.columns)

# ==============================
# DETECTAR VENTAS
# ==============================

col_ventas = None
for col in df.columns:
    if "VENTA" in col.upper():
        col_ventas = col
        break

if col_ventas is None:
    st.error("❌ No se encontró columna de ventas")
    st.stop()

df["Ventas"] = pd.to_numeric(df[col_ventas], errors="coerce")

# ==============================
# DETECTAR FECHA
# ==============================

col_fecha = None
for col in df.columns:
    if "FECHA" in col.upper():
        col_fecha = col
        break

if col_fecha:
    df["Fecha"] = pd.to_datetime(df[col_fecha], errors="coerce")

# ==============================
# DETECTAR VENDEDORA
# ==============================

col_vendedora = None
for col in df.columns:
    if "VENDEDORA" in col.upper():
        col_vendedora = col
        break

if col_vendedora:
    df["Vendedora"] = df[col_vendedora]

# limpiar datos
df = df.dropna(subset=["Ventas"])

# ==============================
# FILTROS
# ==============================
st.sidebar.header("🔎 Filtros")

if "Vendedora" in df.columns:
    seleccion = st.sidebar.selectbox(
        "Vendedora",
        ["Todas"] + list(df["Vendedora"].dropna().unique())
    )

    if seleccion != "Todas":
        df = df[df["Vendedora"] == seleccion]

# ==============================
# KPIs
# ==============================
col1, col2, col3 = st.columns(3)

col1.metric("💰 Ventas Totales", round(df["Ventas"].sum(), 2))
col2.metric("📊 Registros", len(df))
col3.metric("📈 Promedio", round(df["Ventas"].mean(), 2))

# ==============================
# GRAFICOS
# ==============================

st.subheader("📈 Ventas por Fecha")

if "Fecha" in df.columns:
    df_group = df.groupby("Fecha")["Ventas"].sum()
    st.line_chart(df_group)
else:
    st.warning("No hay campo de fecha")

st.subheader("📊 Ventas por Vendedora")

if "Vendedora" in df.columns:
    df_vend = df.groupby("Vendedora")["Ventas"].sum()
    st.bar_chart(df_vend)

# ==============================
# TABLA
# ==============================
st.subheader("📋 Datos")
st.dataframe(df)

# ==============================
# AUTO REFRESH
# ==============================
time.sleep(30)
st.rerun()
