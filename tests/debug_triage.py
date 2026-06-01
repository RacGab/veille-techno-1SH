import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services import fallback_triage, normalize_text
from src.rag_utils import TicketRAGBasic

class MockClient:
    pass

def debug_triage():
    kb_path = 'src/data/knowledge_base.json'
    test_path = 'src/data/billets_test.json'

    # Note: RAG Engine Basic uses embedding. For this debug, we don't want to call Gemini API,
    # but the test_api script failed because of the fallback mechanism.
    # We will simulate the RAG retrieval if it failed by manually mapping them as the prompt did.
    
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb = json.load(f)
        
    with open(test_path, 'r', encoding='utf-8') as f:
        tickets = json.load(f)
        
    # Mapping based on similarity (simulated based on what the real code did)
    mapping = {
        "INC-1001": "Enrôlement mobile Intune ou appareil Samsung",
        "INC-1002": "Compte verrouillé Octopus ou Active Directory",
        "INC-1003": "Perte de connectivité réseau locale Wi-Fi ou Ethernet", # or VPN
        "INC-1004": "Erreur 500 sur application web métier",
        "INC-1005": "Périphérique défectueux écran clavier souris station d'accueil",
        "EDGE-2001": "Imprimante réseau indisponible ou file bloquée",
        "EDGE-2002": "VPN instable ou impossible à connecter", # The RAG will likely pick VPN first
        "EDGE-2003": "Réinitialisation de mot de passe et MFA",
        "EDGE-2004": "Application locale qui plante ou refuse de démarrer",
        "EDGE-2005": "Perte de connectivité réseau locale Wi-Fi ou Ethernet",
        "EDGE-2006": "Périphérique défectueux écran clavier souris station d'accueil",
        "EDGE-2007": "Perte de connectivité réseau locale Wi-Fi ou Ethernet",
        "EDGE-2008": "Réinitialisation de mot de passe et MFA",
        "EDGE-2009": "Périphérique défectueux écran clavier souris station d'accueil",
        "EDGE-2010": "Erreur 500 sur application web métier"
    }

    # Use the real fallback logic
    for ticket in tickets:
        procedure = next((p for p in kb if p['titre'] == mapping[ticket['id']]), None)
        result = fallback_triage(ticket['description'], procedure)
        print(f"[{ticket['id']}] Expected: {ticket['categorie_attendue']} | {ticket['priorite_attendue']} - Got: {result['categorie']} | {result['priorite']}")

if __name__ == '__main__':
    debug_triage()
