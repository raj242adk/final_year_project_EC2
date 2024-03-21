import pandas as pd
import streamlit as st
from Home import face_rec

import numpy as np
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load configuration from config.yaml
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Define and initialize authenticator object with required arguments
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key']
)

# Initialize session state if not already initialized
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False  # Assuming initial state is False

if st.session_state['authentication_status']:
    authenticator.logout('Logout', 'sidebar', key='unique_key')
    st.markdown("<h1 style='text-align:center;'>Report Page</h1>", unsafe_allow_html=True)

    #reterive logs data from Redish.py
    #Extract data from redish List

    name='attendace:logs'
    def load_logs(name,end=-1):
        logs_list = face_rec.r.lrange(name,start=0,end=end)
        return logs_list

    #tabs to show the info
    tab1,tab2,tab3=st.tabs(['Registered Data','Logs','Attendance Report'])

    with tab1:
        # if st.button('Refresh Data'):
        #     with st.spinner('Loading...........'):
        #         redis_face_db = face_rec.retrive_data(name='academy:register')
        #         st.dataframe(redis_face_db[['Name','Role']])

        if st.button('Refresh Data'):
            with st.spinner('Loading...........'):
                # Retrieve data from the database
                redis_face_db = face_rec.retrive_data(name='academy:register')

                # Filter the DataFrame for students and teachers
                students_df = redis_face_db[redis_face_db['Role'] == 'Student']
                teachers_df = redis_face_db[redis_face_db['Role'] == 'Teacher']

                # Display the data for students
                st.subheader('Students:')
                st.dataframe(students_df[['Name', 'Role']])

                # Display the data for teachers
                st.subheader('Teachers:')
                st.dataframe(teachers_df[['Name', 'Role']])

    with tab2:
        if st.button("Refresh Logs"):
             st.write(load_logs(name=name))

    with tab3:

        # this another code for student and teacher
        st.subheader("Attendance Report")

        # Load logs into attribute logs_list
        logs_list = load_logs(name=name)

        # Step 1: Convert the logs from a list of bytes into a list of strings
        logs_list_string = [log.decode('utf-8') for log in logs_list]

        # Step 2: Split each string by "@" to create a nested list
        logs_nested_list = [log.split('@') for log in logs_list_string]

        # Additional step: Split the role and timestamp within each sublist
        for log in logs_nested_list:
            # Check if the log entry contains the expected format
            if len(log) == 2:
                name, role_timestamp = log
                role, timestamp = role_timestamp.split(':', 1)
                log[1] = role
                log.append(timestamp)
            else:
                # Handle unexpected log format
                print("Error: Unexpected log format -", log)

        # Convert nested list info into DataFrame
        logs_df = pd.DataFrame(logs_nested_list, columns=['Name', 'Role', 'Timestamp'])

        # Step 3 Time base analysis or report
        logs_df['Timestamp'] = pd.to_datetime(logs_df['Timestamp'])
        logs_df['Date'] = logs_df['Timestamp'].dt.date

        # Step 3.1: Calculate In time and Out time
        # In time: At which person is first detected in that day (min Timestamp of the date)
        # Out time: At which person is last detected in that day (max Timestamp of the date)

        report_df = logs_df.groupby(['Date', 'Name', 'Role']).agg(
            In_time=pd.NamedAgg('Timestamp', 'min'),  # in time
            Out_time=pd.NamedAgg('Timestamp', 'max')  # out time
        ).reset_index()

        report_df['In_time'] = pd.to_datetime(report_df['In_time'])
        report_df['Out_time'] = pd.to_datetime(report_df['Out_time'])
        report_df['Duration'] = report_df['Out_time'] - report_df['In_time']

        # Step 4: Marking person as present or absent
        all_dates = report_df['Date'].unique()
        name_role = report_df[['Name', 'Role']].drop_duplicates().values.tolist()

        date_name_role_zip = []
        for dt in all_dates:
            for name, role in name_role:
                date_name_role_zip.append([dt, name, role])

        date_name_role_df = pd.DataFrame(date_name_role_zip, columns=['Date', 'Name', 'Role'])

        # Left join with report_df
        date_name_role_zip_df = pd.merge(date_name_role_df, report_df, how='left', on=['Date', 'Name', 'Role'])

        # Duration
        # Hours
        date_name_role_zip_df['Duration_seconds'] = date_name_role_zip_df['Duration'].dt.total_seconds()
        date_name_role_zip_df['Duration_Hours'] = date_name_role_zip_df['Duration_seconds'] / (60 * 60)


        def status_marker(x):
            if pd.Series(x).isnull().all():
                return 'Absent'

            elif x > 0 and x < 1:
                return 'Absent (Less than 1 hr)'

            elif x >= 1 and x < 4:
                return 'Half Day (Less than 4 hrs)'
            elif x >= 4 and x < 6:
                return 'Half Day'
            elif x >= 6:
                return 'Present'


        date_name_role_zip_df['Status'] = date_name_role_zip_df['Duration_Hours'].apply(status_marker)

        # Display separate reports for students and teachers
        students_report = date_name_role_zip_df[date_name_role_zip_df['Role'] == 'Student']
        teachers_report = date_name_role_zip_df[date_name_role_zip_df['Role'] == 'Teacher']

        st.subheader("Students Attendance Report:")
        st.dataframe(students_report)

        st.subheader("Teachers Attendance Report:")
        st.dataframe(teachers_report)
else:
    authenticator.login(fields=['username', 'password'])