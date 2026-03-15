import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import plotly.express as px

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

# 18 COLUMNS TOTAL
COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Site_Audit_Lead", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Project_Lead_Update", 
    "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated", "Approved_By"
]

# Initialize Environment
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

# --- SESSION STATE INITIALIZATION (The Fix) ---
if "auth_status" not in st.session_state:
    st.session_state["auth_status"] = False
if "username" not in st.session_state:
    st.session_state["username"] = "Guest"
if "user_role" not in st.session_state:
    st.session_state["user_role"] = "None"
if "user_site" not in st.session_state:
    st.session_state["user_site"] = "Unknown"

def load_data():
    df = pd.read_csv(CSV_FILE)
    for col in COLUMNS:
        if col not in df.columns: df[col] = ""
    return df[COLUMNS]

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- LOGIN GATE ---
if not st.session_state["auth_status"]:
    st.set_page_config(page_title="MFT Login", layout="centered")
    st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login_gate"):
        u_name = st.text_input("Full Name")
        u_site = st.selectbox("Your Site", ["ORC", "NMGH", "Wythenshawe", "Trafford"])
        u_role = st.selectbox("Your Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Sign In"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state["auth_status"] = True
                st.session_state["username"] = u_name
                st.session_state["user_role"] = u_role
                st.session_state["user_site"] = u_site
                st.rerun()
            else:
                st.error("Access Denied: Check username/password")
    st.stop()

# --- MAIN APP ---
st.set_page_config(page_title="MFT Audit Portal", layout="wide")
df = load_data()

# Professional Header
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 15px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0;">{HOSPITAL_NAME} - {st.session_state.get('user_site', 'MFT')}</h3>
        <p style="margin: 0; opacity: 0.85;">{st.session_state['username']} | {st.session_state['user_role']}</p>
    </div>
""", unsafe_allow_html=True)

# --- VISIBILITY FILTERING ---
role = st.session_state['user_role']
user = st.session_state['username']
site = st.session_state['user_site']

if role == "Project Lead":
    filtered_df = df[df['Project_Lead'] == user]
elif role == "Site Lead":
    filtered_df = df[df['Site'] == site]
else:
    filtered_df = df

tab1, tab2, tab3 = st.tabs(["📊 Audit Register", "⚙️ Actions & Registry", "📈 Analytics"])

with tab1:
    # Traffic Light Indicators
    def get_status_icon(row):
        try:
            due = pd.to_datetime(row['Bimonthly_Due']).date()
            if row['Status'] == "Completed": return "🟢"
            return "🔴" if due < date.today() else "🟢"
        except: return "⚪"

    if not filtered_df.empty:
        display_df = filtered_df.copy()
        display_df.insert(0, "Health", display_df.apply(get_status_icon, axis=1))
        
        # Table Styling
        def style_rows(row):
            try:
                due = pd.to_datetime(row['Bimonthly_Due']).date()
                if row['Status'] == "Completed": return ['background-color: #d4edda'] * len(row)
                if due < date.today(): return ['background-color: #f8d7da'] * len(row)
            except: pass
            return [''] * len(row)

        st.dataframe(display_df.style.apply(style_rows, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info(f"No projects found for {user} at {site}.")

with tab2:
    mode = st.radio("Choose Action:", ["Update Progress", "Register New Audit"], horizontal=True)

    if mode == "Update Progress":
        target_id = st.selectbox("Select ID", ["None"] + filtered_df["Audit_ID"].tolist())
        if target_id != "None":
            row_data = df[df["Audit_ID"] == target_id].iloc[0]
            with st.form("update_form"):
                new_stat = st.selectbox("Audit Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                       index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row_data["Status"]))
                
                # Role-specific update logic
                p_upd = st.text_area("Project Lead Update", value=row_data['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row_data['Project_Lead_Update']
                s_upd = st.text_area("Site Lead Update", value=row_data['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row_data['Site_Lead_Update']
                
                if st.form_submit_button("Sync Update"):
                    df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Last_Updated"]] = [new_stat, p_upd, s_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                    save_data(df); st.success("Updated Successfully"); st.rerun()

    else:
        st.subheader("📝 New Audit Registration")
        with st.form("registry_form"):
            c1, c2 = st.columns(2)
            with c1:
                a_id = st.text_input("New Audit ID (Required)")
                a_title = st.text_input("Audit Title")
                a_dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
            with c2:
                a_lead = st.text_input("Project Lead", value=user)
                a_due = st.date_input("First Bimonthly Update Deadline")
            
            st.markdown("---")
            st.warning("Approval Check")
            is_approved = st.radio("Has the Site Lead approved this project proposal?", ["No", "Yes"], index=0)
            approved_by = st.text_input("Name of Site Lead who approved this:")
            
            if st.form_submit_button("Register Audit"):
                if is_approved == "No":
                    st.error("🚫 REGISTRATION HALTED: Site Lead approval is mandatory. You must not proceed.")
                elif not a_id or not approved_by:
                    st.error("Missing Data: Audit ID and Approver Name are required.")
                else:
                    new_entry = [a_id, "Local", site, a_dept, approved_by, a_title, date.today(), a_lead, "", "Registered", "", a_due, "", "", "", "", datetime.now().strftime("%d/%m/%Y"), approved_by]
                    new_df = pd.DataFrame([new_entry], columns=COLUMNS)
                    df = pd.concat([df, new_df], ignore_index=True)
                    save_data(df); st.success(f"Audit {a_id} Registered!"); st.rerun()

with tab3:
    st.subheader("📈 Performance Visualization")
    if not filtered_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(filtered_df, names='Status', title="Project Status Mix", color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            # Bar chart of updates by lead
            fig2 = px.bar(filtered_df, x='Project_Lead', title="Audits per Lead", color='Status')
            st.plotly_chart(fig2, use_container_width=True)
