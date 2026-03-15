import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

# Internal columns (keeping ID/Title for backend logic)
COLUMNS = ["Audit_ID", "Project_Title", "Lead_Auditor", "Status", "Bimonthly_Due", "Comments", "Start_Date", "Last_Updated"]
# Columns to actually display to the user in the main table
DISPLAY_COLS = ["Status", "Bimonthly_Due", "Comments", "Start_Date", "Last_Updated"]

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(CSV_FILE, index=False)

def load_data():
    df = pd.read_csv(CSV_FILE)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- SECURITY ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if not st.session_state["password_correct"]:
        st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("Department Password", type="password")
            if st.button("Enter Portal"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Access Denied.")
        return False
    return True

if check_password():
    st.set_page_config(page_title="MFT CSS Audit", layout="wide")

    # --- BRANDING HEADER ---
    st.markdown(f"""
        <div style="background-color: #005EB8; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0; font-family: Arial;">{HOSPITAL_NAME}</h1>
            <p style="color: #E8EDF2; margin: 0;">Clinical Audit Department - Workflow Tracker</p>
        </div>
    """, unsafe_allow_html=True)
    
    df = load_data()

    # --- METRICS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Audits", len(df))
    if not df.empty:
        overdue = len(df[(pd.to_datetime(df['Bimonthly_Due']).dt.date < date.today()) & (df['Status'] != 'Completed')])
        m2.metric("Overdue Updates", overdue, delta_color="inverse")
    m3.metric("Completed", len(df[df['Status'] == 'Completed']))

    tab1, tab2 = st.tabs(["📊 Live Workflow View", "⚙️ Update Audit Record"])

    with tab1:
        # Filtering logic stays in the background
        search = st.text_input("🔍 Search Comments or Project Title (Internal)")
        
        filtered_df = df.copy()
        if search:
            # Allows searching by Title/Lead even if they aren't displayed in columns
            filtered_df = filtered_df[filtered_df['Project_Title'].str.contains(search, case=False) | 
                                    filtered_df['Comments'].str.contains(search, case=False)]

        if not filtered_df.empty:
            # Highlight Logic
            def highlight_overdue(row):
                try:
                    deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                    if deadline < date.today() and row['Status'] != "Completed":
                        return ['background-color: #fce4e4; color: #921c1c'] * len(row)
                    return [''] * len(row)
                except: return [''] * len(row)

            # --- DISPLAY TABLE (Removed first 3 columns) ---
            st.dataframe(
                filtered_df[DISPLAY_COLS].style.apply(highlight_overdue, axis=1), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("No audit records found.")

    with tab2:
        st.subheader("Manage Record Data")
        action = st.radio("Task:", ["Register New", "Update Status/Comments", "Delete"], horizontal=True)
        
        with st.form("audit_form"):
            if action == "Register New":
                a_id = st.text_input("Audit ID")
                title = st.text_input("Project Title")
                lead = st.text_input("Lead Auditor")
                status = st.selectbox("Current Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
                b_date = st.date_input("Bimonthly Update Due")
                comments = st.text_area("Initial Comments")
                s_date = st.date_input("Start Date", value=date.today())
            
            else:
                target_id = st.selectbox("Select Audit ID", df["Audit_ID"].tolist() if not df.empty else ["None"])
                if not df.empty and target_id != "None":
                    row = df[df["Audit_ID"] == target_id].iloc[0]
                    st.info(f"**Selected:** {target_id} - {row['Project_Title']}")
                    status = st.selectbox("Update Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                         index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                    b_date = st.date_input("Update Bimonthly Due", value=pd.to_datetime(row["Bimonthly_Due"]).date())
                    comments = st.text_area("Update Comments", value=str(row["Comments"]) if pd.notna(row["Comments"]) else "")
                    s_date = st.date_input("Update Start Date", value=pd.to_datetime(row["Start_Date"]).date())
                    a_id, title, lead = target_id, row['Project_Title'], row['Lead_Auditor']
                else:
                    a_id, title, lead, status, b_date, comments, s_date = "", "", "", "Registered", date.today(), "", date.today()

            submitted = st.form_submit_button("Commit Changes")

        if submitted:
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            if action == "Register New":
                new_row = pd.DataFrame([[a_id, title, lead, status, b_date, comments, s_date, now_ts]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("New audit registered!")
                st.rerun()
            
            elif action == "Update Status/Comments" and target_id != "None":
                df.loc[df["Audit_ID"] == target_id, ["Status", "Bimonthly_Due", "Comments", "Start_Date", "Last_Updated"]] = [status, b_date, comments, s_date, now_ts]
                save_data(df)
                st.success("Record updated!")
                st.rerun()
            
            elif action == "Delete" and target_id != "None":
                df = df[df["Audit_ID"] != target_id]
                save_data(df)
                st.success("Record removed.")
                st.rerun()
