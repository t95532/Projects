from flask import Flask, request, render_template
from app.resume_parser import extract_text_from_pdf
from app.jd_parser import load_text
from app.chains import build_resume_match_chain
import os

app = Flask(__name__)
chain = build_resume_match_chain()

@app.route("/", methods=["GET", "POST"])
def index():
    analysis = None
    error = None
    if request.method == "POST":
        try:
            resume_file = request.files["resume"]
            jd_file = request.files["jd"]

            os.makedirs("data", exist_ok=True)
            resume_path = "data/temp_resume.pdf"
            jd_path = "data/temp_jd.txt"

            resume_file.save(resume_path)
            jd_file.save(jd_path)

            resume_text = extract_text_from_pdf(resume_path)
            jd_text = load_text(jd_path)

            # Use .invoke if using new LangChain, else .run
            try:
                analysis_result = chain.invoke({"resume": resume_text, "job_description": jd_text})
            except AttributeError:
                analysis_result = chain.run(resume=resume_text, job_description=jd_text)

            # Extract text if it's an AIMessage or similar object
            if hasattr(analysis_result, "content"):
                analysis = analysis_result.content
            else:
                analysis = analysis_result
        except Exception as e:
            error = str(e)

    return render_template("index.html", analysis=analysis, error=error)

if __name__ == "__main__":
    app.run(debug=True)