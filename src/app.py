import os
from typing import Literal

from flask import Flask, jsonify, redirect, request, url_for
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from extensions import db, migrate

# Import du moteur RAG
from rag_utils import get_rag_engine
# Import des modèles pour que Flask-Migrate détecte les tables
from models import RagHistory, Ticket, TriageResult
from views import frontend

# Charger les variables du fichier .env dans src/
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_RESET_TOKEN'] = os.environ.get("TICKETFLOW_ADMIN_RESET_TOKEN")
KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'knowledge_base.json')
MAX_DESCRIPTION_LENGTH = 4000

db.init_app(app)
migrate.init_app(app, db)
app.register_blueprint(frontend)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Schéma de sortie structurée forcé (Pydantic)
class TriageResponse(BaseModel):
    categorie: Literal["Matériel", "Logiciel", "Réseau", "Accès"] = Field(
        description="Catégorie du ticket"
    )
    priorite: Literal["Faible", "Moyen", "Élevé", "Critique"] = Field(
        description="Priorité du ticket"
    )
    justification: str = Field(description="Brève justification du choix du triage")

def parse_triage_response(raw_response):
    if hasattr(TriageResponse, "model_validate_json"):
        return TriageResponse.model_validate_json(raw_response).model_dump()

    return TriageResponse.parse_raw(raw_response).dict()


def is_quota_error(error):
    message = str(error).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota" in message
        or "rate limit" in message
    )


def fallback_triage(description, procedure=None):
    text = description.lower()

    if procedure:
        return {
            "categorie": procedure.get("categorie") or "Logiciel",
            "priorite": procedure.get("priorite") or "Moyen",
            "justification": (
                "Gemini est temporairement indisponible à cause du quota. "
                "Le triage local reprend la catégorie et la priorité de la procédure RAG trouvée."
            ),
        }

    category_rules = [
        ("Réseau", ["vpn", "wifi", "wi-fi", "réseau", "internet", "routeur", "ethernet", "dns"]),
        ("Accès", ["mot de passe", "mfa", "compte", "connexion", "verrouillé", "authentification"]),
        ("Matériel", ["écran", "clavier", "souris", "imprimante", "portable", "chargeur", "bsod"]),
        ("Logiciel", ["application", "logiciel", "erreur", "500", "navigateur", "windows"]),
    ]
    priority_rules = [
        ("Critique", ["site complet", "tout le monde", "plus personne", "panne majeure", "production"]),
        ("Élevé", ["urgent", "bloqué", "impossible de travailler", "plusieurs utilisateurs", "critique"]),
        ("Moyen", ["impossible", "erreur", "ne fonctionne pas", "bloque"]),
    ]

    categorie = "Logiciel"
    priorite = "Faible"

    for candidate, keywords in category_rules:
        if any(keyword in text for keyword in keywords):
            categorie = candidate
            break

    for candidate, keywords in priority_rules:
        if any(keyword in text for keyword in keywords):
            priorite = candidate
            break

    return {
        "categorie": categorie,
        "priorite": priorite,
        "justification": (
            "Gemini est temporairement indisponible à cause du quota. "
            "Un triage local approximatif a été produit à partir de mots-clés."
        ),
    }


# Initialisation paresseuse des moteurs RAG pour éviter de bloquer le démarrage
rag_engines = {
    "basic": {"engine": None, "error": None},
    "chroma": {"engine": None, "error": None},
}


def get_or_create_rag_engine(use_chroma=False):
    if client is None:
        return None, "GEMINI_API_KEY n'est pas configurée."

    engine_key = "chroma" if use_chroma else "basic"
    engine_state = rag_engines[engine_key]

    if engine_state["engine"] is not None:
        return engine_state["engine"], None

    if engine_state["error"] is not None:
        return None, engine_state["error"]

    try:
        engine_state["engine"] = get_rag_engine(
            client=client,
            kb_path=KNOWLEDGE_BASE_PATH,
            use_chroma=use_chroma,
        )
        return engine_state["engine"], None
    except Exception as e:
        engine_state["error"] = str(e)
        return None, engine_state["error"]


def is_reset_authorized():
    expected_token = app.config.get("ADMIN_RESET_TOKEN")
    provided_token = request.headers.get("X-Admin-Reset-Token", "")

    return bool(expected_token) and provided_token == expected_token


def rag_status(engine_key):
    engine_state = rag_engines[engine_key]

    if engine_state["engine"] is not None:
        return "Actif"

    if engine_state["error"] is not None:
        return f"Erreur : {engine_state['error']}"

    return "Non initialisé"

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for("frontend.dashboard"))

@app.route('/api/v1/status', methods=['GET'])
def status():
    return jsonify({
        "status": "API TicketFlow fonctionnelle", 
        "ia": "Gemini 2.5 Flash prêt" if client is not None else "GEMINI_API_KEY manquante",
        "rag_basic": rag_status("basic"),
        "rag_chroma": rag_status("chroma"),
        "reset_admin": "Configuré" if app.config.get("ADMIN_RESET_TOKEN") else "Non configuré",
    })

