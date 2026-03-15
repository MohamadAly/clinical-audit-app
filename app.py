import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"
HOSPITAL_NAME = "Manchester University NHS Foundation Trust (CSS)"

# FULL ORDER OF 13 FIELDS
COLUMNS = [
    "Audit_ID", "Audit_Type", "Site", "Department", "Audit_Title", 
    "Start_Date", "Project_Lead", "Project_Supervisor", "Status", 
    "Target_Date", "Bimonthly_Due", "Update_Comments", "Last_Updated"
]

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
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.markdown(f"<h2 style='text-align: center; color: #005EB8;'>{HOSPITAL_NAME}</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        pwd = st.text_input("Department Password", type="password")
        if st.button("Access Portal"):
            if pwd == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Invalid Password")
    st.stop()

# --- APP START ---
st.set_page_config(page_title="MFT Audit Portal", layout="wide")

st.markdown(f"""
    <div style="background-color: #005EB8; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; font-family: Arial;">{HOSPITAL_NAME}</h1>
        <p style="color: #E8EDF2; margin: 0;">CSS Clinical Audit Registration & Live Tracking</p>
    </div>
""", unsafe_allow_html=True)

df = load_data()

tab1, tab2 = st.tabs(["📊 Live Audit Register", "⚙️ Manage/Update Audits"])

with tab1:
    # --- FILTERS ---
    with st.expander("🔍 Filter View"):
        c1, c2, c3 = st.columns(3)
        with c1: f_site = st.multiselect("Site", ["ORC", "NMGH", "Wythenshawe"])
        with c2: f_dept = st.multiselect("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
        with c3: f_status = st.multiselect("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])

    filtered_df = df.copy()
    if f_site: filtered_df = filtered_df[filtered_df['Site'].isin(f_site)]
    if f_dept: filtered_df = filtered_df[filtered_df['Department'].isin(f_dept)]
    if f_status: filtered_df = filtered_df[filtered_df['Status'].isin(f_status)]

    if not filtered_df.empty:
        # Highlighting logic for Bimonthly Updates
        def highlight_overdue(row):
            try:
                deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                if deadline < date.today() and row['Status'] != "Completed":
                    return ['background-color: #fce4e4; color: #921c1c'] * len(row)
                return [''] * len(row)
            except: return [''] * len(row)

        st.dataframe(filtered_df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Current View to CSV", csv, f"Audit_Export_{date.today()}.csv", "text/csv")
    else:
        st.info("No records found.")

with tab2:
    action = st.radio("Choose Task:", ["Register New Audit", "Update Existing Audit", "Delete Audit"], horizontal=True)
    
    with st.form("audit_form", clear_on_submit=True):
        if action == "Register New Audit":
            st.write("### New Registration")
            a_id = st.text_input("1. Audit ID")
            a_type = st.selectbox("2. Audit Type", ["Initial", "Re-audit", "National", "Local Trust", "Other"])
            site = st.selectbox("3. Site", ["ORC", "NMGH", "Wythenshawe"])
            dept = st.selectbox("4. Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"])
            title = st.text_input("5. Audit Title")
            s_date = st.date_input("6. Start Date", value=date.today())
            p_lead = st.text_input("7. Project Lead")
            p_sup = st.text_input("8. Project Supervisor")
            status = st.selectbox("9. Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
            t_date = st.date_input("10. Target Date")
            b_date = st.date_input("11. Next Bimonthly Update Due")
            comments = st.text_area("12. Update (Free Text)")
        
        else:
            target_id = st.selectbox("Select Audit ID to Modify", df["Audit_ID"].tolist() if not df.empty else ["None"])
            if not df.empty and target_id != "None":
                row = df[df["Audit_ID"] == target_id].iloc[0]
                st.info(f"**Modifying:** {row['Audit_Title']}")
                # Re-map fields for editing
                a_id = target_id
                a_type = st.selectbox("Audit Type", ["Initial", "Re-audit", "National", "Local Trust", "Other"], index=["Initial", "Re-audit", "National", "Local Trust", "Other"].index(row["Audit_Type"]))
                site = st.selectbox("Site", ["ORC", "NMGH", "Wythenshawe"], index=["ORC", "NMGH", "Wythenshawe"].index(row["Site"]))
                dept = st.selectbox("Department", ["Anaesthesia", "Critical Care", "DLM", "Radiology"], index=["Anaesthesia", "Critical Care", "DLM", "Radiology"].index(row["Department"]))
                title = st.text_input("Audit Title", value=str(row["Audit_Title"]))
                s_date = st.date_input("Start Date", value=pd.to_datetime(row["Start_Date"]).date())
                p_lead = st.text_input("Project Lead", value=str(row["Project_Lead"]))
                p_sup = st.text_input("Project Supervisor", value=str(row["Project_Supervisor"]))
                status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                t_date = st.date_input("Target Date", value=pd.to_datetime(row["Target_Date"]).date())
                b_date = st.date_input("Next Bimonthly Update Due", value=pd.to_datetime(row["Bimonthly_Due"]).date())
                comments = st.text_area("Update (Free Text)", value=str(row["Update_Comments"]) if pd.notna(row["Update_Comments"]) else "")
            else:
                a_id = ""

        submitted = st.form_submit_button("Confirm and Save")

    if submitted:
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        if action == "Register New Audit":
            if a_id in df["Audit_ID"].values:
                st.error("Audit ID already exists.")
            else:
                new_row = pd.DataFrame([[a_id, a_type, site, dept, title, s_date, p_lead, p_sup, status, t_date, b_date, comments, now_ts]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("Successfully Registered")
                st.rerun()
        
        elif action == "Update Existing Audit" and target_id != "None":
            df.loc[df["Audit_ID"] == target_id, COLUMNS[:-1]] = [a_id, a_type, site, dept, title, s_date, p_lead, p_sup, status, t_date, b_date, comments]
            df.loc[df["Audit_ID"] == target_id, "Last_Updated"] = now_ts
            save_data(df)
            st.success("Successfully Updated")
            st.rerun()
            
        elif action == "Delete Audit" and target_id != "None":
            df = df[df["Audit_ID"] != target_id]
            save_data(df)
            st.success("Successfully Deleted")
            st.rerun()
