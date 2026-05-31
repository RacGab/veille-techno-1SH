# Architecture RAG

Le moteur RAG de TicketFlow sert à enrichir la demande envoyée à Gemini avec une procédure interne pertinente.
Son objectif est de donner au modèle un contexte opérationnel réel avant la classification du billet.

Depuis le Suivi 2, le moteur ne se limite plus à lire un fichier JSON en mémoire.
Il utilise maintenant des embeddings, un seuil de similarité, un cache local et une stratégie de retry pour rendre la récupération plus robuste.

---

## Rôle de `TicketRAG`

La classe `TicketRAG`, définie dans `src/rag_utils.py`, reçoit deux éléments principaux :

- un client Gemini initialisé avec `google-genai` ;
- le chemin vers `src/data/knowledge_base.json`.

Au démarrage, elle charge la base de connaissances, prépare les embeddings des procédures et les garde en mémoire pour les recherches suivantes.

Lorsqu'un billet est soumis à `POST /api/v1/triage`, la méthode `find_relevant_procedure()` :

1. génère un embedding pour la description du billet ;
2. compare cet embedding avec les procédures connues ;
3. calcule une similarité cosinus ;
4. retourne uniquement la procédure la plus pertinente si elle dépasse le seuil configuré.

---

## Base de connaissances

La base de connaissances est stockée dans `src/data/knowledge_base.json`.
Chaque entrée représente une procédure de soutien TI et contient notamment :

| Champ | Rôle |
| :--- | :--- |
| `titre` | Nom lisible de la procédure |
| `categorie` | Catégorie ITSM associée : `Accès`, `Matériel`, `Logiciel`, `Réseau` |
| `priorite` | Priorité recommandée selon le contexte |
| `contenu` | Procédure détaillée et symptômes associés |

Le texte vectorisé ne se limite pas au champ `contenu`.
Le moteur construit plutôt un texte enrichi avec le titre, la catégorie, la priorité et la procédure.
Cette approche améliore la précision du matching, car les métadonnées importantes participent aussi au calcul de similarité.

---

## Cache local des embeddings

Calculer les embeddings de toute la base de connaissances à chaque redémarrage est coûteux et ralentit le serveur.
TicketFlow génère donc un fichier de cache local à côté de la base de connaissances :

```text
src/data/knowledge_base.json.embeddings.json
```

Le cache associe chaque procédure à une clé stable calculée avec SHA-256.
Cette clé dépend du titre, de la catégorie, de la priorité et du contenu.

Conséquences :

- si une procédure ne change pas, son embedding est réutilisé ;
- si une procédure est modifiée, sa clé change et son embedding est recalculé ;
- le serveur évite de rappeler inutilement l'API Gemini au démarrage.

Ce fichier est généré automatiquement et ne doit pas être versionné.
Il est donc ignoré dans `.gitignore` avec :

```gitignore
/src/data/*.embeddings.json
```

---

## Seuil de similarité

Le moteur utilise un seuil de similarité par défaut :

```python
DEFAULT_SIMILARITY_THRESHOLD = 0.68
```

Ce seuil empêche le RAG de retourner une procédure simplement parce qu'elle est la moins mauvaise candidate.
Si le meilleur score est inférieur à `0.68`, aucune procédure n'est transmise à Gemini.

Cette décision réduit le risque d'hallucination guidée par un mauvais contexte.
Dans ce cas, le prompt indique plutôt qu'aucune procédure interne spécifique n'a été trouvée, et Gemini doit appliquer un jugement ITSM général.

Le score retenu est retourné dans la procédure sous la clé `score_similarite`.
Il est ensuite sauvegardé dans la table `RagHistory`, ce qui permet d'auditer la qualité du contexte récupéré.

---

## Similarité cosinus

La similarité cosinus mesure l'angle entre deux vecteurs :

- l'embedding de la description du billet ;
- l'embedding d'une procédure de la base de connaissances.

Un score plus proche de `1.0` indique une forte proximité sémantique.
Un score plus faible indique que le lien entre le billet et la procédure est moins fiable.

La fonction `cosine_similarity()` protège aussi contre les vecteurs nuls afin d'éviter une division par zéro.
Dans ce cas, elle retourne `0.0`.

---

## Exponential Backoff

Les appels à l'API Gemini peuvent échouer temporairement, surtout dans deux cas :

- `429 RESOURCE_EXHAUSTED` : quota ou limite de débit atteint ;
- `503 UNAVAILABLE` : service temporairement indisponible.

La fonction `get_embedding()` applique donc une stratégie de retry avec délai exponentiel.
Lorsqu'une erreur temporaire est détectée, le moteur attend avant de réessayer.

Le délai augmente à chaque tentative :

```text
1 seconde environ, puis 2, puis 4, puis 8
```

Un léger délai aléatoire est ajouté pour éviter que plusieurs requêtes réessaient exactement au même moment.
Après le nombre maximal de tentatives, l'erreur est relancée afin que l'application puisse la gérer proprement.

---

## Flux complet

Le fonctionnement actuel du RAG peut être résumé ainsi :

1. Chargement de `knowledge_base.json`.
2. Chargement du cache `.embeddings.json`, s'il existe.
3. Génération seulement des embeddings manquants.
4. Sauvegarde du cache mis à jour.
5. Réception d'une description de billet.
6. Génération de l'embedding du billet.
7. Comparaison avec les procédures par similarité cosinus.
8. Retour de la meilleure procédure seulement si le score est supérieur ou égal à `0.68`.
9. Sauvegarde du contexte RAG et du score dans la base SQLite.

Cette architecture reste simple pour un projet local, mais elle prépare la transition future vers une base vectorielle spécialisée si le volume de procédures ou de billets historiques augmente.
