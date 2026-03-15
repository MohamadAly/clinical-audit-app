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
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"
]

# Initialize Environment
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

def load_data():
    try:
        df = pd.read_csv(CSV_FILE)
        for col in COLUMNS:
            if col not in df.columns: df[col] = ""
        return df[COLUMNS]
    except Exception:
        if os.path.exists(RECOVERY_FILE):
            return pd.read_csv(RECOVERY_FILE)
        return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)
    shutil.copy(CSV_FILE, RECOVERY_FILE)

# --- SESSION & TIMEOUT LOGIC ---
if "auth_status" not in st.session_state:
    st.session_state.update({
        "auth_status": False, "username": "", "user_role": "", 
        "user_site": "", "last_activity": time.time()
    })

# Check for Inactivity
if st.session_state["auth_status"]:
    now = time.time()
    if now - st.session_state["last_activity"] > (SESSION_TIMEOUT_MINUTES * 60):
        st.session_state.update({"auth_status": False, "username": "", "user_role": "", "user_site": ""})
        st.warning("Session expired due to inactivity. Please log in again.")
        st.stop()
    else:
        st.session_state["last_activity"] = now # Reset timer on every interaction

# --- LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="MFT Login", layout="centered")
    st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Username / Full Name")
        u_site = st.selectbox("Your Site", ["ORC", "NMGH", "Wythenshawe", "Trafford"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Access Portal"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state.update({
                    "auth_status": True, "username": u_name, 
                    "user_role": u_role, "user_site": u_site, 
                    "last_activity": time.time()
                })
                st.rerun()
            else: st.error("Invalid Credentials")
    st.stop()

# --- APP START ---
st.set_page_config(page_title="MFT Audit Portal", layout="wide")
df = load_data()

# Header
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0;">{HOSPITAL_NAME} - {st.session_state['user_site']}</h3>
        <p style="margin: 0; opacity: 0.9;">User: {st.session_state['username']} | Role: {st.session_state['user_role']}</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Live Register", "⚙️ Actions & Registry", "📈 Analytics"])

with tab1:
    with st.expander("🔍 Search and Filter Options", expanded=True):
        search = st.text_input("Global Search (Title, ID, Lead, Update text)")
        c1, c2, c3, c4 = st.columns(4)
        with c1: f_site = st.multiselect("Site", ["ORC", "NMGH", "Wythenshawe", "Trafford"])
        with c2: f_dept = st.multiselect("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
        with c3: f_stat = st.multiselect("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
        with c4: overdue_only = st.toggle("🚨 Overdue Only")

    view_df = df.copy()
    if st.session_state['user_role'] == "Project Lead":
        view_df = view_df[view_df['Project_Lead'] == st.session_state['username']]
    elif st.session_state['user_role'] == "Site Lead":
        view_df = view_df[view_df['Site'] == st.session_state['user_site']]
    
    if search: view_df = view_df[view_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
    if f_site: view_df = view_df[view_df['Site'].isin(f_site)]
    if f_dept: view_df = view_df[view_df['Department'].isin(f_dept)]
    if f_stat: view_df = view_df[view_df['Status'].isin(f_stat)]
    if overdue_only and not view_df.empty:
        view_df = view_df[(pd.to_datetime(view_df['Bimonthly_Due']).dt.date < date.today()) & (view_df['Status'] != 'Completed')]

    st.download_button(
        label="📥 Download Audit Register (CSV)",
        data=view_df.to_csv(index=False).encode('utf-8'),
        file_name=f"MFT_Audit_Export_{date.today()}.csv",
        mime='text/csv',
    )

    def style_table(row):
        try:
            due = pd.to_datetime(row['Bimonthly_Due']).date()
            if row['Status'] == "Completed": return ['background-color: #d4edda'] * len(row)
            if due < date.today(): return ['background-color: #f8d7da; color: #721c24'] * len(row)
        except: pass
        return [''] * len(row)

    if not view_df.empty:
        view_df.insert(0, "Health", view_df.apply(lambda r: "🟢" if r['Status'] == "Completed" or pd.to_datetime(r['Bimonthly_Due']).date() >= date.today() else "🔴", axis=1))
        st.dataframe(view_df.style.apply(style_table, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("No projects match your current view.")

with tab2:
    mode = st.radio("Task:", ["Update Existing Progress", "Register New Audit Proposal"], horizontal=True)

    if mode == "Update Existing Progress":
        target_id = st.selectbox("Select Audit ID", ["None"] + view_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            role = st.session_state['user_role']
            with st.form("update_form"):
                new_stat = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                       index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                a_upd = st.text_area("Audit Dept Update", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
                q_upd = st.text_area("QS Update", value=row['QS_Update']) if role in ["Q&S Department", "Audit Department"] else row['QS_Update']

                if st.form_submit_button("Submit Role-Specific Update"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                        [new_stat, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success("Database Synchronized & Backup Created"); st.rerun()

    else:
        st.subheader("New Audit Proposal Entry")
        with st.form("new_reg"):
            c1, c2 = st.columns(2)
            with c1:
                n_id = st.text_input("Audit ID (Unique)")
                n_title = st.text_input("Audit Title")
                n_type = st.selectbox("Audit Type", ["Initial", "Reaudit", "National"])
                n_dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
            with c2:
                n_lead = st.text_input("Project Lead", value=st.session_state['username'])
                n_sup = st.text_input("Project Supervisor")
                n_due = st.date_input("First Bimonthly Update Deadline")
            
            st.divider()
            approved = st.radio("Has this proposal been approved by the Site Lead?", ["No", "Yes"], index=0)
            app_name = st.text_input("If yes, provide Name of Site Lead who approved it:")
            
            if st.form_submit_button("Register Audit"):
                if approved == "No":
                    st.error("🚫 MUST NOT PROCEED: Site Lead approval is mandatory.")
                elif not n_id or not app_name:
                    st.error("Audit ID and Approver Name are required.")
                else:
                    new_row = [n_id, n_type, st.session_state['user_site'], n_dept, app_name, n_title, date.today(), n_lead, n_sup, "Registered", "", n_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y")]
                    df = pd.concat([df, pd.DataFrame([new_row], columns=COLUMNS)], ignore_index=True)
                    save_data(df); st.success("Audit Registered & Backup Created"); st.rerun()

with tab3:
    st.subheader("📈 Analytics View")
    if not view_df.empty:
        fig = px.pie(view_df, names='Status', title=f"Status Overview for {st.session_state['user_site']}")
        st.plotly_chart(fig, use_container_width=True)

# --- FOOTER ---
backup_time = datetime.fromtimestamp(os.path.getmtime(RECOVERY_FILE)).strftime("%H:%M:%S") if os.path.exists(RECOVERY_FILE) else "N/A"
st.markdown("---")
st.markdown(f"✅ **System Health:** Protected | 🛡️ **Last Backup:** {backup_time} | ⏳ **Timeout:** {SESSION_TIMEOUT_MINUTES}m | 📅 **Date:** {date.today()}")
