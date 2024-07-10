import streamlit as st
import elasticsearch
import dotenv
import json
from time import sleep
from code_editor import code_editor
from components.es_connection_config import es_connection_config_widget, connection_status_widget

st.set_page_config(
    page_title="Elasticsearch ReMapper",
    layout='wide',
    initial_sidebar_state='collapsed'
    )

session_state = st.session_state

# It's useful to be able to specify connection details in env variables for local use
dotenv.load_dotenv(override=True)


######################
# Utility and helper functions
######################


def init_session_state() -> None:
    """
    Initializes the session state with default values if not already initialized.
    """
    if "connected" not in session_state:
        session_state["connected"] = False
    if "slices" not in session_state:
        session_state["slices"] = 3
    if "batch_size" not in session_state:
        session_state["batch_size"] = 5000
    if "replace_index" not in session_state:
        session_state["replace_index"] = True


def get_current_mapping() -> dict:
    """
    Gets the current mapping for the selected index.

    Returns:
        dict: The current mapping for the selected index.
    """
    index_name = session_state.get("index_name")
    es_client = session_state.get("es_client")
    mapping = es_client.indices.get_mapping(index=index_name)
    return mapping[index_name]["mappings"]

def get_aliases(index_name: str) -> list:
    """
    Gets the aliases for the specified index.

    Args:
        index_name (str): The name of the index.
        
    Returns:
        list: A list of aliases for the specified index.
    """
    es_client = session_state.get("es_client")
    response = es_client.indices.get_alias(index=index_name)
    aliases = response[index_name]["aliases"].keys()
    return [alias for alias in aliases if alias != index_name]

def get_indexes() -> list:
    """
    Gets the indexes in the Elasticsearch cluster.

    Returns:
        list: A list of indexes in the Elasticsearch cluster.
    """
    es_client = session_state.get("es_client")
    index_pattern = session_state.get("index_pattern", "*")
    index_pattern=index_pattern+",-.*" # Exclude system indices
    try:
        indices = es_client.indices.get_alias(index=index_pattern)  
    except Exception as e:
        indices = []
    return indices

def get_pipelines(pipeline_name="*") -> list:
    """
    Gets the pipelines in the Elasticsearch cluster.

    Args:
        pipeline_name (str): The name of the pipeline.

    Returns:
        list: A list of pipelines in the Elasticsearch cluster.
    """
    es_client = session_state.get("es_client")
    try:
        pipelines = es_client.ingest.get_pipeline( id=pipeline_name+"*")
    except Exception as e:
        pipelines = []
    return pipelines


def populate_index_info() -> None:
    """
    Populates the index information based on the selected index.
    """
    global session_state

    index_name = session_state.get("index_name")
    old_index_name = session_state.get("old_index_name")
    # Check if the index has changed
    # guards against overwriting changes if nothing has changed
    if old_index_name != index_name:
        index_updated = True
        session_state["old_index_name"] = index_name
    else:
        index_updated = False

    if not index_name:
        return
    mapping = get_current_mapping()
    # Convert to json and pretty print format it
    mapping_pretty = json.dumps(mapping, indent=4)
    # Markdown needs two spaces before a new line to create a new line
    mapping_pretty = mapping_pretty.replace("\n", "  \n")
    st.session_state["current_mapping"] = mapping_pretty
    if index_updated:
        session_state["new_mapping"] = mapping_pretty
    if index_name:
        new_name = index_name+"_remapped"
    else:
        new_name = ""
    st.session_state["new_index_name"] = new_name

######################
# Main functions
######################
    

def get_reindex_progress(task_id: str) -> int:
    """
    Gets the progress of the reindex task.

    Args:
        task_id (str): The task ID of the reindex task.

    Returns:
        int: The progress of the reindex task.
    """
    es_client = session_state.get("es_client")
    response = es_client.tasks.get(task_id=task_id)
    total = response["task"]["status"]["total"]
    progress = response["task"]["status"]["created"] + response["task"]["status"]["updated"]
    completed = response["completed"]
    error = response["error"]if "error" in response else None
    return total, progress, completed, error

