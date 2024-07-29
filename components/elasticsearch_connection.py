# es_connection_config.py

import streamlit as st
import os
import elasticsearch

####################################################################################################
# Elasticsearch Connection Configuration
####################################################################################################

# Sreamlit component to allow a user to configure the Elasticsearch connection
session_state = st.session_state


def initialise_llm():
    # Initialise the LLM connection configuration
    llm_type_default = os.getenv("LLM_TYPE")
    llm_api_key_default = os.getenv("LLM_API_KEY")
    llm_endpoint_default = os.getenv("LLM_ENDPOINT")

    # Check if session state has been initialized
    if "llm_type" not in session_state:
        session_state["llm_type"] = llm_type_default
    if "llm_api_key" not in session_state:
        session_state["llm_api_key"] = llm_api_key_default
    if "llm_endpoint" not in session_state:
        session_state["llm_endpoint"] = llm_endpoint_default

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
        api_key_default = os.getenv("ELASTICSEARCH_API_KEY")

        # Check if session state has been initialized
        if "cloud_id" not in session_state:
            session_state["cloud_id"] = cloud_id_default
        if "elasticsearch_url" not in session_state:
            session_state["elasticsearch_url"] = elasticsearch_url_default
        if "api_key" not in session_state:
            session_state["api_key"] = api_key_default

def get_es_client(force_update: bool = False, prefix : str ="") -> elasticsearch.Elasticsearch:
    """
    Returns an Elasticsearch client instance.

    If an Elasticsearch client instance already exists and is reachable, it will be returned.
    Otherwise, a new Elasticsearch client instance will be created based on the session state.

    Returns:
        elasticsearch.Elasticsearch: An Elasticsearch client instance.
    """
    es_client = session_state.get(prefix+"es_client")
    if es_client and es_client.ping() and not force_update:
        return es_client
    cloud_id = session_state.get(prefix+"cloud_id")
    elasticsearch_url = session_state.get(prefix+"elasticsearch_url")
    api_key = session_state.get(prefix+"api_key")
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

def check_elasticsearch_connection(prefix : str = "") -> tuple[bool, elasticsearch.Elasticsearch]:
    """
    Checks the connection to the Elasticsearch cluster.

    """
    try:
        es_client = get_es_client(force_update=True, prefix=prefix)
        if es_client is None:
            return False, None
        connected=es_client.ping()
    except Exception as e:
        return False, None
    if connected:
        session_state[prefix+"es_client"] = es_client
        session_state[prefix+"connected"] = True
    else:
        session_state[prefix+"connected"] = False
        session_state[prefix+"es_client"] = None


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

def initialise_monitoring(force : bool = False):

    # Initialise the Monitoring connection configuration
    monitoring_cloud_id_default = os.getenv("MONITORING_CLOUD_ID")
    monitoring_elasticsearch_url_default = os.getenv("MONITORING_ELASTICSEARCH_URL")
    monitoring_api_key_default = os.getenv("MONITORING_API_KEY")
    logs_index_name_default = os.getenv("LOGS_INDEX_NAME")
    apm_service_name_default = os.getenv("ELASTIC_APM_SERVICE_NAME")
    apm_environment_default = os.getenv("ELASTIC_APM_ENVIRONMENT")
    apm_secret_token_default = os.getenv("ELASTIC_APM_SECRET_TOKEN")
    apm_url_default = os.getenv("ELASTIC_APM_URL")
    event_dataset_logs_default = os.getenv("EVENT_DATASET_LOGS")

    # Check if session state has been initialized
    if "monitoring_cloud_id" not in session_state or force:
        session_state["monitoring_cloud_id"] = monitoring_cloud_id_default
    if "monitoring_elasticsearch_url" not in session_state or force:
        session_state["monitoring_elasticsearch_url"] = monitoring_elasticsearch_url_default
    if "monitoring_api_key" not in session_state or force:
        session_state["monitoring_api_key"] = monitoring_api_key_default
    if "logs_index_name" not in session_state or force:
        session_state["logs_index_name"] = logs_index_name_default
    if "apm_service_name" not in session_state or force:
        session_state["apm_service_name"] = apm_service_name_default
    if "apm_environment" not in session_state or force:
        session_state["apm_environment"] = apm_environment_default
    if "apm_secret_token" not in session_state or force:
        session_state["apm_secret_token"] = apm_secret_token_default
    if "apm_url" not in session_state or force:
        session_state["apm_url"] = apm_url_default
    if "event_dataset_logs" not in session_state or force:
        session_state["event_dataset_logs"] = event_dataset_logs_default
    
    es_logging_client = check_elasticsearch_connection(prefix="monitoring_")


    

def monitoring_connection_config_widget(container: st.container):
    # Monitoring Cluster Connection Configuration

    # Initialise the Elasticsearch connection configuration
    initialise_monitoring()
    
    #check_elasticsearch_connection()
    
    def save_settings(conatiner : st.container):
        #check_elasticsearch_connection() 
        with container:
            st.write("Updating connection settings")


    with container:
        st.title("Monitoring Cluster Details")
    
        st.text_input("Cloud ID", key="monitoring_cloud_id")
        st.text_input("Elasticsearch URL", key="monitoring_elasticsearch_url")
        st.text_input("Elasticsearch API Key", key="monitoring_api_key")
        st.text_input("Logs Index Name", key="logs_index_name")
        st.text_input("APM Service Name", key="apm_service_name")
        st.text_input("APM Environment", key="apm_environment")
        st.text_input("APM Secret Token" , key="apm_secret_token")
        st.text_input("APM URL", key="apm_url")
        st.text_input("Logs Dataset Name", key="event_dataset_logs")
    
        save_col, reset_col = st.columns(2)
        with save_col:
            st.button("Save", on_click=initialise_monitoring, key="save_monitoring_settings_button")       
        with reset_col:
            st.button("Reset", on_click=initialise_monitoring, args=[True], key="reset_monitoring_settings_button")
        if session_state["monitoring_connected"]:
            st.success("Connected to Monitoring Cluster")
        else:
            st.error("Not connected to Monitoring Cluster")
            try:
                es_client = get_es_client(prefix="monitoring_")
                es_client.info()
            except Exception as e:
                st.error(f"Not connected  \nError: {e}")
    