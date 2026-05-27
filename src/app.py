import os
from flask import Flask, jsonify
from google import genai
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Initialiser le client Gemini avec le nouveau SDK
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

app = Flask(__name__)

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "API TicketFlow fonctionnelle", "ia": "Gemini prêt (Nouveau SDK)"})

if __name__ == '__main__':
    app.run(debug=True)