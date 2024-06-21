import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta, time


# new logic added on 6/2/2024 - objective: to account for overnight shifts that extend to a holiday day. 

def split_shifts(df):
    split_data = []
    
    for index, row in df.iterrows():
        # Combine Date and Start time into a single datetime object
        start = datetime.combine(row['Date'], row['Start'])
        # Combine Date and End time into a single datetime object
        end = datetime.combine(row['Date'], row['End'])
        
        # Check if the shift ends the next day (overnight shift)
        if end <= start:
            end += timedelta(days=1)  # Adjust end time to the next day
            
            # Split the shift into two parts: before and after midnight
            first_shift_end = datetime.combine(row['Date'], time(23, 59, 59))
            second_shift_start = datetime.combine(row['Date'] + timedelta(days=1), time(0, 0, 0))
            
            # Calculate hours for the first part of the shift (before midnight)
            first_shift_hours = (first_shift_end - start).total_seconds() / 3600 + 1 / 3600
            # Calculate hours for the second part of the shift (after midnight)
            second_shift_hours = (end - second_shift_start).total_seconds() / 3600
            
            # Append the first part of the shift to the split_data list
            split_data.append({
                'Date': row['Date'],
                'Start': row['Start'],
                'End': '11:59:59 PM',
                'Shift title': row['Shift title'],
                'Job': row['Job'],
                'Draft': row['Draft'],
                'Users': row['Users'],
                'Location': row['Location'],
                'Hours': round(first_shift_hours, 2),
                'Holiday': 0  # Initial tagging
            })
            
            # Append the second part of the shift to the split_data list
            split_data.append({
                'Date': row['Date'] + timedelta(days=1),
                'Start': '12:00:00 AM',
                'End': row['End'],
                'Shift title': row['Shift title'],
                'Job': row['Job'],
                'Draft': row['Draft'],
                'Users': row['Users'],
                'Location': row['Location'],
                'Hours': round(second_shift_hours, 2),
                'Holiday': 0  # Initial tagging
            })
        else:
            # Calculate hours if the shift does not span midnight
            hours = (end - start).total_seconds() / 3600
            split_data.append({
                'Date': row['Date'],
                'Start': row['Start'],
                'End': row['End'],
                'Shift title': row['Shift title'],
                'Job': row['Job'],
                'Draft': row['Draft'],
                'Users': row['Users'],
                'Location': row['Location'],
                'Hours': round(hours, 2),
                'Holiday': 0  # Initial tagging
            })
    
    # Return a DataFrame with the split shifts
    return pd.DataFrame(split_data)

def holiday_tagger_updated(df):
    # List of holiday dates
    holidays = ['2024-01-01', '2024-05-27', '2024-07-04', '2024-09-02', '2024-12-25', '2024-11-28', '2025-01-01']
    holidays = [datetime.strptime(date, '%Y-%m-%d').date() for date in holidays]
    
    # Convert Date column to datetime.date
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    
    # Tag holidays based on the Date column
    df['Holiday'] = df['Date'].apply(lambda x: 1 if x in holidays else 0)
    
    return df

def daily_hours_worked(df):
    """Calculates the number of hours worked by each employee in the schedule
    parameters:
    merged_test_df: a transformed dataframe

    returns:
    an additional column that computes the hours worked of each employee
    """

    # make sure that time in and out are in datetime formats format='%H:%M:%S'
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])

    #calculate the number of hours worked between time in and time out
    df['Hours'] = df['End'] - df['Start']
    df['Hours'] = df['Hours'].apply(lambda x: x.total_seconds() / 3600 if x.total_seconds() > 0 else (x + pd.Timedelta('1D')).total_seconds() / 3600)
    df['Hours'] = df['Hours'].round(2)
    return df

def holiday_tagger(df):

    """ tags if a day is a holiday or not """
    # List of holiday dates provided by Amanda on 1/18/2024 in an SMS txt message  
    holidays = [ '2024-1-1', '2024-05-27', '2024-07-04', '2024-09-02', '2024-12-25', '2024-11-28', '2025-1-1']

    #convert Date column to datetime format
    df['Date'] = pd.to_datetime(df['Date'])
    # create a holiday column, and assigns the value of 1 if the date of work in 'holidays' list, else assigns a 0
    df['Holiday'] = df['Date'].apply(lambda x: 1 if x.date().isoformat() in holidays else 0)
    # returns the original dataframe, with a new holiday column
    return df

def get_info_from_date(df):
       """ Extracts the week number from the date column and adds it to the dataframe"""
       
       df['Week'] = df['Date'].apply(lambda x: x.isocalendar()[1])
       #Ensure that week is an integer # with no decimals and then convert it to a string so that we can filter on it
       
       df['Week'] = df['Week'].apply(lambda x: str(x))
        # get the year from the date column
       df['Year'] = df['Date'].apply(lambda x: x.year)
        # get the month from the date column
       df['Month'] = df['Date'].apply(lambda x: x.month)

        # return the original dataframe, with three new columns, week, year and month
       return df

