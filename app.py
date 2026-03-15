import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

# Updated columns to include Last_Updated
COLUMNS = ["Audit_ID", "Project_Title", "Lead_Auditor", "Status", "Start_Date", "Bimonthly_Due", "Comments", "Last_Updated"]

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
        st.markdown("<h4 style='text-align: center;'>Clinical Audit Portal Login</h4>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            pwd = st.text_input("Password", type="password")
            if st.button("Access Portal"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Access Denied.")
        return False
    return True

if check_password():
    st.set_page_config(page_title="MFT Clinical Audit", layout="wide")

    # --- FANCY CSS HEADER ---
    st.markdown(f"""
        <div style="background-color: #005EB8; padding: 20px; border-radius: 10px; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0; font-family: Arial;">{HOSPITAL_NAME}</h1>
            <p style="color: #E8EDF2; margin: 0;">Clinical Audit Department - Live Registration & Tracking</p>
        </div>
    """, unsafe_allow_html=True)
    
    df = load_data()

    # --- METRICS DASHBOARD ---
    total_audits = len(df)
    overdue_count = 0
    if not df.empty:
        overdue_count = len(df[(pd.to_datetime(df['Bimonthly_Due']).dt.date < date.today()) & (df['Status'] != 'Completed')])
    completed_count = len(df[df['Status'] == 'Completed'])

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Registered", total_audits)
    m2.metric("Overdue Bimonthly Updates", overdue_count, delta_color="inverse")
    m3.metric("Completed Audits", completed_count)

    st.divider()

    tab1, tab2 = st.tabs(["📊 Audit Dashboard", "⚙️ Data Management"])

    with tab1:
        # --- ADVANCED FILTERING ---
        with st.expander("🔍 Advanced Filters"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                search_term = st.text_input("Search Title/ID")
            with f_col2:
                status_filter = st.multiselect("Filter by Status", options=df["Status"].unique().tolist())
            with f_col3:
                lead_filter = st.multiselect("Filter by Lead Auditor", options=df["Lead_Auditor"].unique().tolist())

        # Apply Filters
        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df['Project_Title'].str.contains(search_term, case=False) | filtered_df['Audit_ID'].str.contains(search_term, case=False)]
        if status_filter:
            filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
        if lead_filter:
            filtered_df = filtered_df[filtered_df['Lead_Auditor'].isin(lead_filter)]

        # --- DATA TABLE ---
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Filtered List", csv, f"MFT_Audit_Export_{date.today()}.csv", "text/csv")

            def highlight_overdue(row):
                try:
                    deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                    if deadline < date.today() and row['Status'] != "Completed":
                        return ['background-color: #fce4e4; color: #921c1c'] * len(row)
                    return [''] * len(row)
                except: return [''] * len(row)

            st.dataframe(filtered_df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("No records match your filters.")

    with tab2:
        st.subheader("Add or Update Audit Records")
        action = st.radio("Task Selection:", ["Register New Audit", "Update Existing Audit", "Delete Record"], horizontal=True)
        
        with st.form("management_form"):
            if action == "Register New Audit":
                a_id = st.text_input("New Audit ID")
                title = st.text_input("Project Title")
                lead = st.text_input("Lead Auditor")
                status = st.selectbox("Initial Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
                s_date = st.date_input("Start Date", value=date.today())
                b_date = st.date_input("Next Bimonthly Update Due", value=date.today())
                comments = st.text_area("Notes/Comments")
            
            else:
                target_id = st.selectbox("Select Audit ID", df["Audit_ID"].tolist() if not df.empty else ["None"])
                if not df.empty and target_id != "None":
                    row = df[df["Audit_ID"] == target_id].iloc[0]
                    st.info(f"**Selected Record:** {target_id} - {row['Project_Title']}")
                    status = st.selectbox("Update Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                         index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                    s_date = st.date_input("Update Start Date", value=pd.to_datetime(row["Start_Date"]).date())
                    b_date = st.date_input("Update Bimonthly Due", value=pd.to_datetime(row["Bimonthly_Due"]).date())
                    comments = st.text_area("Update Comments", value=str(row["Comments"]) if pd.notna(row["Comments"]) else "")
                    a_id, title, lead = target_id, row['Project_Title'], row['Lead_Auditor']
                else:
                    a_id, title, lead, status, s_date, b_date, comments = "", "", "", "Registered", date.today(), date.today(), ""

            submitted = st.form_submit_button(f"Save Changes")

        if submitted:
            now_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
            if action == "Register New Audit":
                if not a_id or not title:
                    st.error("Audit ID and Title are required.")
                elif a_id in df["Audit_ID"].values:
                    st.error("Audit ID already exists.")
                else:
                    new_row = pd.DataFrame([[a_id, title, lead, status, s_date, b_date, comments, now_ts]], columns=COLUMNS)
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("Audit Registered!")
                    st.rerun()
            
            elif action == "Update Existing Audit" and target_id != "None":
                df.loc[df["Audit_ID"] == target_id, ["Status", "Start_Date", "Bimonthly_Due", "Comments", "Last_Updated"]] = [status, s_date, b_date, comments, now_ts]
                save_data(df)
                st.success("Record Updated!")
                st.rerun()
            
            elif action == "Delete Record" and target_id != "None":
                df = df[df["Audit_ID"] != target_id]
                save_data(df)
                st.success("Record Deleted.")
                st.rerun()
