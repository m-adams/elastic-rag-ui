import streamlit as st
from components.elasticsearch import get_elasticsearch_results, get_fields
from components.state import load_state
import json
import pandas as pd
import dotenv
from components.state import force_refresh_of_state
import base64

# Load environment variables
dotenv.load_dotenv()

session_state = st.session_state 
force_refresh_of_state() # Streamlit starts cleaning up elements that aren't used


def search_logs():
    query= session_state["search_logs_query"]
    results = get_elasticsearch_results(query, prefix = "monitoring_")
    session_state.monitoring_search_results = results
    pass

def select_document():
    search_results = session_state.monitoring_search_results
    doc=session_state.monitoring_search_results_table
    row = doc["selection"]["rows"][0]
    selected_doc = search_results[row]
    #print(selected_doc)
    query = selected_doc["_source"]["query"]
    session_state["search_logs_query"] = query



def main():
    # This provides a shortcut to a saved state
    if "state" in st.query_params:
        state_name = st.query_params["state"]
        # Check if we need to load a state
        current_state = session_state.get("state_name")
        if current_state != state_name:
            load_state(state_name)

    query_body = """{
        "query": {
            "multi_match": {
                "query": "{query}",
                "fields": ["message"]
            }
        }
    }"""

    session_state["monitoring_search_body"]= query_body

    # This provides a shortcut to a saved state
    if "state" in st.query_params:
        state_name = st.query_params["state"]
        # Check if we need to load a state
        current_state = session_state.get("state_name")
        if current_state != state_name:
            load_state(state_name)

    st.title("Semantic Logging")
    st.markdown("Find semantically similar, previous Qs and As")

    cloud_id = session_state.get("monitoring_cloud_id")

    if cloud_id is not None:
        cloud_id_parts = cloud_id.split(":")
        name = cloud_id_parts[0]
        base64_content = cloud_id_parts[1]
        cloud_id_decoded = base64.b64decode(base64_content).decode("utf-8")
        cloud_id_decoded_parts = cloud_id_decoded.split("$")
        host_and_port= cloud_id_decoded_parts[0]
        es_uuid = cloud_id_decoded_parts[1]
        kb_uuid = cloud_id_decoded_parts[2]
        elasticsearch_url = f"https://{es_uuid}.{host_and_port}"
        kibana_url = f"https://{kb_uuid}.{host_and_port}/app/home#"
        st.markdown("To view all APM and Log data in Kibana, click the link below:")
        st.markdown(f"[Open Kibana]({kibana_url})")
    logs_index_name = session_state.get("logs_index_name")

    if "monitoring_index_name" not in session_state or session_state["monitoring_index_name"] is None:
        session_state["monitoring_index_name"]= logs_index_name
    else:
        logs_index_name = session_state["monitoring_index_name"]

    logging_es_client = session_state.get("monitoring_es_client", None)
    if logging_es_client is None:
        st.error("Please initialise the Elasticsearch client first.")

    query = st.text_input("Enter your query here", key="search_logs_query", on_change=search_logs)

    
    submit = st.button("Submit", key= "search_logs_button", on_click=search_logs)

    fields = get_fields(logs_index_name, prefix = "monitoring_")

    field_names = [field["field"] for field in fields]

    normal_defaults = ["@timestamp","user.name","query", "reply","doc_references"]

    # Check if normal defaults are present in field names
    present_defaults = [default for default in normal_defaults if default in field_names]

    # Create new defaults list with only the ones which are present
    new_defaults = present_defaults

    # Use new_defaults list for further processing

    selected_fields = st.multiselect("Select fields to display",options= field_names, default=new_defaults)

    monitoring_search_results = session_state.get("monitoring_search_results", None)

    if monitoring_search_results:
        table_data = []
        for hit in monitoring_search_results:
            formatted_hit = json.dumps(hit['_source'], indent=2)
            #print(formatted_hit)
            #print("----")
            #print("\n")
            row = []
            for field in selected_fields:
                if field in hit["_source"]:
                    row.append(hit["_source"][field])
                else:
                    row.append("N/A")
            table_data.append(row)
        df = pd.DataFrame(table_data, columns=selected_fields)
        global doc
        doc = st.dataframe(df, height=400,selection_mode="single-row", key="monitoring_search_results_table", on_select=select_document)




main()