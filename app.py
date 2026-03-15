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
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"
SESSION_TIMEOUT_MINUTES = 30 

# THE 17 ESSENTIAL AUDIT DATA FIELDS RESTORED
COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"
]

# --- 1. SESSION INITIALIZATION ---
if "auth_status" not in st.session_state:
    st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": "", "last_activity": time.time()})

# Timeout Check
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

# --- 3. LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="MFT Login", layout="centered")
    st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Name")
        u_site = st.selectbox("Site", ["ORC", "NMGH", "Wythenshawe", "Trafford"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state.update({"auth_status": True, "username": u_name, "user_role": u_role, "user_site": u_site, "last_activity": time.time()})
                st.rerun()
    st.stop()

# --- 4. MAIN INTERFACE ---
st.set_page_config(page_title="MFT Audit Portal", layout="wide")
df = load_data()

st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0;">{HOSPITAL_NAME} - {st.session_state['user_site']}</h3>
        <p style="margin: 0; opacity: 0.9;">{st.session_state['username']} | {st.session_state['user_role']}</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Registers", "⚙️ Actions & Registry", "📈 Analytics"])

with tab1:
    with st.expander("🔍 Search & Filter", expanded=False):
        search = st.text_input("Global Search (ID, Title, Lead)")
        f_dept = st.multiselect("Filter Department", sorted(list(df['Department'].unique())))

    # Visibility Filter Logic
    view_df = df.copy()
    if st.session_state['user_role'] == "Project Lead":
        view_df = view_df[view_df['Project_Lead'] == st.session_state['username']]
    elif st.session_state['user_role'] == "Site Lead":
        view_df = view_df[view_df['Site'] == st.session_state['user_site']]
    
    if search: view_df = view_df[view_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    if f_dept: view_df = view_df[view_df['Department'].isin(f_dept)]

    # Segregation into Active and Completed
    active_df = view_df[view_df['Status'] != "Completed"].copy()
    done_df = view_df[view_df['Status'] == "Completed"].copy()

    reg_active, reg_completed = st.tabs([f"🚀 Active Audits ({len(active_df)})", f"✅ Completed Audits ({len(done_df)})"])

    with reg_active:
        if not active_df.empty:
            active_df.insert(0, "Health", active_df.apply(lambda r: "🟢" if pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1))
            st.dataframe(active_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active clinical audits found.")

    with reg_completed:
        if not done_df.empty:
            st.dataframe(done_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed clinical audits found.")

with tab2:
    mode = st.radio("Task Selection:", ["Update Progress", "Register New Audit"], horizontal=True)

    if mode == "Update Progress":
        # Can only update things visible in the current user's view
        target_id = st.selectbox("Select Audit ID to Update", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_stat = st.selectbox("Current Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                       index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                
                # Role-Based Editing
                role = st.session_state['user_role']
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                a_upd = st.text_area("Audit Dept Update", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
                q_upd = st.text_area("QS Update", value=row['QS_Update']) if role in ["Q&S Department", "Audit Department"] else row['QS_Update']
                
                if st.form_submit_button("Sync Changes"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                        [new_stat, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success(f"Audit {target_id} Updated Successfully"); st.rerun()

    else:
        st.subheader("📝 New Audit Registration")
        with st.form("new_reg"):
            c1, c2 = st.columns(2)
            with c1:
                n_id = st.text_input("Audit ID (Required)")
                n_title = st.text_input("Audit Title")
                n_type = st.selectbox("Audit Type", ["Initial", "Reaudit", "National"])
                n_dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
            with c2:
                n_lead = st.text_input("Project Lead", value=st.session_state['username'])
                n_sup = st.text_input("Project Supervisor")
                n_due = st.date_input("Bimonthly Update Deadline")
            
            st.divider()
            approved = st.radio("Has the Site Lead approved this proposal?", ["No", "Yes"])
            app_name = st.text_input("Site Lead Name (Approver):")
            
            if st.form_submit_button("Submit Registration"):
                if approved == "Yes" and n_id and app_name:
                    # Map exactly to the 17 essential fields
                    new_row = [n_id, n_type, st.session_state['user_site'], n_dept, app_name, n_title, date.today(), n_lead, n_sup, "Registered", "", n_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y")]
                    df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                    save_data(df); st.success("Audit Registered into Active Database"); st.rerun()
                else:
                    st.error("Site Lead Approval and Audit ID are mandatory.")

with tab3:
    st.subheader("📈 Performance Visualization")
    if not view_df.empty:
        fig = px.pie(view_df, names='Status', title="Clinical Audit Status Mix", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

# Footer Safety
backup_time = datetime.fromtimestamp(os.path.getmtime(RECOVERY_FILE)).strftime("%H:%M:%S") if os.path.exists(RECOVERY_FILE) else "N/A"
st.markdown(f"--- \n ✅ **System Health:** Protected | 🛡️ **Last Shadow Copy:** {backup_time} | ⏳ **Session Timeout:** {SESSION_TIMEOUT_MINUTES}m")
