# TicketFlow : Automatisation ITSM via IA

**Projet de Veille technologique (420-1SH-SW)** **Réalisé par :** Gabriel Racine  

Ce dépôt fait office de base de connaissances et de code source pour le développement d'une application de triage intelligent automatisant la classification des incidents informatiques.
Le projet expose une API REST et un tableau de bord web destiné aux techniciens.

---

# 📚 Base de connaissances

Voici les liens vers la documentation du projet :

* **[Cahier de recherche (Suivi 01)](recherche.md)**
* **[Architecture RAG](architecture_rag.md)**
* **[Architecture des données](database.md)**
* **[Interface Web](interface_web.md)**

---

## 🛠️ Installation initiale

Si vous clonez ce projet pour la première fois, le dossier `venv` et le fichier `.env` ne sont pas inclus (sécurité Git). Voici comment configurer l'environnement :

1. **Cloner le dépôt :**
```bash
git clone https://github.com/VOTRE_UTILISATEUR/veille-techno-1SH.git
cd veille-techno-1SH
```

2. **Créer et activer un nouvel environnement virtuel :**
```bash
# Création
python -m venv venv

# Activation (Windows)
venv\Scripts\activate
# Activation (Mac/Linux)
source venv/bin/activate
```

3. **Installer les dépendances requises :**
```bash
pip install -r src/requirements.txt
```

4. **Configurer la clé API :**
* Créez un fichier nommé `.env` dans le dossier `src/`.
* Ajoutez-y votre clé Google Gemini Pro :
```text
GEMINI_API_KEY=votre_cle_api_ici
```

---

## 📖 Utilisation de la documentation (MkDocs)

Pour visualiser cette documentation sous forme de site web local :

```bash
# Lancer le serveur de documentation
mkdocs serve
```
La documentation sera accessible sur `http://127.0.0.1:8000`.

---

## 🚀 Démarrage rapide (Serveur API local)

Voici les commandes pour lancer l'API TicketFlow en environnement de développement local :

```bash
# 1. Activer l'environnement virtuel
# Sur Windows :
src\venv\Scripts\activate
# Sur Mac/Linux :
source src/venv/bin/activate

# 2. Lancer l'API
cd src
python app.py
```

Le serveur sera accessible à l'adresse `http://127.0.0.1:5000`.

L'interface technicien est disponible ici :

```text
http://127.0.0.1:5000/dashboard
```

La route racine `/` redirige automatiquement vers ce tableau de bord.
Le formulaire web consomme l'API interne `POST /api/v1/triage`, ce qui permet de garder une seule logique de triage pour les clients REST et pour l'interface.
