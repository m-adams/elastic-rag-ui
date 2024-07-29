
import dotenv
from components.elasticsearch_connection import es_connection_config_widget, connection_status_widget, monitoring_connection_config_widget
from components.state import saved_state_widget, load_state
from components.search_results import search_results_widget
from components.elasticsearch import index_selector_widget, search
from components.llm import llm_config_widget, llm_chat_widget
from components.llm_functions import function_select_widget
import streamlit as st
from code_editor import code_editor
import json
from tools import loggeres
import ecs_logging
import logging
import sys
import elasticapm

session_state = st.session_state

st.set_page_config(
    page_title=session_state.get("app_name", "Elastic AI Search"),
    layout='wide',
    initial_sidebar_state='collapsed'
    )

logger = None

def set_std_logger():
    global logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(logging.StreamHandler())
    session_state["logger_client"] = logger

def setup_logging():
    # setup logging 
    global logger
    eslogger = session_state.get("monitoring_es_client")
    print("Setting up logging")
    print(eslogger)
    print("normal es client")
    print(session_state.get("es_client"))
    if eslogger is None:
        print("No monitoring client, setting up standard logger")
        set_std_logger()
        return
    logs_index_name = session_state.get("logs_index_name")
    event_dataset_logs = session_state.get("event_dataset_logs", "ldemo-logs")
    handler = loggeres.ElasticHandler(logging.INFO,eslogger,logs_index_name)
    handler.setFormatter(ecs_logging.StdlibFormatter())
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.addFilter(loggeres.SystemLogFilter(event_dataset_logs)) # We always need to add this filter to add the event.dataset field
    session_state["logger_client"] = logger


def set_apm():
    print("Setting up APM")
    if session_state.get("apm_client"):
        print("APM already set")
        return session_state["apm_client"]
    if elasticapm.get_client():
        print("APM already set")
        session_state["apm_client"] = elasticapm.get_client()
        return session_state["apm_client"]
    service_name = session_state.get("apm_service_name", "elastic-ai-search")
    environment = session_state.get("apm_environment", "development")
    secret_token = session_state.get("apm_secret_token")
    server_url = session_state.get("apm_url")
    try:
        print("Setting up APM with new client")
        print(session_state.get("apm_client"))
        apm = elasticapm.Client(service_name=service_name, environment=environment, secret_token=secret_token, server_url=server_url,)
        print("APM set up")
        print(apm)

        if apm:
            elasticapm.instrument()
            session_state["apm_client"] = apm
    except Exception as e:
        #print("Error setting up APM", e)
        apm = None

    return apm

# Load environment variables
dotenv.load_dotenv()

# Load default query body
with open("default_query_body.json") as f:
    default_query_body = f.read().strip()

# Load default markdown template
with open("default_md_template.md") as f:
    default_md_template = f.read().strip()


def initialize_session_state():
    if "search_body" not in session_state:
        session_state["search_body"] = default_query_body
    if "index_pattern" not in session_state:
        session_state["index_pattern"] = "*"
    if "num_results" not in session_state:
        session_state["num_results"] = 5
        if "search_query" not in session_state:
            session_state["search_query"] = "*"
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []



def main():

    initialize_session_state()

    # This provides a shortcut to a saved state
    if "state" in st.query_params:
        state_name = st.query_params["state"]
        # Check if we need to load a state
        current_state = session_state.get("state_name")
        if current_state != state_name:
            load_state(state_name)


################## Header ##################
            
    img_col, title_col = st.columns([1, 4])
    with img_col:
        st.image(session_state.get("img_url","https://www.elastic.co/static-res/images/elastic-logo-200.png"), width=100) 
        
    with title_col:
        st.title(session_state.get("app_name", "Elastic AI Search"))


################## Sidebar ##################
    with st.sidebar:
        st.title("Settings")
        app_settings_container = st.expander(label="App Settings")
        with app_settings_container:
            st.title("App Settings")
            app_name = st.text_input("App Name", key="app_name", value=session_state.get("app_name", "Elastic AI Search"))
            img_url = st.text_input("Logo URL", key="img_url", value=session_state.get("img_url", "https://www.elastic.co/static-res/images/elastic-logo-200.png"))

        es_connection_container = st.expander(label="Elasticsearch Connection")
        es_connection_config_widget(es_connection_container)

        llm_config_container = st.expander(label="LLM Configuration")
        llm_config_widget(llm_config_container)

        llm_function_expander = st.expander(label="LLM Functions")
        llm_functions = function_select_widget(llm_function_expander)
        #print("llm_functions:",llm_functions)
        session_state["llm_functions"] = llm_functions

        monitoring_connection_expander = st.expander(label="Monitoring Cluster")
        monitoring_connection_config_widget(monitoring_connection_expander)
        set_apm()
        setup_logging()

        state_management_expander = st.expander(label="State")
        saved_state_widget(state_management_expander)



################## Main Content ##################
    mode_select = st.radio("Select Mode", ["View", "Edit"],horizontal=True)
    
    
################## Search Configuration ##################
    
    if mode_select == "Edit":
        connection_status_container= st.empty()
        connection_status_widget(connection_status_container)
        doc_format_expander = st.expander("Document Display Format")
        with doc_format_expander:
            doc_md_template = st.text_area("Document Display Template", value=session_state.get("doc_md_template",default_md_template), key="doc_md_template")
        with st.expander("Search Function"):
            index_pattern_col, num_results_col = st.columns([4,1])
            with index_pattern_col:
                index_selector_widget(st.container())
            with num_results_col:
                num_results = st.number_input("Number of Results", key="num_results", value=session_state.get("num_results", 10))
            st.write("Define your query. Tip: Try Playground in Kibana")
            search_body_editor = code_editor(
                session_state.get("search_body", default_query_body),
                lang="json",
                key="search_function",
                allow_reset=True
            )
            if search_body_editor["text"] != "":
                #print(search_body_editor["text"])
                session_state["search_body"] = search_body_editor["text"]

    
################## Manual Search ##################
    manual_search_container = None
    if mode_select == "View":
        search_col, chat_col = st.columns([2, 2])
        with search_col:
            manual_search_container = st.container()
    else:
        manual_search_container = st.expander("Manual Search")
    with manual_search_container:
        # Search box
        search_col, button_col = st.columns([3, 1])
        with search_col:
            search_query = st.text_input("Search", key="search_query_box",value=session_state.get("search_query", ""),on_change=search, args=[session_state.get("search_query_box", "*")])
        with button_col:
            search_button = st.button("Search", on_click=search, args=[session_state.get("search_query_box", "*")])
        if session_state.get("search_results") is not None:
            results = session_state.get("search_results")
            search_results_container = st.container()
            search_results_widget(search_results_container, docs=results, md_template=session_state.get("doc_md_template", default_md_template))

    ################## LLM Chat ##################
    if mode_select == "Edit":
        llm_chat_container = st.expander(label="LLM Chat")
    else:
        with chat_col:
            llm_chat_container = st.container()
            with llm_chat_container:
                st.write("Chat with your documents")
    llm_chat_widget(llm_chat_container)



if __name__ == "__main__":
    main()
