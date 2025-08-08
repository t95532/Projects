from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

def build_resume_match_chain():
    # Load the prompt template from file safely
    prompt_path = "app/prompts/feedback_prompt.txt"
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_text = f.read()
    except FileNotFoundError:
        prompt_text = "Compare the following resume and job description:\nResume: {resume}\nJob Description: {job_description}\nAnalysis:"

    prompt_template = PromptTemplate(
        input_variables=["resume", "job_description"],
        template=prompt_text
    )

    # Initialize the LLM (Google Gemini Pro)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.4,
        google_api_key="AIzaSyDRrD8u8wDrevvyA3e4ywCEo2GhSoCIM6s"
        #google_api_key=os.getenv("GOOGLE_API_KEY", "")
    )

    # Build a RunnableSequence chain
    return prompt_template | llm