import streamlit as st
from Home import face_rec
from streamlit_webrtc import webrtc_streamer
import av
import numpy as np
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Define the send_email function
def send_email(receiver_email, person_name):
    sender_email = "raj242adk@gmail.com"  # Update with your sender email
    password = "ukme yxqq motz kqbq"  # Update with your sender email password

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Registration Confirmation"

    body = f"Hello {person_name},\n\nYou have successfully registered.\n\nBest regards,\nYour Organization"

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

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
    st.header('Registration Form')
    registration_form = face_rec.RegistrationForm()

    # Step 1 collect person name, email, and role
    person_name = st.text_input(label='Name', placeholder='First and Last Name')
    email = st.text_input(label='Email', placeholder='Your Email Address')
    role = st.selectbox(label='Select your Role', options=('Student', 'Teacher'))


    # Step 2 Collect facial embedding of that person
    def video_callback_func(frame):
        img = frame.to_ndarray(format="bgr24")
        reg_img, embedding = registration_form.get_embedding(img)
        if embedding is not None:
            with open('face_embedding.txt', mode='ab') as f:
                np.savetxt(f, embedding)
        return av.VideoFrame.from_ndarray(reg_img, format="bgr24")


    webrtc_streamer(key='registration', video_frame_callback=video_callback_func,
                    rtc_configuration={
                        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                    }
                    )

    if st.button('Submit'):
        return_val = registration_form.save_data_in_redish_db(person_name, role)
        if return_val == True:
            st.success(f"{person_name} registered successfully")

            # Send email upon successful registration
            send_email(email, person_name)

        elif return_val == 'name_false':
            st.error('Please enter a valid name')
        elif return_val == 'file_false':
            st.error('face_embedding.txt is not found')

else:
    authenticator.login(fields=['username', 'password'])

