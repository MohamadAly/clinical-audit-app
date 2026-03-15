import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import plotly.express as px  # Professional charts

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

st.markdown(f"""
    <div style="background: linear-gradient(90deg, #005EB8 0%, #003087 100%); padding: 20px; border-radius: 12px; color: white; margin-bottom: 20px;">
        <h2 style="margin: 0;">{HOSPITAL_NAME}</h2>
        <p style="margin: 0; opacity: 0.9;">User: {st.session_state['username']} | Role: {st.session_state['user_role']}</p>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Live Register", "⚙️ Manage Updates", "📈 Analytics"])

with tab1:
    # FILTERS RESTORED
    with st.expander("🔍 Advanced Filters", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: f_site = st.multiselect("Filter Site", ["ORC", "NMGH", "Wythenshawe"])
        with c2: f_dept = st.multiselect("Filter Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
        with c3: f_stat = st.multiselect("Filter Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
        with c4: overdue_only = st.toggle("🚨 Overdue Only")

    view_df = df.copy()
    if f_site: view_df = view_df[view_df['Site'].isin(f_site)]
    if f_dept: view_df = view_df[view_df['Department'].isin(f_dept)]
    if f_stat: view_df = view_df[view_df['Status'].isin(f_stat)]
    
    if overdue_only and not view_df.empty:
        # Convert to datetime safely
        view_df['Bimonthly_Due'] = pd.to_datetime(view_df['Bimonthly_Due'])
        view_df = view_df[(view_df['Bimonthly_Due'].dt.date < date.today()) & (view_df['Status'] != 'Completed')]

    # COLOR CODING FOR STATUS AND DATES
    def color_coding(row):
        styles = [''] * len(row)
        # Status Coding
        if row['Status'] == "Completed":
            styles = ['background-color: #d4edda; color: #155724;'] * len(row)
        elif row['Status'] == "Data Collection":
            styles = ['background-color: #fff3cd; color: #856404;'] * len(row)
        
        # Overdue Date Coding (Priority)
        try:
            due = pd.to_datetime(row['Bimonthly_Due']).date()
            if due < date.today() and row['Status'] != "Completed":
                styles = ['background-color: #f8d7da; color: #721c24; font-weight: bold; border: 1px solid #f5c6cb;'] * len(row)
        except: pass
        return styles

    st.dataframe(view_df.style.apply(color_coding, axis=1), use_container_width=True, hide_index=True)

with tab2:
    target_id = st.selectbox("Select Audit ID to Update", ["None"] + df["Audit_ID"].tolist())
    if target_id != "None":
        row = df[df["Audit_ID"] == target_id].iloc[0]
        role = st.session_state['user_role']
        with st.form("update_form"):
            st.write(f"### Update Record: {target_id}")
            new_status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                     index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
            
            # Show update fields based on Role
            p_upd = st.text_area("Project Lead Update", value=row['Project_Lead_Update']) if role in ["Project Lead", "Audit Department"] else row['Project_Lead_Update']
            s_upd = st.text_area("Site Lead Update", value=row['Site_Lead_Update']) if role in ["Site Lead", "Audit Department"] else row['Site_Lead_Update']
            a_upd = st.text_area("Audit Dept Update", value=row['Audit_Dept_Update']) if role == "Audit Department" else row['Audit_Dept_Update']
            q_upd = st.text_area("QS Update", value=row['QS_Update']) if role in ["Q&S Department", "Audit Department"] else row['QS_Update']
            
            if st.form_submit_button("Submit Role Update"):
                df.loc[df["Audit_ID"] == target_id, ["Status", "Project_Lead_Update", "Site_Lead_Update", "Audit_Dept_Update", "QS_Update", "Last_Updated"]] = \
                    [new_status, p_upd, s_upd, a_upd, q_upd, datetime.now().strftime("%d/%m/%Y %H:%M")]
                save_data(df)
                st.success(f"Update successful for {role}")
                st.rerun()

with tab3:
    st.subheader("📈 Performance Analytics")
    if not df.empty:
        c1, c2 = st.columns(2)
        
        with c1:
            # Pie Chart using Plotly (Fixes the AttributeError)
            status_data = df['Status'].value_counts().reset_index()
            status_data.columns = ['Status', 'Count']
            fig_pie = px.pie(status_data, values='Count', names='Status', title="Project Status Distribution",
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            # Bar Chart for Site distribution
            site_data = df['Site'].value_counts().reset_index()
            site_data.columns = ['Site', 'Count']
            fig_bar = px.bar(site_data, x='Site', y='Count', title="Workload by Site",
                             color='Site', color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.write("### Departmental Breakdown")
        dept_data = df['Department'].value_counts().reset_index()
        dept_data.columns = ['Department', 'Count']
        fig_dept = px.bar(dept_data, x='Count', y='Department', orientation='h', title="Projects by Department")
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("No data available to analyze.")
