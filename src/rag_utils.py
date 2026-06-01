import hashlib
import json
import os
import random
import time
import requests

import numpy as np

try:
    import chromadb
except ImportError:
    chromadb = None


DEFAULT_EMBEDDING_MODEL = "gemini-embedding-2"
HF_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_SIMILARITY_THRESHOLD = 0.68
DEFAULT_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "data", "chroma_db")
MAX_RETRIES = 4


def _is_retryable_error(error):
    message = str(error).lower()
    return (
        "429" in message
        or "503" in message
        or "resource_exhausted" in message
        or "unavailable" in message
    )


def get_embedding_hf(text, api_key):
    """Génère un vecteur d'embedding via Hugging Face Inference API (Fallback)."""
    api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": text, "options": {"wait_for_model": True}})
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429 or response.status_code >= 500:
                time.sleep((2 ** attempt) + random.uniform(0, 0.5))
                continue
            else:
                raise Exception(f"HF Error: {response.text}")
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep((2 ** attempt) + random.uniform(0, 0.5))
    return None


def get_embedding(client, text, model=DEFAULT_EMBEDDING_MODEL):
    """Génère un vecteur d'embedding avec retry exponentiel et fallback HF."""
    last_error = None
    provider = "gemini"
    
    # 1. Tentative Gemini
    if client:
        for attempt in range(MAX_RETRIES):
            try:
                result = client.models.embed_content(
                    model=model,
                    contents=text,
                )
                return result.embeddings[0].values, "gemini"
            except Exception as error:
                last_error = error
                if not _is_retryable_error(error) or attempt == MAX_RETRIES - 1:
                    break 

                delay = (2 ** attempt) + random.uniform(0, 0.5)
                time.sleep(delay)

    # 2. Fallback Hugging Face (si configuré)
    hf_key = os.environ.get("HUGGINGFACE_API_KEY")
    if hf_key and hf_key != "votre_cle_hf_ici":
        try:
            return get_embedding_hf(text, hf_key), "hf"
        except Exception as e:
            print(f"Échec fallback HF: {e}")

    if last_error:
        raise last_error
    raise Exception("Aucun moteur d'embedding disponible (Gemini/HF)")


def cosine_similarity(v1, v2):
    """Calcule une similarité cosinus sécurisée contre les vecteurs nuls."""
    vector_1 = np.array(v1, dtype=float)
    vector_2 = np.array(v2, dtype=float)

    if vector_1.shape != vector_2.shape:
        # Incompatibilité de dimension (ex: switch entre Gemini et HF)
        return 0.0

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


class TicketRAGBasic:
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
                vector, provider = get_embedding(
                    self.client,
                    _build_embedding_text(item),
                    model=self.embedding_model,
                )
                self.embedding_cache[cache_key] = vector

            item["embedding"] = self.embedding_cache[cache_key]

    def find_relevant_procedure(self, ticket_description):
        """Retourne la procédure la plus pertinente si elle dépasse le seuil configuré."""
        query_embedding, provider = get_embedding(
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


class TicketRAGChroma:
    def __init__(
        self,
        client,
        kb_path,
        threshold=DEFAULT_SIMILARITY_THRESHOLD,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
    ):
        if chromadb is None:
            raise RuntimeError(
                "ChromaDB n'est pas installé. Installez la dépendance 'chromadb' "
                "ou gardez USE_CHROMADB = False."
            )

        self.client = client
        self.kb_path = kb_path
        self.threshold = threshold
        self.embedding_model = embedding_model
        self.chroma_client = chromadb.PersistentClient(path=DEFAULT_CHROMA_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name="procedures_itsm",
            metadata={"hnsw:space": "cosine"},
        )

        self._sync_collection()

    def _load_knowledge_base(self):
        with open(self.kb_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _sync_collection(self):
        knowledge_base = self._load_knowledge_base()
        current_items = {
            _stable_cache_key(item): item
            for item in knowledge_base
        }

        existing_records = self.collection.get()
        existing_ids = set(existing_records.get("ids", []))
        current_ids = set(current_items.keys())
        stale_ids = list(existing_ids - current_ids)

        if stale_ids:
            self.collection.delete(ids=stale_ids)

        missing_ids = [
            item_id
            for item_id in current_ids
            if item_id not in existing_ids
        ]

        if not missing_ids:
            return

        ids = []
        metadatas = []
        documents = []
        embeddings = []

        print("Synchronisation de la collection ChromaDB RAG...")

        for item_id in missing_ids:
            item = current_items[item_id]
            ids.append(item_id)
            metadatas.append({
                "titre": item.get("titre", ""),
                "categorie": item.get("categorie", ""),
                "priorite": item.get("priorite", ""),
            })
            documents.append(item.get("contenu", ""))
            vector, provider = get_embedding(
                self.client,
                _build_embedding_text(item),
                model=self.embedding_model,
            )
            embeddings.append(vector)

        self.collection.add(
            ids=ids,
            metadatas=metadatas,
            documents=documents,
            embeddings=embeddings,
        )

    def find_relevant_procedure(self, ticket_description):
        """Retourne la procédure ChromaDB la plus pertinente si elle dépasse le seuil."""
        query_embedding, provider = get_embedding(
            self.client,
            ticket_description,
            model=self.embedding_model,
        )

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=1,
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents or not metadatas or not distances:
            return None

        score = 1 - distances[0]

        if score < self.threshold:
            return None

        metadata = metadatas[0]

        return {
            "titre": metadata.get("titre", ""),
            "categorie": metadata.get("categorie", ""),
            "priorite": metadata.get("priorite", ""),
            "contenu": documents[0],
            "score_similarite": round(score, 4),
        }


TicketRAG = TicketRAGBasic


def get_rag_engine(client, kb_path, use_chroma=False, threshold=DEFAULT_SIMILARITY_THRESHOLD):
    if use_chroma:
        return TicketRAGChroma(client, kb_path, threshold=threshold)

    return TicketRAGBasic(client, kb_path, threshold=threshold)
