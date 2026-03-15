import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import shutil

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ARCHIVE_FILE = 'archived_audits.csv'
BACKUP_DIR = 'backups'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Comment", "Audit_Dept_Comment", "QS_Comment", "Last_Updated"
]

# Initialize Environment
for f in [CSV_FILE, ARCHIVE_FILE]:
    if not os.path.exists(f):
        pd.DataFrame(columns=COLUMNS).to_csv(f, index=False)
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def load_data(file=CSV_FILE):
    df = pd.read_csv(file)
    for col in COLUMNS:
        if col not in df.columns: df[col] = ""
    return df[COLUMNS]

def save_data(df, file=CSV_FILE):
    df.to_csv(file, index=False)

# --- SECURITY & ROLE MANAGEMENT ---
if "auth_status" not in st.session_state:
    st.session_state["auth_status"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None

if not st.session_state["auth_status"]:
    st.set_page_config(page_title="MFT Login", page_icon="🏥")
    st.markdown(f"<div style='text-align: center; padding-top: 50px;'><h2 style='color: #005EB8;'>{HOSPITAL_NAME}</h2></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.form("login_form"):
            u_name = st.text_input("Username")
            u_role = st.selectbox("Your Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
            pwd = st.text_input("Department Password", type="password")
            login_submit = st.form_submit_button("Access Portal")
            
            if login_submit:
                if pwd == ADMIN_PASSWORD and u_name:
                    st.session_state["auth_status"] = True
                    st.session_state["user_role"] = u_role
                    st.session_state["username"] = u_name
                    st.rerun()
                else:
                    st.error("Invalid Credentials. Please enter username and correct password.")
    st.stop()

# --- APP START ---
st.set_page_config(page_title="MFT Clinical Audit Portal", layout="wide")

# Header with Role Badge
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0; font-family: Arial; font-size: 24px;">{HOSPITAL_NAME}</h1>
            <p style="margin: 0; opacity: 0.85;">Welcome, {st.session_state['username']} ({st.session_state['user_role']})</p>
        </div>
        <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; text-align: right;">
            <span style="font-weight: bold;">Session Role:</span><br>{st.session_state['user_role']}
        </div>
    </div>
""", unsafe_allow_html=True)

df = load_data()

tab1, tab2, tab3 = st.tabs(["📊 Live Register", "⚙️ Role-Based Updates", "📈 Analytics"])

with tab1:
    # (Global Search and Overdue Toggle same as before)
    view_df = df.copy()
    st.dataframe(view_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader(f"Data Management for {st.session_state['user_role']}s")
    
    # Logic to filter which fields are editable based on role
    current_role = st.session_state['user_role']
    
    mode = st.radio("Task:", ["Update Existing Record", "Register New Audit"], horizontal=True)
    
    if mode == "Update Existing Record":
        target_id = st.selectbox("Select Audit ID to update", df["Audit_ID"].tolist() if not df.empty else ["None"])
        
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            
            with st.form("role_update_form"):
                st.info(f"**Project:** {row['Audit_Title']}")
                
                # Everyone can see/update basic status if needed, or you can restrict this too
                new_status = st.selectbox("Overall Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                         index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                
                # --- ROLE-BASED FIELD FILTERING ---
                if current_role == "Project Lead":
                    st.markdown("### 📝 Project Lead Section")
                    p_upd = st.text_area("Project Lead Update", value=str(row['Project_Lead_Update']))
                    # Hidden from this role for editing:
                    s_com, a_com, q_com = row['Site_Lead_Comment'], row['Audit_Dept_Comment'], row['QS_Comment']
                    
                elif current_role == "Site Lead":
                    st.markdown("### 🏢 Site Lead Section")
                    s_com = st.text_area("Site Lead Comment", value=str(row['Site_Lead_Comment']))
                    p_upd, a_com, q_com = row['Project_Lead_Update'], row['Audit_Dept_Comment'], row['QS_Comment']
                    
                elif current_role == "Audit Department":
                    st.markdown("### 📂 Audit Department Section")
                    a_com = st.text_area("Audit Dept Comment", value=str(row['Audit_Dept_Comment']))
                    p_upd, s_com, q_com = row['Project_Lead_Update'], row['Site_Lead_Comment'], row['QS_Comment']
                    
                elif current_role == "Q&S Department":
                    st.markdown("### 🛡️ Quality & Safety Section")
                    q_com = st.text_area("Q&S Comment", value=str(row['QS_Comment']))
                    p_upd, s_com, a_com = row['Project_Lead_Update'], row['Site_Lead_Comment'], row['Audit_Dept_Comment']

                if st.form_submit_button("Save Role Update"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Comment", "Audit_Dept_Comment", "QS_Comment", "Last_Updated"]] = \
                        [new_status, p_upd, s_com, a_com, q_com, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df)
                    st.success(f"Update saved as {current_role}")
                    st.rerun()

    elif mode == "Register New Audit":
        # New Registration remains open to all roles, or restrict to Audit Dept only
        if current_role != "Audit Department":
            st.warning("Only the Audit Department should usually register new IDs. Proceed with caution.")
        # [Registration form code...]
