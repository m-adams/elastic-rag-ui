import streamlit as st
from streamlit_mic_recorder import mic_recorder, speech_to_text

session_state = st.session_state

if "messages" not in session_state:
    session_state.messages = []

def speech_widget(container : st.container, callback : callable, args: list = []):
    with container:
        text = speech_to_text(language='en', use_container_width=False, just_once=True, key='STT', callback=callback, args=args)
        if text:
            session_state['audio_question_text']=text
        st.write("You asked: "+session_state.get("audio_question_text",''))
    if text:
        return text


