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
        st.warning("Session expired for security.")
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

# --- 3. CUSTOM STYLING ---
def apply_custom_styling():
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{BG_IMAGE_URL}");
            background-attachment: fixed;
            background-size: cover;
        }}
        /* Data container styling */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.94);
            border-radius: 12px;
            padding: 2.5rem;
            margin-top: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        /* Sidebar/Tab styling */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #f0f2f6;
            border-radius: 5px 5px 0 0;
            padding: 10px 20px;
        }}
        </style>
        """, unsafe_allow_html=True)

# --- 4. LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="CSS Audit Login", layout="centered")
    apply_custom_styling()
    
    # Header with Logo for Login
    l_col, r_col = st.columns([0.7, 0.3])
    with r_col: st.image(LOGO_URL, width=150)
    
    st.markdown(f"<h2 style='color: #005EB8; margin-top: -20px;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Staff Name")
        u_site = st.selectbox("Primary Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site (CSS Central)"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Access CSS Portal"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state.update({"auth_status": True, "username": u_name, "user_role": u_role, "user_site": u_site, "last_activity": time.time()})
                st.rerun()
    st.stop()

# --- 5. MAIN INTERFACE ---
st.set_page_config(page_title="CSS Audit Portal", layout="wide")
apply_custom_styling()
df = load_data()

# Main Header Layout
head_col, logo_col = st.columns([0.8, 0.2])
with head_col:
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #005EB8 0%, #009639 100%); padding: 18px; border-radius: 12px; color: white;">
            <h2 style="margin: 0; font-size: 24px;">{HOSPITAL_NAME}</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 16px;">
                <b>{st.session_state['username']}</b> | <b>{st.session_state['user_site']}</b> | <b>{st.session_state['user_role']}</b>
            </p>
        </div>
    """, unsafe_allow_html=True)

with logo_col:
    st.image(LOGO_URL, width=180)
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": ""})
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 CSS Registers", "⚙️ Actions & Registry", "📈 Directorate Analytics"])

with tab1:
    with st.expander("🔍 Filter CSS Directorate Data", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1: search = st.text_input("Global Search")
        with c2: f_site = st.multiselect("Filter by Hospital", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
        with c3: f_dept = st.multiselect("Filter by CSS Dept", sorted(list(df['Department'].unique())))

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

    reg_active, reg_completed = st.tabs([f"🚀 Active CSS Audits ({len(active_df)})", f"✅ Completed CSS Audits ({len(done_df)})"])

    with reg_active:
        if not active_df.empty:
            active_df.insert(0, "Health", active_df.apply(lambda r: "🟢" if pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1))
            st.dataframe(active_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active CSS audits currently listed.")

    with reg_completed:
        if not done_df.empty:
            st.dataframe(done_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed CSS audits found.")

with tab2:
    mode = st.radio("Task Selection:", ["Update Progress", "Register New CSS Audit"], horizontal=True)

    if mode == "Update Progress":
        target_id = st.selectbox("Select Audit ID", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_stat = st.selectbox("Current Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                       index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                
                role = st.session_state['user_role']
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                a_upd = st.text_area("Audit Dept Update", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
                q_upd = st.text_area("QS Update", value=row['QS_Update']) if role in ["Q&S Department", "Audit Department"] else row['QS_Update']
                
                if st.form_submit_button("Update Audit"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                        [new_stat, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success("Database Synchronized"); st.rerun()

    else:
        st.subheader("📝 New CSS Audit Registration")
        with st.form("new_reg"):
            c1, c2 = st.columns(2)
            with c1:
                n_id = st.text_input("Audit ID")
                n_title = st.text_input("Audit Title")
                n_site = st.selectbox("Location Site", ["ORC", "NMGH", "Wythenshawe", "Trafford", "Cross-Site"])
                n_dept = st.selectbox("CSS Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology", "Pharmacy", "Physiotherapy"])
            with c2:
                n_lead = st.text_input("Project Lead", value=st.session_state['username'])
                n_sup = st.text_input("Project Supervisor")
                n_due = st.date_input("Initial Bimonthly Deadline")
            
            st.divider()
            approved = st.radio("Site Lead Approved?", ["No", "Yes"])
            app_name = st.text_input("Approving Lead Name:")
            
            if st.form_submit_button("Register Audit"):
                if approved == "Yes" and n_id:
                    new_row = [n_id, "Local", n_site, n_dept, app_name, n_title, date.today(), n_lead, n_sup, "Registered", "", n_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y")]
                    df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                    save_data(df); st.success("Audit Successfully Registered"); st.rerun()

with tab3:
    st.subheader("📈 Directorate-Wide Analytics")
    if not view_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(view_df, names='Status', title="Overall Status Distribution", hole=0.3), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(view_df, x='Site', color='Status', title="Workload by Hospital Site"), use_container_width=True)

# Footer Safety
st.markdown(f"--- \n ✅ **System Health:** Online | 🛡️ **Shadow Copy:** {datetime.fromtimestamp(os.path.getmtime(RECOVERY_FILE)).strftime('%H:%M:%S') if os.path.exists(RECOVERY_FILE) else 'N/A'}")
