import streamlit as st
import elasticapm

session_state = st.session_state

definition = {
    "name": "get_content",
    "description": "Get the content of a document from the elasticsearch index using the title",
    "parameters": {
    "type": "object",
    "properties": {
        "title": {
        "type": "string",
        "description": "The title of the document to get the content for"
        }
    },
    "required": ["title"]
    }
}

@elasticapm.capture_span("bm25_search")
def get_content(title: str):

    results = session_state.get("search_results")

    if results is None:
        return "No results found"
    for result in results:
        if result["_source"]["title"] == title:
            return result["_source"]