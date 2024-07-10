# es_connection_config.py

import streamlit as st
import os
import elasticsearch

####################################################################################################
# Elasticsearch Connection Configuration
####################################################################################################

# Sreamlit component to allow a user to configure the Elasticsearch connection
session_state = st.session_state

def reset_es_defaults():

    # Reset the Elasticsearch connection configuration to the default values
    cloud_id_default = os.getenv("CLOUD_ID")
    elasticsearch_url_default = os.getenv("ELASTICSEARCH_URL")
    api_key_default = os.getenv("API_KEY")

    # Reset the Elasticsearch connection configuration to the default values
    session_state["cloud_id"] = cloud_id_default
    session_state["elasticsearch_url"] = elasticsearch_url_default
    session_state["api_key"] = api_key_default

def initialise_es():
    
        # Initialise the Elasticsearch connection configuration
        cloud_id_default = os.getenv("CLOUD_ID")
        elasticsearch_url_default = os.getenv("ELASTICSEARCH_URL")
        api_key_default = os.getenv("API_KEY")

        # Check if session state has been initialized
        if "cloud_id" not in session_state:
            session_state["cloud_id"] = cloud_id_default
        if "elasticsearch_url" not in session_state:
            session_state["elasticsearch_url"] = elasticsearch_url_default
        if "api_key" not in session_state:
            session_state["api_key"] = api_key_default

def get_es_client(force_update: bool = False) -> elasticsearch.Elasticsearch:
    """
    Returns an Elasticsearch client instance.

    If an Elasticsearch client instance already exists and is reachable, it will be returned.
    Otherwise, a new Elasticsearch client instance will be created based on the session state.

    Returns:
        elasticsearch.Elasticsearch: An Elasticsearch client instance.
    """
    es_client = session_state.get("es_client")
    if es_client and es_client.ping() and not force_update:
        return es_client
    cloud_id = session_state.get("cloud_id")
    elasticsearch_url = session_state.get("elasticsearch_url")
    api_key = session_state.get("api_key")
    if cloud_id:
        es_client = elasticsearch.Elasticsearch(
            cloud_id=cloud_id,
            api_key=api_key
        )
    else:
        es_client = elasticsearch.Elasticsearch(
            hosts=[elasticsearch_url],
            api_key=api_key
        )
    return es_client

def check_elasticsearch_connection() -> tuple[bool, elasticsearch.Elasticsearch]:
    """
    Checks the connection to the Elasticsearch cluster.

    """
    try:
        es_client = get_es_client(force_update=True)
        if es_client is None:
            return False, None
        connected=es_client.ping()
    except Exception as e:
        return False, None
    if connected:
        session_state["es_client"] = es_client
        session_state["connected"] = True
    else:
        session_state["connected"] = False
        session_state["es_client"] = None


def es_connection_config_widget(container: st.container):
    # Elasticsearch Connection Configuration

    # Initialise the Elasticsearch connection configuration
    initialise_es()
    
    check_elasticsearch_connection()
    
    def save_settings(conatiner : st.container):
        check_elasticsearch_connection() 
        with container:
            st.write("Updating connection settings")


    with container:
        st.title("Connection Details")
    
        st.text_input("Cloud ID", key="cloud_id")
        st.text_input("Elasticsearch URL", key="elasticsearch_url")
        st.text_input("Elasticsearch API Key", key="api_key")
    
        save_col, reset_col = st.columns(2)
        with save_col:
            st.button("Save", on_click=save_settings, args=([container]))       
        with reset_col:
            st.button("Reset", on_click=reset_es_defaults)


    
def connection_status_widget(status : st.empty):
    # Connection Status Widget
    status.empty()
    connected = session_state.get("connected", False)
    if connected:
        status.success("Connected to Elastic")
    else:
        status.empty()
        status.error("Not connected to Elastic")
        #Try to call elasticsearch and capture the exception and output the reason to status_updates
        try:
            es_client = get_es_client()
            es_client.info()
        except Exception as e:
            status.error(f"Not connected  \nError: {e}") 


    