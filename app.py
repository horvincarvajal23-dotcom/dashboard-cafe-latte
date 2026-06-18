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
# LOGIN
# ==============================

import streamlit_authenticator as stauth

# 🔐 Generar password en HASH (importante para evitar errores)
hashed_passwords = stauth.Hasher(["1234"]).generate()

# Credenciales en formato correcto
credentials = {
    "usernames": {
        "admin": {
            "name": "Admin",
            "password": hashed_passwords[0]
        }
    }
}

# Crear autenticador
authenticator = stauth.Authenticate(
    credentials,
    "dashboard_cookie",
    "clave_secreta",
    cookie_expiry_days=1
)

# Mostrar login
name, auth_status, username = authenticator.login("🔐 Login", "main")

# Validaciones
if auth_status is False:
    st.error("❌ Usuario o contraseña incorrectos")
    st.stop()

if auth_status is None:
    st.warning("⚠️ Ingrese sus credenciales")
    st.stop()

# Si login OK
st.success(f"✅ Bienvenido {name}")

name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    st.stop()

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
# LIMPIEZA
# ==============================

if "INGRESE EL TOTAL DE LA VENTA" in df.columns:
    df["Ventas"] = pd.to_numeric(
        df["INGRESE EL TOTAL DE LA VENTA"],
        errors="coerce"
    )

if "FECHA" in df.columns:
    df["Fecha"] = pd.to_datetime(df["FECHA"], errors="coerce")

if "VENDEDORA" in df.columns:
    df["Vendedora"] = df["VENDEDORA"]

# eliminar nulos
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