# Suivi 01 : Cahier de recherche et documentation de base

**Projet :** TicketFlow - Automatisation ITSM via IA
**Étudiant :** Gabriel Racine
**Date :** 26 mai 2026

---

## 1. Documentation technique officielle

**1.1. Framework Web : Flask**
* **Lien :** https://flask.palletsprojects.com/
* **Résumé :** Documentation officielle du micro-framework Flask. Indispensable pour comprendre le routage (endpoints), la gestion des requêtes POST et le retour de réponses au format JSON.
* **Pertinence :** 10/10

**1.2. Intelligence Artificielle : Google GenAI SDK**
* **Lien :** https://github.com/googleapis/python-genai
* **Résumé :** Dépôt officiel et guide d'utilisation du nouveau SDK `google-genai`. Cette source remplace l'ancienne librairie obsolète et documente l'initialisation du client, la gestion de la clé API et la génération de contenu textuel.
* **Pertinence :** 10/10

**1.3. Gestion des variables d'environnement : Python-dotenv**
* **Lien :** https://pypi.org/project/python-dotenv/
* **Résumé :** Page du paquet permettant de charger les variables d'environnement depuis un fichier `.env`. Crucial pour sécuriser la clé API de Google et éviter de la publier sur GitHub.
* **Pertinence :** 8/10

---

## 2. Concepts et architectures (RAG & API)

**2.1. Comprendre le RAG (Retrieval-Augmented Generation)**
* **Lien :** https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation
* **Résumé :** Article explicatif d'IBM détaillant le fonctionnement de la génération augmentée par la recherche. Utile pour la rédaction du rapport final afin de justifier de manière théorique comment cette architecture limite les hallucinations du modèle et contextualise les réponses.
* **Pertinence :** 9/10

**2.2. Tutoriel : Création d'une API REST avec Flask**
* **Lien :** https://realpython.com/api-integration-in-python/
* **Résumé :** Guide technique exhaustif sur la création d'une architecture API robuste en Python. Permettra d'appliquer les bonnes pratiques de l'industrie pour structurer les routes et gérer les erreurs HTTP.
* **Pertinence :** 8/10

---

## 3. Médiagraphie provisoire (Format APA)

Google. (2024). *Google GenAI SDK for Python*. GitHub. Récupéré le 26 mai 2026, de https://github.com/googleapis/python-genai

IBM. (2023). *Qu'est-ce que la génération augmentée par la recherche (RAG) ?* IBM Topics. Récupéré le 26 mai 2026, de https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation

Pallets Projects. (2010). *Flask Documentation (3.0.x)*. Récupéré le 26 mai 2026, de https://flask.palletsprojects.com/

Real Python. (2023). *API Integration in Python*. Récupéré le 26 mai 2026, de https://realpython.com/api-integration-in-python/

Saurabh, K. (2020). *python-dotenv*. Python Package Index (PyPI). Récupéré le 26 mai 2026, de https://pypi.org/project/python-dotenv/