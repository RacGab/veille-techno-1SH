# Architecture RAG

Le moteur RAG de TicketFlow sert à enrichir la demande envoyée à Gemini avec une procédure interne pertinente.
Son objectif est de donner au modèle un contexte opérationnel réel avant la classification du billet.

Depuis le Suivi 3, l'application ne dépend plus d'un seul moteur RAG.
Elle utilise une architecture multi-moteurs basée sur le patron de conception **Stratégie**, avec un moteur léger en mémoire et un moteur vectoriel persistant.

---

## Patron Stratégie et Factory

Le fichier `src/rag_utils.py` expose une fonction de création :

```python
get_rag_engine(client, kb_path, use_chroma=False, threshold=0.68)
```

Cette fonction agit comme une **Factory**.
Elle masque le détail d'instanciation du moteur RAG et retourne une stratégie compatible avec l'interface attendue par l'application.

Les deux moteurs implémentent la même méthode principale :

```python
find_relevant_procedure(ticket_description)
```

Cette méthode retourne soit `None`, soit un dictionnaire contenant la procédure trouvée :

```python
{
    "titre": "...",
    "categorie": "...",
    "priorite": "...",
    "contenu": "...",
    "score_similarite": 0.82
}
```

Cette uniformité permet à `src/app.py` de changer de moteur sans modifier la logique de triage, de sauvegarde en base ou de génération du prompt Gemini.

---

## Moteur `TicketRAGBasic`

`TicketRAGBasic` correspond au moteur historique de TicketFlow.
Il repose sur :

- `src/data/knowledge_base.json` pour les procédures ITSM ;
- Gemini Embeddings pour vectoriser les procédures et les billets ;
- NumPy pour calculer la similarité cosinus en mémoire ;
- un cache local `.embeddings.json` pour éviter de recalculer les vecteurs à chaque redémarrage.

Ce moteur est simple, rapide à comprendre et très léger.
Il demeure utile comme fallback local, pour les démonstrations rapides, les tests hors architecture vectorielle complète ou les environnements où ChromaDB n'est pas disponible.

---

## Moteur `TicketRAGChroma`

`TicketRAGChroma` ajoute une vraie base de données vectorielle locale avec ChromaDB.

ChromaDB est utilisé pour préparer TicketFlow à un volume plus important de procédures ou d'historiques de billets.
Contrairement au moteur Basic, les vecteurs ne vivent pas seulement dans une liste Python en mémoire.
Ils sont persistés sur disque dans :

```text
src/data/chroma_db/
```

Ce dossier est ignoré par Git, car il s'agit d'un artefact local généré automatiquement.

Au démarrage, le moteur ChromaDB :

1. ouvre un client persistant avec `chromadb.PersistentClient(...)` ;
2. crée ou récupère la collection `procedures_itsm` ;
3. vérifie si la collection est vide ;
4. si nécessaire, lit `knowledge_base.json` ;
5. génère les embeddings avec la fonction commune `get_embedding()` ;
6. insère les documents, métadonnées et embeddings dans ChromaDB.

Les métadonnées conservées dans ChromaDB incluent :

| Métadonnée | Rôle |
| :--- | :--- |
| `titre` | Nom de la procédure |
| `categorie` | Catégorie ITSM recommandée |
| `priorite` | Priorité recommandée |

Le contenu de la procédure est stocké comme document.

---

## Métrique cosinus

La collection ChromaDB est créée avec la configuration suivante :

```python
metadata={"hnsw:space": "cosine"}
```

Ce choix est important : il aligne ChromaDB sur la même logique mathématique que le moteur Basic.

Le moteur Basic calcule directement une similarité cosinus avec NumPy.
ChromaDB, lui, retourne une distance.
Pour conserver un score comparable, TicketFlow transforme cette distance en score :

```python
score = 1 - distance
```

Cette stratégie réduit le risque de régression lors du passage d'un moteur à l'autre.
Un score élevé garde le même sens : plus il est proche de `1.0`, plus la procédure est pertinente.

---

## Seuil de similarité

Les deux moteurs utilisent le même seuil par défaut :

