# Structure du Projet

Ce document explique le rôle de chaque fichier et dossier clé dans l'architecture du projet TicketFlow.

## Racine du projet

*   **`run.py`** : Point d'entrée principal. C'est le script que l'on exécute (`python run.py`) pour démarrer le serveur de développement Flask.
*   **`requirements.txt`** : Liste de toutes les bibliothèques Python nécessaires au projet (Flask, Google GenAI, Groq, ChromaDB, SQLAlchemy, etc.).
*   **`.env`** : Fichier (non versionné) contenant les secrets et la configuration locale (Clés API Gemini, Groq, Hugging Face, et jeton administrateur).
*   **`.gitignore`** : Indique à Git quels fichiers ne doivent pas être envoyés sur le dépôt (ex: bases de données SQLite, clés API, environnements virtuels).
*   **`mkdocs.yml`** : Fichier de configuration si l'on souhaite générer un site web statique pour la documentation avec MkDocs.
*   **`README.md`** : La proposition initiale du projet de veille technologique.

## Dossier `src/` (Code source)

C'est le cœur de l'application web, structurée avec le patron *Application Factory* et des *Blueprints* Flask.

*   **`__init__.py`** : Instancie l'application Flask, configure la base de données et enregistre les différentes routes (API et Frontend).
*   **`extensions.py`** : Sépare l'initialisation des extensions (SQLAlchemy pour la BDD, Migrate pour les migrations) pour éviter les dépendances circulaires.
*   **`models.py`** : Définit la structure des tables de la base de données (modèles `Ticket`, `RagHistory`, `TriageResult`).
*   **`services.py`** : Contient la logique d'affaires ("Business Logic") :
    *   Validation Pydantic (`TriageResponse`).
    *   Triage LLM alternatif avec **Groq** (`groq_triage`).
    *   Triage algorithmique local (`fallback_triage`) en cas de panne totale des IA.
*   **`rag_utils.py`** : Gère les moteurs de recherche sémantique (RAG) :
    *   `get_embedding` : Génère les vecteurs (avec Gemini en priorité, ou Hugging Face en secours).
    *   `TicketRAGBasic` : Moteur de recherche en mémoire avec similarité cosinus.
    *   `TicketRAGChroma` : Moteur de recherche avec la base vectorielle persistante ChromaDB.

### Sous-dossiers de `src/`

*   **`api/`** : Logique de l'API REST.
    *   `routes.py` : Expose les points de terminaison (`/api/v1/triage`, `/api/v1/status`, `/api/v1/tickets`). C'est ici qu'est orchestré le flux de triage (Gemini -> Groq -> Local).
*   **`frontend/`** : Logique de l'interface graphique.
    *   `routes.py` : Expose la route `/dashboard` pour les techniciens.
*   **`templates/`** : Fichiers HTML (rendus avec Jinja2).
    *   `base.html` : Squelette principal de la page web (Menu, CSS Bootstrap).
    *   `dashboard.html` : L'interface principale contenant le formulaire de soumission et le tableau des résultats.
*   **`data/`** : Fichiers de données et de connaissances.
    *   `knowledge_base.json` : Le "cerveau" du RAG. Contient les procédures ITSM de référence.
    *   `billets_test.json` : Données de test utilisées par les scripts de validation.
    *   `chroma_db/` *(généré)* : Dossier où ChromaDB sauvegarde sa base vectorielle.

## Autres dossiers

*   **`docs/`** : Documentation technique détaillée au format Markdown.
*   **`migrations/`** : Contient l'historique des modifications de la structure de la base de données, généré automatiquement par Flask-Migrate (Alembic).
*   **`tests/`** : Scripts isolés pour valider le bon fonctionnement du système.
    *   `test_api.py` : Soumet tous les `billets_test.json` à l'API en marche pour calculer le taux de succès du triage IA.
    *   `debug_triage.py` : Script utilitaire pour tester la logique locale (mots-clés) hors connexion.
*   **`instance/`** *(généré)* : Dossier par défaut où Flask sauvegarde la base de données locale (`ticketflow.db`).
*   **`venv/`** *(généré)* : Dossier contenant l'environnement virtuel Python (les bibliothèques isolées).