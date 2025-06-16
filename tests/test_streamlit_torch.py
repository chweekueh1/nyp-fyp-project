import streamlit as st
import torch # Keep this import, as it's the trigger

# These lines should run fine based on your test
st.write(f"PyTorch version: {torch.__version__}")
st.write(f"CUDA available: {torch.cuda.is_available()}")

st.title("My Minimal PyTorch App")
st.write("This is a test to see if Streamlit loads with PyTorch.")

# Only add your actual app logic here if the minimal app works
# For now, keep it super simple.
