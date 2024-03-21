import streamlit as st
import datetime
import cv2
import face_rec


st.set_page_config(page_title="Fast Face Recognition System", layout="wide")

selected_date = st.date_input("Today Date is", value=datetime.date.today())



from streamlit_apexjs import st_apexcharts
options = {
    "chart": {
        "toolbar": {
            "show": False
        }
    },

    "labels": ['Today', 'Yesterday', 'Last Week', 'Last Month', 'Last Year']
    ,
    "legend": {
        "show": True,
        "position": "bottom",
    },

    }

series = [44, 55, 41, 17, 15]

st_apexcharts(options, series, 'donut', '600', 'Attandance Using Face Recognition System')