def remap_index(container: st.container,progress_bar : st.progress) -> None:
    """
    Remaps the index based on the specified configuration.

    Args:
        container (st.container): The Streamlit container to write the status updates to.
    """

    es_client = session_state.get("es_client")
    new_index_name = session_state.get("new_index_name")
    index_name = session_state.get("index_name")
    alias_name = session_state.get("alias_name")
    create_alias = session_state.get("create_alias")
    new_alias_name = session_state.get("new_alias_name")
    replace_index = session_state.get("replace_index", False)
    max_docs = session_state.get("max_docs")
    use_pipeline = session_state.get("use_pipeline")
    pipeline = session_state.get("pipeline")
    mapping = session_state.get("new_mapping")

    if (index_name == None or  new_index_name==None or mapping==None):
        return
    # Check if the index already exusts
    container.markdown(f"Remapping {index_name} to {new_index_name }")
    if es_client.indices.exists(index=new_index_name):
        if replace_index:
            container.markdown("* Deleting existing index")
            es_client.indices.delete(index=new_index_name)
        else:
            raise Exception("Index already exists and replace index is not checked")
    # Create the new index
    container.markdown("* Creating new index")

    mapping_json = json.loads(mapping)

    body = {
        "mappings": mapping_json
    }

    try:
        es_client.indices.create(index=new_index_name,body=body)  
    except Exception as e:
        with container:
            st.error(f"Error creating index: {e}")
        return
    
    # Set the refresh interval to -1
    container.markdown("* Setting refresh interval to -1")
    try:
        es_client.indices.put_settings(index=new_index_name, body={"refresh_interval": "-1"})
    except Exception as e:
        container.error(f"Error setting refresh interval: {e}")
        return
    
    # Set the number of replicas to 0
    container.markdown("* Setting number of replicas to 0")
    try:
        es_client.indices.put_settings(index=new_index_name, body={"number_of_replicas": 0})
    except Exception as e:
        container.error(f"Error setting number of replicas: {e}")
        return
    
    # Reindex the data, include the pipeline if it's defined
    container.markdown("* Reindexing data")
    batch_size = session_state.get("batch_size")
    slices = session_state.get("slices")
    body = {
        "source": {
            "index": index_name,
            "size": batch_size
        },
        "dest": {
            "index": new_index_name
        }
    }
    if use_pipeline and pipeline != None and pipeline != "":
        body["dest"]["pipeline"] = pipeline
    try:
        if not max_docs or max_docs == -1:
            response = es_client.reindex(body=body, wait_for_completion=False, slices=slices)  
        else:
            response = es_client.reindex(body=body, wait_for_completion=False,max_docs=max_docs,slices=slices)
        task_id = response["task"]
        container.markdown(f"* Reindex task ID: {task_id}")
        completed = False
        total = 0
        while not completed:
            total, progress, completed,error = get_reindex_progress(task_id)
            if total!= 0:        
                progress_bar.progress(progress/total, text=f"{progress}/{total} documents reindexed")
                session_state["progress"] = progress/total
            sleep(5)

    except Exception as e:
        container.error(f"Error reindexing data: {e}")
        return
    if error:
        container.error(f"Error reindexing data: {error}")
        return
    #Check if the reindex was successful
    if total == progress:
        # Set the refresh interval back to 1s
        container.markdown("* Setting refresh interval to 1s")
        try:
            es_client.indices.put_settings(index=new_index_name, body={"refresh_interval": "1s"})
        except Exception as e:
            container.error(f"Error setting refresh interval: {e}")
            return
        # Set the number of replicas back to 1
        container.markdown("* Setting number of replicas to 1")
        try:
            es_client.indices.put_settings(index=new_index_name, body={"number_of_replicas": 1})
        except Exception as e:
            container.error(f"Error setting number of replicas: {e}")
            return
        with container:
            with st.container():
                st.markdown(f"Reindex successful, {total} documents reindexed")
                
                # Update the alias
                if alias_name or (new_alias_name and create_alias):
                    st.markdown("* Updating Alias")
                    move_alias()
    else:
        container.error(f"Reindex failed {progress}/{total} documents reindexed")
        return

