import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime

# ================= CONFIG =================
st.set_page_config(page_title="LKPM System", layout="wide")

# --- PENTING: GANTI DENGAN KEY KAMU SUPAYA JALAN ---
SUPABASE_URL = "https://CONTOHREFSUPABASE.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= STYLE =================
st.markdown("""
<style>
.kpi-box {
    background: white;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #1f4e79;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ================= LOGIN =================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login LKPM")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login", use_container_width=True):
            try:
                # Cek login ke Supabase
                res = supabase.table("users").select("*").eq("username", u).eq("password", p).maybe_single().execute()
                if res.data:
                    st.session_state.login = True
                    st.session_state.user = res.data
                    st.rerun()
                else:
                    st.error("❌ Username atau Password salah")
            except Exception as e:
                st.error(f"Error koneksi: {e}")

    st.stop()

# ================= SIDEBAR =================
role = st.session_state.user["role"]

with st.sidebar:
    st.write(f"👋 Halo, **{st.session_state.user['username']}**")
    if role == "admin":
        menu = st.radio("Menu", ["Dashboard", "Data", "Import", "Log"])
    else:
        menu = st.radio("Menu", ["Dashboard", "Data"])
    
    if st.button("Logout"):
        st.session_state.login = False
        st.rerun()

# ================= LOAD DATA =================
def load():
    try:
        data = supabase.table("lkpm").select("*").execute()
        return pd.DataFrame(data.data)
    except:
        return pd.DataFrame()

df = load()

# Handle Data Kosong
if df.empty:
    df = pd.DataFrame(columns=["id", "nama", "kecamatan", "status", "pic", "wa"])

# Filter untuk user kecamatan
if role != "admin" and not df.empty:
    df = df[df["kecamatan"] == st.session_state.user["username"]]

# ================= DASHBOARD =================
if menu == "Dashboard":
    st.title("🏛️ Dashboard LKPM")

    if df.empty or len(df) == 0:
        st.info("👋 Selamat datang! Data masih kosong, silakan import data.")
    else:
        total = len(df)
        sudah = len(df[df["status"] == "Sudah"])
        belum = len(df[df["status"] == "Belum"])

        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Total Perusahaan", total)
        c2.metric("✅ Sudah Lapor", sudah)
        c3.metric("⚠️ Belum Lapor", belum)

        st.markdown("---")
        
        # Grafik
        if "kecamatan" in df.columns:
            rank = df.groupby("kecamatan").size().reset_index(name="jumlah")
            fig = px.bar(rank, x="kecamatan", y="jumlah", color="jumlah", title="Persebaran Data")
            st.plotly_chart(fig, use_container_width=True)

# ================= DATA =================
elif menu == "Data":
    st.subheader("📋 Data Perusahaan")
    
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download CSV", csv, "data_lkpm.csv", "text/csv")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Data tidak tersedia.")

# ================= IMPORT =================
elif menu == "Import" and role == "admin":
    st.subheader("📤 Import Excel")

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        try:
            df_import = pd.read_excel(file)
            st.dataframe(df_import.head())
            
            cols = df_import.columns.tolist()
            
            with st.form("mapping_form"):
                st.write("Mapping Kolom:")
                nama = st.selectbox("Nama Perusahaan", cols)
                kec = st.selectbox("Kecamatan", cols)
                stat = st.selectbox("Status", cols)
                pic = st.selectbox("PIC", ["-"] + cols)
                wa = st.selectbox("No. WA", cols)
                
                submitted = st.form_submit_button("Proses Import")

            if submitted:
                # Validasi WA (pastikan angka)
                invalid_rows = df_import[~df_import[wa].astype(str).str.isdigit()]
                if not invalid_rows.empty:
                    st.error(f"Ada {len(invalid_rows)} nomor WA tidak valid.")
                else:
                    prog = st.progress(0, text="Memulai import...")
                    sukses = 0
                    dup = 0

                    for i, row in df_import.iterrows():
                        # Cek duplikat
                        cek = supabase.table("lkpm").select("id").eq("nama", str(row[nama])).execute()
                        
                        if cek.data:
                            dup += 1
                        else:
                            supabase.table("lkpm").insert({
                                "nama": str(row[nama]),
                                "kecamatan": str(row[kec]),
                                "status": str(row[stat]),
                                "pic": str(row[pic]) if pic != "-" else "",
                                "wa": str(row[wa])
                            }).execute()
                            sukses += 1
                        
                        prog.progress((i+1)/len(df_import), text=f"Proses {i+1}/{len(df_import)}")

                    # Log Import
                    supabase.table("log_import").insert({
                        "user": st.session_state.user["username"],
                        "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "total": len(df_import),
                        "berhasil": sukses,
                        "duplikat": dup
                    }).execute()

                    st.success(f"✅ Selesai! Sukses: {sukses}, Duplikat: {dup}")
                    st.rerun()
        except Exception as e:
            st.error(f"Error file: {e}")

# ================= LOG =================
elif menu == "Log" and role == "admin":
    st.subheader("📜 Log Aktivitas")
    log = supabase.table("log_import").select("*").order("id", desc=True).execute()
    if log.data:
        st.dataframe(pd.DataFrame(log.data), use_container_width=True)
    else:
        st.info("Belum ada log.")
