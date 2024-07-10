import streamlit as st

default_md_template = """
# {title}

"""

def deslay_doc(doc: dict, md_template: str = None):

    with st.container():
        for key, value in doc.items():
            st.write(f"**{key}**: {value}")
    st.write(doc)

def search_results_widget(search_results_container,docs: list[dict]):
    with search_results_container:
        st.title("Search Results")
        for doc in docs:
            deslay_doc(doc)
