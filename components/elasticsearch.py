import streamlit as st
import elasticsearch
import json

session_state = st.session_state

def get_indexes(index_pattern : str = "*",prefix : str ="") -> list:
    """
    Gets the indexes in the Elasticsearch cluster.

    Returns:
        list: A list of indexes in the Elasticsearch cluster.
    """
    es_client = session_state.get(prefix+"es_client")
    index_pattern=index_pattern+",-.*" # Exclude system indices
    try:
        indices = es_client.indices.get_alias(index=index_pattern)  
    except Exception as e:
        indices = []
    return indices

def set_index_pattern(prefix: str = ''):

    index_pattern=session_state[prefix+"index_pattern"]
    print("Setting index pattern to", index_pattern)
    session_state[prefix+"index_pattern"] = index_pattern
    session_state[prefix+"index_options"] = get_indexes(index_pattern, prefix=prefix)

    return

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
            index_pattern=st.text_input("Search Index Pattern", key=prefix+"index_pattern", value=session_state.get(prefix+"index_pattern", "*"), on_change=set_index_pattern, args=[prefix])
        with col2:
            index_options = session_state.get(prefix+"index_options", get_indexes(session_state.get(prefix+"index_pattern", "*")))
            index_name = st.selectbox("Selecr Index Name", options=index_options, key=prefix+"index_name", on_change=select_index, args=[prefix])
    return index_name

def select_index(prefix: str = ''):
    """
    Selects the specified index.

    Parameters:
    - index_name (str): Name of the index.

    Returns:

    """
    index_name = session_state[prefix+"index_name"] 
    print("Setting index name to", index_name)
    fields = get_fields(index_name, prefix=prefix)
    field_names = [field["field"] for field in fields]
    keyword_fields = [field["field"] for field in fields if field["type"] == "keyword"]
    text_fields = [field["field"] for field in fields if field["type"] == "text"]
    geo_fields = [field["field"] for field in fields if field["type"] == "geo_point"]
    numeric_fields = [field["field"] for field in fields if field["type"] in ["long", "integer", "short", "byte", "double", "float", "half_float", "scaled_float"]]
    date_fields = [field["field"] for field in fields if field["type"] == "date"]
    keyword_and_text_fields = keyword_fields + text_fields

    session_state[prefix+"fields"] = get_fields(index_name)
    session_state[prefix+"keyword_fields"] = keyword_fields
    session_state[prefix+"text_fields"] = text_fields
    session_state[prefix+"geo_fields"] = geo_fields
    session_state[prefix+"numeric_fields"] = numeric_fields
    session_state[prefix+"date_fields"] = date_fields
    session_state[prefix+"keyword_and_text_fields"] = keyword_and_text_fields


def get_fields(index_name: str, prefix: str = "") -> list:
    """
    Gets the fields in the specified index.

    Parameters:
    - index_name (str): Name of the index.

    Returns:
        list: A list of fields in the specified index.
    """
    es_client : elasticsearch.Elasticsearch = session_state.get(prefix+"es_client")
    fields=[]
    # Create a list of dictionaries with each field and the mapping type
    try:
        field_caps = es_client.field_caps(index=index_name,fields="*")
        #print(field_caps)
        field_caps = field_caps["fields"]
        for field in field_caps:
            key = list(field_caps[field].keys())[0]
            type = field_caps[field][key]["type"]
            fields.append({"field": field, "type": type})
    except Exception as e:
        st.error(f"Error getting fields\n{e}")
        fields = []
    return fields


def get_elasticsearch_results(query, prefix: str = ""):
    es_client = session_state.get(prefix+"es_client")
    es_query  = session_state.get(prefix+"search_body", "*")

    if query is None or query == "" or query == "*":
        es_query = {
            "query": {
                "match_all": {}
            }
        }
    else:
        es_query = es_query.replace("{query}", query)
        try:
            es_query = json.loads(es_query)
        except Exception as e:
            print(e)
            print("Error parsing query")
            print(es_query)
            st.error(f"Error parsing query\n{e}")
            es_query = {
                "query": {
                    "match_all": {}
                }
            }
    es_query["size"] = session_state.get(prefix+"num_results", 10)
    index_pattern = session_state.get(prefix+"index_name", "*")
   # print("Querying Elasticsearch")
    #print(query)
    #print(es_query)
    #print(index_pattern)
    try:
        result = es_client.search(index=index_pattern, body=es_query)
    except Exception as e:
        print(e)
        print("Error querying Elasticsearch")
        print(es_query)
        st.error(f"Error querying Elasticsearch\n{e}")
        result = {}
    #print(result)
    try:
        result = result["hits"]["hits"]
    except Exception as e:
        print(e)
        print("Error parsing results")
        print("index_pattern:", index_pattern)
        print("es_query:", es_query)
        print("result",result)
        st.error(f"Error parsing results\n{e}")
        result = {}
    return result

def search(query, prefix: str = ""):
    apm_client = session_state.get("apm_client")
    if apm_client:
        apm_client.begin_transaction(transaction_type="script")
    results = get_elasticsearch_results(query, prefix=prefix)
    n_results = len(results)
    print(f"Found {n_results} results")
    session_state[prefix+"search_results"] = results
    if apm_client:
        apm_client.end_transaction(name="manual_search", result="success")
    return results