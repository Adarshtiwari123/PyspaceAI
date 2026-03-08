import streamlit as st

def login_ui():
    st.markdown("<h1 style='text-align:center;'>🚀 PYSPACE AI Interview</h1>", unsafe_allow_html=True)

    with st.container():
        st.subheader("Login to Continue")

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        login_btn = st.button("Login")

        if login_btn:
            if email and password:
                st.session_state["user"] = email
                st.success("Login Successful!")
                st.rerun()
            else:
                st.error("Please fill all fields")