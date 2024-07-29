
import streamlit as st
import components.speech
from components.llm import llm_chat

import importlib
importlib.reload(components.speech)
from components.speech import speech_widget # Required to refresh for testing


session_state = st.session_state 

st.title("Talk to me")
st.markdown("Ask questions with your voice and get a spoken reposnse.")
st.markdown("Coming soon...")


def main():
    question = speech_widget(st.container())
    # question=None
    print(f"question is {question}")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        llm_chat(st.container())
    pass

main()