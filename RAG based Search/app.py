import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import Chroma
from IPython.display import Markdown as md
import streamlit as st

# Set up Streamlit app layout
st.set_page_config(
    page_title="Retrieval Augmented Generation Based Search engine",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Collect API Key
GOOGLE_API_KEY = st.text_input("Enter your Google API Key:")

# Customize Streamlit style
st.markdown(
    """
    <style>
    body {
        background-color: #f0f9ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display Q&A System
if GOOGLE_API_KEY:
    st.header("Retrieval Augmented Generation Based Search engine")

    # Setup API Key
    chat_model = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-1.5-pro-latest")

    embedding_model = GoogleGenerativeAIEmbeddings(google_api_key=GOOGLE_API_KEY, model="models/embedding-001")

    # Setting a Connection with the ChromaDB
    db_connection = Chroma(persist_directory="./chroma_db_", embedding_function=embedding_model)

    # Converting CHROMA db_connection to Retriever Object
    retriever = db_connection.as_retriever(search_kwargs={"k": 5})

    chat_template = ChatPromptTemplate.from_messages([
        # System Message Prompt Template
        SystemMessage(content="""You are a Helpful AI Bot. 
        You take the context and question from user. Your answer should be based on the specific context."""),
        # Human Message Prompt Template
        HumanMessagePromptTemplate.from_template("""Aswer the question based on the given context.
        Context:
        {context}
        
        Question: 
        {question}
        
        Answer: """)
    ])

    output_parser = StrOutputParser()

    from langchain_core.runnables import RunnablePassthrough

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | chat_template
        | chat_model
        | output_parser
    )

    user_question = st.text_input("Enter the question here:")
    if st.button("Submit"):
        response = rag_chain.invoke(user_question)
        st.markdown(response)
else:
    st.warning("Please enter your Google API Key.")
