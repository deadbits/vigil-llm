# github.com/deadbits/vigil-llm
import os
import json

import requests
import streamlit as st  # type: ignore

from streamlit_extras.badges import badge  # type: ignore
from streamlit_extras.stateful_button import button  # type: ignore


st.header("Vigil - LLM security scanner")
st.subheader("Web Playground", divider="rainbow")

# Initialize session state for storing history
if "history" not in st.session_state:
    st.session_state["history"] = []

with st.sidebar:
    st.header("Vigil - LLM security scanner", divider="rainbow")
    st.write(
        "[documentation](https://vigil.deadbits.ai) | [github](https://github.com/deadbits/vigil-llm)"
    )
    badge(type="github", name="deadbits/vigil-llm")
    st.divider()

page = st.sidebar.radio(
    "Select a page:", ["Prompt Analysis", "Upload YARA Rule", "History", "Settings"]
)

if page == "Prompt Analysis":
    # Text input for the user to enter the prompt
    prompt = st.text_area("Enter prompt:")

    if button("Submit", key="button1"):
        if prompt:
            response = requests.post(
                "http://localhost:5000/analyze/prompt",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"prompt": prompt}),
            )

            # Check if the response was successful
            if response.status_code == 200:
                data = response.json()

                # Add to history
                st.session_state["history"].append(
                    {"timestamp": data["timestamp"], "prompt": prompt, "response": data}
                )

                # Display the input prompt
                st.write("**Prompt:** ", data["prompt"])
                st.write("**Entropy:** ", data["prompt_entropy"])
                st.write("**UUID:** ", data["uuid"])

                # Display messages
                if data["messages"]:
                    for message in data["messages"]:
                        # the messages field holds scanners matches so raise them
                        # as a "warning" on the UI
                        st.warning(message, icon="⚠️")

                # Display errors
                if data["errors"]:
                    st.write("Errors:")
                    for error in data["errors"]:
                        st.error(error)

                # Display results
                for scanner, details in data["results"].items():
                    st.write(f"**{scanner}**")
                    for match in details["matches"]:
                        st.write(match)
            else:
                st.error("Failed to get a response from the server.")

elif page == "History":
    st.title("History")
    # Sort history by timestamp (newest first)
    sorted_history = sorted(
        st.session_state["history"], key=lambda x: x["timestamp"], reverse=True
    )

    for item in sorted_history:
        st.write("Timestamp:", item["timestamp"])
        st.write("Prompt:", item["prompt"])
        st.write("Response:", item["response"])
        st.write("-" * 50)

elif page == "Settings":
    st.title("Settings")

    response = requests.get("http://localhost:5000/settings")

    if response.status_code == 200:
        settings_data = response.json()

        st.json(settings_data)
    else:
        st.error("Failed to retrieve settings from the server.")

elif page == "Upload YARA Rule":
    st.title("Upload Custom YARA Rule")

    # YARA rule template
    template = """
    rule MyRule_custom: customTag
    {
        meta:
            category = "Prompt Injection"
            description = "Detects prompts that contain some custom strings or regex"
        strings:
            ...
        condition:
            ...
    }
    """

    rule_name = st.text_input("Rule Name", "MyRule_custom")
    rule_content = st.text_area("YARA Rule", value=template, height=300)

    if st.button("Save"):
        rule_filename = f"{rule_name}.yar"
        path = os.path.join("data", "yara", rule_filename)

        # Check if the directory exists, if not, create it
        if not os.path.exists(os.path.join("data", "yara")):
            os.makedirs(os.path.join("data", "yara"))

        # Save the YARA rule to the specified file
        with open(path, "w") as file:
            file.write(rule_content)

        st.success(f"Saved YARA rule to {path}")
