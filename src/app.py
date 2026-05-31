import os
import json
from flask import Flask, jsonify, request
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from extensions import db, migrate

# Import du moteur RAG
from rag_utils import TicketRAG
# Import des modèles pour que Flask-Migrate détecte les tables
from models import RagHistory, Ticket, TriageResult

# Charger les variables du fichier .env
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Schéma de sortie structurée forcé (Pydantic)
class TriageResponse(BaseModel):
    categorie: str = Field(description="Catégorie du ticket (Matériel, Logiciel, Réseau, Accès)")
    priorite: str = Field(description="Priorité (Faible, Moyen, Élevé, Critique)")
    justification: str = Field(description="Brève justification du choix du triage")

# Initialisation paresseuse du RAG pour éviter de bloquer le démarrage en cas d'erreur de clé API
rag_engine = None

@app.before_request
def init_rag():
    global rag_engine
    # Initialise le RAG uniquement si ce n'est pas déjà fait
    if rag_engine is None:
        kb_path = os.path.join(os.path.dirname(__file__), 'data', 'knowledge_base.json')
        try:
            rag_engine = TicketRAG(client, kb_path)
        except Exception as e:
            print(f"⚠️ Erreur d'initialisation du RAG: {e}")

@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
        <head><title>TicketFlow API</title></head>
        <body style="font-family: sans-serif; padding: 2rem;">
            <h1>TicketFlow API</h1>
            <p>Le serveur de développement est actif.</p>
            <ul>
                <li><a href="/api/v1/status">Vérifier le statut de l'API (/api/v1/status)</a></li>
            </ul>
        </body>
    </html>
    '''

@app.route('/api/v1/status', methods=['GET'])
def status():
    rag_status = "Actif" if rag_engine is not None else "Inactif / Erreur d'initialisation"
    return jsonify({
        "status": "API TicketFlow fonctionnelle", 
        "ia": "Gemini 2.5 Flash prêt",
        "rag": rag_status
    })

@app.route('/api/v1/triage', methods=['POST'])
def triage():
    data = request.get_json()
    
    if not data or 'description' not in data:
        return jsonify({"erreur": "Requête invalide. Veuillez fournir une 'description' en JSON."}), 400
        
    description = data['description']
    
    # 1. Étape RAG : Recherche de procédures pertinentes
    procedure = rag_engine.find_relevant_procedure(description) if rag_engine else None
    
    # 2. Construction du prompt augmenté
    prompt = "Tu es un agent de triage ITSM expert. Ton but est de classifier les incidents informatiques.\n"
    prompt += f"Analyse le ticket utilisateur suivant :\n'{description}'\n\n"
    
    if procedure:
        prompt += f"--- PROCÉDURE INTERNE TROUVÉE ({procedure['titre']}) ---\n"
        prompt += f"{procedure['contenu']}\n"
        prompt += "--------------------------------------\n"
        prompt += "IMPORTANT: Base ton triage en priorité sur cette procédure.\n"
    else:
        prompt += "Aucune procédure spécifique n'a été trouvée. Utilise ton jugement professionnel standard d'ITSM.\n"
        
    # 3. Appel à l'IA avec Structured Output
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TriageResponse,
                temperature=0.1 # Température très basse pour un résultat logique et constant
            ),
        )
        
        # Le SDK retourne une chaîne JSON validée par Pydantic
        result_json = json.loads(response.text)
        
        # Ajout d'une métadonnée pour la transparence (savoir si le RAG a aidé)
        result_json['_meta'] = {
            "rag_utilise": procedure['titre'] if procedure else False
        }
        
        return jsonify(result_json), 201
        
    except Exception as e:
        return jsonify({"erreur": f"Échec de l'analyse IA : {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
