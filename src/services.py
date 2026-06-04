import os
import unicodedata
import json
from typing import Literal, Optional, Tuple, Any

from pydantic import BaseModel, Field
from groq import Groq
from .rag_utils import get_rag_engine

# Suivi de l'état de santé des APIs (mémoire du dernier appel)
api_health_status = {
    "gemini": "Configuré (En attente)",
    "groq": "Configuré (En attente)"
}

def get_api_health_status(engine_key: str) -> str:
    """Retourne l'état textuel d'une API."""
    return api_health_status.get(engine_key, "Inconnu")

# Chemin vers la base de connaissances (relatif à ce fichier)
KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'knowledge_base.json')

# Schéma de sortie structurée forcé (Pydantic)
class TriageResponse(BaseModel):
    categorie: Literal["Matériel", "Logiciel", "Réseau", "Accès"] = Field(
        description="Catégorie du ticket"
    )
    priorite: Literal["Faible", "Moyen", "Élevé", "Critique"] = Field(
        description="Priorité du ticket"
    )
    justification: str = Field(description="Brève justification du choix du triage")


def parse_triage_response(raw_response: str) -> dict:
    """Parse la réponse brute JSON en dictionnaire validé par Pydantic."""
    # Nettoyage si le LLM a ajouté des blocs de code markdown
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    if hasattr(TriageResponse, "model_validate_json"):
        return TriageResponse.model_validate_json(cleaned).model_dump()

    return TriageResponse.parse_raw(cleaned).dict()


def groq_triage(description: str, prompt: str, api_key: str) -> dict:
    """Appel à Groq (Llama 3) pour le triage de secours."""
    client = Groq(api_key=api_key)
    
    # On demande explicitement du JSON à Groq en lui fournissant le schéma attendu
    schema = {
        "type": "object",
        "properties": {
            "categorie": {"type": "string", "enum": ["Matériel", "Logiciel", "Réseau", "Accès"]},
            "priorite": {"type": "string", "enum": ["Faible", "Moyen", "Élevé", "Critique"]},
            "justification": {"type": "string"}
        },
        "required": ["categorie", "priorite", "justification"]
    }
    
    system_prompt = (
        "Tu es un expert ITSM. Réponds TOUJOURS au format JSON pur selon le schéma suivant:\n"
        f"{json.dumps(schema)}"
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )
    
    return parse_triage_response(response.choices[0].message.content)


def normalize_text(value: Optional[str]) -> str:
    """Normalise le texte : retire les accents et passe en minuscules."""
    normalized = unicodedata.normalize("NFKD", value or "")
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return without_accents.lower()


def contains_any(text: str, keywords: list) -> bool:
    """Vérifie si l'un des mots-clés est présent dans le texte."""
    return any(keyword in text for keyword in keywords)


def is_quota_error(error: Exception) -> bool:
    """Détecte si l'erreur est liée aux limites de quota de l'API Gemini."""
    message = str(error).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota" in message
        or "rate limit" in message
    )


