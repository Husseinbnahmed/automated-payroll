import pandas as pd
import numpy as np
import streamlit as st
import connectteams as ct
import time
import openpyxl


st.title("ConnectTeams to ADP")
st.caption(""" ✨ This app bridges the gap between Connect Teams and ADP, transforming your schedules into a payroll-ready format.  
FYI: Some employees may have different names in each system, so keep an eye out for those.

""")

st.video()

tst = pd.DataFrame()

with st.form(key='my_form'):
 
    #upload the schedule downloaded from connect teams for both weeks and save them as dataframes
    df = st.file_uploader(" 1- Upload excel file for **week 1** 📗", accept_multiple_files=False)
    df_1 = st.file_uploader(" 2- Upload excel file for **week 2** 📗", accept_multiple_files=False)
    # paychex = st.file_uploader("🧑 UPLOAD EMPLOYEE DATA FROM **PAYCHEX**: In this step you will need to upload data from paychex that contains the employee name, their employee ID, please make sure that the sheet name is **Data**", accept_multiple_files=False)
    submit_button = st.form_submit_button(label='➡️ Submit files')
    
    if submit_button:
        # try:
            df = pd.read_excel(df)
            df_1 = pd.read_excel(df_1)
            #merge df and df_1
            df_two_week_schedule = pd.concat([df, df_1])
            # Convert Date column to datetime
            df_two_week_schedule['Date'] = pd.to_datetime(df_two_week_schedule['Date'])
            # Convert Start and End times to datetime.time
            df_two_week_schedule['Start'] = pd.to_datetime(df_two_week_schedule['Start'], format='%I:%M%p').dt.time
            df_two_week_schedule['End'] = pd.to_datetime(df_two_week_schedule['End'], format='%I:%M%p').dt.time
            # paychex = pd.read_excel(paychex, sheet_name="Data")

            #process the files
            df_two_week_schedule_1 = ct.split_shifts(df_two_week_schedule)
            df_two_week_schedule_2 = ct.holiday_tagger_updated(df_two_week_schedule_1)
            df_two_week_schedule_3 = ct.get_info_from_date(df_two_week_schedule_2)
            df_two_week_schedule_4= ct.get_building_and_job(df_two_week_schedule_3)
            df_two_week_schedule_5 = ct.create_time_sheet(df_two_week_schedule_4)
            df_two_week_schedule_6= ct.adjust_hours(df_two_week_schedule_5)

            #group by users and agg sum the regular, holiday and overtime hours
            df_two_week_schedule_6 = df_two_week_schedule_6.groupby(["Users"]).agg({"Regular Hours": "sum", "Holiday Hours": "sum", "Overtime Hours": "sum"}).reset_index()
            # reorganize the user's column 
            first_name = df_two_week_schedule_6['Users'].str.split(" ").str[0]
            last_name = df_two_week_schedule_6['Users'].str.split(" ").str[1]
            #update the user's column 
  
            df_two_week_schedule_6["Users"] = last_name + ", " + first_name
            #sort the users column alphabetically
            df_two_week_schedule_6 = df_two_week_schedule_6.sort_values(by=['Users'])
            #reset the index
            df_two_week_schedule_6 = df_two_week_schedule_6.reset_index(drop=True)
            #group by Job and sum regular, holiday and overtime hours
            df_two_week_schedule_5 = df_two_week_schedule_5.groupby(["Job"]).agg({"Regular Hours": "sum", "Holiday Hours": "sum", "Overtime Hours": "sum"}).reset_index()


            st.write("✅ Success! Your files have been processed.")

            # tst = ct.get_paychex_template(paychex, df, df_1)
            # st.write(len(tst["Worker ID"].unique()), "Employees were processed")
            st.dataframe(df_two_week_schedule_6, width=1000, height=500)

            st.dataframe(df_two_week_schedule_5, width=1000, height=500)
            
           
            st.balloons()
            #count the unique worker id to see how many employees were processed


        # except Exception as e:
        #     print(e)
        #     st.warning("No files uploaded, or something went wrong")
    else:
        st.caption(" You must click on the submit button to process the files")


try:
    st.download_button(label=":arrow_down: Download to CSV", data=df_two_week_schedule_6.to_csv(), file_name='adp_template_upload.csv', mime='text/csv')
except:
    st.warning("No files processed")
