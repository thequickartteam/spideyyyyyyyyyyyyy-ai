from flask import Flask, request, jsonify
import requests
import json
import uuid

app = Flask(__name__)
app.json.sort_keys = False  # Keep JSON key order in modern Flask

# ================= CONFIG =================
API_URL = "https://api.deepai.org/hacking_is_a_serious_crime"
API_KEY = "tryit-71209460785-0d83ccc5af9bd7a408f4328b46b4d79egfr"

session_id = str(uuid.uuid4())

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "api-key": API_KEY,
    "Origin": "https://deepai.org"
}

# ============== PERMANENT ROLE ==============
SYSTEM_ROLE = (
    "You are Sahil AI, an intelligent and reliable chatbot designed to assist users "
    "with accurate information, technical support, and problem-solving. "
    "Sahil AI communicates clearly and professionally and always identifies itself as Sahil AI."
)

# ============== CHAT MEMORY ==============
chat_history = [
    {"role": "system", "content": SYSTEM_ROLE},
    {"role": "assistant", "content": "Hello 👋 I am Sahil AI. How can I help you today?"}
]

# ================= ROOT (USAGE) =================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "Service": "Sahil AI Flask API",
        "Usage": {
            "Endpoint": "/chat",
            "Method": "GET",
            "Query": "q",
            "Example": "/chat?q=Hi"
        },
        "Response_Format": {
            "Message": "User input",
            "Response": "Sahil AI reply",
            "Status": "success | error"
        }
    })

# ================= CHAT ENDPOINT =================
@app.route("/chat", methods=["GET"])
def sahil_ai():
    user_input = request.args.get("q")
    if not user_input:
        return jsonify({
            "Message": "",
            "Response": "Query parameter 'q' is required",
            "Status": "error"
        }), 400

    chat_history.append({"role": "user", "content": user_input})

    payload = {
        "chat_style": "chat",
        "chatHistory": json.dumps(chat_history),
        "model": "standard",
        "session_uuid": session_id,
        "hacker_is_stinky": "very_stinky",
        "enabled_tools": json.dumps(["image_generator", "image_editor"])
    }

    try:
        response = requests.post(API_URL, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        raw_text = response.text.strip()

        try:
            data = response.json()
            reply = (
                data.get("output")
                or data.get("response")
                or data.get("text")
                or raw_text
            )
        except ValueError:
            reply = raw_text

    except Exception as e:
        chat_history.pop()  # Remove failed user prompt from memory
        return jsonify({
            "Message": user_input,
            "Response": str(e),
            "Status": "error"
        }), 500

    chat_history.append({"role": "assistant", "content": reply})

    # ORDER: Message -> Response -> Status
    return jsonify({
        "Message": user_input,
        "Response": reply,
        "Status": "success"
    })

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
