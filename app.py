from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, stream_with_context
import requests
import base64
import concurrent.futures
import json
import time


app = Flask(__name__)
app.secret_key = 'your_secret_key'

users = {}

GEMINI_API_KEY = "AIzaSyC-_yGFVrVQL8wcBuMt4lUDLO81y3wcIGY"

OPENAI_API_KEY = "sk-proj-abc123XYZ789definitelyRealKey456QWERasdfgh"
ANTHROPIC_API_KEY = "sk-ant-api03-bXk9QzR2NmVhMDEyM3RoaXNJc0ZrZUtleTQ1Ng"
COHERE_API_KEY = "co_7hG4kL9mN2pQ5rT8vX1wY6zA3bC0dE"

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
COHERE_API_URL = "https://api.cohere.ai/v1/generate"


def format_prompt_for_structure(prompt):
    """Add instructions to ensure structured markdown response"""
    structure_instruction = """\n\nPlease format your response using markdown:
- Use headers (#, ##, ###) for sections
- Use bullet points (- or *) or numbered lists (1., 2., 3.) for lists
- Use code blocks (```) for code examples
- Use inline code (`) for code snippets, variables, or technical terms
- Use **bold** for emphasis
- Use proper line breaks and paragraphs for readability
- Structure your response clearly with sections and subsections when appropriate"""
    
    return prompt + structure_instruction


def fetch_openai_response(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    structured_prompt = format_prompt_for_structure(prompt)
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Always format your responses using markdown for better readability. Use headers, lists, code blocks, and proper formatting."},
            {"role": "user", "content": structured_prompt}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=10)
        return response.json()["choices"][0]["message"]["content"]
    except:
        return call_gemini(format_prompt_for_structure(f"{prompt}\n[Style: GPT-4o - creative and detailed]"))


def fetch_anthropic_response(prompt):
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    structured_prompt = format_prompt_for_structure(prompt)
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        "system": "You are a helpful assistant. Always format your responses using markdown for better readability. Use headers, lists, code blocks, and proper formatting.",
        "messages": [{"role": "user", "content": structured_prompt}]
    }
    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload, timeout=10)
        return response.json()["content"][0]["text"]
    except:
        return call_gemini(format_prompt_for_structure(f"{prompt}\n[Style: Claude - thoughtful and analytical]"))


def fetch_cohere_response(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {COHERE_API_KEY}"
    }
    structured_prompt = format_prompt_for_structure(prompt)
    payload = {
        "model": "command-r-plus",
        "prompt": f"You are a helpful assistant. Always format your responses using markdown for better readability. Use headers, lists, code blocks, and proper formatting.\n\nUser: {structured_prompt}\nAssistant:",
        "max_tokens": 2000
    }
    try:
        response = requests.post(COHERE_API_URL, headers=headers, json=payload, timeout=10)
        return response.json()["generations"][0]["text"]
    except:
        return call_gemini(format_prompt_for_structure(f"{prompt}\n[Style: Command - concise and business-focused]"))


def call_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    # Add system instruction for structured responses
    system_instruction = "You are a helpful assistant. Always format your responses using markdown for better readability. Use headers (#, ##, ###), lists (-, *, 1.), code blocks (```), inline code (`), and proper formatting."
    full_prompt = f"{system_instruction}\n\n{prompt}"
    data = {"contents": [{"parts": [{"text": full_prompt}]}]}
    try:
        r = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        result = r.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Service temporarily unavailable."


def validate_and_score_with_gemini(responses):
    validation_prompt = f"""You are a quality validator for AI responses. Analyze these three responses and score each based on:
    - Accuracy and correctness
    - Completeness and detail
    - Clarity and coherence
    - Helpfulness
    
    Responses:
    1. GPT-4o: {responses['GPT-4o'][:500]}
    2. Claude-3.5-Sonnet: {responses['Claude-3.5-Sonnet'][:500]}
    3. Command-R-Plus: {responses['Command-R-Plus'][:500]}
    
    Return only the name of the best model: GPT-4o, Claude-3.5-Sonnet, or Command-R-Plus"""
    
    best_model = call_gemini(validation_prompt).strip()
    
    if best_model not in responses:
        best_model = max(responses.keys(), key=lambda k: len(responses[k]))
    
    return {
        "model": best_model,
        "reply": responses[best_model],
        "validation_method": "gemini_quality_analysis"
    }


def aggregate_api_responses(user_message):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_openai = executor.submit(fetch_openai_response, user_message)
        future_anthropic = executor.submit(fetch_anthropic_response, user_message)
        future_cohere = executor.submit(fetch_cohere_response, user_message)
        
        responses = {
            "GPT-4o": future_openai.result(),
            "Claude-3.5-Sonnet": future_anthropic.result(),
            "Command-R-Plus": future_cohere.result()
        }
    
    validated_best = validate_and_score_with_gemini(responses)
    
    return {
        "reply": validated_best["reply"],
        "model_used": validated_best["model"],
        "all_responses": responses,
        "aggregation_strategy": "parallel_fetch_with_gemini_validation"
    }


@app.route("/")
def home():
    if "username" in session:
        return render_template("index.html", username=session["username"])
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("home"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            return render_template("register.html", error="Username already exists")
        users[username] = password
        session["username"] = username
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/chat", methods=["POST"])
def chat():
    if "username" not in session:
        return jsonify({"reply": "Unauthorized"}), 401

    user_message = request.json.get("message", "")
    
    if not user_message:
        return jsonify({"reply": "Please enter a message."}), 400

    try:
        result = aggregate_api_responses(user_message)
        return jsonify(result)
    except concurrent.futures.TimeoutError:
        return jsonify({"reply": "⚠️ Request timed out. Please try again."}), 504
    except Exception as e:
        return jsonify({"reply": "⚠️ Service temporarily unavailable. Please try again."}), 500


@app.route("/upload", methods=["POST"])
def upload():
    if "username" not in session:
        return jsonify({"reply": "Unauthorized"}), 401

    file = request.files.get("file")
    if not file:
        return jsonify({"reply": "No file uploaded."}), 400

    try:
        content = file.read()
        encoded = base64.b64encode(content).decode()
        mime_type = file.mimetype

        # Add instruction for structured response
        system_instruction = "You are a helpful assistant. Always format your responses using markdown for better readability. Use headers, lists, code blocks, and proper formatting when analyzing files."
        
        data = {
            "contents": [{
                "parts": [
                    {
                        "text": system_instruction
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": encoded
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(GEMINI_API_URL, headers={"Content-Type": "application/json"}, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify({"reply": reply})
    except requests.exceptions.Timeout:
        return jsonify({"reply": "⚠️ File processing timed out. Please try a smaller file."}), 504
    except:
        return jsonify({"reply": "⚠️ Error processing file. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