# Extract the Building Name and the Job title from the Job column and add them to the dataframe by splitting on =>
def get_building_and_job(df):
    """ Extracts the building name and the job title from the Job column and adds them to the dataframe by splitting on =>"""
    df['Building'] = df['Job'].str.split('=>').str[0]
    df['Job'] = df['Job'].str.split('=>').str[1]
    return df

def create_time_sheet(df):
    """
    Takes a dataframe and categorizes the total hours by each employee into three categories (holiday, regular and overtime hours) and shows the result by month, year, week, building and job to be made

    """

    # Create a new DataFrame with the desired columns
    result = pd.DataFrame(columns=['Users', 'Month', 'Year', 'Holiday Hours', 'Regular Hours', 'Overtime Hours'])
    
    # Group the data by employee and week of year
    grouped = df.groupby(['Users', 'Week', 'Year', 'Month', 'Building', 'Job'])
    
    # Iterate over each group and calculate the hours
    for name, group in grouped:
        holiday_hours = group[group['Holiday'] == 1]['Hours'].sum()
        regular_hours = group[group['Holiday'] == 0]['Hours'].sum()
        overtime_hours = 0
        if regular_hours > 40:
            overtime_hours = regular_hours - 40
            #convert overtime_hours to float

            regular_hours = 40
        
        month = group.loc[:,'Month']
            
       # Create a single-row DataFrame for this group and concatenate it with the result DataFrame
        row = pd.DataFrame({'Users': [name[0]],
                            'Job': [name[4]],
                            'Building': [name[5]],
                            'Week': [name[1]],
                            'Month': [name[3]], 
                            'Year': [name[2]],
                            'Holiday Hours': [holiday_hours], 
                            'Regular Hours': [regular_hours], 
                            'Overtime Hours': [overtime_hours]})
        
        result = pd.concat([result, row], ignore_index=True)
        #convert overtime_hours to float
        result['Overtime Hours'] = result['Overtime Hours'].astype(float)
        #convert week to str
        result['Week'] = result['Week'].astype(str)
        #convert month to str
        result['Month'] = result['Month'].astype(str)
        #convert year to date format
        result['Year'] = result['Year'].astype(str)

    return result

def get_final_dataframe(tst_schedule, payrates):

    """ merges the payrates from paychex with the connect teams scheduler"""

    payrates['Full name_2'] = payrates['Full name'].apply(lambda x: x.split(' ')[1]+ " " + x.split(' ')[0]).str.replace(",","")
    #merge the payrates dataframe with the tst_schedule dataframe
    merged_test_df = pd.merge(tst_schedule, payrates, left_on='Users', right_on='Full name_2', how='left')
    #fill na in the pay rate 1 column with the average pay rate
    merged_test_df['Pay rate 1'] = merged_test_df['Pay rate 1'].fillna(17)

    #create a column called holiday hours payment that calculates the holiday hours payment by multiplying holiday hours with pay rate 1 x 1.5
    merged_test_df['Holiday Hours Payment'] = merged_test_df['Holiday Hours'] * (merged_test_df['Pay rate 1'] * 1.5)
    #create a column called regular hours payment that calculates the regular hours payment by multiplying regular hours with pay rate 1
    merged_test_df['Regular Hours Payment'] = merged_test_df['Regular Hours'] * merged_test_df['Pay rate 1']
    #create a column called overtime hours payment that calculates the overtime hours payment by multiplying overtime hours with pay rate 1 x 1.5
    merged_test_df['Overtime Hours Payment'] = merged_test_df['Overtime Hours'] * (merged_test_df['Pay rate 1'] * 1.5)
    #create a column called total payment that calculates the total payment by adding holiday hours payment, regular hours payment and overtime hours payment
    merged_test_df['Total Payment'] = merged_test_df['Holiday Hours Payment'] + merged_test_df['Regular Hours Payment'] + merged_test_df['Overtime Hours Payment']

    #drop rows where the pay rate 1 > 100
    merged_test_df = merged_test_df[merged_test_df['Pay rate 1'] < 100]
    return merged_test_df

