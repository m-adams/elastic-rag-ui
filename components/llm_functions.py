import streamlit as st
import llm_functions
from pkgutil import iter_modules

session_state = st.session_state

def function_select_widget(container : st.container):
    """
    Renders a widget for selecting a function to run.

    Parameters:
    - container (st.container): Streamlit container to render the widget in.

    Returns:

    """

    modules = list(iter_modules(getattr(llm_functions,"__path__")))

    available_functions = []
    for submodule in iter_modules(getattr(llm_functions,"__path__")):
        if submodule.ispkg:
            pass
        else:
            mod= __import__(f"llm_functions.{submodule.name}",fromlist=["llm_functions"])
            definition = getattr(mod,"definition")
            func = getattr(mod,submodule.name)
            available_functions.append({"name":submodule.name,"definition":definition,"function":func})

    with container:
        for function in available_functions:
            definition_col, enable_col = st.columns([1,1])
            with definition_col:
                with st.popover(label=function["definition"]["name"]):
                    st.write(function["definition"])
            with enable_col:
                st.checkbox("Enable", key="llm_function_"+function["name"],value=True)

    for function in available_functions:
        if session_state.get("llm_function_"+function["name"])== False:
            available_functions.remove(function)
    return available_functions

if __name__ == "__main__":
    st.title("Function Selector")
    function_select_widget(st.container())