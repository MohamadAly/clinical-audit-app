import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
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

COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated",
    "Closing_Date", "Level_of_Assurance", "Reaudit_Date", "Improvement_Notes", "Key_Learning"
]

# --- 1. SESSION INITIALIZATION ---
if "auth_status" not in st.session_state:
    st.session_state["auth_status"] = False
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = time.time()
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_role" not in st.session_state:
    st.session_state["user_role"] = ""
if "user_site" not in st.session_state:
    st.session_state["user_site"] = ""

if st.session_state["auth_status"]:
    now = time.time()
    if now - st.session_state.get("last_activity", now) > (SESSION_TIMEOUT_MINUTES * 60):
        st.session_state["auth_status"] = False
        st.warning("Session expired.")
        st.stop()
    else:
        st.session_state["last_activity"] = now

# --- 2. DATA HANDLING ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        for col in COLUMNS:
            if col not in df.columns: df[col] = ""
        return df[COLUMNS]
    except Exception:
        return pd.read_csv(RECOVERY_FILE) if os.path.exists(RECOVERY_FILE) else pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)
    shutil.copy(CSV_FILE, RECOVERY_FILE)

# --- 3. LOGIN ---
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
        <p style="margin: 0; opacity: 0.9;">{st.session_state['username']} ({st.session_state['user_role']})</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Registers", "⚙️ Actions & Registry", "📈 Analytics"])

with tab1:
    # FILTERS (Applicable to both lists)
    with st.expander("🔍 Filters & Search", expanded=False):
        search = st.text_input("Search ID or Title")
        f_dept = st.multiselect("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])

    # Base Visibility Filter
    view_df = df.copy()
    if st.session_state['user_role'] == "Project Lead":
        view_df = view_df[view_df['Project_Lead'] == st.session_state['username']]
    elif st.session_state['user_role'] == "Site Lead":
        view_df = view_df[view_df['Site'] == st.session_state['user_site']]
    
    if search: view_df = view_df[view_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    if f_dept: view_df = view_df[view_df['Department'].isin(f_dept)]

    # --- THE TWO SECTIONS ---
    reg_active, reg_completed = st.tabs(["🚀 Active Audits", "✅ Completed Audits"])

    with reg_active:
        active_df = view_df[view_df['Status'] != "Completed"]
        if not active_df.empty:
            active_df.insert(0, "Health", active_df.apply(lambda r: "🟢" if pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1))
            st.dataframe(active_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active audits found.")

    with reg_completed:
        done_df = view_df[view_df['Status'] == "Completed"]
        if not done_df.empty:
            st.dataframe(done_df, use_container_width=True, hide_index=True)
        else:
            st.info("No completed audits to show.")

with tab2:
    mode = st.radio("Task:", ["Update Progress", "Register New Audit"], horizontal=True)

    if mode == "Update Progress":
        target_id = st.selectbox("Select Audit ID", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_stat = st.selectbox("Update Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                       index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                
                # Role-specific updates
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if st.session_state['user_role'] in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if st.session_state['user_role'] in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                
                # Conditional Closure Fields
                if new_stat == "Completed":
                    st.divider()
                    st.subheader("🏁 Completion Details")
                    c_date = st.date_input("Closing Date", value=date.today())
                    c_assur = st.selectbox("Assurance Level", ["High", "Significant", "Moderate", "Limited", "None"])
                    c_reaudit = st.date_input("Re-audit Date", value=date.today() + timedelta(days=365))
                    c_learn = st.text_area("Learning/Improvement Notes")
                
                if st.form_submit_button("Sync to Database"):
                    update_data = [new_stat, p_upd, s_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    cols_to_upd = ["Status", "Project_Lead_Update", "Site_Lead_Update", "Last_Updated"]
                    
                    if new_stat == "Completed":
                        update_data += [c_date, c_assur, c_reaudit, c_learn]
                        cols_to_upd += ["Closing_Date", "Level_of_Assurance", "Reaudit_Date", "Key_Learning"]
                    
                    df.loc[df["Audit_ID"] == target_id, cols_to_upd] = update_data
                    save_data(df); st.success("Update Successful - Data Moved if Completed"); st.rerun()

    else:
        st.subheader("New Audit Proposal Entry")
        with st.form("new_reg"):
            n_id = st.text_input("Audit ID")
            n_title = st.text_input("Audit Title")
            n_dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
            n_lead = st.text_input("Project Lead", value=st.session_state['username'])
            n_due = st.date_input("First Bimonthly Update Deadline")
            st.divider()
            approved = st.radio("Approved by Site Lead?", ["No", "Yes"])
            app_name = st.text_input("Approver Name:")
            
            if st.form_submit_button("Register"):
                if approved == "Yes" and n_id and app_name:
                    new_row = [n_id, "Local", st.session_state['user_site'], n_dept, app_name, n_title, date.today(), n_lead, "", "Registered", "", n_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y"), "", "", "", "", ""]
                    df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                    save_data(df); st.success("Registered"); st.rerun()
                else: st.error("Approval and ID required.")

with tab3:
    st.subheader("📈 Performance View")
    if not view_df.empty:
        st.plotly_chart(px.pie(view_df, names='Status', title="Current Progress Mix"), use_container_width=True)

# Footer
backup_time = datetime.fromtimestamp(os.path.getmtime(RECOVERY_FILE)).strftime("%H:%M:%S") if os.path.exists(RECOVERY_FILE) else "N/A"
st.markdown(f"--- \n ✅ **Status:** Online | 🛡️ **Last Backup:** {backup_time}")
