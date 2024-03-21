import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import time

st.subheader("Real-time Attendance System")



# Retrive the data from the database

with st.spinner("Retriving Data form DB"):
    redis_face_db = face_rec.retrive_data(name='academy:register')
    #st.dataframe(redis_face_db)
st.success("Data Retrieved from Database")

st.markdown("<h3 style='color:blue'>Show your face to the camera and get identified</h3>", unsafe_allow_html=True)

waitTime=30
setTime=time.time()
realtimepred=face_rec.RealTimePred()


# RealTime Predection


# CallBack function
def video_frame_callback(frame):
    global setTime
    img = frame.to_ndarray(format="bgr24")
    pred_img = realtimepred.face_prediction(img, redis_face_db, 'facial_features', ['Name', 'Role'], thresh=0.5)


    timenow=time.time()
    diffTime=timenow-setTime

    if diffTime>=waitTime:
        realtimepred.saveLogs_redish()
        setTime=time.time()#Reseat Time

        print("Save Data to database")


    return av.VideoFrame.from_ndarray(pred_img, format="bgr24")


webrtc_streamer(key="realtimePrediction", video_frame_callback=video_frame_callback,
rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    }
                )

