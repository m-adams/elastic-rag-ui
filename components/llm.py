import streamlit as st
import os
from openai import AzureOpenAI
from openai import OpenAI
import json
import llm_functions as llmfs
import elasticapm
from components.speech import speech_widget # Required to refresh for testing

session_state = st.session_state

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def test_llm_connection():
    llm_client = session_state.get("llm_client")
    if not llm_client:
        return False
    if session_state.get("llm_type") == "azure":
        print("Testing Azure LLM Connection")
        try:
            messages = [
                {"role": "system", "content": "you are a friendly chatbot"},
                {"role": "user", "content": "Just checking the connection"}
                ]
            response = llm_client.chat.completions.create(model=session_state.get("azure_openai_deployment_name"),messages=messages)
            #print(response.choices[0].message.content) 
            session_state["llm_connected"] = True
            return True
        except Exception as e:
            print(e)
            session_state["llm_connected"] = False
            return False

def connect_llm():
    llm_type = session_state.get("llm_type")
    if llm_type == "azure":
        azure_openai_key = session_state.get("azure_openai_key")
        azure_openai_deployment_name = session_state.get("azure_openai_deployment_name")
        azure_openai_endpoint = session_state.get("azure_openai_endpoint")
        llm_client = AzureOpenAI(
            api_key=azure_openai_key,  
            api_version="2023-10-01-preview",
            azure_endpoint = azure_openai_endpoint
        )
        session_state["llm_client"] = llm_client
        # Check if the client is connected
        if "llm_connected" not in session_state:
            # First time connecting
            test_llm_connection()
        
    elif llm_type == "openai":
        openai_key = session_state.get("openai_key")
        return openai_key
    elif llm_type == "bedrock":
        return None


def llm_config_widget(container: st.container):
    # Initialise the LLM connection configuration
    llm_type_default = os.getenv("LLM_TYPE")
    azure_openai_key_default = os.getenv("AZURE_OPENAI_KEY")
    azure_openai_deployment_name_default = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if "llm_type" not in session_state:
        session_state["llm_type"] = llm_type_default
    azure_openai_endpoint_default = os.getenv("AZURE_OPENAI_ENDPOINT")
    llm_typres = ["","azure","openai","bedrock"]

    # LLM Configuration
    with container:

        system_prompt = st.text_area("System Prompt", key="system_prompt", value=session_state.get("system_prompt", "you are a friendly chatbot"))
        corpus_description = st.text_area("Corpus Description", key="corpus_description", value=session_state.get("corpus_description", "A collection of corporate data"))
        llm_type = st.selection = st.selectbox(label="Select LLM Type",options=llm_typres,key="llm_type")


        if llm_type == "azure":
            st.text_input("Azure API Key", key="azure_openai_key", value=session_state.get("azure_openai_key",azure_openai_key_default))
            st.text_input("Azure Deployment Name", key="azure_openai_deployment_name", value=session_state.get("azure_openai_deployment_name",azure_openai_deployment_name_default))
            st.text_input("Azure Endpoint", key="azure_openai_endpoint", value=session_state.get("azure_openai_endpoint",azure_openai_endpoint_default))
            connect_llm()

        elif llm_type == "openai":
            st.write("OpenAI LLM Configuration")
            st.text_input("OpenAI API Key")
        elif llm_type == "bedrock":
            st.write("Bedrock LLM Configuration")
            st.write("Coming Soon")
        
        st.button("Test Connection", on_click=test_llm_connection, key="test_llm_connection_button")
        
        connection_status_container = st.empty()
        with connection_status_container:
            if "llm_connected" in session_state:
                if session_state["llm_connected"]:
                    st.success("Connected to LLM")
                else:
                    st.error("Failed to connect to LLM")
            else:
                st.warning("Not connected to LLM")
    return


@elasticapm.capture_span( "llm_chat")
def llm_chat(container : st.container):

    llm_client = session_state.get("llm_client")

    user_name = session_state.get("user_name", "alice")

    system_prompt = session_state.get("system_prompt")  

    messages = [{"role": "system", "content": session_state.get("system_prompt")}]
    last_message = st.session_state.messages[-1]["content"]
    for message in st.session_state.messages:
        messages.append({"role": message["role"], "content": message["content"]})

    llm_funct= session_state.get("llm_functions")

    function_definitions = []
    function_functions = {}

    

    for function in llm_funct:
        function_definitions.append(function["definition"])
        function_name = function["definition"]["name"]
        #print("Function Name")
        #print(function_name)
        funct = getattr(getattr(llmfs,function_name),function_name)
        #print(funct)
        function_functions[function["definition"]["name"]] = funct

    user_reply = False
    while user_reply == False:
        with st.spinner('ok, just a sec ...'):
            response = llm_client.chat.completions.create(
                            model=st.session_state.get("azure_openai_deployment_name"),
                            messages=messages,
                            stream=False,
                            functions= function_definitions
                        )
        choice = response.choices[0]
        if choice.finish_reason == "function_call":
            print("LLM Function Call")
            function_call = choice.message.function_call
            function_name = function_call.name
            function_args = function_call.arguments
            if isinstance(function_args, str):
                function_args = json.loads(function_args)
            print(function_name)
            print(function_args)
            function = function_functions[function_name]

            with container:
                user_update = st.write(f"To help answer your question I'm calling the function {function_name} with the following arguments: {function_args}")


            response = function(**function_args)
            #print("Response:",response)
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": json.dumps(function_args),
                    },
                }
            )
            messages.append(
                {
                    "role": "function", 
                    "name": function_name, 
                    "content": f'{{"result": {str(response)} }}'}
            )
        else:
            user_reply = True
            response = choice.message.content
            with container:
                st.write(response)

    elasticapm.label(es_query=last_message)
    audit_message = f'User {user_name} asked {last_message} and received {response}'
    audit_context = {'user.full_name': user_name}
    audit_context['reply'] = response
    audit_context['query'] = last_message
    audit_context['doc_references'] = []
    results = session_state.get("search_results")
    if results is not None:
        for result in results:
            audit_context['doc_references'].append(result["_source"]["title"])
    logger = session_state.get("logger_client")
    logger.info(audit_message,extra=audit_context)
            
    return response

def reset_chat():
    st.session_state.messages = []

def submit_audio(container : st.container):
    question = session_state.get("STT_output")
    #session_state["chat_input"] = question
    submit_chat(container, prompt=question)
    return

def submit_chat(chat_container : st.container, prompt : str = None):
    if prompt is None:
        prompt = session_state.get("chat_input")
    apm_client = session_state.get("apm_client")
    if  apm_client:
        apm_client.begin_transaction(transaction_type="script")
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_container:
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        response = llm_chat(st.chat_message("assistant"))

        if response:
            # Add LLM response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    if apm_client:
        apm_client.end_transaction(name="llm_chat", result="success")
    return

def llm_chat_widget(container : st.container):

    llm_client = session_state.get("llm_client")
    # Chat Widget
    with container:
        col_name, col_reset = st.columns(2)
        with col_name:
            st.text_input("What is your name?", key="user_name", value=session_state.get("user_name", "alice"))
        with col_reset:    
            st.button("Clear Chat", on_click=reset_chat)
        # Display chat messages from history on app rerun
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        prompt_container = st.container()
        with prompt_container:
            # Accept user input
            st.chat_input("How can I help?",key="chat_input",on_submit=submit_chat, args=[chat_container])
            st.write("Speak the question")
            
            question = speech_widget(st.container(),submit_audio, args=[chat_container])

    return