@app.route('/api/v1/tickets', methods=['DELETE'])
def delete_tickets():
    if not app.config.get("ADMIN_RESET_TOKEN"):
        return jsonify({
            "erreur": "Réinitialisation désactivée. Configurez TICKETFLOW_ADMIN_RESET_TOKEN."
        }), 403

    if not is_reset_authorized():
        return jsonify({"erreur": "Jeton administrateur invalide ou manquant."}), 403

    try:
        RagHistory.query.delete()
        TriageResult.query.delete()
        Ticket.query.delete()
        db.session.commit()

        return jsonify({"message": "Base de données réinitialisée"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": f"Échec de la réinitialisation : {str(e)}"}), 500

@app.route('/api/v1/triage', methods=['POST'])
def triage():
    data = request.get_json(silent=True)
    
    if not data or 'description' not in data:
        return jsonify({"erreur": "Requête invalide. Veuillez fournir une 'description' en JSON."}), 400
        
    description = data['description']

    if not isinstance(description, str):
        return jsonify({"erreur": "La description doit être une chaîne de caractères."}), 400

    description = description.strip()

    if not description:
        return jsonify({"erreur": "La description ne peut pas être vide."}), 400

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return jsonify({
            "erreur": f"La description dépasse la limite de {MAX_DESCRIPTION_LENGTH} caractères."
        }), 400

    use_chroma = bool(data.get('use_chroma', False))
    engine, engine_error = get_or_create_rag_engine(use_chroma=use_chroma)
    rag_engine_name = "Chroma" if use_chroma else "Basic"
    rag_warning = None

    if engine is None:
        rag_warning = f"Le moteur RAG {rag_engine_name} n'est pas disponible : {engine_error}"
    
    # 1. Étape RAG : Recherche de procédures pertinentes
    try:
        procedure = engine.find_relevant_procedure(description) if engine else None
    except Exception as e:
        procedure = None
        rag_warning = f"Échec de la recherche RAG {rag_engine_name} : {str(e)}"
    
    # 2. Construction du prompt augmenté
    prompt = "Tu es un agent de triage ITSM expert pour un centre de services TI.\n"
    prompt += "Tu dois classifier uniquement des incidents de soutien informatique aux utilisateurs.\n"
    prompt += "Si la demande concerne de la programmation pure, de la révision de code, du débogage applicatif ou un framework de développement, assigne la priorité 'Faible' et indique que le centre de services ne fait pas de débogage de code.\n"
    prompt += "Les catégories autorisées sont strictement : Matériel, Logiciel, Réseau, Accès.\n"
    prompt += "Les priorités autorisées sont strictement : Faible, Moyen, Élevé, Critique.\n"
    prompt += f"Analyse le ticket utilisateur suivant :\n'{description}'\n\n"
    
    if procedure:
        prompt += f"--- PROCÉDURE INTERNE TROUVÉE ({procedure['titre']}) ---\n"
        prompt += f"{procedure['contenu']}\n"
        prompt += "--------------------------------------\n"
        prompt += "IMPORTANT: Base ton triage en priorité sur cette procédure.\n"
    else:
        prompt += "Aucune procédure spécifique n'a été trouvée. Utilise ton jugement professionnel standard d'ITSM.\n"
        
    # 3. Appel à l'IA avec Structured Output
    ai_fallback = False
    ai_warning = None

    try:
        if client is None:
            result_json = fallback_triage(description, procedure)
            ai_fallback = True
            ai_warning = "Clé Gemini manquante; triage local de secours utilisé."
        else:
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
                result_json = parse_triage_response(response.text)
            except Exception as e:
                if not is_quota_error(e):
                    raise

                result_json = fallback_triage(description, procedure)
                ai_fallback = True
                ai_warning = "Quota Gemini atteint; triage local de secours utilisé."
        
        ticket = Ticket(description=description, statut='Trié')
        db.session.add(ticket)
        db.session.flush()

        if procedure:
            rag_entry = RagHistory(
                ticket_id=ticket.id,
                contexte_retrouve=procedure.get('contenu') or str(procedure),
                source=f"[{rag_engine_name}] {procedure.get('titre')}",
                score_similarite=procedure.get('score_similarite'),
                categorie_reference=procedure.get('categorie'),
                priorite_reference=procedure.get('priorite'),
            )
            db.session.add(rag_entry)

        triage_result = TriageResult(
            ticket_id=ticket.id,
            categorie=result_json['categorie'],
            priorite=result_json['priorite'],
            justification=result_json['justification'],
            modele_ia='fallback-local' if ai_fallback else 'gemini-2.5-flash',
        )
        db.session.add(triage_result)
        db.session.commit()
        
        # Ajout d'une métadonnée pour la transparence (savoir si le RAG a aidé)
        result_json['_meta'] = {
            "ticket_id": ticket.id,
            "rag_utilise": procedure['titre'] if procedure else False,
            "moteur_rag": rag_engine_name,
            "fallback_local": ai_fallback,
            "avertissement_ia": ai_warning,
            "avertissement_rag": rag_warning,
        }
        
        return jsonify(result_json), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": f"Échec du triage : {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
