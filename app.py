import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

# EXACT 12 COLUMNS AS REQUESTED
COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Update_Comments"
]

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(CSV_FILE, index=False)

def load_data():
    df = pd.read_csv(CSV_FILE)
    # Ensure the dataframe matches the requested 12-column structure
    if list(df.columns) != COLUMNS:
        df = pd.DataFrame(columns=COLUMNS)
    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- SECURITY GATE ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.set_page_config(page_title="MFT Login", page_icon="🏥")
    st.markdown(f"<h2 style='text-align: center; color: #005EB8; font-family: Arial;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("Department Password", type="password")
        if st.button("Enter Portal"):
            if pwd == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Incorrect Password")
    st.stop()

# --- APP LAYOUT ---
st.set_page_config(page_title="MFT Clinical Audit Portal", layout="wide")

# MFT CSS Header
st.markdown(f"""
    <div style="background-color: #005EB8; padding: 25px; border-radius: 15px; margin-bottom: 30px; border-left: 10px solid #00A1DE;">
        <h1 style="color: white; margin: 0; font-family: Arial;">{HOSPITAL_NAME}</h1>
        <p style="color: #E8EDF2; margin: 0; font-size: 1.2rem;">Clinical Audit Registration & Live Tracking Platform</p>
    </div>
""", unsafe_allow_html=True)

df = load_data()

# --- KPI METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Projects", len(df))
if not df.empty:
    overdue = len(df[(pd.to_datetime(df['Bimonthly_Due']).dt.date < date.today()) & (df['Status'] != 'Completed')])
    m2.metric("Overdue (2-Month)", overdue, delta_color="inverse")
    m3.metric("NMGH Projects", len(df[df['Site'] == 'NMGH']))
    m4.metric("ORC Projects", len(df[df['Site'] == 'ORC']))

st.write("---")

tab1, tab2 = st.tabs(["📊 Live Audit Register", "⚙️ Manage & Edit Data"])

with tab1:
    # FILTERS
    with st.expander("🔍 Filter & Search Options"):
        f1, f2, f3 = st.columns(3)
        with f1: f_site = st.multiselect("Filter by Site", ["ORC", "NMGH", "Wythenshawe"])
        with f2: f_dept = st.multiselect("Filter by Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
        with f3: f_type = st.multiselect("Filter by Type", ["Initial", "Reaudit", "National", "Local Trust"])
    
    filtered_df = df.copy()
    if f_site: filtered_df = filtered_df[filtered_df['Site'].isin(f_site)]
    if f_dept: filtered_df = filtered_df[filtered_df['Department'].isin(f_dept)]
    if f_type: filtered_df = filtered_df[filtered_df['Audit_Type'].isin(f_type)]

    if not filtered_df.empty:
        # Highlighting logic for 2-month update
        def highlight_overdue(row):
            try:
                deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                if deadline < date.today() and row['Status'] != "Completed":
                    return ['background-color: #fce4e4; color: #721c24; border-bottom: 1px solid #f5c6cb'] * len(row)
                return [''] * len(row)
            except: return [''] * len(row)

        st.dataframe(filtered_df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Current Register to CSV", csv, f"MFT_Audit_Export_{date.today()}.csv", "text/csv")
    else:
        st.info("No projects found in the register.")

with tab2:
    st.subheader("Project Management")
    mode = st.radio("Select Operation:", ["Add New Project", "Edit Existing Project", "Delete Project"], horizontal=True)

    with st.form("management_form", clear_on_submit=True):
        if mode == "Add New Project":
            c1, c2 = st.columns(2)
            with c1:
                a_id = st.text_input("1. Audit ID")
                a_type = st.selectbox("2. Audit Type", ["Initial", "Reaudit", "National", "Local Trust", "Other"])
                site = st.selectbox("3. Site", ["ORC", "NMGH", "Wythenshawe"])
                dept = st.selectbox("4. Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
                title = st.text_input("5. Audit Title")
                s_date = st.date_input("6. Start Date", value=date.today())
            with c2:
                p_lead = st.text_input("7. Project Lead")
                p_sup = st.text_input("8. Project Supervisor")
                status = st.selectbox("9. Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
                t_date = st.date_input("10. Target Date")
                b_date = st.date_input("11. Every 2 Months Update (Next Due)")
                comments = st.text_area("12. Update (Free Text)")
        
        else:
            target_id = st.selectbox("Select Audit ID", df["Audit_ID"].tolist() if not df.empty else ["No Records"])
            if not df.empty and target_id != "No Records":
                row = df[df["Audit_ID"] == target_id].iloc[0]
                st.info(f"Modifying Record: {target_id}")
                c1, c2 = st.columns(2)
                with c1:
                    a_id = target_id
                    a_type = st.selectbox("Audit Type", ["Initial", "Reaudit", "National", "Local Trust"], index=["Initial", "Reaudit", "National", "Local Trust"].index(row["Audit_Type"]) if row["Audit_Type"] in ["Initial", "Reaudit", "National", "Local Trust"] else 0)
                    site = st.selectbox("Site", ["ORC", "NMGH", "Wythenshawe"], index=["ORC", "NMGH", "Wythenshawe"].index(row["Site"]))
                    dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"], index=["Anaesthesia", "Critical Care", "DLM", "Radiology"].index(row["Department"]))
                    title = st.text_input("Audit Title", value=str(row["Audit_Title"]))
                    s_date = st.date_input("Start Date", value=pd.to_datetime(row["Start_Date"]).date())
                with c2:
                    p_lead = st.text_input("Project Lead", value=str(row["Project_Lead"]))
                    p_sup = st.text_input("Project Supervisor", value=str(row["Project_Supervisor"]))
                    status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                    t_date = st.date_input("Target Date", value=pd.to_datetime(row["Target_Date"]).date())
                    b_date = st.date_input("Next 2-Month Update Due", value=pd.to_datetime(row["Bimonthly_Due"]).date())
                    comments = st.text_area("Update (Free Text)", value=str(row["Update_Comments"]) if pd.notna(row["Update_Comments"]) else "")
            else:
                a_id = ""

        confirm = st.form_submit_button(f"Save {mode}")

    if confirm:
        if mode == "Add New Project":
            if a_id in df["Audit_ID"].values:
                st.error("Audit ID already exists.")
            else:
                new_row = pd.DataFrame([[a_id, a_type, site, dept, title, s_date, p_lead, p_sup, status, t_date, b_date, comments]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("Successfully Registered")
                st.rerun()
        
        elif mode == "Edit Existing Project" and target_id != "No Records":
            df.loc[df["Audit_ID"] == target_id, COLUMNS] = [a_id, a_type, site, dept, title, s_date, p_lead, p_sup, status, t_date, b_date, comments]
            save_data(df)
            st.success("Successfully Updated")
            st.rerun()
            
        elif mode == "Delete Project" and target_id != "No Records":
            df = df[df["Audit_ID"] != target_id]
            save_data(df)
            st.success("Successfully Deleted")
            st.rerun()
