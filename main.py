from flask import Flask, render_template, request, redirect, url_for  # Added redirect, url_for
import google.generativeai as genai
import os
from dotenv import load_dotenv
import PyPDF2

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB max file size

# Set up the Google API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------- Helper Functions ----------------------

def predict_fake_or_real_email_content(text):
    prompt = f"""
    You are an expert in identifying scam messages in text, email etc. Analyze the given text and classify it as:

    - **Real/Legitimate** (Authentic, safe message)
    - **Scam/Fake** (Phishing, fraud, or suspicious message)

    **for the following Text:**
    {text}

    **Return a clear message indicating whether this content is real or a scam. 
    If it is a scam, mention why it seems fraudulent. If it is real, state that it is legitimate.**

    **Only return the classification message and nothing else.**
    Note: Don't return empty or null, you only need to return message for the input text
    """
    response = model.generate_content(prompt)
    return response.text.strip() if response else "Classification failed."


def url_detection(url):
    prompt = f"""
    You are an advanced AI model specializing in URL security classification. Analyze the given URL and classify it as one of the following categories:

    1. Benign**: Safe, trusted, and non-malicious websites such as google.com, wikipedia.org, amazon.com.
    2. Phishing**: Fraudulent websites designed to steal personal information. Indicators include misspelled domains (e.g., paypa1.com instead of paypal.com), unusual subdomains, and misleading content.
    3. Malware**: URLs that distribute viruses, ransomware, or malicious software. Often includes automatic downloads or redirects to infected pages.
    4. Defacement**: Hacked or defaced websites that display unauthorized content, usually altered by attackers.

    **Example URLs and Classifications:**
    - **Benign**: "https://www.microsoft.com/"
    - **Phishing**: "http://secure-login.paypa1.com/"
    - **Malware**: "http://free-download-software.xyz/"
    - **Defacement**: "http://hacked-website.com/"

    **Input URL:** {url}

    **Output Format:**  
    - Return only a string class name
    - Example output for a phishing site:  

    Analyze the URL and return the correct classification (Only name in lowercase such as benign etc.
    Note: Don't return empty or null, at any cost return the corrected class
    """
    response = model.generate_content(prompt)
    if not response:
        return "unknown"
    classification = response.text.lower().strip().split()[0]  # Take only first word
    if classification not in ['benign', 'phishing', 'malware', 'defacement']:
        classification = 'unknown'
    return classification


# ---------------------- Routes ----------------------

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/scan-url')
def scan_url_page():
    return render_template("scan_url.html")

@app.route('/scan-file')
def scan_file_page():
    return render_template("scan_file.html")

@app.route('/result')
def result_page():
    classification = request.args.get('classification')
    input_url = request.args.get('input_url')
    message = request.args.get('message')
    return render_template("result.html", classification=classification, input_url=input_url, message=message)

@app.route('/scam/', methods=['POST'])
def detect_scam():
    if 'file' not in request.files:
        return redirect(url_for('result_page', message="No file uploaded."))

    file = request.files['file']
    extracted_text = ""

    if file.mimetype == 'application/pdf':
        pdf_reader = PyPDF2.PdfReader(file)
        extracted_text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    elif file.mimetype == 'text/plain':
        extracted_text = file.read().decode("utf-8")
    else:
        return redirect(url_for('result_page', message="Invalid file type. Please upload a PDF or TXT file."))

    if not extracted_text.strip():
        return redirect(url_for('result_page', message="File is empty or text could not be extracted."))

    message = predict_fake_or_real_email_content(extracted_text)
    return redirect(url_for('result_page', message=message))


@app.route('/predict', methods=['POST'])
def predict_url():
    url = request.form.get('url', '').strip()

    if not url.startswith(("http://", "https://")):
        return redirect(url_for('result_page', message="Invalid URL format.", input_url=url))

    classification = url_detection(url)
    return redirect(url_for('result_page', input_url=url, classification=classification))


if __name__ == '__main__':
    app.run(debug=True)
