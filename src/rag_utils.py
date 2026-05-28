import numpy as np
import json
import os

def get_embedding(client, text):
    """Génère un vecteur (embedding) pour un texte donné via Gemini."""
    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    return result.embeddings[0].values

def cosine_similarity(v1, v2):
    """Calcule la similarité entre deux vecteurs."""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

class TicketRAG:
    def __init__(self, client, kb_path):
        self.client = client
        with open(kb_path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)
        
        # Pré-calculer les embeddings de la base de connaissances
        # (Dans un vrai projet, on stockerait ça dans une base vectorielle)
        print("Chargement de la base de connaissances...")
        for item in self.knowledge_base:
            item['embedding'] = get_embedding(self.client, item['contenu'])

    def find_relevant_procedure(self, ticket_description):
        """Trouve la procédure la plus proche de la description du ticket."""
        query_embedding = get_embedding(self.client, ticket_description)
        
        best_score = -1
        best_procedure = None
        
        for item in self.knowledge_base:
            score = cosine_similarity(query_embedding, item['embedding'])
            if score > best_score:
                best_score = score
                best_procedure = item
        
        # On ne retourne la procédure que si elle est assez pertinente (> 0.6)
        return best_procedure if best_score > 0.6 else None
