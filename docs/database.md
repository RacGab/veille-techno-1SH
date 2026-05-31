# Architecture des données

Le Suivi 2 de TicketFlow transforme le MVP initial en une application persistante.
Au lieu de traiter un billet uniquement en mémoire, l'API sauvegarde maintenant les billets soumis, le contexte RAG utilisé et le résultat de triage généré par Gemini.

Cette évolution permet de conserver un historique exploitable pour l'analyse, le débogage, l'amélioration du système RAG et les futures interfaces de consultation.

---

## Technologies utilisées

La persistance repose sur les outils suivants :

- **SQLite** : base de données locale utilisée en développement.
- **Flask-SQLAlchemy** : ORM permettant de manipuler les tables avec des modèles Python.
- **Flask-Migrate** : intégration d'Alembic pour versionner l'évolution du schéma de base de données.

La base SQLite est générée localement dans le dossier `instance/`, qui ne doit pas être versionné dans Git.

---

## Modèle `Ticket`

Le modèle `Ticket` représente le billet soumis par un utilisateur ou un technicien.

Champs principaux :

| Champ | Description |
| :--- | :--- |
| `id` | Identifiant unique du billet |
| `description` | Texte brut soumis à l'API |
| `statut` | État du billet, par exemple `Nouveau` |
| `date_creation` | Date de création du billet |
| `date_modification` | Date de dernière modification |

Chaque appel valide à la route `POST /api/v1/triage` crée d'abord un objet `Ticket`.
Ce premier enregistrement est effectué immédiatement afin de générer une clé primaire utilisée par les autres tables.

---

## Modèle `RagHistory`

Le modèle `RagHistory` conserve le contexte récupéré par le système RAG.

Champs principaux :

| Champ | Description |
| :--- | :--- |
| `id` | Identifiant unique de l'entrée RAG |
| `ticket_id` | Clé étrangère vers le billet associé |
| `contexte_retrouve` | Contenu de la procédure ou connaissance retrouvée |
| `source` | Titre ou source de la procédure |
| `score_similarite` | Float : score de pertinence cosinus entre la description du billet et la procédure trouvée |
| `categorie_reference` | Catégorie associée au contexte retrouvé |
| `priorite_reference` | Priorité associée au contexte retrouvé |
| `date_creation` | Date de création de l'entrée |

Cette table permet de savoir si l'IA a été influencée par une procédure interne, par exemple une procédure liée à un verrouillage de compte ou à un accès réseau.

---

## Modèle `TriageResult`

Le modèle `TriageResult` représente la réponse produite par Gemini après l'analyse du billet.

Champs principaux :

| Champ | Description |
| :--- | :--- |
| `id` | Identifiant unique du résultat |
| `ticket_id` | Clé étrangère vers le billet associé |
| `categorie` | Catégorie assignée : `Matériel`, `Logiciel`, `Réseau`, `Accès` |
| `priorite` | Priorité assignée : `Faible`, `Moyen`, `Élevé`, `Critique` |
| `justification` | Justification générée par l'IA |
| `tokens_utilises` | Nombre de tokens utilisés, si disponible |
| `modele_ia` | Modèle utilisé, par défaut `gemini-2.5-flash` |
| `date_creation` | Date de création du résultat |

La relation entre `Ticket` et `TriageResult` est de type un-à-un : un billet possède un résultat de triage IA.

---

## Flux de persistance

Lorsqu'un client appelle `POST /api/v1/triage`, l'API effectue maintenant les étapes suivantes :

1. Lecture et validation du champ `description`.
2. Création immédiate d'un `Ticket` en base de données.
3. Recherche d'un contexte pertinent avec le système RAG.
4. Sauvegarde d'un `RagHistory` si une procédure est trouvée.
5. Appel au modèle Gemini 2.5 Flash.
6. Sauvegarde du `TriageResult`.
7. Retour de la réponse JSON au client avec le `ticket_id` dans les métadonnées.

Chaque étape d'écriture utilise une gestion d'erreur avec `try/except`.
En cas d'échec lors d'une transaction, `db.session.rollback()` est appelé pour éviter de laisser la session SQLAlchemy dans un état invalide.

---

## Initialisation des migrations

Pour initialiser la base de données sur un poste de développement, exécuter les commandes suivantes depuis la racine du projet :

```powershell
cd src
$env:FLASK_APP = "app.py"
.\venv\Scripts\flask.exe db init
.\venv\Scripts\flask.exe db migrate -m "create ticketflow core tables"
.\venv\Scripts\flask.exe db upgrade
cd ..
```

Après ces commandes, Flask-Migrate crée le dossier `migrations/` et SQLite génère la base locale dans `instance/ticketflow.db`.

---

## Bonnes pratiques Git

Les fichiers suivants ne doivent pas être versionnés :

```gitignore
/src/instance/
*.db
```

Le dossier `migrations/`, lui, doit être versionné afin que les autres développeurs puissent reproduire le schéma de base de données.
