import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

st.set_page_config(page_title="LKPM System", layout="wide")

# ================= SAFE CONFIG (ANTI ERROR) =================
SUPABASE_URL = ""
SUPABASE_KEY = ""

if "SUPABASE_URL" in st.secrets:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]

if "SUPABASE_KEY" in st.secrets:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = None

if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.title("🔐 Login LKPM")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):

        if supabase is None:
            st.error("Supabase belum dikonfigurasi")
            st.stop()

        res = supabase.table("users") \
            .select("*") \
            .eq("username", u) \
            .eq("password", p) \
            .execute()

        if res.data:
            st.session_state.user = res.data[0]
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Login gagal")

    st.stop()

# ================= USER =================
user = st.session_state.user
role = user["role"]

menu = st.sidebar.radio("Menu", ["Dashboard", "Data", "Import"])

# ================= LOAD DATA =================
def load_data():
    if supabase is None:
        return pd.DataFrame()

    data = supabase.table("lkpm").select("*").execute().data
    df = pd.DataFrame(data)

    if role == "kecamatan":
        df = df[df["kecamatan"] == user["username"]]

    return df

df = load_data()

# ================= DASHBOARD =================
if menu == "Dashboard":

    st.title("🏛️ Dashboard LKPM")

    if df.empty:
        st.warning("Belum ada data / Supabase belum aktif")
    else:
        c1, c2, c3 = st.columns(3)

        c1.metric("Total", len(df))
        c2.metric("Sudah", len(df[df["status"] == "Sudah"]))
        c3.metric("Belum", len(df[df["status"] == "Belum"]))

        st.bar_chart(df["kecamatan"].value_counts())

# ================= DATA =================
elif menu == "Data":

    st.title("📊 Data Perusahaan")

    st.dataframe(df, use_container_width=True)

# ================= IMPORT =================
elif menu == "Import":

    st.title("📁 Import Excel")

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:

        df_import = pd.read_excel(file)
        st.dataframe(df_import)

        cols = df_import.columns.tolist()

        nama = st.selectbox("Nama", cols)
        kec = st.selectbox("Kecamatan", cols)
        stat = st.selectbox("Status", cols)
        wa = st.selectbox("WA", cols)

        if st.button("Simpan"):

            if supabase is None:
                st.error("Supabase belum dikonfigurasi")
                st.stop()

            sukses = 0
            dup = 0

            for _, row in df_import.iterrows():

                cek = supabase.table("lkpm") \
                    .select("nama") \
                    .eq("nama", row[nama]) \
                    .execute()

                if cek.data:
                    dup += 1
                    continue

                supabase.table("lkpm").insert({
                    "nama": row[nama],
                    "kecamatan": row[kec],
                    "status": row[stat],
                    "wa": str(row[wa]),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }).execute()

                sukses += 1

            st.success(f"Berhasil: {sukses} | Duplikat: {dup}")
