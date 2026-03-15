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
LOGO_URL = "https://i.postimg.cc/sX22qTD7/Logo.png"
BG_IMAGE_URL = "https://i.postimg.cc/JzWzMr49/BG.png"

COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"
]

# --- DATA INITIALIZATION ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        for col in COLUMNS:
            if col not in df.columns: df[col] = ""
        return df
    except:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)
    shutil.copy(CSV_FILE, RECOVERY_FILE)

# --- STYLING ---
def apply_custom_styling():
    st.markdown(f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)), url("{BG_IMAGE_URL}");
            background-size: cover;
            background-attachment: fixed;
        }}
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.4);
            border-radius: 15px;
            padding: 2.5rem;
        }}
        .meeting-box {{
            background-color: #FFF0F0;
            border: 2px solid #FF4B4B;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- AUTHENTICATION ---
if "auth_status" not in st.session_state:
    st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": ""})

if not st.session_state["auth_status"]:
    st.set_page_config(page_title="CSS Portal Login", layout="centered")
    apply_custom_styling()
    st.image(LOGO_URL, width=300)
    st.title(HOSPITAL_NAME)
    with st.form("login"):
        u_name = st.text_input("Name")
        u_site = st.selectbox("Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Enter Portal"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.update({"auth_status": True, "username": u_name, "user_role": u_role, "user_site": u_site})
                st.rerun()
    st.stop()

# --- MAIN INTERFACE ---
st.set_page_config(page_title="CSS Audit Portal", layout="wide")
apply_custom_styling()
df = load_data()

# Header
h_col1, h_col2 = st.columns([0.7, 0.3])
with h_col1:
    st.markdown(f"## {HOSPITAL_NAME}")
    st.write(f"Logged in: **{st.session_state['username']}** | Site: **{st.session_state['user_site']}**")
with h_col2:
    st.image(LOGO_URL, width=280)
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state["auth_status"] = False
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 Audit Registers", "⚙️ Management", "📈 Analytics"])

with tab1:
    # MEETING MODE TOGGLE
    meeting_mode = st.toggle("🚨 **ENABLE MEETING MODE** (Focus on Red/Unapproved items only)")
    
    view_df = df.copy()
    
    # Calculate health for filtering
    view_df['Health'] = view_df.apply(lambda r: "🟢" if pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1)
    
    if meeting_mode:
        st.markdown('<div class="meeting-box"><b>Bimonthly Review Active:</b> Showing only projects that are overdue or require Site Lead sign-off.</div>', unsafe_allow_html=True)
        # Filter for Red health OR missing Site Lead approval
        view_df = view_df[(view_df['Health'] == "🔴") | (view_df['Site_Lead_Update'].isna()) | (view_df['Site_Lead_Update'] == "")]

    st.dataframe(view_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Action Center")
    mode = st.radio("Task", ["Add Progress Update", "Register New Audit (Link to Office Form)"], horizontal=True)
    
    if mode == "Add Progress Update":
        audit_id = st.selectbox("Select Audit", df['Audit_ID'].unique())
        with st.form("update_form"):
            new_status = st.selectbox("Status", ["Data Collection", "Analysis", "Drafting Report", "Complete"])
            new_comment = st.text_area("Progress Update")
            if st.form_submit_button("Sync Update"):
                df.loc[df['Audit_ID'] == audit_id, ['Status', 'Project_Lead_Update', 'Last_Updated']] = [new_status, new_comment, datetime.now().strftime("%d/%m/%Y")]
                save_data(df)
                st.success("Update Saved")
    else:
        st.info("🔗 [Click here to open the official MFT Audit Registration Office Form]")
        with st.form("reg_form"):
            n_id = st.text_input("Audit ID (from Office Form)")
            n_title = st.text_input("Project Title")
            n_site = st.selectbox("Hospital Site", ["ORC", "NMGH", "Wythenshawe", "Trafford"])
            if st.form_submit_button("Register in Portal"):
                new_row = [n_id, "Local", n_site, "CSS", "", n_title, date.today(), st.session_state['username'], "", "Registered", "", date.today(), "", "", "", "", date.today()]
                df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                save_data(df)
                st.rerun()

with tab3:
    st.subheader("Directorate Health Check")
    if not df.empty:
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.pie(df, names='Status', title="Project Stages"), use_container_width=True)
        c2.plotly_chart(px.bar(df, x='Site', color='Status', title="Site Workload"), use_container_width=True)

st.divider()
st.caption("CSS Audit Portal v2.0 | Targeting December 2026 Completion")
