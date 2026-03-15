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

# Color Palette Definitions
MFT_BLUE = "#005EB8"
CSS_GREEN = "#009639"
TEXT_COLOR = "#333333"

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

# --- 3. CUSTOM STYLING (Watermark & Modern UI) ---
def apply_custom_styling():
    st.markdown(f"""
        <style>
        /* Faded Watermark Background Effect */
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.95)), url("{BG_IMAGE_URL}");
            background-size: cover;
            background-attachment: fixed;
        }}
        
        /* Main Container Styling */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.4);
            border-radius: 15px;
            padding: 2.5rem;
            margin-top: 1rem;
        }}
        
        /* Header Box Styling */
        .css-header {{
            background: linear-gradient(90deg, #00A3DA 0%, {MFT_BLUE} 40%, {CSS_GREEN} 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 25px;
        }}
        
        .stButton button {{ border-radius: 10px; }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="CSS Login", layout="centered")
    apply_custom_styling()
    
    col_l, col_r = st.columns([0.5, 0.5])
    with col_r: st.image(LOGO_URL, width=280)
    
    st.markdown(f"<h2 style='color: {MFT_BLUE};'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Full Name")
        u_site = st.selectbox("Your Home Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site (CSS Central)"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Log into CSS Portal"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state.update({"auth_status": True, "username": u_name, "user_role": u_role, "user_site": u_site})
                st.rerun()
    st.stop()

# --- 5. MAIN INTERFACE ---
st.set_page_config(page_title="CSS Audit Portal", layout="wide")
apply_custom_styling()
df = load_data()

# Header Layout
head_col, logo_col = st.columns([0.72, 0.28])
with head_col:
    st.markdown(f"""
        <div class="css-header">
            <h2 style="margin: 0; font-size: 28px;">{HOSPITAL_NAME}</h2>
            <p style="margin: 8px 0 0 0; opacity: 0.9; font-size: 18px;">
                <b>User:</b> {st.session_state['username']} | <b>Site:</b> {st.session_state['user_site']} | <b>Role:</b> {st.session_state['user_role']}
            </p>
        </div>
    """, unsafe_allow_html=True)

with logo_col:
    st.image(LOGO_URL, width=300)
    if st.button("🚪 Secure Sign Out", use_container_width=True):
        st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": ""})
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 CSS Audit Registers", "⚙️ Actions & Registry", "📈 Directorate Analytics"])

with tab1:
    with st.expander("🔍 Advanced Search & Filter", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1: search = st.text_input("Global Filter (Title, ID, Lead)")
        with c2: f_site = st.multiselect("Filter Hospital", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
        with c3: f_dept = st.multiselect("Filter Department", sorted(list(df['Department'].unique())))

    # Visibility Logic
    view_df = df.copy()
    if st.session_state['user_role'] == "Project Lead":
        view_df = view_df[view_df['Project_Lead'] == st.session_state['username']]
    elif st.session_state['user_role'] == "Site Lead":
        view_df = view_df[view_df['Site'] == st.session_state['user_site']]
    
    if search: view_df = view_df[view_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    if f_site: view_df = view_df[view_df['Site'].isin(f_site)]
    if f_dept: view_df = view_df[view_df['Department'].isin(f_dept)]

    active_df = view_df[view_df['Status'] != "Completed"].copy()
    done_df = view_df[view_df['Status'] == "Completed"].copy()

    t1, t2 = st.tabs([f"🚀 Active CSS Audits ({len(active_df)})", f"✅ Completed Archive ({len(done_df)})"])
    
    with t1:
        if not active_df.empty:
            active_df.insert(0, "Health", active_df.apply(lambda r: "🟢" if pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1))
            st.dataframe(active_df, use_container_width=True, hide_index=True)
        else: st.info("No active audits found for your current view.")

    with t2:
        st.dataframe(done_df, use_container_width=True, hide_index=True)

with tab2:
    mode = st.radio("Management Task:", ["Update Progress", "Register New Audit"], horizontal=True)
    if mode == "Update Progress":
        target_id = st.selectbox("Select Project ID", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_stat = st.selectbox("Current Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], index=0)
                
                role = st.session_state['user_role']
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Oversight", value=row['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                a_upd = st.text_area("Audit Dept Comment", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
                q_upd = st.text_area("QS Safety Update", value=row['QS_Update']) if role in ["Q&S Department", "Audit Department"] else row['QS_Update']
                
                if st.form_submit_button("Sync Changes"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                        [new_stat, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success("Database Updated Successfully"); st.rerun()
    else:
        st.subheader("📝 Register New Directorate Audit")
        with st.form("reg_form"):
            c1, c2 = st.columns(2)
            with c1:
                n_id = st.text_input("Audit ID")
                n_title = st.text_input("Project Title")
                n_site = st.selectbox("Hospital", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
                n_dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology", "Pharmacy", "Physiotherapy"])
            with c2:
                n_lead = st.text_input("Lead Name", value=st.session_state['username'])
                n_sup = st.text_input("Project Supervisor")
                n_due = st.date_input("Next Bimonthly Due Date")
            
            st.divider()
            approved = st.radio("Approved by Site Audit Lead?", ["No", "Yes"])
            app_name = st.text_input("Approving Lead's Name:")
            
            if st.form_submit_button("Confirm Registration"):
                if approved == "Yes" and n_id:
                    new_row = [n_id, "Local", n_site, n_dept, app_name, n_title, date.today(), n_lead, n_sup, "Registered", "", n_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y")]
                    df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                    save_data(df); st.success("Project Logged in CSS Database"); st.rerun()

with tab3:
    st.subheader("📈 CSS Directorate Overview")
    if not view_df.empty:
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(view_df, names='Status', title="Active Audit mix", hole=0.3), use_container_width=True)
        with c2: st.plotly_chart(px.bar(view_df, x='Site', color='Status', title="Workload per Hospital Site"), use_container_width=True)

st.markdown(f"--- \n ✅ **Directorate Database:** {CSV_FILE} | **Last System Sync:** {datetime.now().strftime('%H:%M:%S')}")
