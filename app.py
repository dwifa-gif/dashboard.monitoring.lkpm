import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="LKPM System", layout="wide")

SUPABASE_URL = "ISI_URL_KAMU"
SUPABASE_KEY = "ISI_KEY_KAMU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login LKPM")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()

        if res.data:
            st.session_state.login = True
            st.session_state.user = res.data[0]
            st.rerun()
        else:
            st.error("Login gagal")

    st.stop()

# ================= MENU =================
menu = st.sidebar.radio("Menu", ["Dashboard", "Data", "Import", "Log"])

# ================= LOAD DATA =================
def load_data():
    data = supabase.table("lkpm").select("*").execute()
    return pd.DataFrame(data.data)

df = load_data()

# ================= DASHBOARD =================
if menu == "Dashboard":

    st.title("🏛️ Dashboard LKPM")

    if df.empty:
        st.warning("Belum ada data")
    else:
        total = len(df)
        sudah = len(df[df["status"] == "Sudah"])
        belum = len(df[df["status"] == "Belum"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Total", total)
        c2.metric("Sudah", sudah)
        c3.metric("Belum", belum)

        chart = df.groupby("kecamatan").size().reset_index(name="jumlah")
        fig = px.bar(chart, x="kecamatan", y="jumlah")
        st.plotly_chart(fig, use_container_width=True)

# ================= DATA =================
elif menu == "Data":

    st.subheader("Data Perusahaan")

    if not df.empty:
        df["wa_link"] = "https://wa.me/" + df["wa"].astype(str)
        st.dataframe(df)
    else:
        st.info("Data kosong")

# ================= IMPORT =================
elif menu == "Import":

    st.subheader("Import Excel")

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:

        df_import = pd.read_excel(file)
        st.dataframe(df_import)

        cols = df_import.columns.tolist()

        nama = st.selectbox("Nama", cols)
        kec = st.selectbox("Kecamatan", cols)
        stat = st.selectbox("Status", cols)
        wa = st.selectbox("WA", cols)

        if st.button("Import Data"):

            sukses = 0
            dup = 0

            for _, row in df_import.iterrows():

                cek = supabase.table("lkpm").select("nama").eq("nama", row[nama]).execute()

                if cek.data:
                    dup += 1
                    continue

                supabase.table("lkpm").insert({
                    "nama": row[nama],
                    "kecamatan": row[kec],
                    "status": row[stat],
                    "pic": "",
                    "wa": str(row[wa])
                }).execute()

                sukses += 1

            supabase.table("log_import").insert({
                "user": st.session_state.user["username"],
                "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "total": len(df_import),
                "berhasil": sukses,
                "duplikat": dup
            }).execute()

            st.success(f"Import selesai ✔ Berhasil: {sukses} | Duplikat: {dup}")

# ================= LOG =================
elif menu == "Log":

    st.subheader("Log Import")

    log = supabase.table("log_import").select("*").execute()

    if log.data:
        st.dataframe(pd.DataFrame(log.data))
    else:
        st.info("Belum ada log")
