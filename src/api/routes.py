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
    
    engine, engine_error = get_or_create_rag_engine(client, use_chroma=use_chroma)
    rag_engine_name = "Chroma" if use_chroma else "Basic"
    rag_warning = None

    if engine is None:
        rag_warning = f"Le moteur RAG {rag_engine_name} n'est pas disponible : {engine_error}"
    
    try:
        procedure = engine.find_relevant_procedure(description) if engine else None
    except Exception as e:
        procedure = None
        rag_warning = f"Recherche RAG {rag_engine_name} ignorée (pas de clé ou erreur réseau)."
        print(f"Échec RAG silencieux: {e}")
    
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
        
    ai_fallback = False
    ai_warning = None
    model_used = None
    result_json = None

    try:
        # 1. Tentative avec Gemini
        if ai_provider in ['auto', 'gemini'] and client:
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TriageResponse,
                        temperature=0.1
                    ),
                )
                result_json = parse_triage_response(response.text)
                model_used = 'gemini-2.5-flash'
            except Exception as e:
                print(f"Erreur Gemini: {e}")
                if not is_quota_error(e):
                    raise

        # 2. Tentative avec Groq
        if result_json is None and ai_provider in ['auto', 'groq'] and GROQ_API_KEY and GROQ_API_KEY != "votre_cle_groq_ici":
            try:
                result_json = groq_triage(description, prompt, GROQ_API_KEY)
                model_used = 'groq/llama-3.3-70b'
                if ai_provider == 'auto' and client:
                    ai_warning = "Quota Gemini atteint; triage via Groq (Llama 3) utilisé."
            except Exception as e:
                print(f"Erreur Groq: {e}")

        # 3. Triage Local (Fallback 2)
        if result_json is None:
            result_json = fallback_triage(description, procedure)
            ai_fallback = True
            model_used = 'fallback-local'
            
            if ai_provider == 'gemini':
                ai_warning = "Gemini indisponible ou clé manquante; triage local utilisé."
            elif ai_provider == 'groq':
                ai_warning = "Groq indisponible ou clé manquante; triage local utilisé."
            elif ai_provider == 'local':
                ai_warning = "Triage algorithmique local forcé manuellement."
            else:
                ai_warning = "IA indisponible (Quota); triage local utilisé."
        
        ticket = Ticket(description=description, statut='en_attente')

        if procedure:
            rag_entry = RagHistory(
                ticket=ticket,
                contexte_retrouve=procedure.get('contenu') or str(procedure),
                source=f"[{rag_engine_name}] {procedure.get('titre')}",
                score_similarite=procedure.get('score_similarite'),
                categorie_reference=procedure.get('categorie'),
                priorite_reference=procedure.get('priorite'),
            )
            db.session.add(rag_entry)

        triage_result = TriageResult(
            ticket=ticket,
            categorie=result_json['categorie'],
            priorite=result_json['priorite'],
            justification=result_json['justification'],
            modele_ia=model_used,
        )
        db.session.add(triage_result)
        
        ticket.statut = 'Trié'
        db.session.add(ticket)
        db.session.commit()
        
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
