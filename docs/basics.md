# 🎟️ TicketFlow : Automatisation ITSM via IA

**Projet de Veille technologique (420-1SH-SW)** **Réalisé par :** Gabriel Racine  

Ce dépôt fait office de base de connaissances et de code source pour le développement d'une API de triage intelligent automatisant la classification des incidents informatiques.

---

# 📚 Base de connaissances

Voici les liens vers la documentation du projet :

* 🔗 **[Suivi 01 : Document des liens et cahier de recherche](../travaux/suivi_01_liens.md)**
* 🧠 **[Carte mentale de l'architecture du projet](../assets/mindmap.pdf)** *(À adapter selon le nom et l'emplacement exact du fichier)*

---

## 🛠️ Installation initiale

Si vous clonez ce projet pour la première fois, le dossier `venv` et le fichier `.env` ne sont pas inclus (sécurité Git). Voici comment configurer l'environnement :

1. **Cloner le dépôt et se déplacer dans le dossier source :**
```bash
   git clone [https://github.com/VOTRE_UTILISATEUR/veille-techno-1SH.git](https://github.com/VOTRE_UTILISATEUR/veille-techno-1SH.git)
   cd veille-techno-1SH/src
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

3. Installer les dépendances requises :
```bash
pip install -r requirements.txt
```

4. Configurer la clé API :
* Créez un fichier nommé .env dans le dossier src/.
* Ajoutez-y votre clé Google Gemini Pro :
```text
GEMINI_API_KEY=votre_cle_api_ici
```

Une fois cette configuration initiale terminée, vous pouvez utiliser les commandes de la section **Démarrage rapide** ci-dessous pour lancer l'API.

## 🚀 Démarrage rapide (Serveur local)

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

Le serveur sera accessible à l'adresse http://127.0.0.1:5000