```python
DEFAULT_SIMILARITY_THRESHOLD = 0.68
```

Ce seuil empêche le RAG de retourner une procédure simplement parce qu'elle est la moins mauvaise candidate.
Si le meilleur score est inférieur à `0.68`, aucune procédure n'est transmise à Gemini.

Cette décision réduit le risque d'hallucination guidée par un mauvais contexte.
Dans ce cas, le prompt indique qu'aucune procédure interne spécifique n'a été trouvée, et Gemini applique un jugement ITSM général.

---

## Basculement dynamique depuis le dashboard

Le tableau de bord expose un interrupteur Bootstrap :

```text
Activer le moteur vectoriel ChromaDB
```

Ce switch permet au technicien de choisir le moteur RAG pour chaque requête, sans redémarrer le serveur.

Lorsque le formulaire est soumis, le JavaScript envoie le paramètre suivant à l'API :

```json
{
  "description": "...",
  "use_chroma": true
}
```

La route `POST /api/v1/triage` sélectionne ensuite le moteur en mémoire :

- `use_chroma: false` utilise `TicketRAGBasic` ;
- `use_chroma: true` utilise `TicketRAGChroma`.

Les deux moteurs coexistent donc en mémoire.
Cette approche permet de comparer les résultats pendant une démonstration et de prouver que l'architecture est flexible sans redéploiement ni redémarrage.

Pour rendre le choix visible dans le tableau, la source RAG sauvegardée est préfixée avec le moteur utilisé, par exemple :

```text
[Basic] VPN instable ou impossible à connecter
[Chroma] VPN instable ou impossible à connecter
```

---

## Cache local des embeddings

Le moteur Basic conserve un cache local à côté de la base de connaissances :

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

La base ChromaDB est aussi ignorée :

```gitignore
/src/data/chroma_db/
```

---

## Exponential Backoff

Les appels à l'API Gemini peuvent échouer temporairement, surtout dans deux cas :

- `429 RESOURCE_EXHAUSTED` : quota ou limite de débit atteint ;
- `503 UNAVAILABLE` : service temporairement indisponible.

La fonction commune `get_embedding()` applique une stratégie de retry avec délai exponentiel.
Lorsqu'une erreur temporaire est détectée, le moteur attend avant de réessayer.

Le délai augmente à chaque tentative :

```text
1 seconde environ, puis 2, puis 4, puis 8
```

Un léger délai aléatoire est ajouté pour éviter que plusieurs requêtes réessaient exactement au même moment.
Après le nombre maximal de tentatives, ou en cas d'erreur de permission (`403`), l'erreur est relancée. 
Cependant, l'API intercepte cette erreur silencieusement pour éviter de planter l'application. La procédure RAG devient simplement "vide", ce qui permet au système de triage de secours (IA via **Groq** ou mots-clés) de s'exécuter de façon transparente.

---

## Flux complet

Le fonctionnement actuel du RAG peut être résumé ainsi :

1. Le serveur initialise paresseusement les moteurs `TicketRAGBasic` et `TicketRAGChroma`.
2. Le dashboard soumet un billet à `POST /api/v1/triage`.
3. Le paramètre `use_chroma` indique le moteur souhaité, et `ai_provider` indique le modèle IA (Auto, Gemini, Groq).
4. L'API sélectionne la stratégie RAG correspondante.
5. Le moteur génère l'embedding du billet avec Gemini (si disponible).
6. Le moteur cherche la procédure la plus proche.
7. Le score est comparé au seuil `0.68`.
8. Si une procédure est pertinente, elle enrichit le prompt.
9. L'IA analyse le prompt :
    *   **Gemini** (Priorité 1)
    *   **Groq Llama 3** (Fallback 1 - si Gemini échoue)
    *   **Algorithme Mots-clés** (Fallback 2 - si l'IA échoue)
10. Le contexte RAG, la source, le score et le résultat IA sont sauvegardés dans SQLite.

Cette architecture conserve la simplicité du MVP tout en préparant TicketFlow à une recherche vectorielle plus scalable et garantit une disponibilité à 100% grâce à ses mécanismes de secours dynamiques.
