import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"

# Ensure all columns exist, including the new 'Comments' column
COLUMNS = ["Audit_ID", "Project_Title", "Lead_Auditor", "Status", "Start_Date", "Bimonthly_Due", "Comments"]

if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(CSV_FILE, index=False)

def load_data():
    df = pd.read_csv(CSV_FILE)
    # Ensure any older CSVs are updated with the Comments column if missing
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
        st.title("🔒 Clinical Audit Login")
        pwd = st.text_input("Enter Department Password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password.")
        return False
    return True

if check_password():
    st.set_page_config(page_title="Audit Portal", layout="wide")
    st.title("🏥 Clinical Audit Live Portal")
    
    df = load_data()

    # --- TABS FOR BETTER ORG ---
    tab1, tab2 = st.tabs(["📊 View Register", "⚙️ Manage Audits"])

    with tab2:
        st.subheader("Add, Edit, or Delete Audits")
        
        # Select action
        action = st.radio("What would you like to do?", ["Add New", "Edit Existing", "Delete"], horizontal=True)
        
        with st.form("audit_mgmt_form", clear_on_submit=True):
            if action == "Add New":
                a_id = st.text_input("New Audit ID")
                existing_data = {"Title":"", "Lead":"", "Status":"Registered", "Start":date.today(), "Due":date.today(), "Comm":""}
            else:
                target_id = st.selectbox("Select Audit ID to Change/Delete", df["Audit_ID"].tolist())
                row = df[df["Audit_ID"] == target_id].iloc[0]
                a_id = target_id
                existing_data = {
                    "Title": row["Project_Title"], 
                    "Lead": row["Lead_Auditor"], 
                    "Status": row["Status"],
                    "Start": pd.to_datetime(row["Start_Date"]).date(),
                    "Due": pd.to_datetime(row["Bimonthly_Due"]).date(),
                    "Comm": row["Comments"] if pd.notna(row["Comments"]) else ""
                }

            # Form Fields
            title = st.text_input("Project Title", value=existing_data["Title"])
            lead = st.text_input("Lead Auditor", value=existing_data["Lead"])
            status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                 index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(existing_data["Status"]))
            s_date = st.date_input("Start Date", value=existing_data["Start"])
            b_date = st.date_input("Next Bimonthly Update Due", value=existing_data["Due"])
            comments = st.text_area("Comments (Free Text)", value=existing_data["Comm"])
            
            submitted = st.form_submit_button(f"Confirm {action}")

            if submitted:
                if action == "Add New":
                    if a_id in df["Audit_ID"].values:
                        st.error("Audit ID already exists!")
                    else:
                        new_row = pd.DataFrame([[a_id, title, lead, status, s_date, b_date, comments]], columns=COLUMNS)
                        df = pd.concat([df, new_row], ignore_index=True)
                        save_data(df)
                        st.success("Audit added!")
                        st.rerun()
                
                elif action == "Edit Existing":
                    df.loc[df["Audit_ID"] == a_id, ["Project_Title", "Lead_Auditor", "Status", "Start_Date", "Bimonthly_Due", "Comments"]] = [title, lead, status, s_date, b_date, comments]
                    save_data(df)
                    st.success("Audit updated!")
                    st.rerun()
                
                elif action == "Delete":
                    df = df[df["Audit_ID"] != a_id]
                    save_data(df)
                    st.success("Audit deleted!")
                    st.rerun()

    with tab1:
        st.subheader("Live Audit Register")
        if not df.empty:
            # CSV Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export to CSV", csv, f"audit_export_{date.today()}.csv", "text/csv")

            # Highlighting logic
            def highlight_overdue(row):
                try:
                    deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                    if deadline < date.today() and row['Status'] != "Completed":
                        return ['background-color: #ffcccc'] * len(row)
                    return [''] * len(row)
                except: return [''] * len(row)

            st.dataframe(df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("No audits found.")
