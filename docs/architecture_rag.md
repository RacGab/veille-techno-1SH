# 🧠 Architecture Avancée d'un Système RAG Robuste

Pour passer d'un MVP ("Naive RAG") à un système de triage ITSM fiable en production, il est nécessaire d'implémenter des mécanismes d'auto-correction et d'utiliser une infrastructure de données spécialisée. 

Ce document synthétise les meilleures pratiques de l'industrie pour la conception d'un tel système.

---

## 1. La Fondation : Base de Données Vectorielle et Indexation

Le succès d'un RAG repose à 80% sur la qualité de la récupération des données (Retrieval). Si l'IA reçoit de mauvais documents, elle hallucine ou se trompe.

### Bases de données vectorielles (Vector DBs)
Pour un environnement de production, une simple liste Python ou un fichier JSON en mémoire n'est pas viable. Il faut une base de données optimisée pour la recherche par similarité cosinus ou euclidienne.
*   **Options populaires :** **Pinecone** (Cloud managé, facile), **Qdrant** (Open source, très rapide en Rust), **ChromaDB** (Excellent pour le développement local et Python), ou **Weaviate**.
*   **L'approche hybride :** Les meilleurs RAG utilisent une recherche hybride. Ils combinent la recherche sémantique (Dense Retrieval - sens du texte) avec la recherche par mots-clés (Sparse Retrieval - BM25). Cela permet de trouver un ticket "d'écran noir" (sémantique) mais de ne pas rater le ticket mentionnant le code d'erreur exact "ERR-9001" (mot-clé).

### Algorithmes de Chunking (Découpage)
Il ne faut pas injecter des documents entiers dans le vecteur. Le texte doit être découpé intelligemment.
*   **Semantic Chunking :** Au lieu de couper arbitrairement tous les 500 mots, on découpe par paragraphes ou sections logiques pour ne pas briser le contexte.
*   **Enrichissement par Métadonnées :** Chaque chunk (morceau de texte) doit être accompagné de métadonnées (ex: `{"source": "SOP_Reseau", "date": "2025", "categorie": "Critique"}`). Cela permet de filtrer la recherche vectorielle *avant* de calculer la similarité, augmentant drastiquement la précision et la vitesse.

---

## 2. Le RAG Auto-Correcteur : CRAG et Self-RAG

Un "Naive RAG" récupère des documents et force l'IA à répondre avec, même s'ils sont hors sujet. Les architectures modernes sont "Agentiques" : elles évaluent et se corrigent.

### A. CRAG (Corrective Retrieval Augmented Generation)
Le CRAG ajoute un "évaluateur" entre la recherche et la génération.
1.  **Recherche :** Le système cherche dans la Vector DB.
2.  **Évaluation (Retrieval Evaluator) :** Un modèle léger note les documents trouvés comme *Corrects*, *Incorrects* ou *Ambigus*.
3.  **Action :**
    *   Si *Correct* : L'IA génère la réponse.
    *   Si *Incorrect* : Le système déclenche un plan de secours (fallback), comme faire une recherche Web ou chercher dans une base d'archives lointaine, puis tente de répondre.
    *   Si *Ambigu* : Il combine les connaissances internes avec des recherches externes.

### B. Self-RAG (Self-Reflective RAG)
Le Self-RAG est une approche où l'IA génère des "jetons de réflexion" (Reflection Tokens) pendant son processus pour s'autocritiquer.
1.  **Critique de la pertinence (`IsSup`) :** L'IA vérifie si les documents qu'on lui fournit sont vraiment pertinents par rapport au ticket soumis.
2.  **Critique de la génération (`IsUseful`) :** Avant de renvoyer le résultat final à l'utilisateur, l'IA vérifie si sa propre réponse résout réellement le ticket de départ sans halluciner.
3.  **Boucle de correction :** Si l'IA réalise que sa réponse n'est pas soutenue par les documents, elle peut demander au système de relancer une nouvelle recherche vectorielle reformulée.

---

## 3. Évaluation : La Triade du RAG

Pour s'assurer que le système TicketFlow s'améliore et reste fiable, il faut monitorer trois métriques clés (souvent via des frameworks comme **RAGAS** ou **TruLens**) :

1.  **Faithfulness (Fidélité) :** La réponse est-elle issue *uniquement* de la base de connaissances fournie ? (Le taux d'hallucination doit être à 0%).
2.  **Answer Relevance (Pertinence) :** La catégorie et la priorité générées ont-elles un sens par rapport à la description du ticket ?
3.  **Context Precision (Précision du contexte) :** Les procédures remontées par la Vector DB étaient-elles les bonnes ?

---

### Résumé pour l'implémentation de TicketFlow
Pour notre MVP, nous commencerons avec un **Naive RAG** (recherche sémantique simple en mémoire via Numpy) pour prouver le concept d'interaction avec Gemini. Cependant, l'architecture finale documentée dans notre projet devra viser une structure **CRAG** avec **ChromaDB** pour gérer les milliers de tickets historiques d'un vrai centre de services sans perdre en précision.
