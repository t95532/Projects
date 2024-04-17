from flask import Flask, render_template, request
import re

app = Flask(__name__)

# Index Route
@app.route('/')
def index():
    return render_template('index.html')

# Regex Pattern Matching Routes
@app.route('/regex')
def regex_home():
    return render_template('regex_index.html')

@app.route('/regex/results', methods=['POST'])
def regex_results():
    test_string = request.form['test_string']
    regex_pattern = request.form['regex_pattern']

    # Highlight pattern in the string and count occurrences
    matches = re.findall(regex_pattern, test_string)
    highlighted_string = re.sub(regex_pattern, r'<mark>\g<0></mark>', test_string, flags=re.IGNORECASE)
    match_count = len(matches)

    return render_template('regex_results.html', highlighted_string=highlighted_string, match_count=match_count)

# Email Validation Routes
@app.route('/email')
def email_home():
    return render_template('email_index.html')

@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.form['email']

    # Validate email address
    if re.match(r'^[\w\.-]+@[a-zA-Z]+\.(com|in|org)$', email):
        result = "Valid"
    else:
        result = "Invalid"

    return render_template('result.html', email=email, result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)