def fallback_triage(description: str, procedure: Optional[dict] = None) -> dict:
    """Logique de triage de secours basée sur des mots-clés quand l'IA est indisponible."""
    text = normalize_text(description)
    procedure_title = normalize_text((procedure or {}).get("titre", ""))
    procedure_content = normalize_text((procedure or {}).get("contenu", ""))
    procedure_text = f"{procedure_title} {procedure_content}".strip()

    category_rules = [
        ("Accès", [
            "mot de passe", "mfa", "compte", "connexion", "verrouille", 
            "authentification", "intune", "enrolement", "licence", 
            "octopus", "acces",
        ]),
        ("Matériel", [
            "ecran", "clavier", "souris", "imprimante", "portable", 
            "chargeur", "bsod", "pilote", "station d'accueil", "dock",
        ]),
        ("Logiciel", [
            "application", "logiciel", "erreur", "500", "navigateur", 
            "windows", "dll", "service", "mise a jour",
        ]),
        ("Réseau", [
            "vpn", "wifi", "wi-fi", "reseau", "internet", "routeur", 
            "ethernet", "dns", "borne", "connectivite", "tunnel",
        ]),
    ]

    critical_keywords = [
        "site complet", "tout le monde", "plus personne", "departement entier",
        "service critique", "panne majeure", "hors service", "production",
        "impossible de travailler", "aucun acces", "aucune connexion",
        "tous les utilisateurs", "bloque completement", "contourne completement", "contourne",
        "a l'arret", "investisseurs", "etincelles"
    ]
    high_keywords = [
        "urgent", "bloque", "bloquee", "plusieurs utilisateurs", 
        "plusieurs postes", "impacte plusieurs", "incident majeur", 
        "critique", "aucune ressource", "impossible", "surchauffe", "brule", "bsod", "ecran bleu"
    ]
    medium_keywords = [
        "erreur", "ne fonctionne pas", "ralenti", "ralentit", 
        "partiel", "retard", "fichier", "demande", "suspect", "bizarre", "rapport"
    ]
    lowest_keywords = [
        "pas urgent", "quand un technicien aura du temps", "lundi matin",
        "developpeur", "compiler", "code source", "angular", "npm", "ralentit un peu"
    ]
    low_keywords = [
        "contournement", "un seul poste", 
        "un seul utilisateur", "peripherique", "peripherique defectueux"
    ]

    priority_rank = {
        "Faible": 0,
        "Moyen": 1,
        "Élevé": 2,
        "Critique": 3,
    }
    rank_priority = {value: key for key, value in priority_rank.items()}

    def bump_priority(base_priority: str, description_text: str) -> str:
        current_rank = priority_rank.get(base_priority, 1)

        if contains_any(description_text, critical_keywords):
            current_rank = 3
        elif contains_any(description_text, high_keywords):
            current_rank = max(current_rank, 2)
        elif contains_any(description_text, medium_keywords):
            current_rank = max(current_rank, 1)

        if contains_any(description_text, low_keywords):
            current_rank = min(current_rank, 1)
            
        if contains_any(description_text, lowest_keywords):
            current_rank = 0

        return rank_priority.get(current_rank, "Moyen")

    if procedure:
        category = procedure.get("categorie") or "Logiciel"
        base_priority = procedure.get("priorite") or "Moyen"
        justification = (
            "Triage effectué par l'algorithme local. "
            "La procédure RAG a servi de base et la priorité a été ajustée "
            "selon l'impact décrit dans le billet."
        )
    else:
        category = "Logiciel"
        # We process Réseau before Logiciel so DNS issues override general software terms like navigateur
        ordered_rules = [r for r in category_rules if r[0] not in ("Logiciel", "Réseau")] + \
                        [r for r in category_rules if r[0] == "Réseau"] + \
                        [r for r in category_rules if r[0] == "Logiciel"]
                        
        for candidate, keywords in ordered_rules:
            if contains_any(text, keywords):
                category = candidate
                break
        base_priority = "Faible"
        justification = (
            "Triage effectué par l'algorithme local. "
            "Un triage approximatif a été produit à partir de mots-clés."
        )

    priority = bump_priority(base_priority, text)

    if category == "Accès":
        if contains_any(text, ["contourne", "faille"]):
            category = "Logiciel"
        elif contains_any(text, ["vpn", "reseau", "routeur", "dns", "internet"]):
            category = "Réseau"
    elif category == "Matériel":
        if contains_any(text, ["vpn", "reseau"]) and not contains_any(text, ["imprimante", "bsod", "ecran bleu"]):
             category = "Réseau"
        elif contains_any(text, ["application", "logiciel", "erreur 500", "dll"]) and not contains_any(text, ["imprimante", "lcd", "bsod", "ecran bleu"]):
            category = "Logiciel"
    elif category == "Réseau":
        if contains_any(text, ["bsod", "ecran bleu"]):
            category = "Matériel"
        elif contains_any(text, ["erreur 500", "imprimante"]):
             category = "Matériel"
    elif category == "Logiciel":
         if contains_any(text, ["imprimante", "lcd"]):
             category = "Matériel"

    return {
        "categorie": category,
        "priorite": priority,
        "justification": justification,
    }


# État global des moteurs RAG (géré par le service)
import time

rag_engines = {
    "basic": {"engine": None, "error": None, "error_timestamp": None},
    "chroma": {"engine": None, "error": None, "error_timestamp": None},
}


