# Document de Support - Projet TicketFlow

**Cours :** Veille technologique (420-1SH-SW)  
**Étudiant :** Gabriel Racine  
**Date :** 5 juin 2026  
**Enseignant :** Nicolas Bourré  

---

## 1. Introduction
Dans les environnements informatiques modernes, les centres de services (ITSM) font face à un volume croissant de requêtes. Chaque jour, les techniciens doivent lire, catégoriser et prioriser manuellement des centaines de billets. Ce processus de triage, bien qu'essentiel, est chronophage, retarde la résolution des incidents critiques et augmente le risque d'erreur humaine, particulièrement en période de forte affluence. Le triage manuel est ainsi devenu un goulot d'étranglement majeur pour la productivité des équipes de support technique.

L'objectif de ce projet est de proposer une solution d'automatisation intelligente pour fluidifier ce processus et permettre aux experts de se concentrer sur la résolution technique plutôt que sur l'administration des billets.

## 2. Explication du projet
TicketFlow est un système de gestion d'incidents (ITSM) de bout en bout conçu pour éliminer le temps de triage manuel. En exploitant l'intelligence artificielle générative, le système automatise la classification et la priorisation des incidents dès leur soumission. 

Contrairement à un simple système de formulaires, TicketFlow analyse le langage naturel utilisé par le demandeur pour comprendre l'intention et l'urgence du problème. Cette approche permet non seulement de gagner du temps, mais aussi d'assurer une cohérence dans la catégorisation, souvent variable selon les techniciens. Le projet démontre comment des technologies de pointe comme les modèles de langage (LLM) et la recherche sémantique peuvent être intégrées de manière fiable dans une infrastructure d'entreprise classique (Flask/SQLite).

## 3. Explication des fonctionnalités

### 3.1 Moteur RAG (Retrieval-Augmented Generation)
L'innovation majeure de TicketFlow réside dans son moteur RAG. Pour éviter les "hallucinations" (réponses inventées) des modèles d'IA, chaque billet est comparé à une base de connaissances de procédures internes avant d'être traité. 

**Le processus technique se divise en trois étapes :**
1.  **Vectorisation (Embeddings)** : La description du ticket est transformée en un vecteur numérique représentant son sens sémantique.
2.  **Recherche de Similarité** : Le système calcule la similarité cosinus entre ce vecteur et ceux de la base de connaissances.
3.  **Augmentation du Prompt** : Si une procédure est trouvée avec un score de pertinence supérieur à 75 %, elle est injectée dans le contexte envoyé à l'IA.

Le système propose deux moteurs : **TicketRAGBasic** (en mémoire) et **TicketRAGChroma** (persistant via ChromaDB).

### 3.2 Architecture des données et Persistance
Pour assurer un suivi historique et une analyse post-triage, TicketFlow utilise une base de données **SQLite** gérée via l'ORM **SQLAlchemy**. L'architecture est structurée en trois modèles atomiques :
*   **Ticket** : Contient la description brute et l'horodatage UTC.
*   **RagHistory** : Enregistre quelle procédure a été consultée, son contenu exact au moment du triage et le score de similarité obtenu. Cela permet de justifier "pourquoi" l'IA a pris une décision.
*   **TriageResult** : Stocke la catégorie (Matériel, Logiciel, Réseau, Accès), la priorité et la justification générée.

### 3.3 Cascade de résilience (Fallback)
Pour garantir une disponibilité de 100 %, TicketFlow implémente un système de secours à trois niveaux :
1.  **Gemini 2.5 Flash** : Moteur principal via Google GenAI SDK.
2.  **Groq / Llama 3** : Moteur de secours ultra-rapide utilisé automatiquement en cas d'erreur de quota (HTTP 429) ou de latence réseau excessive de Gemini.
3.  **Algorithme local par mots-clés** : Un moteur de triage basé sur des règles déterministes et la normalisation de texte (NFC/NFKD), garantissant un service minimal même sans connexion internet.

### 3.4 Interface Web et Expérience Utilisateur
Développée avec **Flask Blueprints**, l'interface sépare strictement l'API REST du Frontend. Utilisant **Bootstrap 5**, elle offre :
*   **Tableau de Bord Technicien** : Permet de visualiser les billets en temps réel, de filtrer par priorité et de tester différents modèles d'IA.
*   **Soumission Asynchrone** : Utilisation de l'API `fetch()` pour une expérience fluide sans rechargement de page.
*   **Localisation des dates** : Les dates sont stockées en UTC et converties dynamiquement dans le fuseau horaire du navigateur via JavaScript (`toLocaleString`).

## 4. Conclusion
TicketFlow prouve que l'intégration de l'IA dans les processus d'affaires ne nécessite pas de compromis sur la fiabilité. En combinant des mécanismes de résilience et d'ancrage documentaire, le projet offre une solution robuste. Cette automatisation libère des ressources humaines précieuses et modernise l'approche traditionnelle du support informatique.

## 5. Médiagraphie (Format APA)

* Google. (2024). *Google GenAI SDK for Python*. GitHub. [https://github.com/googleapis/python-genai](https://github.com/googleapis/python-genai)
* IBM. (2023). *Qu'est-ce que la génération augmentée par la recherche (RAG) ?* IBM Topics. [https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation](https://www.ibm.com/fr-fr/topics/retrieval-augmented-generation)
* Pallets Projects. (2010). *Flask Documentation (3.1.x)*. [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
* Real Python. (2023). *API Integration in Python*. [https://realpython.com/api-integration-in-python/](https://realpython.com/api-integration-in-python/)
* Saurabh, K. (2020). *python-dotenv*. Python Package Index (PyPI). [https://pypi.org/project/python-dotenv/](https://pypi.org/project/python-dotenv/)
