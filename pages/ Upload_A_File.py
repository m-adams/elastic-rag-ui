import streamlit as st
from components.elasticsearch import index_selector_widget

session_state = st.session_state

def main():
    st.title("Upload a File")

    new_or_existing = st.radio("New or Existing Index", ("New", "Existing"))
    index_container = st.container()
    if new_or_existing == "New":
        index_name = st.text_input("Index Name")
    else:
        index_name=index_selector_widget(index_container, prefix="upload_")
    uploaded_file = st.file_uploader("Choose a file")
    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
        st.write(file_details)
        st.write(uploaded_file)


if __name__ == "__main__":
    main()
else:
    main()
