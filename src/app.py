import os
from flask import Flask, jsonify
from google import genai
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Initialiser le client Gemini avec le nouveau SDK
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

app = Flask(__name__)

# Route racine retourne une page avec un lien vers le status de l'API
@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
        <head><title>TicketFlow API</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h1>TicketFlow API</h1>
            <p>Le serveur de développement est actif.</p>
            <br>
            <a href="/api/status" style="padding: 10px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Vérifier le statut de l'API (/api/status)
            </a>
        </body>
    </html>
    '''

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "API TicketFlow fonctionnelle", "ia": "Gemini prêt (Nouveau SDK)"})

if __name__ == '__main__':
    app.run(debug=True)