def adjust_hours(df):

    """ If we stopped at previous functions, the output will calculate regular and overtime hours for each employee at a building level of detail, ignoring that one employee could have worked at multiple buildings for the same week. This
    function will make an adjustmed to look at the Users and Week level of detail and ignore the building level of detail, while making the calculation. Hocine Massoud was the problem"""
    df.sort_values(['Users', 'Week', 'Building'], inplace=True)

    new_rows = []
    total_regular_hours = {}

    for i, row in df.iterrows():
        key = (row['Users'], row['Week'])

        if key not in total_regular_hours:
            total_regular_hours[key] = 0.0

        new_total = total_regular_hours[key] + row['Regular Hours']

        if new_total > 40:
            overtime = new_total - 40
            regular = 40 - total_regular_hours[key]
        else:
            regular = row['Regular Hours']
            overtime = row['Overtime Hours']

        total_regular_hours[key] += regular

        new_row = row.copy()
        new_row['Regular Hours'] = regular
        new_row['Overtime Hours'] = overtime 
        # make regular hours and overtime hours with 2 decimal points
        new_row['Regular Hours'] = round(new_row['Regular Hours'], 2)
        new_row['Overtime Hours'] = round(new_row['Overtime Hours'], 2)

        # new_row['Regular Hours Payment'] = regular * row['Pay rate 1']
        # new_row['Overtime Hours Payment'] = (overtime + row['Overtime Hours']) * row['Pay rate 1'] * 1.5
        # new_row['Total Payment'] = new_row['Regular Hours Payment'] + new_row['Overtime Hours Payment'] + row['Holiday Hours Payment']

        new_rows.append(new_row)

    adjusted_df = pd.DataFrame(new_rows)
    return adjusted_df

# + row['Overtime Hours']

def adjust_hours_updated(df):
    """ Adjusts regular and overtime hours for each employee at a weekly level. """
    df.sort_values(['Users', 'Week'], inplace=True)

    new_rows = []
    total_regular_hours = {}

    for i, row in df.iterrows():
        key = (row['Users'], row['Week'])

        if key not in total_regular_hours:
            total_regular_hours[key] = 0.0

        current_regular_hours = total_regular_hours[key]
        new_total_regular_hours = current_regular_hours + row['Regular Hours']

        if new_total_regular_hours > 40:
            if current_regular_hours < 40:
                regular = 40 - current_regular_hours
                overtime = new_total_regular_hours - 40
            else:
                regular = 0
                overtime = row['Regular Hours']
        else:
            regular = row['Regular Hours']
            overtime = row['Overtime Hours']

        total_regular_hours[key] += regular

        new_row = row.copy()
        new_row['Regular Hours'] = regular
        new_row['Overtime Hours'] = round(overtime, 2)

        new_rows.append(new_row)

    adjusted_df = pd.DataFrame(new_rows)
    return adjusted_df

def get_paychex_template(paychex, file_1, file_2):

    # #this is the paychex data
    # paychex = pd.read_excel(paychex_employee_info_data, sheet_name='Data')

    # #bring in connect teams data
    # file_1 = pd.read_excel(file_1)
    # file_2 = pd.read_excel(file_2)

    #combine the two dataframes
    schedule = pd.concat([file_1, file_2])

    #apply a transformation to it
    daily_hours_worked(schedule)

    #make some adjustments
    #convert start and end times to AM and PM format
    schedule['Start'] = schedule['Start'].dt.strftime('%I:%M %p')
    schedule['End'] = schedule['End'].dt.strftime('%I:%M %p')

    #filter on needed columns only which are Date, Start, End, User, Hours
    schedule = schedule.loc[:,['Date', 'Start', 'End', 'User', 'Hours']]

    #convert the full name column to match the User column format in the tst_schedule dataframe
    paychex['Paychex Name Mapper'] = paychex['Full name'].apply(lambda x: x.split(' ')[1]+ " " + x.split(' ')[0]).str.replace(",","")

    #merge the tst_schedule dataframe with the payrates dataframe
    merged_test_df = pd.merge(schedule, paychex, left_on='User', right_on='Paychex Name Mapper', how='left')
    merged_test_df

    #drop na rows if employee ID is null
    merged_test_df = merged_test_df.dropna(subset=['Employee ID'])

    #make employee ID column an integer
    merged_test_df['Employee ID'] = merged_test_df['Employee ID'].astype(int)
    #make sure company id is an integer
    merged_test_df['Company ID'] = merged_test_df['Company ID'].astype(int)

    #Create an empty dataframe with the fields, Company ID	Worker ID	Punch/Apply Date	Punch Time 1	Punch Time 2	Total Hours
    paychex_template_df = pd.DataFrame(columns=['Company ID', 'Worker ID', 'Punch/Apply Date', 'Punch Time 1', 'Punch Time 2', 'Total Hours'])

    #iterate over each row in the merged_test_df dataframe and create a new row in the paychex_template_df dataframe
    paychex_template_df['Company ID'] = merged_test_df['Company ID']
    paychex_template_df['Worker ID'] = merged_test_df['Employee ID']
    paychex_template_df['Punch/Apply Date'] = merged_test_df['Date']
    paychex_template_df['Punch Time 1'] = merged_test_df['Start']
    paychex_template_df['Punch Time 2'] = merged_test_df['End']
    paychex_template_df['Total Hours'] = merged_test_df['Hours']

    return paychex_template_df
