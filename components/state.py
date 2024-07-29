import os
import pickle
import streamlit as st
import dotenv



# Define the directory where the states will be saved
states_directory = "./saved-states"
session_state = st.session_state
stste={}
# Function to save the current state
def save_state(state_name: str, container: st.container):
    """
    Saves the session state to a file.

    Parameters:
    - state_name (str): The name of the state to be saved.
    - container (st.container): The Streamlit container to display the success message.

    Returns:
    None
    """

    global states_directory, state
    print(f"Saving session state as: {state_name}")
    if state_name:
        session_state["state_name"] = state_name
        state_name = state_name.strip()
        state_name = state_name.replace(" ", "_")
        state_file = os.path.join(states_directory, f"{state_name}.pkl")
        with open(state_file, "wb") as f:
            print(f"Saving session state:\n{session_state}\nTo filename: {state_file}")
            state = {}
            for key in session_state.keys():
                if key.endswith("_client") or key.endswith("_button"):
                    # Skip these keys as they are not serializable or cause errors
                    continue
                else:
                    state[key] = session_state[key]
                    #print(f"Key: {key}, Value: {session_state[key]}")
            pickle.dump(state, f)

        with container:
            st.success("State saved successfully!")

def get_states():
    state_files = os.listdir(states_directory)
    # Get filenames without the extension
    state_names = [file.split(".")[0] for file in state_files]
    return state_names

# Function to load a state
def load_state(state_name,container :st.container = None):
    print(f"Loading state:{state_name}")
    if state_name:
        state_file = os.path.join(states_directory, f"{state_name}.pkl")
        with open(state_file, "rb") as f:
            state = pickle.load(f)
        for key in state.keys():
            session_state[key] = state[key]
        if container:
            with container:
                st.success("State loaded successfully!")
    return

# Function to delete a state
def delete_state(state_name : str, container : st.container):
    if state_name:
        state_file = os.path.join(states_directory, f"{state_name}.pkl")
        os.remove(state_file)
        with container:
            st.success("State deleted successfully!")


def delete_all_states(container : st.container):
    state_files = os.listdir(states_directory)
    for file in state_files:
        if file.endswith(".pkl"):
            state_file = os.path.join(states_directory, file)
            os.remove(state_file)
    with container:
        st.success("All states deleted successfully!")

# Main function
def saved_state_widget(container: st.container):
    """
    Renders a widget for managing saved states.

    Parameters:
    - container (st.container): Streamlit container to render the widget in.

    Returns:
    None
    """

    with container:
        # Check that the environment is a local one via an environment variable
        if os.getenv("IS_LOCAL") != "true":
            st.warning("This feature is only available in a local environment.")
            return

        st.title("State Management")
        st.markdown("Save current state")
        name_col, save_col = st.columns([0.7, 0.3])

        with name_col:
            name = st.text_input("Name", key="state-name-box")

        with save_col:
            st.write(" ") # Fix the vertical alignment
            save_button = st.button("Save",key="save_state_button", on_click=save_state, args=[name,container])

        st.markdown("Saved States")
        existing_state = st.selectbox(options=get_states(), label="Saved States")

        load_col, delete_col, delete_all_col = st.columns(3)

        with load_col:
            load_button = st.button("Load", on_click=load_state, args=[existing_state,container])

        with delete_col:
            delete_button = st.button("Delete", on_click=delete_state, args=[existing_state,container])

        with delete_all_col:
            delete_button = st.button("Clear All", on_click=delete_all_states, args=[container])

    #print(session_state)

if __name__ == "__main__":
    dotenv.load_dotenv(override=True)
    st.text_input(value="",key="test", label="Test state here:")
    saved_state_widget(st.container())