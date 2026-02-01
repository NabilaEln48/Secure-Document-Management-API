import streamlit as st
import requests

st.set_page_config(page_title="Secure Doc Portal", layout="centered")

st.title("🛡️ Secure Document Portal")
st.markdown("---")

# --- LOGIN SECTION ---
if 'token' not in st.session_state:
    st.subheader("Login to Access")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        login_data = {"username": email, "password": password}
        response = requests.post("http://127.0.0.1:8000/auth/login", data=login_data)
        
        if response.status_code == 200:
            st.session_state['token'] = response.json()["access_token"]
            st.session_state['email'] = email
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- UPLOAD SECTION ---
else:
    st.sidebar.success(f"Logged in as: {st.session_state['email']}")
    if st.sidebar.button("Logout"):
        del st.session_state['token']
        st.rerun()

    st.subheader("Upload New Document")
    doc_title = st.text_input("Document Title")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'xlsx'])

    if st.button("Submit to Backend"):
        if doc_title and uploaded_file:
            headers = {"Authorization": f"Bearer {st.session_state['token']}"}
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data = {"title": doc_title}
            
            with st.spinner("Uploading..."):
                res = requests.post("http://127.0.0.1:8000/documents/", headers=headers, data=data, files=files)
            
            if res.status_code == 200:
                st.success(f"✅ Successfully uploaded: {res.json().get('message')}")
            else:
                st.error(f"Upload failed: {res.text}")
        else:
            st.warning("Please provide both a title and a file.")