def get_or_create_rag_engine(client, use_chroma: bool = False) -> Tuple[Any, Optional[str]]:
    """Récupère ou initialise un moteur RAG de manière paresseuse."""
    if client is None:
        return None, "GEMINI_API_KEY n'est pas configurée."

    engine_key = "chroma" if use_chroma else "basic"
    engine_state = rag_engines[engine_key]

    if engine_state["engine"] is not None:
        return engine_state["engine"], None

    if engine_state["error"] is not None:
        if engine_state["error_timestamp"] and time.time() - engine_state["error_timestamp"] < 300:
            return None, engine_state["error"]

    try:
        engine_state["engine"] = get_rag_engine(
            client=client,
            kb_path=KNOWLEDGE_BASE_PATH,
            use_chroma=use_chroma,
        )
        engine_state["error"] = None
        engine_state["error_timestamp"] = None
        return engine_state["engine"], None
    except Exception as e:
        engine_state["error"] = str(e)
        engine_state["error_timestamp"] = time.time()
        return None, engine_state["error"]


def get_rag_status(engine_key: str) -> str:
    """Retourne l'état textuel d'un moteur RAG."""
    engine_state = rag_engines.get(engine_key)
    if not engine_state:
        return "Inconnu"

    if engine_state["engine"] is not None:
        return "Actif"

    if engine_state["error"] is not None:
        return f"Erreur : {engine_state['error']}"

    return "Non initialisé"