def move_alias():
    es_client = session_state.get("es_client")
    alias = session_state.get("alias_name")
    new_alias = session_state.get("new_alias_name")
    index = session_state.get("index_name")
    new_index = session_state.get("new_index_name")

    if not (alias or new_alias) or not index or not new_index:
        return
    if alias:
        body = {    
            "actions": [
                {"remove": {"index": index, "alias": alias}},
                {"add": {"index": new_index, "alias": alias}}
            ]
        }
        es_client.indices.update_aliases( body=body)
    if new_alias:
        es_client.indices.put_alias(index=new_index, name=new_alias)

def test_pipeline(container: st.container= None):
    es_client = session_state.get("es_client")
    pipeline = session_state.get("pipeline")
    index_name = session_state.get("index_name")

    print("Testing pipeline")
    print(pipeline)
    # Get random document from index
    try:
        response = es_client.search(index=index_name, size=1)
        doc = response["hits"]["hits"][0]
        print(doc)
    except Exception as e:
        st.error(f"Error getting document: {e}")
        return
    # Test the pipeline
    if not pipeline:
        return
    try:
        body = {
            "docs": [doc]
        }
        print(body)
        response = es_client.ingest.simulate(id=pipeline, body=body, pretty=True)
        doc = response["docs"]
        response = json.dumps(response["docs"][0]["doc"], indent=4)
        response = response.replace("\n", "  \n")
        if container:
            with container:
                with st.popover(label="Pipeline Output"):
                    st.code(response,language="json")
        else:
            with st.popover(label="Pipeline Output"):
                    st.code(response,language="json")
        
    except Exception as e:
        st.error(f"Error testing pipeline: {e}")

