# 🔍 Cahier de recherche et documentation approfondie (Suivi 01)

Ce document détaille les recherches technologiques et théoriques effectuées pour le projet TicketFlow. L'analyse a été approfondie en consultant directement les documentations techniques et les guides d'architecture.

---

## 1. Documentation technique : Outils de développement

### 🌐 Framework Web : Flask (3.1.x)
*   **Source :** [Flask Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/)
*   **Concepts clés pour TicketFlow :**
    *   **Routage avancé :** Utilisation des décorateurs `@app.post('/triage')` pour une gestion sémantique des requêtes. Le routage dynamique permettrait à terme de gérer des ressources spécifiques (ex: `/ticket/<id>`).
    *   **Gestion des données JSON :** L'objet `request.get_json()` est la méthode recommandée pour extraire les descriptions de tickets envoyées de manière structurée.
    *   **Réponses automatisées :** Flask transforme nativement les dictionnaires Python en objets JSON, ce qui facilite l'envoi des résultats de l'IA (catégorie, priorité, score de confiance).
    *   **Codes de statut HTTP :** Importance d'utiliser `201 Created` pour un triage réussi et `400 Bad Request` ou `422 Unprocessable Entity` pour des entrées invalides.

### 🤖 Intelligence Artificielle : Google GenAI SDK
*   **Source :** [Google Gen AI Python SDK (GitHub)](https://github.com/googleapis/python-genai)
*   **Fonctionnalités retenues :**
    *   **Client unifié :** Utilisation de `genai.Client(api_key=...)`. Le SDK supporte également Vertex AI pour des besoins "Enterprise" (sécurité accrue).
    *   **Contrôle du format de sortie (Structured Output) :** Possibilité de forcer le modèle à répondre en JSON pur via le paramètre `response_mime_type: 'application/json'`, ce qui élimine le besoin de parseurs complexes.
    *   **Modèle Gemini 2.5 Flash :** Choisi pour son excellent rapport vitesse/coût, idéal pour une application de triage en temps réel.
    *   **Function Calling :** Potentiel futur pour permettre à l'IA d'interroger des bases de données de noms d'utilisateurs ou de statuts de serveurs avant de décider de la priorité.

---

## 2. Architecture et concepts théoriques

### 🧠 RAG : Retrieval-Augmented Generation
*   **Source :** [IBM - Qu'est-ce que le RAG ?](https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation)
*   **Analyse pour le projet :**
    *   **Problématique des Hallucinations :** Les modèles de langage peuvent inventer des solutions. Le RAG résout ce problème en ancrant la réponse dans une base de connaissances externe (ex: base de connaissances ITSM ou historique des tickets).
    *   **Processus technique :** Conversion des documents en *embeddings* (vecteurs), stockage dans une base vectorielle, puis récupération des segments les plus pertinents pour enrichir le "prompt" envoyé à Gemini.
    *   **Avantages opérationnels :** Permet au système de citer ses sources (ex: "Procédure basée sur la documentation SOP-042"), ce qui est crucial pour la confiance des techniciens de support.

### 🏗️ Architecture d'API REST
*   **Source :** [Real Python - API Integration](https://realpython.com/api-integration-in-python/)
*   **Bonnes pratiques intégrées :**
    *   **Dénomination des ressources :** Utilisation de noms au pluriel (ex: `/api/v1/incidents`).
    *   **Versionnage :** Préfixer les routes par `/v1/` pour assurer la pérennité de l'API lors de changements majeurs de modèles d'IA.
    *   **Gestion d'erreurs descriptive :** Ne pas se contenter d'un code erreur, mais renvoyer un objet JSON expliquant *pourquoi* la requête a échoué (ex: champ 'description' manquant).

---

## 3. Médiagraphie (Format APA)

* Google. (2024). *Google GenAI SDK for Python*. GitHub. [https://github.com/googleapis/python-genai](https://github.com/googleapis/python-genai)
* IBM. (2023). *Qu'est-ce que la génération augmentée par la recherche (RAG) ?* IBM Topics. [https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation](https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation)
* Pallets Projects. (2010). *Flask Documentation (3.1.x)*. [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
* Real Python. (2023). *API Integration in Python*. [https://realpython.com/api-integration-in-python/](https://realpython.com/api-integration-in-python/)
* Saurabh, K. (2020). *python-dotenv*. Python Package Index (PyPI). [https://pypi.org/project/python-dotenv/](https://pypi.org/project/python-dotenv/)
