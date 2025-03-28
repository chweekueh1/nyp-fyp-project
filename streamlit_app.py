import streamlit as st
import requests

def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password", key="password_input")

    if st.sidebar.button("Login"):
        if username == "staff" and password == "password123":
            st.session_state.logged_in = True
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Invalid username or password")

def main():
    st.title("NYP AI Chatbot Helper")

    # Check login status
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
        return
    
    # Change button to Logout when logged in
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # File Upload Section
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx", "xlsx", "pptx", "jpg", "jpeg", "png"])
    if uploaded_file is not None:
        files = {"file": uploaded_file}
        response = requests.post("http://127.0.0.1:5001/upload", files=files)
        if response.status_code == 200:
            st.success("File uploaded and processed successfully!")
        else:
            st.error(f"File upload failed: {response.json().get('error')}")

    # Question Answering Section
    st.header("Ask a Question")
    question = st.text_input("Enter your question")
    if st.button("Submit Question") and question:
        payload = {"question": question}
        response = requests.post("http://127.0.0.1:5001/ask", json=payload)
        if response.status_code == 200:
            st.write("Answer:")
            st.write(response.json().get("answer"))
        else:
            st.error("Failed to get an answer: " + response.json().get("error"))

if __name__ == "__main__":
    main()