def main():
    ############################
    # App Heading
    ############################
    image_col, title_col2= st.columns([1,4])
    with image_col:
    # Show Elasticsearch cluster logo
        st.image("https://www.elastic.co/static-res/images/elastic-logo-200.png", width=100)
    with title_col2:
        st.title("Elasticsearch ReMapper")

    ############################
    # Configuration section
    ############################
    es_config_container = st.sidebar.container()
    es_connection_config_widget(es_config_container)
    init_session_state()
    
    ############################
    # Connection Status updates section
    ############################
    # Status container so we can show if we are connected to a cluster
    status= st.empty()
    # Display connection message
    connection_status_widget(status)

    # Expander for instructions
    with st.expander("Instructions"):
        with open("instructions.md", "r") as file:
            instructions = file.read()
        st.markdown(instructions)
    # Status updates expander
    status_updates = st.expander("Status Updates")

    with status_updates:
        # Add containers for each step of the process
        # This will allow us to update the status of each step
        # Each step will have a container split in to 2 columns, one for the title and one for the status

        # Connection status
        connection_container = st.container()
        with connection_container:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("Connection")
            with col2:
                connection_status=st.empty()
                with connection_status:
                    if session_state.get("connected"):
                        connection_status.success(":white_check_mark: Connected")
                    else:
                        connection_status.error(session_state.get("connection_error", "Not Connected"))
        
        # Index info
        index_info_container = st.container()
        with index_info_container:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("Select Index")
            with col2:
                index_info_status = st.empty()
                with index_info_status:
                    if session_state.get("index_name"):
                        index_info_status.success(":white_check_mark: Index selected: "+session_state.get("index_name"))

        # Mapping info
        mapping_info_container = st.container()
        with mapping_info_container:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("Retrieve Current Mapping")
            with col2:
                mapping_info_status = st.empty()
                with mapping_info_status:
                    if session_state.get("current_mapping"):
                        mapping_info_status.success(":white_check_mark: Mapping loaded")


    ############################
    # Progress section
    ############################
    progress_container =  st.container()
    with progress_container:
        progress_text = "Reindex Progress"
        progress_bar = st.progress(session_state.get("pregress",0), text=progress_text )


    ############################
    # Main section
    ############################
    index_settings_container = st.container()

    if session_state.get("connected", True):
        with index_settings_container:
            old, new = st.columns(2)

            with old:
                st.title("Existing Index")
                col1 , col2 = st.columns(2)
                with col1:
                    index_pattern=st.text_input("Search Index Pattern", key="index_pattern", value=session_state.get("index_pattern", "*"))
                
                with col2:
                    st.selectbox("Selecr Index Name", options=get_indexes(), key="index_name")
                st.button("Select Index", on_click=populate_index_info)
                st.write("Aliases")
                col1, col2 = st.columns(2)
                with col1:
                    st.selectbox("Select existing Alias to Move", options=get_aliases(session_state.get("index_name", "")), key="alias_name")
                #with col2:
                    #st.checkbox("Create New Alias", key="create_alias")
                if session_state.get("create_alias"):
                    st.text_input("New Alias", key="new_alias_name")
                st.write("Current Mapping")
                old_mapping = st.code(session_state.get("current_mapping", ""), language="json")
            
            with new:
                st.title("New Index")

                st.text_input("New Index Name", key="new_index_name")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.checkbox("Replace index if it exists", key="replace_index")
                with col3:
                    st.checkbox("Use Pipeline", key="use_pipeline")
                if session_state.get("use_pipeline"):
                    pipeline_select = st.container()
                    col1, col2 = pipeline_select.columns(2)
                    with col1:
                        def populate_pipelines():
                            session_state["pipelines"] = get_pipelines(session_state.get("pipeline_name", "*"))

                        st.text_input("Pipeline Pattern", key="pipeline_name", on_change=populate_pipelines())
                    with col2:
                        st.selectbox("Pipeline Name", options=session_state["pipelines"], key="pipeline")
                    test_pipeline_container = st.container()
                    with test_pipeline_container:
                        button, output = st.columns(2)
                        with button:
                            st.button("Test Pipeline", on_click=test_pipeline, args=([output]))  

                advanced_reindex=st.checkbox("Advanced Reindex Options", key="advanced_reindex_options")
                if advanced_reindex:
                    slices_col, batch_col, max_docs_col = st.columns(3)
                    with slices_col:
                        st.number_input("Slices", key="slices", value= session_state.get("slices", 3))  
                    with batch_col:
                        st.number_input("Batch Size", key="batch_size", value= session_state.get("batch_size", 1000))
                    with max_docs_col:
                        st.number_input("Max Docs", key="max_docs", value= session_state.get("max_docs", -1))
                st.button("Remap", on_click=remap_index,args=([status_updates, progress_bar]), key="remap_button")
            
                def confirm_new_mapping():
                    session_state["_new_mapping"] = session_state.get("new_mapping") != session_state.get("_new_mapping")
                    st.toast("New Mapping Saved, Click Remap To Apply")
                    return
                
                buttons=[
 {
   "name": "Copy",
   "feather": "Copy",
   "hasText": True,
   "alwaysOn": True,
   "commands": ["copyAll"],
   "style": {"top": "0.46rem", "right": "0.4rem"}
 },
 {
   "name": "Save",
   "feather": "Save",
   "hasText": True,
    "alwaysOn": True,
   "commands": ["save-state", ["response","saved"]],
   "response": "saved",
   "style": {"top": "0.4rem", "left": "4rem"}
 }]
                
                response_dict = code_editor(session_state.get("new_mapping"),lang="json",allow_reset=True,key="mapping_editor",buttons=buttons)
                if response_dict["text"] and response_dict["text"] != "":
                    session_state["new_mapping"] = response_dict["text"]
                    print(session_state["new_mapping"])
                #response_dict = st.text_area(label="New Mapping",value=session_state.get("_new_mapping"),key="new_mapping",height=500,on_change=confirm_new_mapping) 








if __name__ == "__main__":
    main()