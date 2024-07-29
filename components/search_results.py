import streamlit as st

session_state = st.session_state

# Load default markdown template
with open("default_md_template.md") as f:
    default_md_template = f.read().strip()



def render_document(doc: dict, md_template: str = None):

    if md_template:
        source = doc["_source"]
        try:
            doc = md_template.format(**source)
            st.markdown(doc)
        except Exception as e:
            print(e)
            print("Error in writing doc")
            print(source)

def search_results_widget(search_results_container,docs: list[dict], md_template: str = None):
    with search_results_container:
        for doc in docs:
            render_document(doc, md_template)
