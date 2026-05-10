import streamlit as st
import pandas as pd

st.set_page_config(page_title="LKPM System", layout="wide")

# ================= THEME =================
st.markdown("""
<style>

/* BACKGROUND */
body {
    background-color: #0e1117;
}

/* TITLE */
.title {
    font-size: 34px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 10px;
}

/* SUBTITLE */
.subtitle {
    color: #9aa4b2;
    margin-bottom: 30px;
}

/* CARD */
.card {
    background: linear-gradient(145deg, #161b22, #0f141b);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: 0.3s ease;
    border: 1px solid #222b36;
}

/* ANIMASI HOVER */
.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.6);
    border: 1px solid #2f81f7;
}

/* METRIC */
.metric {
    font-size: 28px;
    font-weight: bold;
    color: #ffffff;
}

.label {
    font-size: 13px;
    color: #8b949e;
}

/* LOGIN BOX */
.login-box {
    background: #161b22;
    padding: 30px;
    border-radius: 16px;
    border: 1px solid #30363d;
}

/* BUTTON */
.stButton>button {
    width: 100%;
    border-radius: 10px;
    background: #2f81f7;
    color: white;
    font-weight: bold;
    border: none;
}

.stButton>button:hover {
    background: #1f6feb;
}

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
            if u == "admin" and p == "admin":
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Login gagal")

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ================= DATA MOCK =================
df = pd.DataFrame({
    "kecamatan": ["A", "B", "C", "A", "B", "C"],
    "status": ["Sudah", "Belum", "Sudah", "Sudah", "Belum", "Sudah"]
})

# ================= HEADER =================
st.markdown("<div class='title'>Dashboard Monitoring LKPM</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Sistem Monitoring Investasi Daerah</div>", unsafe_allow_html=True)

# ================= KPI CARDS =================
total = len(df)
sudah = len(df[df["status"] == "Sudah"])
belum = len(df[df["status"] == "Belum"])

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="card">
        <div class="metric">{total}</div>
        <div class="label">Total Perusahaan</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="card">
        <div class="metric">{sudah}</div>
        <div class="label">Sudah Lapor</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="card">
        <div class="metric">{belum}</div>
        <div class="label">Belum Lapor</div>
    </div>
    """, unsafe_allow_html=True)

# ================= TABLE =================
st.markdown("### 📊 Data Monitoring")

st.dataframe(df, use_container_width=True)

# ================= CHART =================
st.markdown("### 📈 Analitik Kecamatan")

st.bar_chart(df["kecamatan"].value_counts())

# ================= FOOTER =================
st.markdown("---")
st.markdown("🔐 Sistem Monitoring LKPM • Version Premium UI")
