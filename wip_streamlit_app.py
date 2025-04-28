import streamlit as st
import requests

def upload_file(file):
    """Upload file to backend"""
    with st.spinner("Uploading and processing file(s)..."):
        files = {"file": file}
        username = st.session_state.username
        result, error = requests.post("http://127.0.0.1:5001/upload", files,  data={"username": username}, timeout=30)
        
        if error:
            st.error(error)
            return False
        
        return True

def file_upload_section():
    failure = 0

    """Handle file upload"""
    with st.form('Upload file(s)', clear_on_submit=True):
        uploaded_files = st.file_uploader("Choose a file", type=[
        'bmp', 'csv', 'doc', 'docx', 'eml', 'epub', 'heic', 'html',
        'jpeg', 'jpg', 'png', 'md', 'msg', 'odt', 'org', 'p7s', 'pdf',
        'ppt', 'pptx', 'rst', 'rtf', 'tiff', 'txt', 'tsv', 'xls', 'xlsx', 'xml'
        ]
        , accept_multiple_files=True)
    
        submitted = st.form_submit_button('Upload')

        if submitted and uploaded_files is not None:
            for uploaded_file in uploaded_files:
                if not upload_file(uploaded_file):
                    failure += 1
            success = len(uploaded_files) - failure
            st.success(f'Uploaded {success} file(s) successfully, {failure} file(s) failed')