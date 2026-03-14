import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'
ADMIN_PASSWORD = "ClinicalAudit2026"  # CHANGE THIS PASSWORD TO YOUR CHOICE

# Initialize the CSV file if it doesn't exist
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["Audit_ID", "Project_Title", "Lead_Auditor", "Status", "Start_Date", "Bimonthly_Due"])
    df.to_csv(CSV_FILE, index=False)

def load_data():
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- SECURITY GATE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔒 Clinical Audit Department Login")
        pwd = st.text_input("Enter Department Password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
        return False
    return True

# --- MAIN APP LOGIC ---
if check_password():
    st.set_page_config(page_title="Audit Portal", layout="wide")
    st.title("🏥 Clinical Audit Live Department Portal")
    
    # --- DATA LOADING ---
    df_display = load_data()

    # --- SIDEBAR: REGISTRATION ---
    st.sidebar.header("Register / Update Audit")
    with st.sidebar.form("audit_form", clear_on_submit=True):
        audit_id = st.text_input("Audit ID (Unique)")
        title = st.text_input("Project Title")
        lead = st.text_input("Lead Auditor")
        status = st.selectbox("Status", ["Registered", "Data Collection", "Analysis", "Drafting Report", "Completed"])
        s_date = st.date_input("Start Date", value=date.today())
        b_date = st.date_input("Next Bimonthly Update Due")
        
        submit = st.form_submit_button("Save to Register")

    if submit:
        if not audit_id or not title:
            st.sidebar.error("Please provide an ID and Title.")
        else:
            # Add new row
            new_entry = pd.DataFrame([[audit_id, title, lead, status, s_date, b_date]], 
                                    columns=df_display.columns)
            updated_df = pd.concat([df_display, new_entry], ignore_index=True)
            save_data(updated_df)
            st.sidebar.success(f"Audit {audit_id} saved!")
            st.rerun()

    # --- MAIN DASHBOARD ---
    st.subheader("Live Audit Register")

    # Export Feature
    if not df_display.empty:
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Register as CSV",
            data=csv,
            file_name=f"audit_register_{date.today()}.csv",
            mime='text/csv',
        )

        # Highlight overdue bimonthly dates in Red
        def highlight_overdue(row):
            try:
                deadline = pd.to_datetime(row['Bimonthly_Due']).date()
                if deadline < date.today() and row['Status'] != "Completed":
                    return ['background-color: #ffcccc'] * len(row) # Light Red
                return [''] * len(row)
            except:
                return [''] * len(row)

        st.dataframe(
            df_display.style.apply(highlight_overdue, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption("💡 Red rows indicate audits that are past their Bimonthly Update deadline.")
    else:
        st.info("The register is currently empty. Use the sidebar to add audits.")

    # --- REFRESH BUTTON ---
    if st.button("🔄 Refresh Data"):
        st.rerun()
