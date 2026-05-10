import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import urllib.parse
from fpdf import FPDF

# ================= CONFIG =================
st.set_page_config(page_title="SIMPEL LKPM", layout="wide")

# ================= DATA =================
@st.cache_data
def load_data():
    return pd.DataFrame({
        "Nama":["PT Maju","CV Digital","PT Sejahtera","PT Properti","CV Logistik"],
        "NIB":["001","002","003","004","005"],
        "Kecamatan":["Menteng","Senen","Tanah Abang","Kemayoran","Gambir"],
        "Status":["✅ Sudah","❌ Belum","✅ Sudah","❌ Belum","❌ Belum"],
        "Frekuensi":[3,0,2,0,1],
        "Lat":[-6.18,-6.17,-6.16,-6.19,-6.18],
        "Lng":[106.84,106.85,106.83,106.82,106.84],
        "Periode":["Jan","Feb","Mar","Apr","Mei"]
    })

df = load_data()

# ================= LOGIN =================
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "staff": {"password": "123", "role": "staff"}
}

if "login" not in st.session_state:
    st.session_state.login = False
if "user" not in st.session_state:
    st.session_state.user = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# ================= LOGIN PAGE =================
if not st.session_state.login:
    st.title("🏛️ SIMPEL LKPM")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in users and p == users[u]["password"]:
            st.session_state.login = True
            st.session_state.user = u
            st.session_state.role = users[u]["role"]
            st.rerun()
        else:
            st.error("Username / Password salah")

# ================= DASHBOARD =================
else:
    st.markdown("## 📊 Dashboard Monitoring LKPM")

    # SIDEBAR
    with st.sidebar:
        st.success(f"Login: {st.session_state.user}")
        st.write(f"Role: {st.session_state.role}")

        if st.button("Logout"):
            st.session_state.login = False
            st.rerun()

        kec = st.multiselect("Kecamatan", df.Kecamatan.unique(), default=df.Kecamatan.unique())
        stat = st.multiselect("Status", df.Status.unique(), default=df.Status.unique())

    f = df[(df.Kecamatan.isin(kec)) & (df.Status.isin(stat))]

    # KPI
    total = len(f)
    sudah = len(f[f.Status.str.contains("Sudah")])
    belum = len(f[f.Status.str.contains("Belum")])
    persen = (sudah / total * 100) if total > 0 else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Data", total)
    c2.metric("Sudah Lapor", sudah)
    c3.metric("Belum Lapor", belum)
    c4.metric("Kepatuhan", f"{persen:.1f}%")

    st.divider()

    # CHART
    col1, col2 = st.columns(2)

    with col1:
        if not f.empty:
            fig = px.pie(f, names='Status', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

            bar = f.groupby('Kecamatan').size().reset_index(name='Jumlah')
            fig2 = px.bar(bar, x='Kecamatan', y='Jumlah')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Tidak ada data")

    with col2:
        if not f.empty:
            hist = px.histogram(f, x='Frekuensi', color='Status')
            st.plotly_chart(hist, use_container_width=True)

            trend = f.groupby('Periode').size().reset_index(name='Jumlah')
            fig3 = px.line(trend, x='Periode', y='Jumlah', markers=True)
            st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # TABLE
    st.subheader("📋 Data Perusahaan")
    st.dataframe(f, use_container_width=True)

    # DOWNLOAD CSV
    csv = f.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", csv, "lkpm.csv")

    # PDF
    def make_pdf(data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        for _, r in data.iterrows():
            pdf.cell(200, 8, txt=f"{r['Nama']} - {r['Status']}", ln=True)

        pdf.output("laporan.pdf")

    if st.button("📄 Export PDF"):
        make_pdf(f)
        with open("laporan.pdf", "rb") as file:
            st.download_button("Download PDF", file, "laporan.pdf")

    st.divider()

    # WA FOLLOW UP
    st.subheader("📲 Follow Up WhatsApp")

    for _, r in f.iterrows():
        if "Belum" in r.Status:
            msg = f"Halo {r.Nama}, mohon segera melakukan pelaporan LKPM."
            link = "https://wa.me/?text=" + urllib.parse.quote(msg)
            st.link_button(f"Kirim WA ke {r.Nama}", link)

    st.divider()

    # MAP
    st.subheader("🗺️ Peta Sebaran")

    if not f.empty:
        m = folium.Map(location=[-6.18,106.84], zoom_start=12)

        for _, r in f.iterrows():
            color = "green" if r.Frekuensi > 1 else "red"

            folium.Marker(
                [r.Lat, r.Lng],
                popup=f"{r.Nama} - {r.Status}",
                icon=folium.Icon(color=color)
            ).add_to(m)

        st_folium(m, width=1000, height=500)
    else:
        st.warning("Tidak ada data peta")