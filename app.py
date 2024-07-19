import pandas as pd
import streamlit as st
from typing import List
import connectteams as ct

def load_and_process_data(files: List[st.runtime.uploaded_file_manager.UploadedFile]) -> pd.DataFrame:
    """Load and process uploaded Excel files."""
    dfs = [pd.read_excel(file) for file in files if file is not None]
    if not dfs:
        raise ValueError("No valid files uploaded")
    df_combined = pd.concat(dfs, ignore_index=True)
    df_combined['Date'] = pd.to_datetime(df_combined['Date'])
    df_combined['Start'] = pd.to_datetime(df_combined['Start'], format='%I:%M%p').dt.time
    df_combined['End'] = pd.to_datetime(df_combined['End'], format='%I:%M%p').dt.time
    df_combined = df_combined.drop_duplicates()
    return df_combined

def process_timesheet(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """Process the timesheet data."""
    df = ct.split_shifts(df)
    df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    df = ct.holiday_tagger_updated(df)
    df = ct.get_info_from_date(df)
    return ct.create_time_sheet(df)

def format_user_names(df: pd.DataFrame) -> pd.DataFrame:
    """Format user names from 'First Last' to 'Last, First'."""
    df['Users'] = df['Users'].str.split().apply(lambda x: f"{x[-1]}, {' '.join(x[:-1])}")
    return df.sort_values('Users').reset_index(drop=True)

st.title("ConnectTeams to ADP Converter")
st.caption("✨ Connecteams to ADP in minutes")


with st.form(key='upload_form'):
    files = [
        st.file_uploader("1- **Upload Connecteams export for LAST month**", accept_multiple_files=False),
        st.file_uploader("2- **Upload Connecteams export for THIS month**", accept_multiple_files=False)
    ]
    start_date = pd.to_datetime(st.date_input("3- Payroll start date", value=pd.Timestamp.today().date()))
    end_date = pd.to_datetime(st.date_input("4- Payroll end date", value=pd.Timestamp.today().date()))
    submit_button = st.form_submit_button(label='➡️ Process Files')

if submit_button:
    if not any(files):
        st.error("Please upload at least one file before processing.")
    else:
        try:
            df_combined = load_and_process_data(files)
            time_sheet = process_timesheet(df_combined, start_date, end_date)
            time_sheet_user = time_sheet.groupby("Users").agg({
                "Regular Hours": "sum",
                "Holiday Hours": "sum",
                "Overtime Hours": "sum"
            }).reset_index()
            time_sheet_user = format_user_names(time_sheet_user)

            st.success("✅ Files processed successfully!")
            st.dataframe(time_sheet_user, use_container_width=True)
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
    st.info("Please upload files and click 'Process Files' to begin.")

