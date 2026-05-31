import hashlib
import json
import os
import random
import time

import numpy as np


DEFAULT_EMBEDDING_MODEL = "gemini-embedding-2"
DEFAULT_SIMILARITY_THRESHOLD = 0.68
MAX_RETRIES = 4


def _is_retryable_error(error):
    message = str(error).lower()
    return (
        "429" in message
        or "503" in message
        or "resource_exhausted" in message
        or "unavailable" in message
    )


def get_embedding(client, text, model=DEFAULT_EMBEDDING_MODEL):
    """Génère un vecteur d'embedding avec retry exponentiel."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            result = client.models.embed_content(
                model=model,
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as error:
            last_error = error
            if not _is_retryable_error(error) or attempt == MAX_RETRIES - 1:
                raise

            delay = (2 ** attempt) + random.uniform(0, 0.5)
            time.sleep(delay)

    raise last_error


def cosine_similarity(v1, v2):
    """Calcule une similarité cosinus sécurisée contre les vecteurs nuls."""
    vector_1 = np.array(v1, dtype=float)
    vector_2 = np.array(v2, dtype=float)

    norm_1 = np.linalg.norm(vector_1)
    norm_2 = np.linalg.norm(vector_2)

    if norm_1 == 0 or norm_2 == 0:
        return 0.0

    return float(np.dot(vector_1, vector_2) / (norm_1 * norm_2))


def _stable_cache_key(item):
    raw_value = "|".join([
        item.get("titre", ""),
        item.get("categorie", ""),
        item.get("priorite", ""),
        item.get("contenu", ""),
    ])
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


def _build_embedding_text(item):
    return "\n".join([
        f"Titre: {item.get('titre', '')}",
        f"Catégorie: {item.get('categorie', '')}",
        f"Priorité: {item.get('priorite', '')}",
        f"Procédure: {item.get('contenu', '')}",
    ])


class TicketRAG:
    def __init__(
        self,
        client,
        kb_path,
        threshold=DEFAULT_SIMILARITY_THRESHOLD,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
    ):
        self.client = client
        self.kb_path = kb_path
        self.threshold = threshold
        self.embedding_model = embedding_model
        self.cache_path = f"{kb_path}.embeddings.json"

        with open(kb_path, "r", encoding="utf-8") as file:
            self.knowledge_base = json.load(file)

        self.embedding_cache = self._load_embedding_cache()
        self._prepare_embeddings()
        self._save_embedding_cache()

    def _load_embedding_cache(self):
        if not os.path.exists(self.cache_path):
            return {}

        try:
            with open(self.cache_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_embedding_cache(self):
        with open(self.cache_path, "w", encoding="utf-8") as file:
            json.dump(self.embedding_cache, file, ensure_ascii=False, indent=2)

    def _prepare_embeddings(self):
        print("Chargement de la base de connaissances RAG...")

        for item in self.knowledge_base:
            cache_key = _stable_cache_key(item)

            if cache_key not in self.embedding_cache:
                self.embedding_cache[cache_key] = get_embedding(
                    self.client,
                    _build_embedding_text(item),
                    model=self.embedding_model,
                )

            item["embedding"] = self.embedding_cache[cache_key]

    def find_relevant_procedure(self, ticket_description):
        """Retourne la procédure la plus pertinente si elle dépasse le seuil configuré."""
        query_embedding = get_embedding(
            self.client,
            ticket_description,
            model=self.embedding_model,
        )

        best_score = -1.0
        best_procedure = None

        for item in self.knowledge_base:
            score = cosine_similarity(query_embedding, item["embedding"])

            if score > best_score:
                best_score = score
                best_procedure = item

        if best_procedure is None or best_score < self.threshold:
            return None

        procedure = {
            key: value
            for key, value in best_procedure.items()
            if key != "embedding"
        }
        procedure["score_similarite"] = round(best_score, 4)

        return procedure
