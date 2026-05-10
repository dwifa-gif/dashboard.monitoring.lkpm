import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard LKPM PRO", layout="wide")

# =========================
# LOGIN
# =========================
users = {
    "admin": "12345",
    "user": "12345"
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login Dashboard")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and users[u] == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Username / Password salah")
    st.stop()

# =========================
# HEADER
# =========================
st.title("📊 Dashboard Monitoring LKPM PRO")
st.caption("Versi Instansi + PIC Wilayah")

# =========================
# UPLOAD DATA
# =========================
file = st.sidebar.file_uploader("Upload Data OSS / LKPM", type=["xlsx"])

if not file:
    st.warning("Upload file dulu")
    st.stop()

df = pd.read_excel(file)

# =========================
# CLEANING
# =========================
df = df.rename(columns={
    "real NIB": "NIB",
    "nama_perusahaan": "Nama",
    "kecamatan_usaha": "Kecamatan"
})

df = df[["NIB", "Nama", "Kecamatan"]]
df = df.drop_duplicates(subset="NIB")
df = df.fillna("")

# =========================
# STATUS LKPM
# =========================
df["Frekuensi"] = 1
df["Status"] = df["Frekuensi"].apply(lambda x: "Sudah" if x > 0 else "Belum")

# =========================
# PIC PER KECAMATAN
# =========================
pic_map = {
    "Tanah Abang": {"PIC": "Budi", "WA": "08123456789"},
    "Menteng": {"PIC": "Sari", "WA": "08234567890"},
    "Gambir": {"PIC": "Andi", "WA": "08345678901"}
}

def get_pic(kec):
    return pic_map.get(kec, {}).get("PIC", "-")

def get_wa(kec):
    return pic_map.get(kec, {}).get("WA", "-")

df["PIC"] = df["Kecamatan"].apply(get_pic)
df["WA"] = df["Kecamatan"].apply(get_wa)

# =========================
# LINK WHATSAPP
# =========================
def wa_link(nomor, nama):
    if nomor == "-" or nomor == "":
        return ""
    nomor = nomor.replace("0", "62", 1)
    return f"https://wa.me/{nomor}?text=Halo%20{nama}%20terkait%20LKPM"

df["Chat"] = df.apply(lambda x: wa_link(x["WA"], x["Nama"]), axis=1)

# =========================
# KPI
# =========================
st.subheader("📌 Ringkasan")

col1, col2, col3 = st.columns(3)

total = len(df)
sudah = len(df[df["Status"] == "Sudah"])
belum = len(df[df["Status"] == "Belum"])

col1.metric("Total Perusahaan", total)
col2.metric("Sudah Lapor", sudah)
col3.metric("Belum Lapor", belum)

# =========================
# FILTER
# =========================
kecamatan = st.multiselect(
    "Filter Kecamatan",
    df["Kecamatan"].unique(),
    default=df["Kecamatan"].unique()
)

df = df[df["Kecamatan"].isin(kecamatan)]

# =========================
# GRAFIK
# =========================
st.subheader("📊 Ranking Kecamatan")

rank = df["Kecamatan"].value_counts().reset_index()
rank.columns = ["Kecamatan", "Jumlah"]

fig = px.bar(rank, x="Kecamatan", y="Jumlah")
st.plotly_chart(fig, use_container_width=True)

# =========================
# MAP
# =========================
df["Lat"] = -6.17
df["Lng"] = 106.83
st.subheader("🗺️ Peta")
st.map(df[["Lat", "Lng"]])

# =========================
# TABEL
# =========================
st.subheader("📋 Data Perusahaan")

st.dataframe(df[["Nama", "Kecamatan", "Status", "PIC", "WA"]], use_container_width=True)

# =========================
# KONTAK WA
# =========================
st.subheader("📲 Kontak PIC")

for i, row in df.iterrows():
    if row["Chat"]:
        st.markdown(f"""
        **{row['Nama']}** - {row['Kecamatan']}  
        PIC: {row['PIC']}  
        📲 [Chat WhatsApp]({row['Chat']})
        """)

# =========================
# EXPORT CSV
# =========================
csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Download CSV",
    data=csv,
    file_name="lkpm.csv",
    mime="text/csv"
)

# =========================
# EXPORT PDF (NO ERROR)
# =========================
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def make_pdf(data):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "LAPORAN LKPM", 0, 1, "C")

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Tanggal: {datetime.now()}", 0, 1)

    for i, row in data.iterrows():
        pdf.cell(0, 8, clean_text(row["Nama"]), 0, 1)

    pdf.output("laporan.pdf")

if st.button("📄 Export PDF"):
    make_pdf(df)
    with open("laporan.pdf", "rb") as f:
        st.download_button("Download PDF", f, file_name="laporan.pdf")
