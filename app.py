import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import os

# ================= CONFIG =================
st.set_page_config(page_title="LKPM System", layout="wide")

# --- SETUP AMAN (BISA PAKAI SECRETS ATAU LANGSUNG) ---
# Cara aman: Cek dulu ada tidak di secrets/env
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Kalau tidak ada (untuk testing lokal), isi manual di sini sementara:
if not url:
    url = "ISI_URL_SUPABASE_KAMU_DISINI" 
if not key:
    key = "ISI_KEY_SUPABASE_KAMU_DISINI"

try:
    supabase = create_client(url, key)
except Exception as e:
    st.error("Koneksi database gagal. Cek URL/Key.")
    st.stop()

# ================= THEME PREMIUM =================
st.markdown("""
<style>
body { background-color: #0e1117; }
.title { font-size: 34px; font-weight: 800; color: #ffffff; margin-bottom: 10px; }
.subtitle { color: #9aa4b2; margin-bottom: 30px; }
.card {
    background: linear-gradient(145deg, #161b22, #0f141b);
    padding: 20px; border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    border: 1px solid #222b36; margin-bottom: 15px;
}
.metric { font-size: 28px; font-weight: bold; color: #ffffff; }
.label { font-size: 13px; color: #8b949e; }
.login-box { background: #161b22; padding: 30px; border-radius: 16px; border: 1px solid #30363d; }
.stButton>button { width: 100%; border-radius: 10px; background: #2f81f7; color: white; font-weight: bold; border: none; }
.stButton>button:hover { background: #1f6feb; }
/* Agar table dark mode juga */
div.stDataFrame { background-color: #161b22; border-radius: 10px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# ================= LOGIN PAGE =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.markdown("<div class='title'>🏛️ LKPM System</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Dashboard Monitoring Investasi - Instansi</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            # Cek ke Database
            try:
                res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
                if res.data:
                    st.session_state.login = True
                    st.session_state.user = res.data[0]
                    st.rerun()
                else:
                    st.error("❌ Login gagal")
            except:
                st.error("❌ Error koneksi DB (Cek URL/Key)")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ================= LOAD DATA REAL =================
def load():
    try:
        data = supabase.table("lkpm").select("*").execute()
        return pd.DataFrame(data.data)
    except:
        return pd.DataFrame()

df = load()
if df.empty:
    df = pd.DataFrame(columns=["id", "nama", "kecamatan", "status", "pic", "wa"])

# ================= SIDEBAR =================
role = st.session_state.user.get("role", "user")
with st.sidebar:
    st.markdown(f"👋 **{st.session_state.user.get('username', 'User')}**")
    if role == "admin":
        menu = st.radio("Menu", ["Dashboard", "Data", "Import"])
    else:
        menu = "Dashboard"
    if st.button("Logout"):
        st.session_state.login = False
        st.rerun()

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.markdown("<div class='title'>Dashboard Monitoring LKPM</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Sistem Monitoring Investasi Daerah</div>", unsafe_allow_html=True)

    # Filter Role
    if role != "admin":
        df = df[df["kecamatan"] == st.session_state.user["username"]]

    total = len(df)
    sudah = len(df[df["status"] == "Sudah"]) if "status" in df.columns else 0
    belum = len(df[df["status"] == "Belum"]) if "status" in df.columns else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><div class='metric'>{total}</div><div class='label'>Total Perusahaan</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div class='metric' style='color:#3fb950;'>{sudah}</div><div class='label'>Sudah Lapor</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div class='metric' style='color:#f85149;'>{belum}</div><div class='label'>Belum Lapor</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Data Monitoring")
    st.dataframe(df, use_container_width=True)

# ================= IMPORT (ADMIN ONLY) =================
elif menu == "Import" and role == "admin":
    st.markdown("### 📤 Import Data Excel")
    file = st.file_uploader("Upload Excel", type=["xlsx"])
    if file:
        df_import = pd.read_excel(file)
        st.dataframe(df_import.head())
        cols = df_import.columns.tolist()
        
        with st.form("map"):
            nama = st.selectbox("Kolom Nama", cols)
            kec = st.selectbox("Kolom Kecamatan", cols)
            stat = st.selectbox("Kolom Status", cols)
            wa = st.selectbox("Kolom WA", cols)
            submit = st.form_submit_button("Import")

        if submit:
            for i, row in df_import.iterrows():
                supabase.table("lkpm").insert({
                    "nama": str(row[nama]),
                    "kecamatan": str(row[kec]),
                    "status": str(row[stat]),
                    "wa": str(row[wa])
                }).execute()
            st.success("Import Selesai!")
            st.rerun()
