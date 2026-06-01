# Interface Web

Le Suivi 3 ajoute une interface web directement intégrée à l'application Flask.
Cette interface transforme TicketFlow en outil utilisable par un technicien, sans devoir passer par Postman ou `curl`.

Le tableau de bord est accessible à l'adresse suivante lorsque le serveur Flask est lancé :

```text
http://127.0.0.1:5000/dashboard
```

La route racine `/` redirige aussi vers `/dashboard`.

---

## Séparation avec les Blueprints

La logique web est isolée dans le fichier `src/views.py` à l'aide d'un Blueprint Flask nommé `frontend`.

Cette séparation permet de distinguer deux responsabilités :

- `src/app.py` conserve les routes API, comme `POST /api/v1/triage` et `GET /api/v1/status` ;
- `src/views.py` gère les routes destinées à l'interface web, dont `GET /dashboard`.

Le Blueprint est enregistré dans l'application principale avec `app.register_blueprint(frontend)`.
Cette approche prépare le projet à une architecture plus modulaire, où l'API REST et l'interface technicien peuvent évoluer séparément.

---

## Rendu avec Jinja2 et Bootstrap 5

L'interface utilise les templates Jinja2 placés dans le dossier :

```text
src/templates/
```

Deux templates principaux structurent l'interface :

| Fichier | Rôle |
| :--- | :--- |
| `base.html` | Layout commun, CDN Bootstrap 5, barre de navigation et bloc de contenu |
| `dashboard.html` | Formulaire de soumission et tableau des billets triés |

Bootstrap 5 est utilisé pour accélérer la mise en forme :

- navbar sombre `TicketFlow ITSM` ;
- cartes pour séparer le formulaire et la liste des billets ;
- tableau responsive avec lignes alternées ;
- badges de couleur pour les priorités ;
- spinner de chargement pendant l'analyse IA.

---

## Fonctionnement du dashboard

La route `/dashboard` récupère les billets depuis SQLite avec SQLAlchemy.
Elle charge aussi les relations associées :

- `TriageResult` pour afficher la catégorie, la priorité et la justification IA ;
- `RagHistory` pour afficher la procédure RAG utilisée et son score de similarité.

Les billets sont triés du plus récent au plus ancien afin que le technicien voie immédiatement les demandes les plus récentes.

---

## Soumission asynchrone avec `fetch`

Le formulaire du dashboard ne recharge pas immédiatement la page.
Il utilise JavaScript et `fetch()` pour envoyer la description du billet à l'API interne :

```text
POST /api/v1/triage
```

Le flux est le suivant :

1. Le technicien saisit une description dans le champ texte.
2. JavaScript intercepte la soumission du formulaire.
3. Le bouton est désactivé pour éviter les doubles soumissions.
4. Un spinner Bootstrap est affiché.
5. La description est envoyée à `/api/v1/triage` en JSON.
6. Si l'API retourne `201 Created`, la page est rechargée pour afficher le nouveau billet.
7. En cas d'erreur, une alerte JavaScript affiche le message retourné par l'API.

Cette mécanique réutilise l'API REST existante au lieu de dupliquer la logique de triage côté interface.
Le dashboard devient donc un client interne de l'API TicketFlow.

---

## Gestion des fuseaux horaires

Les dates sont enregistrées côté backend en UTC afin de conserver une référence uniforme dans la base de données.

Dans le tableau, le backend expose la date de création en format ISO dans un attribut HTML :

```html
data-utc="2026-05-31T20:10:00Z"
```

Le navigateur lit ensuite cette valeur avec JavaScript, crée un objet `Date`, puis affiche la date avec `toLocaleString()`.
La conversion se fait donc automatiquement selon le fuseau horaire local du technicien.

Cette stratégie évite d'imposer un fuseau horaire côté serveur et améliore l'expérience si l'application est consultée depuis plusieurs postes ou régions.

---

## Navigation

La barre de navigation contient :

- un lien vers le dashboard via le titre `TicketFlow ITSM` ;
- un lien `Statut API` vers `/api/v1/status`, ouvert dans un nouvel onglet.

Le lien de statut permet de vérifier rapidement que l'API et le moteur RAG sont disponibles sans quitter le tableau de bord.
