import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Dashboard Café Latte", layout="wide")

st.title("📊 Dashboard Café Latte (Tiempo Real)")
# ==============================
# LOGIN ESTABLE (SIN DUPLICADOS)
# ==============================

import streamlit as st
import streamlit_authenticator as stauth

# ✅ SOLO CREAR UNA VEZ (uso de session_state)
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

# ✅ LOGIN (solo una vez)
authenticator.login()

# ✅ VALIDACIONES
if st.session_state.get("authentication_status") is False:
    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

if st.session_state.get("authentication_status") is None:
    st.warning("⚠️ Ingrese sus credenciales")
    st.stop()

# ✅ LOGIN OK
st.success(f"✅ Bienvenido {st.session_state.get('name')}")
# ==============================
# ✅ CONEXION A SHAREPOINT
# ==============================

@st.cache_data(ttl=30)
def load_data():

    try:
        url = "PEGA_AQUI_TU_LINK_DIRECTO"  # 👈 IMPORTANTE

        response = requests.get(url)
        file = BytesIO(response.content)

        df = pd.read_excel(file)

        return df

    except Exception as e:
        st.error("Error cargando datos")
        return pd.DataFrame()

df = load_data()

# ==============================
# LIMPIEZA CORRECTA Y ROBUSTA
# ==============================

# ✅ convertir nombres de columnas a string limpio
df.columns = [str(col).strip() for col in df.columns]

# ✅ eliminar columnas basura tipo "Unnamed"
df = df.loc[:, ~pd.Series(df.columns).str.contains("Unnamed", case=False)]

# ✅ DEBUG (opcional, puedes quitar después)
st.write("Columnas detectadas:", df.columns)

# ==============================
# DETECTAR COLUMNA DE VENTAS
# ==============================

col_ventas = None

for col in df.columns:
    if "VENTA" in col.upper():
        col_ventas = col
        break

if col_ventas is None:
    st.error("❌ No se encontró columna de ventas en el Excel")
    st.stop()

# ✅ crear columna estándar
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

# ==============================
# LIMPIAR DATOS INVALIDOS
# ==============================

df = df.dropna(subset=["Ventas"])
# ==============================
# FILTROS
# ==============================
st.sidebar.header("Filtros")

if "Vendedora" in df:
    vendedor = st.sidebar.selectbox(
        "Vendedora",
        ["Todas"] + list(df["Vendedora"].dropna().unique())
    )

    if vendedor != "Todas":
        df = df[df["Vendedora"] == vendedor]

# ==============================
# KPIs
# ==============================
col1, col2, col3 = st.columns(3)

col1.metric("💰 Ventas Totales", round(df["Ventas"].sum(),2))
col2.metric("📊 Registros", len(df))
col3.metric("📈 Promedio", round(df["Ventas"].mean(),2))

# ==============================
# GRAFICOS
# ==============================

st.subheader("📈 Ventas por Fecha")

df_fecha = df.groupby("Fecha")["Ventas"].sum()

st.line_chart(df_fecha)

# ==============================
# TABLA
# ==============================
st.subheader("📋 Datos")

st.dataframe(df)

# ==============================
# AUTO REFRESH
# ==============================
import time
time.sleep(30)
st.rerun()
