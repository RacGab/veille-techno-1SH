import os
from flask import Blueprint, jsonify, request
from google import genai
from google.genai import types

from ..extensions import db
from ..models import RagHistory, Ticket, TriageResult
from ..services import (
    TriageResponse,
    parse_triage_response,
    is_quota_error,
    groq_triage,
    fallback_triage,
    get_or_create_rag_engine,
    get_rag_status
)

api_bp = Blueprint('api', __name__)

MAX_DESCRIPTION_LENGTH = 4000
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def is_reset_authorized():
    from flask import current_app
    expected_token = current_app.config.get("ADMIN_RESET_TOKEN")
    provided_token = request.headers.get("X-Admin-Reset-Token", "")
    return bool(expected_token) and provided_token == expected_token

@api_bp.route('/status', methods=['GET'])
def status():
    from flask import current_app
    return jsonify({
        "status": "API TicketFlow fonctionnelle", 
        "ia_gemini": "Prêt" if client is not None else "Clé manquante",
        "ia_groq": "Prêt" if GROQ_API_KEY and GROQ_API_KEY != "votre_cle_groq_ici" else "Clé manquante",
        "rag_basic": get_rag_status("basic"),
        "rag_chroma": get_rag_status("chroma"),
        "reset_admin": "Configuré" if current_app.config.get("ADMIN_RESET_TOKEN") else "Non configuré",
    })

@api_bp.route('/tickets', methods=['DELETE'])
def delete_tickets():
    from flask import current_app
    if not current_app.config.get("ADMIN_RESET_TOKEN"):
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

@api_bp.route('/triage', methods=['POST'])
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
    ai_provider = str(data.get('ai_provider', 'auto')).lower()
    
    try:
        from ..services import process_ticket_triage
        result_json = process_ticket_triage(
            description=description,
            use_chroma=use_chroma,
            ai_provider=ai_provider,
            client=client
        )
        return jsonify(result_json), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": f"Échec du triage : {str(e)}"}), 500
