import os
import unicodedata
import json
from typing import Literal, Optional, Tuple, Any

from pydantic import BaseModel, Field
from groq import Groq
from .rag_utils import get_rag_engine

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
            "Gemini est temporairement indisponible à cause du quota. "
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
            "Gemini est temporairement indisponible à cause du quota. "
            "Un triage local approximatif a été produit à partir de mots-clés."
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
rag_engines = {
    "basic": {"engine": None, "error": None},
    "chroma": {"engine": None, "error": None},
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
