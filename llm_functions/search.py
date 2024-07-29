import streamlit as st
import elasticapm
# Add the parent directory to the path
import sys
sys.path.append("..")
from components.elasticsearch import search as es_search

session_state = st.session_state


if "corpus_description" in session_state and session_state["corpus_description"] is not None:
    description ="The function searches an elasticsearch index to help provide accurate and up to date information to the user and returns a list of available titles. The description of the corpus is: "+ session_state["corpus_description"]
else:
    description = "The function searches an elasticsearch index to help provide accurate and up to date information to the user and returns a list of available titles."

definition = {
    "name": "search",
    "description": description,
    "parameters": {
        "type": "object",
        "properties": {
        "query_text": {
            "type": "string",
            "description": "The query text to search for. This should be an expansive set of keywords to find the best document, for example including synonymns"
        }
        },
        "required": ["query_text"]
    }
}

@elasticapm.capture_span("bm25_search")
def search(query_text: str):

    print("Searching for: ", query_text )


    search_results = es_search(query_text)

    #print("Search results: ", search_results)
    session_state["search_query"] = query_text
    session_state["search_results"] = search_results
    titles = [result["_source"]["title"] for result in search_results]  
    return titles
