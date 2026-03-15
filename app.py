import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"

# Column definitions
COLUMNS = ["Audit_ID", "Project_Title", "Lead_Auditor", "Status", "Start_Date", "Bimonthly_Due", "Comments"]

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
    tab1, tab2 = st.tabs(["📊 View Register", "⚙️ Manage Audits"])

    with tab2:
        st.subheader("Add, Edit, or Delete Audits")
        action = st.radio("Choose Action:", ["Add New", "Edit Existing", "Delete"], horizontal=True)
        
        # We wrap the entire input area in one form
        with st.form("audit_management_form"):
            if action == "Add New":
                a_id = st.text_input("New Audit ID")
                title = st.text_input("Project Title")
                lead = st.text_input("Lead Auditor")
                status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
                s_date = st.date_input("Start Date", value=date.today())
                b_date = st.date_input("Next Bimonthly Update Due", value=date.today())
                comments = st.text_area("Comments")
            
            else:
                # For Edit or Delete, show a selector first
                target_id = st.selectbox("Select Audit ID", df["Audit_ID"].tolist() if not df.empty else ["None"])
                
                if not df.empty and target_id != "None":
                    row = df[df["Audit_ID"] == target_id].iloc[0]
                    # Fields pre-filled for editing
                    title = st.text_input("Project Title", value=str(row["Project_Title"]))
                    lead = st.text_input("Lead Auditor", value=str(row["Lead_Auditor"]))
                    status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"], 
                                         index=["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"].index(row["Status"]))
                    s_date = st.date_input("Start Date", value=pd.to_datetime(row["Start_Date"]).date())
                    b_date = st.date_input("Next Bimonthly Update Due", value=pd.to_datetime(row["Bimonthly_Due"]).date())
                    comments = st.text_area("Comments", value=str(row["Comments"]) if pd.notna(row["Comments"]) else "")
                else:
                    st.warning("No audits available to edit or delete.")
                    title, lead, status, s_date, b_date, comments = "", "", "Registered", date.today(), date.today(), ""

            # THE CRITICAL SUBMIT BUTTON - Always visible at the bottom of the form
            submit_label = f"Confirm {action}"
            submitted = st.form_submit_button(submit_label)

        # Logic after the form is submitted
        if submitted:
            if action == "Add New":
                if not a_id:
                    st.error("Audit ID is required.")
                elif a_id in df["Audit_ID"].values:
                    st.error("This ID already exists.")
                else:
                    new_row = pd.DataFrame([[a_id, title, lead, status, s_date, b_date, comments]], columns=COLUMNS)
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("New Audit added successfully!")
                    st.rerun()
            
            elif action == "Edit Existing" and target_id != "None":
                df.loc[df["Audit_ID"] == target_id, ["Project_Title", "Lead_Auditor", "Status", "Start_Date", "Bimonthly_Due", "Comments"]] = [title, lead, status, s_date, b_date, comments]
                save_data(df)
                st.success("Audit updated successfully!")
                st.rerun()
            
            elif action == "Delete" and target_id != "None":
                df = df[df["Audit_ID"] != target_id]
                save_data(df)
                st.success("Audit deleted successfully!")
                st.rerun()

    with tab1:
        st.subheader("Live Audit Register")
        if not df.empty:
            # Search filter
            search = st.text_input("🔍 Search by Title or Lead Auditor")
            filtered_df = df[df['Project_Title'].str.contains(search, case=False) | df['Lead_Auditor'].str.contains(search, case=False)]
            
            # Export
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Current View to CSV", csv, f"audit_export_{date.today()}.csv", "text/csv")

            # Color Highlighting
            def highlight_overdue(row):
                try:
                    deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                    if deadline < date.today() and row['Status'] != "Completed":
                        return ['background-color: #ffcccc; color: black'] * len(row)
                    return [''] * len(row)
                except: return [''] * len(row)

            st.dataframe(filtered_df.style.apply(highlight_overdue, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("The register is currently empty.")
