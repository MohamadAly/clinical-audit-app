import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import plotly.express as px

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated", "Approved_By"
]

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

def load_data():
    df = pd.read_csv(CSV_FILE)
    for col in COLUMNS:
        if col not in df.columns: df[col] = ""
    return df[COLUMNS]

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- LOGIN SYSTEM ---
if "auth_status" not in st.session_state:
    st.session_state.update({"auth_status": False, "user_role": None, "username": None, "user_site": None})

if not st.session_state["auth_status"]:
    st.set_page_config(page_title="MFT Login", layout="centered")
    st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Username")
        u_site = st.selectbox("Your Site Location", ["ORC", "NMGH", "Wythenshawe", "Trafford"])
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state.update({"auth_status": True, "user_role": u_role, "username": u_name, "user_site": u_site})
                st.rerun()
    st.stop()

# --- APP START ---
st.set_page_config(page_title="MFT Audit Portal", layout="wide")
df = load_data()

# Header
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0;">{HOSPITAL_NAME} - {st.session_state['user_site']}</h3>
        <p style="margin: 0; opacity: 0.9;">{st.session_state['username']} ({st.session_state['user_role']})</p>
    </div>
""", unsafe_allow_html=True)

# --- DATA VISIBILITY LOGIC ---
if st.session_state['user_role'] == "Project Lead":
    filtered_df = df[df['Project_Lead'] == st.session_state['username']]
elif st.session_state['user_role'] == "Site Lead":
    filtered_df = df[df['Site'] == st.session_state['user_site']]
else: # Audit/QS Dept see everything
    filtered_df = df

tab1, tab2, tab3 = st.tabs(["📊 My Register", "⚙️ Actions & Registry", "📈 Analytics"])

with tab1:
    # Traffic Light Calculation
    def get_traffic_light(row):
        try:
            due = pd.to_datetime(row['Bimonthly_Due']).date()
            if row['Status'] == "Completed": return "🟢"
            return "🔴" if due < date.today() else "🟢"
        except: return "⚪"

    if not filtered_df.empty:
        display_df = filtered_df.copy()
        display_df.insert(0, "Health", display_df.apply(get_traffic_light, axis=1))
        
        # Color coding for the table
        def row_styler(row):
            due = pd.to_datetime(row['Bimonthly_Due']).date() if row['Bimonthly_Due'] else date.max
            if row['Status'] == "Completed": return ['background-color: #e6ffed'] * len(row)
            if due < date.today(): return ['background-color: #fff5f5'] * len(row)
            return [''] * len(row)

        st.dataframe(display_df.style.apply(row_styler, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("No projects linked to your profile/site.")

with tab2:
    action = st.radio("Select Action:", ["Update Audit", "Register New Audit"], horizontal=True)

    if action == "Update Audit":
        target_id = st.selectbox("Select Audit ID", ["None"] + filtered_df["Audit_ID"].tolist())
        if target_id != "None":
            row = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], index=0)
                # Field access logic based on Role
                p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if st.session_state['user_role'] in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if st.session_state['user_role'] in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
                
                if st.form_submit_button("Sync Update"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Last_Updated"]] = [new_status, p_upd, s_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success("Updated"); st.rerun()

    else:
        st.subheader("New Audit Proposal")
        with st.form("reg_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_id = st.text_input("Audit ID")
                new_title = st.text_input("Audit Title")
                new_type = st.selectbox("Type", ["Initial", "Reaudit", "National"])
            with c2:
                new_lead = st.text_input("Project Lead Name", value=st.session_state['username'])
                new_due = st.date_input("First 2-Month Update Due")
            
            st.markdown("---")
            approved = st.radio("Has this proposal been approved by the Site Lead?", ["No", "Yes"], index=0)
            approver_name = st.text_input("If yes, provide Site Lead Name:")
            
            submit_reg = st.form_submit_button("Register Audit")
            
            if submit_reg:
                if approved == "No":
                    st.error("⛔ Registration halted: Site Lead approval is mandatory to proceed.")
                elif not new_id or not approver_name:
                    st.error("Please ensure Audit ID and Approver Name are provided.")
                else:
                    new_row = pd.DataFrame([[new_id, new_type, st.session_state['user_site'], "CSS", approver_name, new_title, date.today(), new_lead, "", "Registered", "", new_due, "", "", "", "", datetime.now(), approver_name]], columns=COLUMNS)
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df); st.success("Registered successfully!"); st.rerun()

with tab3:
    st.subheader("Site Analytics")
    if not filtered_df.empty:
        fig = px.pie(filtered_df, names='Status', title=f"Audit Progress for {st.session_state['user_site']}")
        st.plotly_chart(fig, use_container_width=True)
