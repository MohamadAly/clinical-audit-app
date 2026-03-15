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
        st.warning("Session expired.")
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

# --- 3. CUSTOM STYLING (The Watermark Rework) ---
def apply_custom_styling():
    st.markdown(f"""
        <style>
        /* Define the background on the app root */
        .stApp {{
            background-image: url("{BG_IMAGE_URL}");
            background-attachment: fixed;
            background-size: cover;
            position: relative;
        }}
        
        /* THE WATERMARK EFFECT: Add a faded, transparent white overlay BEFORE the main content */
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(255, 255, 255, 0.96); /* Extremely transparent white to fade the BG into a faint ghost */
            z-index: -1; /* Place it between the app-bg and the content */
        }}
        
        /* Data container styling - now fully transparent to let the ghosted BG show through */
        .main .block-container {{
            background-color: transparent; /* No longer a heavy white block, letting the ghosted BG through */
            border-radius: 12px;
            padding: 2.5rem;
            margin-top: 1rem;
        }}
        
        /* Modernized Tab Styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 15px;
            padding: 10px 0;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: rgba(240, 242, 246, 0.8);
            border-radius: 8px 8px 0 0;
            padding: 12px 25px;
            color: {TEXT_COLOR};
        }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{
            background-color: #FFFFFF;
            font-weight: bold;
            color: {MFT_BLUE};
        }}

        /* Rounded Buttons across the UI */
        .stButton button {{
            border-radius: 8px;
        }}
        
        /* Automatically hide the indices of st.dataframe */
        [data-testid="stDataFrame"] > div:first-child {{
            hide-index: True;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="CSS Portal Login", layout="centered")
    apply_custom_styling()
    
    l_col, r_col = st.columns([0.6, 0.4])
    with r_col: st.image(LOGO_URL, width=250)
    
    st.markdown(f"<h2 style='color: {MFT_BLUE}; margin-top: -30px;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Staff Name")
        u_site = st.selectbox("Primary Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Access CSS Portal"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state.update({"auth_status": True, "username": u_name, "user_role": u_role, "user_site": u_site, "last_activity": time.time()})
                st.rerun()
            else: st.error("Access Denied.")
    st.stop()

# --- 5. MAIN INTERFACE ---
st.set_page_config(page_title="CSS Audit Portal", layout="wide")
apply_custom_styling()
df = load_data()

# Main Header Layout
head_col, logo_col = st.columns([0.75, 0.25])
with head_col:
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #00A3DA 0%, {MFT_BLUE} 40%, {CSS_GREEN} 100%); padding: 20px; border-radius: 12px; color: white; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="margin: 0; font-size: 26px;">{HOSPITAL_NAME}</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.95; font-size: 16px;">
                🧑‍⚕️ <b>{st.session_state['username']}</b> | 🏥 <b>{st.session_state['user_site']}</b> | 🛡️ <b>{st.session_state['user_role']}</b>
            </p>
        </div>
    """, unsafe_allow_html=True)

with logo_col:
    st.image(LOGO_URL, width=280)
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": ""})
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 CSS Audit Registers", "⚙️ Actions & Registry", "📈 Directorate Intelligence"])

with tab1:
    with st.expander("🔍 Filter CSS Directorate Data", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1: search = st.text_input("Search ID, Title, Lead")
        with c2: f_site = st.multiselect("Filter by Hospital", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
        with c3: f_dept = st.multiselect("Filter by CSS Dept", sorted(list(df['Department'].unique())))

    # Multi-Level Data Visibility Logic
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

    reg_active, reg_completed = st.tabs([f"🚀 Active Workload ({len(active_df)})", f"✅ CSS Completed Archive ({len(done_df)})"])

    with reg_active:
        if not active_df.empty:
            active_df.insert(0, "Health", active_df.apply(lambda r: "🟢" if pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1))
            st.dataframe(active_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active audits found.")

    with reg_completed:
        if not done_df.empty:
            st.dataframe(done_df, use_container_width=True, hide_index=True)
        else:
            st.info("Archive is empty.")

with tab2:
    mode = st.radio("Task Selection:", ["Update Progress", "Register New Audit Proposal"], horizontal=True)

    if mode == "Update Progress":
        target_id = st.selectbox("Select ID to Update", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_stat = st.selectbox("Current Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                       index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                
                role = st.session_state['user_role']
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                a_upd = st.text_area("Audit Dept Comment", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
                q_upd = st.text_area("Q&S Safety Note", value=row['QS_Update']) if role in ["Q&S Department", "Audit Department"] else row['QS_Update']
                
                if st.form_submit_button("Update Audit"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                        [new_stat, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success("Database Synchronized"); st.rerun()

    else:
        st.subheader("📝 New CSS Audit Proposal")
        with st.form("new_reg"):
            c1, c2 = st.columns(2)
            with c1:
                n_id = st.text_input("Audit ID (Unique)")
                n_title = st.text_input("Audit Title")
                n_site = st.selectbox("Hospital Location", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site (Directorate)"])
                n_dept = st.selectbox("CSS Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology", "Pharmacy", "Physiotherapy"])
            with c2:
                n_lead = st.text_input("Project Lead", value=st.session_state['username'])
                n_due = st.date_input("First Bimonthly Deadline")
            
            st.divider()
            approved = st.radio("Approved by Site Lead?", ["No", "Yes"])
            app_name = st.text_input("Approving Lead Name:")
            
            if st.form_submit_button("Register Proposal"):
                if approved == "Yes" and n_id and app_name:
                    new_row = [n_id, "Local", n_site, n_dept, app_name, n_title, date.today(), n_lead, "", "Registered", "", n_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y")]
                    df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                    save_data(df); st.success("Registered in Directorate Workload"); st.rerun()

with tab3:
    st.subheader("📈 Directorate Intelligence")
    if not view_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(view_df, names='Status', title="Active Workload Mix", hole=0.3), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(view_df, x='Site', color='Status', title="CSS Audits by Hospital Site"), use_container_width=True)

# Footer Safety Display
st.markdown(f"--- \n ✅ **System Health:** Protected | 🛡️ **Last Backup:** {datetime.fromtimestamp(os.path.getmtime(RECOVERY_FILE)).strftime('%H:%M:%S') if os.path.exists(RECOVERY_FILE) else 'N/A'}")
