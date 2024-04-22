import openai
import streamlit as st

# Define Streamlit app layout
st.set_page_config(page_title="OpenAI ChatGPT Demo")

# Add a section for entering the API key manually
api_key = st.sidebar.text_input("Enter your OpenAI API key:")

# Check if the API key is provided
if api_key:
    # Set the OpenAI API key
    openai.api_key = api_key

    # Add a section for entering the code
    st.title("AI Code Reviewer")
    #st.sidebar.header("Settings")

    code = st.text_area("Enter your code:", height=300, help="Enter your code here...")

    # Add a button to generate the response
    if st.button("Generate"):
        # Call the OpenAI API to generate a response
        with st.spinner("Generating response..."):
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=code,
                max_tokens=100,
                temperature=0.7,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=["\n"]
            )

        # Display the generated response
        st.header("Generated Response")
        st.write(response.choices[0].text.strip())

else:
    st.sidebar.warning("Please enter your OpenAI API key.")
