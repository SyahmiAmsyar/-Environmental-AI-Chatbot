from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)
OLLAMA_URL = "http://localhost:11434/api/generate"  # Ollama local endpoint

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form["message"]

    payload = {"model": "llama3.2", "prompt": user_message}

    response = requests.post(OLLAMA_URL, json=payload, stream=True)

    bot_reply = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            bot_reply += data.get("response", "")

    return bot_reply

if __name__ == "__main__":
    app.run(debug=True)
