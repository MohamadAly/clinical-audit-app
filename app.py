import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

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
    df = pd.read_csv(CSV_FILE)
    for col in COLUMNS:
        if col not in df.columns: df[col] = ""
    return df[COLUMNS]

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- SECURITY ---
if "auth_status" not in st.session_state:
    st.session_state["auth_status"] = False

if not st.session_state["auth_status"]:
    st.set_page_config(page_title="MFT Login", layout="centered")
    st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u_name = st.text_input("Username")
        u_role = st.selectbox("Role", ["Project Lead", "Site Lead", "Audit Department", "Q&S Department"])
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if pwd == ADMIN_PASSWORD and u_name:
                st.session_state["auth_status"] = True
                st.session_state["user_role"] = u_role
                st.session_state["username"] = u_name
                st.rerun()
    st.stop()

# --- APP START ---
st.set_page_config(page_title="MFT Audit Portal", layout="wide")
df = load_data()

# CSS for Fancy Header
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h2 style="margin: 0;">{HOSPITAL_NAME}</h2>
        <p style="margin: 0; opacity: 0.9;">User: {st.session_state['username']} | Role: {st.session_state['user_role']}</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Live Register", "⚙️ Manage Updates", "📈 Analytics"])

with tab1:
    # RESTORED FILTERS
    with st.expander("🔍 Advanced Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: f_site = st.multiselect("Site", ["ORC", "NMGH", "Wythenshawe"])
        with c2: f_dept = st.multiselect("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
        with c3: f_stat = st.multiselect("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
        with c4: overdue_only = st.toggle("🚨 Overdue Only")

    view_df = df.copy()
    if f_site: view_df = view_df[view_df['Site'].isin(f_site)]
    if f_dept: view_df = view_df[view_df['Department'].isin(f_dept)]
    if f_stat: view_df = view_df[view_df['Status'].isin(f_stat)]
    
    if overdue_only and not view_df.empty:
        view_df = view_df[(pd.to_datetime(view_df['Bimonthly_Due']).dt.date < date.today()) & (view_df['Status'] != 'Completed')]

    # COLOR CODING LOGIC
    def color_coding(row):
        styles = [''] * len(row)
        # Status Color Coding
        status_colors = {
            "Completed": "background-color: #d4edda; color: #155724;",     # Green
            "Data Collection": "background-color: #fff3cd; color: #856404;", # Yellow
            "Analysis": "background-color: #d1ecf1; color: #0c5460;",       # Blue
            "Drafting Report": "background-color: #e2e3e5; color: #383d41;" # Grey
        }
        if row['Status'] in status_colors:
            styles = [status_colors[row['Status']]] * len(row)
        
        # Overdue Date Highlighting (Red text for Bimonthly Due)
        try:
            due = pd.to_datetime(row['Bimonthly_Due']).date()
            if due < date.today() and row['Status'] != "Completed":
                styles = ['background-color: #f8d7da; color: #721c24; font-weight: bold;'] * len(row)
        except: pass
        return styles

    st.dataframe(view_df.style.apply(color_coding, axis=1), use_container_width=True, hide_index=True)

with tab2:
    # Role-based editing (Update labels changed from "Comment" to "Update")
    target_id = st.selectbox("Select Audit ID", ["None"] + df["Audit_ID"].tolist())
    if target_id != "None":
        row = df[df["Audit_ID"] == target_id].iloc[0]
        role = st.session_state['user_role']
        with st.form("update_form"):
            st.write(f"Updating: **{row['Audit_Title']}**")
            new_status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                     index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
            
            # Role-specific fields
            p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role == "Project Lead" or role == "Audit Department" else row['Project_Lead_Update']
            s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if role == "Site Lead" or role == "Audit Department" else row['Site_Lead_Update']
            a_upd = st.text_area("Audit Dept Update", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
            q_upd = st.text_area("QS Update", value=row['QS_Update']) if role == "Q&S Department" or role == "Audit Department" else row['QS_Update']
            
            if st.form_submit_button("Save Update"):
                df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                    [new_status, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                save_data(df)
                st.success("Record Updated!")
                st.rerun()

with tab3:
    st.subheader("📈 Visual Performance Metrics")
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Project Volume by Site**")
            st.bar_chart(df['Site'].value_counts())
        with c2:
            st.write("**Current Project Status**")
            st.pie_chart(df['Status'].value_counts())
        
        st.write("**Workload by Department**")
        st.bar_chart(df['Department'].value_counts())
    else:
        st.info("No data available for analytics yet.")
