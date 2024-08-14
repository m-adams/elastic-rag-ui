import streamlit as st
import openai
import os
import base64
import os
import azure.cognitiveservices.speech as speechsdk


from streamlit_mic_recorder import speech_to_text

session_state = st.session_state

if "messages" not in session_state:
    session_state.messages = []

def speech_widget(container : st.container, callback : callable, args: list = []):
    with container:
        but_col, text_col = st.columns([1, 4])
        with but_col:
            text = speech_to_text(language='en', use_container_width=False, just_once=True, key='STT')
        with text_col:
            if text:
                st.write("You said: "+text)
        args.append(text)
        st.button("Send", on_click=callback, args=args)
    if text:
        return text



def initialise_t2s(force=False):
    openai_api_key_default = os.getenv("OPENAI_API_KEY")
    azure_speech_key_default = os.getenv("AZURE_SPEECH_KEY")
    azure_speech_region_default = os.getenv("AZURE_SPEECH_REGION")
    if "t2s_opmai_api_key" not in session_state or force:
        session_state.t2s_opmai_api_key = openai_api_key_default
    if "t2s_type" not in session_state or force:
        session_state.t2s_type = "OpenAI"
    if "t2s_turn_on" not in session_state or force:
        session_state.t2s_turn_on = False
    if "azure_speech_key" not in session_state or force:
        session_state.azure_speech_key = azure_speech_key_default
    if "azure_speech_region" not in session_state or force:
        session_state.azure_speech_region = azure_speech_region_default

def test_t2s_config(container : st.container):
    test_message = "Hi, how can I help?"
    generate_and_play_speech(test_message, container)

def create_t2s_client():
    type = session_state.get("t2s_type")
    if type == "Azure":
        speech_key = session_state.get("azure_speech_key")
        speech_region = session_state.get("azure_speech_region")
        speech_model = session_state.get("azure_speech_model")
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        #audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        speech_config.speech_synthesis_voice_name=speech_model
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        session_state.t2s_client = speech_synthesizer
    elif type == "OpenAI":
        client = openai.Client(api_key=session_state.get("t2s_opmai_api_key"))
        session_state.t2s_client = client
        return client

def azure_t2s(text):
    speech_synthesizer = session_state.get("t2s_client")
    speech_synthesis_result = speech_synthesizer.speak_text(text)
    data = speech_synthesis_result.audio_data
    return data


def generate_and_play_speech(text, container : st.container):
    data = generate_speech(text)
    play_audio(data, container)



def play_audio(data, container : st.container):
    try:
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        with container:
            st.markdown(
                md,
                unsafe_allow_html=True,
            )
    except Exception as e:
        with container:
            st.error("Error playing audio")
            st.error(e)

def generate_speech(text):
    type = session_state.get("t2s_type")
    client = session_state.get("t2s_client")
    if client is None:
        st.error("Please configure the settings first")
        return
    if type == "Azure":
        bytes = azure_t2s(text)
    elif type == "OpenAI":
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        bytes= response.read()
    return bytes

def text_to_speech_config_widget(container : st.container):
    initialise_t2s()
    with container:
        turn_on = st.checkbox("Enable Text To Speech",key="t2s_turn_on", value=session_state.get("t2s_turn_on", False))
        if turn_on:
            type = st.selectbox("Select the service", ["Azure", "OpenAI"], key="t2s_type")
            if type == "Azure":

                azure_speech_key = st.text_input("Azure Speech Key", key="azure_speech_key", value=session_state.get("azure_speech_key", ""))
                azure_speech_region = st.text_input("Azure Speech Region", key="azure_speech_region", value=session_state.get("azure_speech_region", ""))
                azure_speech_model = st.selectbox("Azure Speech Model", ["en-US-AriaNeural", "en-US-AvaNeural"], key="azure_speech_model")
            elif type == "OpenAI":
                st.write("OpenAI Configuration")
                opmai_api_key = st.text_input("OpenAI API Key", key="t2s_opmai_api_key", value=session_state.get("t2s_opmai_api_key", ""))
            
            create_t2s_client()
            buttons_container = st.container()
            test_output_container = st.container()
            with buttons_container:
                test_col, reset_col = st.columns([1, 1])
            with test_col:
                st.button("Test", on_click=test_t2s_config, args=[test_output_container], key="t2s_test_button")
            with reset_col:
                st.button("Reset", on_click=initialise_t2s, args=[True], key="t2s_reset_button")
            
