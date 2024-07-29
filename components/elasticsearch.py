import streamlit as st
import json

session_state = st.session_state

def get_indexes(index_pattern : str = "*") -> list:
    """
    Gets the indexes in the Elasticsearch cluster.

    Returns:
        list: A list of indexes in the Elasticsearch cluster.
    """
    es_client = session_state.get("es_client")
    index_pattern=index_pattern+",-.*" # Exclude system indices
    try:
        indices = es_client.indices.get_alias(index=index_pattern)  
    except Exception as e:
        indices = []
    return indices

def index_selector_widget(container: st.container, prefix: str = ''):
    """
    Renders a widget for selecting an index pattern.

    Parameters:
    - container (st.container): Streamlit container to render the widget in.
    - prefix (str): Prefix for the widget keys.

    Returns:

    """
    with container:
        col1 , col2 = st.columns(2)
        with col1:
            index_pattern=st.text_input("Search Index Pattern", key=prefix+"index_pattern", value=session_state.get("index_pattern", "*"))
        with col2:
            index_name = st.selectbox("Selecr Index Name", options=get_indexes(index_pattern), key=prefix+"index_name")
    return index_name


def get_elasticsearch_results(query):
    es_client = session_state.get("es_client")
    es_query  = session_state.get("search_body", "*")

    if query is None or query == "" or query == "*":
        es_query = {
            "query": {
                "match_all": {}
            }
        }
    else:
        es_query = es_query.replace("{query}", query)
        es_query = json.loads(es_query)
    es_query["size"] = session_state.get("num_results", 10)
    index_pattern = session_state.get("index_name", "*")
    print("Querying Elasticsearch")
    #print(query)
    #print(es_query)
    #print(index_pattern)
    result = es_client.search(index=index_pattern, body=es_query)
    #print(result)
    return result["hits"]["hits"]

def search(query):
    apm_client = session_state.get("apm_client")
    if apm_client:
        apm_client.begin_transaction(transaction_type="script")
    results = get_elasticsearch_results(query)
    n_results = len(results)
    print(f"Found {n_results} results")
    session_state["search_results"] = results
    if apm_client:
        apm_client.end_transaction(name="manual_search", result="success")
    return results