import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import plotly.express as px
import shutil
import time

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
RECOVERY_FILE = 'audit_database_RECOVERY.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "MFT Clinical Support Services (CSS) - Cross-Site Portal"
SESSION_TIMEOUT_MINUTES = 30 
LOGO_URL = "https://i.postimg.cc/sX22qTD7/Logo.png"
BG_IMAGE_URL = "https://i.postimg.cc/JzWzMr49/BG.png"

# Color Palette
MFT_BLUE = "#005EB8"
CSS_GREEN = "#009639"

COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"
]

# --- 1. SESSION INITIALIZATION ---
if "auth_status" not in st.session_state:
    st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": "", "last_activity": time.time()})

if st.session_state["auth_status"]:
    if time.time() - st.session_state.get("last_activity", 0) > (SESSION_TIMEOUT_MINUTES * 60):
        st.session_state["auth_status"] = False
        st.stop()
    else:
        st.session_state["last_activity"] = time.time()

# --- 2. DATA ENGINE ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        for col in COLUMNS:
            if col not in df.columns: df[col] = ""
        return df[COLUMNS]
    except:
        return pd.read_csv(RECOVERY_FILE) if os.path.exists(RECOVERY_FILE) else pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)
    shutil.copy(CSV_FILE, RECOVERY_FILE)

# --- 3. CUSTOM STYLING (STABLE WATERMARK) ---
def apply_custom_styling():
    # We use a white gradient overlay on top of the image to 'fade' it into a watermark
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.94), rgba(255, 255, 255, 0.94)), url("{BG_IMAGE_URL}");
            background-size: cover;
            background-attachment: fixed;
        }}
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.4); /* Subtle boost for clarity */
            padding: 2rem;
            border-radius: 15px;
        }}
        .stButton button {{ border-radius: 8px; }}
        /* Header styling */
        .css-header {{
            background: linear-gradient(90deg, #00A3DA 0%, {MFT_BLUE} 40%, {CSS_GREEN} 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
            margin-bottom: 20px;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="CSS Login", layout="centered")
    apply_custom_styling()
    
    col_l, col_r = st.columns([0.4, 0.6])
    with col_r: st.image(LOGO_URL, width=280) # Increased logo size
    
    st.markdown(f"<h2 style='color: {MFT_BLUE};'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Name")
        u_site = st.selectbox("Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Access Portal"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.update({"auth_status": True, "username": u_name, "user_role": u_role, "user_site": u_site})
                st.rerun()
    st.stop()

# --- 5. MAIN INTERFACE ---
st.set_page_config(page_title="CSS Audit Portal", layout="wide")
apply_custom_styling()
df = load_data()

# Header with Logo and Sign Out
head_col, logo_col = st.columns([0.7, 0.3])
with head_col:
    st.markdown(f"""
        <div class="css-header">
            <h2 style="margin: 0;">{HOSPITAL_NAME}</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;"><b>{st.session_state['username']}</b> | {st.session_state['user_site']} | {st.session_state['user_role']}</p>
        </div>
    """, unsafe_allow_html=True)

with logo_col:
    st.image(LOGO_URL, width=280) # Increased logo size
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.update({"auth_status": False})
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 CSS Registers", "⚙️ Actions & Registry", "📈 Analytics"])

with tab1:
    with st.expander("🔍 Filters", expanded=False):
        c1, c2 = st.columns(2)
        search = c1.text_input("Search")
        f_site = c2.multiselect("Hospital", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])

    view_df = df.copy()
    if st.session_state['user_role'] == "Project Lead":
        view_df = view_df[view_df['Project_Lead'] == st.session_state['username']]
    elif st.session_state['user_role'] == "Site Lead":
        view_df = view_df[view_df['Site'] == st.session_state['user_site']]
    
    if search: view_df = view_df[view_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    if f_site: view_df = view_df[view_df['Site'].isin(f_site)]

    active_df = view_df[view_df['Status'] != "Completed"]
    done_df = view_df[view_df['Status'] == "Completed"]

    t_active, t_done = st.tabs([f"🚀 Active ({len(active_df)})", f"✅ Completed ({len(done_df)})"])
    with t_active: st.dataframe(active_df, use_container_width=True, hide_index=True)
    with t_done: st.dataframe(done_df, use_container_width=True, hide_index=True)

with tab2:
    mode = st.radio("Task:", ["Update", "Register"], horizontal=True)
    if mode == "Update":
        target_id = st.selectbox("Audit ID", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("upd"):
                new_stat = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], index=0)
                upd_text = st.text_area("Latest Update", value=row["Project_Lead_Update"])
                if st.form_submit_button("Save Changes"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Last_Updated"]] = [new_stat, upd_text, datetime.now().strftime("%d/%m/%Y")]
                    save_data(df); st.success("Updated"); st.rerun()
    else:
        with st.form("reg"):
            n_id = st.text_input("Audit ID")
            n_title = st.text_input("Title")
            n_site = st.selectbox("Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
            n_dept = st.selectbox("Dept", ["Anaesthesia", "Critical Care", "DLM", "Radiology", "Pharmacy"])
            if st.form_submit_button("Register"):
                new_row = [n_id, "Local", n_site, n_dept, "", n_title, date.today(), st.session_state['username'], "", "Registered", "", date.today(), "", "", "", "", datetime.now().strftime("%d/%m/%Y")]
                df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                save_data(df); st.success("Registered"); st.rerun()

with tab3:
    if not view_df.empty:
        st.plotly_chart(px.pie(view_df, names='Status', title="Directorate Mix", hole=0.3), use_container_width=True)

st.markdown("---")
st.caption(f"Directorate Database: {CSV_FILE} | Protected by clinical audit standards.")
