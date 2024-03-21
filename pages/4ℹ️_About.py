import streamlit as st

def main():
    # Set page layout and background color
    st.set_page_config(page_title="About Face Recognition App", layout="wide", page_icon=":smiley:", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
        body {
            color: #333333;
            background-color: #ffffff;
        }
        .sidebar .sidebar-content {
            background-color: #f0f0f0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Main content
    st.title("About Face Recognition App")



    st.write("""
        This is a real-time attendance system using face recognition. 
        It identifies registered users and logs their attendance.
    """)

    st.subheader("How it Works")
    st.write("""
        1. **Registration**: Users register their faces along with their names and roles.
        2. **Real-time Recognition**: When a user shows their face to the camera, the app detects and identifies them in real-time.
        3. **Attendance Logging**: The app logs the attendance of recognized users.
    """)

    st.subheader("Meet the Team")
    st.write("""
        - Rabindra Adhikari
        - Ramdev Tamang
        - Chandra Laxmi Napit
    """)

    st.subheader("Contact Us")
    st.write("""
        If you have any questions or feedback, feel free to reach out to us at jamestamang544@gmail.com.
    """)

# Add image
    st.image("face1.jpg", width=300)
if __name__ == "__main__":
    main()
