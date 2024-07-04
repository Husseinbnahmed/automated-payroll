import pandas as pd
import streamlit as st
from typing import List
import connectteams as ct

def load_and_process_data(files: List[st.UploadedFile]) -> pd.DataFrame:
    """Load and process uploaded Excel files."""
    dfs = [pd.read_excel(file) for file in files]
    df_combined = pd.concat(dfs, ignore_index=True)
    df_combined['Date'] = pd.to_datetime(df_combined['Date'])
    df_combined['Start'] = pd.to_datetime(df_combined['Start'], format='%I:%M%p').dt.time
    df_combined['End'] = pd.to_datetime(df_combined['End'], format='%I:%M%p').dt.time
    return df_combined

def process_timesheet(df: pd.DataFrame) -> pd.DataFrame:
    """Process the timesheet data."""
    df = ct.split_shifts(df)
    df = ct.holiday_tagger_updated(df)
    df = ct.get_info_from_date(df)
    return ct.create_time_sheet(df)

def format_user_names(df: pd.DataFrame) -> pd.DataFrame:
    """Format user names from 'First Last' to 'Last, First'."""
    df['Users'] = df['Users'].str.split().apply(lambda x: f"{x[1]}, {x[0]}")
    return df.sort_values('Users').reset_index(drop=True)

st.title("ConnectTeams to ADP Converter")
st.caption("✨ This app bridges the gap between Connect Teams and ADP, transforming your schedules into a payroll-ready format.")

with st.form(key='upload_form'):
    files = [
        st.file_uploader("1- Upload excel file for **week 1** 📗", accept_multiple_files=False),
        st.file_uploader("2- Upload excel file for **week 2** 📗", accept_multiple_files=False)
    ]
    submit_button = st.form_submit_button(label='➡️ Process Files')

if submit_button and all(files):
    try:
        df_combined = load_and_process_data(files)
        time_sheet = process_timesheet(df_combined)
        time_sheet_user = time_sheet.groupby("Users").agg({
            "Regular Hours": "sum",
            "Holiday Hours": "sum",
            "Overtime Hours": "sum"
        }).reset_index()
        time_sheet_user = format_user_names(time_sheet_user)

        st.success("✅ Files processed successfully!")
        st.dataframe(time_sheet_user, width=1000, height=500)
        st.balloons()

        csv = time_sheet_user.to_csv(index=False)
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name='adp_template_upload.csv',
            mime='text/csv'
        )
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
else:
    st.info("Please upload both files and click 'Process Files' to begin.")