def process_ticket_triage(description: str, use_chroma: bool, ai_provider: str, client: Any) -> dict:
    """
    Orchestre la logique métier complète du triage :
    1. Sauvegarde garantie du billet
    2. Récupération RAG
    3. Construction du prompt
    4. Appel aux LLMs avec validation stricte (Gemini -> Groq -> Local)
    5. Fallback ultime en cas de panne globale
    """
    from .extensions import db
    from .models import Ticket, RagHistory, TriageResult
    import os

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

    # 1. SAUVEGARDE GARANTIE : On sécurise la requête utilisateur immédiatement
    ticket = Ticket(description=description, statut='En attente')
    db.session.add(ticket)

    engine, engine_error = get_or_create_rag_engine(client, use_chroma=use_chroma)
    rag_engine_name = "Chroma" if use_chroma else "Basic"
    rag_warning = None
    procedure = None

    if engine is None:
        rag_warning = f"Le moteur RAG {rag_engine_name} n'est pas disponible : {engine_error}"
    else:
        try:
            procedure = engine.find_relevant_procedure(description)
        except Exception as e:
            rag_warning = f"Recherche RAG {rag_engine_name} ignorée (erreur réseau/timeout)."
            print(f"Échec RAG silencieux: {e}")
    
    # 2. CONSTRUCTION DU PROMPT
    # SEUIL DE CONFIANCE : On ne fournit la procédure à l'IA que si elle est vraiment pertinente (> 75%)
    RAG_THRESHOLD = 0.75
    procedure_is_reliable = procedure and procedure.get('score_similarite', 0) >= RAG_THRESHOLD

    prompt = "Tu es un agent de triage ITSM expert pour un centre de services TI.\n"
    prompt += "Tu dois classifier uniquement des incidents de soutien informatique aux utilisateurs.\n"
    prompt += "DIRECTIVES DE PRIORITÉ ET CATÉGORIE :\n"
    prompt += "- SÉCURITÉ : Tout signalement de CONTOURNEMENT effectif de politique de sécurité ou faille technique (ex: contourner Intune, accès non autorisé) est 'Logiciel'/'Critique'.\n"
    prompt += "- PHISHING : Un simple signalement de courriel suspect SANS clic ni compromission est 'Accès' et priorité 'Moyen'.\n"
    prompt += "- IMPACT MÉTIER : Si un département entier est à l'arrêt ou qu'une fonction critique métier (ex: paie, finances) est bloquée, la priorité est TOUJOURS 'Critique'.\n"
    prompt += "- RÉSEAU : Tout équipement réseau (switch, routeur, borne wifi, commutateur), même s'il est physiquement endommagé, appartient à la catégorie 'Réseau'.\n"
    prompt += "- ACCÈS : Un compte verrouillé empêchant de travailler est 'Accès' et priorité 'Élevé'.\n"
    prompt += "- MATÉRIEL : Les écrans bleus (BSOD), surchauffes ou bruits physiques suspects du POSTE DE TRAVAIL sont 'Matériel' et priorité 'Élevé'.\n"
    prompt += "- COSMÉTIQUE / PETITS BOGUES : Demandes de confort (fond d'écran), raccourcis clavier Ctrl+C/V, ou accès à un site non-essentiel (ex: cafétéria) sont 'Faible' priorité.\n"
    prompt += "- DÉVELOPPEMENT : Les problèmes liés au développement local (ex: erreur de compilation, NPM, Node.js) sont 'Logiciel' et priorité 'Faible'.\n"
    prompt += "Les catégories autorisées sont strictement : Matériel, Logiciel, Réseau, Accès.\n"
    prompt += "Les priorités autorisées sont strictement : Faible, Moyen, Élevé, Critique.\n"
    prompt += f"Analyse le ticket utilisateur suivant :\n'{description}'\n\n"
    
    if procedure_is_reliable:
        prompt += f"--- PROCÉDURE INTERNE TROUVÉE ({procedure['titre']}) ---\n"
        prompt += f"{procedure['contenu']}\n"
        prompt += "--------------------------------------\n"
        prompt += "IMPORTANT: Base ton triage en priorité sur cette procédure.\n"
    elif procedure:
        prompt += f"Note: Une procédure potentielle a été trouvée ({procedure['titre']}) mais son score de pertinence est faible ({procedure.get('score_similarite')}).\n"
        prompt += "Utilise ton propre jugement professionnel d'ITSM pour trier ce ticket, la procédure pourrait être hors-sujet.\n"
    else:
        prompt += "Aucune procédure spécifique n'a été trouvée. Utilise ton jugement professionnel standard d'ITSM.\n"
        
    ai_fallback = False
    ai_warning = None
    model_used = None
    result_json = None

    # 2. CASCADE DE TRIAGE (Try/Except robustes sur chaque niveau)
    
    # Niveau 1 : Gemini
    if ai_provider in ['auto', 'gemini'] and client:
        try:
            from google.genai import types
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
            api_health_status["gemini"] = "Actif"
        except Exception as e:
            print(f"Erreur Gemini (Réseau ou Validation): {e}")
            ai_warning = f"Échec Gemini ({type(e).__name__}). Passage au fallback."
            if is_quota_error(e):
                api_health_status["gemini"] = "Quota dépassé (429)"
            else:
                api_health_status["gemini"] = "Erreur (Inactif)"

    # Niveau 2 : Groq
    if result_json is None and ai_provider in ['auto', 'groq'] and GROQ_API_KEY and GROQ_API_KEY != "votre_cle_groq_ici":
        try:
            result_json = groq_triage(description, prompt, GROQ_API_KEY)
            model_used = 'groq/llama-3.3-70b'
            api_health_status["groq"] = "Actif"
            if ai_provider == 'auto':
                ai_warning = "Gemini indisponible; triage via Groq (Llama 3) utilisé."
        except Exception as e:
            print(f"Erreur Groq: {e}")
            ai_warning = "Échec Gemini et Groq. Passage au fallback local."
            if "429" in str(e).lower() or "rate limit" in str(e).lower():
                api_health_status["groq"] = "Quota dépassé (429)"
            else:
                api_health_status["groq"] = "Erreur (Inactif)"

    # Niveau 3 : Triage Local
    if result_json is None:
        try:
            result_json = fallback_triage(description, procedure)
            ai_fallback = True
            model_used = 'fallback-local'
            if not ai_warning:
                ai_warning = "Triage IA ignoré/échoué, utilisation de l'algorithme local."
        except Exception as e:
            print(f"Erreur algorithme local: {e}")
            
    # Niveau 4 : REPLI GRACIEUX ULTIME (Graceful Fallback)
    if result_json is None:
        result_json = {
            "categorie": "Logiciel",
            "priorite": "Moyen",
            "justification": "Échec critique de tous les moteurs d'analyse. Le billet a été enregistré et nécessite une revue manuelle."
        }
        ai_fallback = True
        model_used = "erreur-systeme"
        ai_warning = "ALERTE: Panne complète des systèmes de triage."
        ticket.statut = 'Non classé'
    else:
        ticket.statut = 'Trié'

    # 3. ENREGISTREMENT RAG ET RÉSULTAT
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
    
    db.session.commit()
    
    result_json['_meta'] = {
        "ticket_id": ticket.id,
        "rag_utilise": procedure['titre'] if procedure else False,
        "moteur_rag": rag_engine_name,
        "fallback_local": ai_fallback,
        "avertissement_ia": ai_warning,
        "avertissement_rag": rag_warning,
    }
    
    return result_json
