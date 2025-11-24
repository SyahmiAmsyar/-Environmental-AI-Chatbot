from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)

# Ollama API endpoint (make sure Ollama is running locally)
OLLAMA_URL = "http://localhost:11434/api/generate"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]

    # Option 2: Force structured response in 5 sections
    prompt = f"""
You are an environmental expert. Answer the following question ONLY about environmental topics. 
Your answer MUST be structured with the following 5 sections EXACTLY:

🌱 1. Definition:
🔹 2. Types / Components:
⚡ 3. Sources / Causes:
⚠️ 4. Effects / Impact:
💡 5. Solutions / Prevention:

If a section has no information, write "No information provided."

Question: {user_message}
"""

    payload = {
        "model": "llama3.2",
        "prompt": prompt
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        bot_reply = ""

        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                bot_reply += data.get("response", "")

        return bot_reply

    except Exception as e:
        print(f"Error: {e}")
        return "Error: Could not reach AI service."

if __name__ == "__main__":
    app.run(debug=True)
