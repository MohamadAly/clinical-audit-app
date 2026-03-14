import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION ---
CSV_FILE = 'audit_database.csv'

# Initialize the CSV file if it doesn't exist
if not os.path.exists(CSV_FILE):
    df = pd.DataFrame(columns=["ID", "Title", "Lead", "Status", "Start_Date", "Bimonthly_Due"])
    df.to_csv(CSV_FILE, index=False)

def load_data():
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- UI SETUP ---
st.set_page_config(page_title="Clinical Audit Hub", layout="wide")
st.title("🏥 Clinical Audit Live Department Portal")

# --- SIDEBAR: INPUT DATA ---
st.sidebar.header("Register / Update Audit")
with st.sidebar.form("audit_form"):
    audit_id = st.text_input("Audit ID (e.g., CA-202) ")
    title = st.text_input("Project Title")
    lead = st.text_input("Lead Auditor Name")
    status = st.selectbox("Current Status", ["Registered", "Data Collection", "Analysis", "Completed"])
    s_date = st.date_input("Start Date", value=date.today())
    b_date = st.date_input("Next Bimonthly Update Due")
    
    submit = st.form_submit_button("Update Register")

if submit:
    df = load_data()
    new_data = pd.DataFrame([[audit_id, title, lead, status, s_date, b_date]], 
                            columns=df.columns)
    df = pd.concat([df, new_data], ignore_index=True)
    save_data(df)
    st.sidebar.success("Database Updated!")

# --- MAIN DISPLAY ---
st.subheader("Current Audit Register")
df_display = load_data()

if not df_display.empty:
    def highlight_overdue(val):
        try:
            deadline = pd.to_datetime(val).date()
            if deadline < date.today():
                return 'background-color: #ffcccc; color: black'
            return ''
        except:
            return ''

    st.dataframe(
        df_display.style.applymap(highlight_overdue, subset=['Bimonthly_Due']),
        use_container_width=True
    )
else:
    st.info("No audits found. Use the sidebar to add the first one.")
