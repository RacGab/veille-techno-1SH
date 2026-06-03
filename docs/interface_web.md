# Interface Web

Le projet propose une interface web complète directement intégrée à l'application Flask, remplaçant la nécessité d'utiliser Postman ou `curl`.

L'interface offre désormais une expérience séparée selon le rôle de l'utilisateur :

- **Page d'accueil (`/`)** : Choix du portail.
- **Portail Demandeur (`/portail`)** : Formulaire épuré pour la soumission de billets sans métadonnées superflues.
- **Dashboard Technicien (`/dashboard`)** : Vue globale des billets triés et options avancées (sélection de l'IA, moteur RAG).

---

## Séparation avec les Blueprints

La logique web est isolée dans le fichier `src/frontend/routes.py` à l'aide d'un Blueprint Flask nommé `frontend`.

Cette séparation permet de distinguer deux responsabilités :

- `src/api/routes.py` conserve les routes API, comme `POST /api/v1/triage` et `GET /api/v1/status` ;
- `src/frontend/routes.py` gère les routes destinées à l'interface web (`/`, `/portail`, `/dashboard`).

Le Blueprint est enregistré dans l'application principale avec `app.register_blueprint(frontend_bp)`.
Cette approche prépare le projet à une architecture plus modulaire, où l'API REST et l'interface utilisateur peuvent évoluer séparément.

---

## Rendu avec Jinja2 et Bootstrap 5

L'interface utilise les templates Jinja2 placés dans le dossier :

```text
src/templates/
```

Quatre templates principaux structurent l'interface :

| Fichier | Rôle |
| :--- | :--- |
| `base.html` | Layout commun, CDN Bootstrap 5, barre de navigation globale et bloc de contenu |
| `landing.html` | Page d'accueil présentant les deux points d'accès |
| `portail.html` | Formulaire simplifié pour les demandeurs (retour d'informations ciblé) |
| `dashboard.html` | Formulaire avancé et tableau des billets triés pour les techniciens |

Bootstrap 5 est utilisé pour accélérer la mise en forme (composants responsifs, spinners, alertes).

---

## Fonctionnement du dashboard technicien

La route `/dashboard` récupère les billets depuis SQLite avec SQLAlchemy.
Elle charge aussi les relations associées :

- `TriageResult` pour afficher la catégorie, la priorité et la justification ;
- `RagHistory` pour afficher la procédure RAG utilisée et son score de similarité.

Les billets sont triés du plus récent au plus ancien.

---

## Soumission asynchrone avec `fetch`

Les formulaires du portail et du dashboard ne rechargent pas immédiatement la page.
Ils utilisent JavaScript et `fetch()` pour envoyer la description du billet à l'API interne :

```text
POST /api/v1/triage
```

Le flux est le suivant :

1. L'utilisateur saisit une description dans le champ texte.
2. JavaScript intercepte la soumission du formulaire et affiche un spinner Bootstrap.
3. La requête est envoyée à `/api/v1/triage` en JSON de manière asynchrone.
4. Si le triage (effectué dans une transaction SQLite atomique) réussit et retourne `201 Created` :
   - Le dashboard se recharge pour afficher le nouveau billet.
   - Le portail demandeur masque le formulaire et affiche le résultat du triage à la place.
5. En cas d'erreur, une alerte JavaScript affiche le message retourné par l'API sans casser l'expérience utilisateur.

---

## Sélection de l'IA et du moteur RAG (Dashboard)

Le dashboard permet de manipuler les requêtes manuellement pour tester l'API :

- **Sélection IA** : Possibilité de forcer l'usage de Gemini, Groq, ou de se replier sur l'algorithmique local pur (Sans IA). Le backend inclut une validation stricte de ces paramètres.
- **Moteur vectoriel** : Possibilité d'activer ChromaDB au lieu du moteur RAG en mémoire (Basic).

Un mécanisme de cache avec un délai de 5 minutes (retry automatique) a été mis en place pour éviter qu'une erreur de réseau initiale ne bloque définitivement les moteurs RAG.

---

## Gestion adaptative des fuseaux horaires

Les dates sont enregistrées côté backend en UTC strict.

Dans le tableau HTML, le backend génère la date de création avec le format ISO exact incluant le suffixe UTC `Z` :

```html
data-utc="2026-06-03T17:35:27Z"
```

Le navigateur lit ensuite cette valeur avec JavaScript, crée un objet `Date` natif, puis affiche la date avec `toLocaleString()`.
La conversion s'effectue automatiquement selon le fuseau horaire local de la machine de la personne consultant la page.

---

## Navigation

La barre de navigation globale (`base.html`) permet de se déplacer entre :

- L'Accueil
- Le Portail
- Le Dashboard
- Le statut de l'API (ouvert dans un nouvel onglet)
