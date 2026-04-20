# Proposition formelle : Veille technologique (420-1SH-SW)

**Titre du projet** : Automatisation du triage des incidents informatiques via une API Flask et l'IA  
**Date de remise** : 19 avril 2026  
**Réalisé par** : Gabriel Racine  

---

# Introduction

Dans le cadre de mon cheminement en informatique et de mon expérience en soutien aux 
opérations, j'ai constaté que la gestion manuelle du volume de billets peut rapidement devenir un frein à l'efficacité. 
L'identification de la nature d'un incident et son 
niveau d'urgence sont des étapes critiques pour le respect des ententes de niveau de 
service (SLA) dans tout centre de services.

Ce projet vise à explorer comment l'intelligence artificielle peut transformer le rôle 
de technicien en automatisant le triage initial. Mon objectif est de concevoir un système 
capable de qualifier et prioriser les demandes techniques sans intervention humaine, 
permettant ainsi aux équipes de se concentrer sur la résolution plutôt que sur 
l'administration d'un système de billetterie.

---

# Prérecherche

Avant de fixer mon choix, j'ai exploré plusieurs avenues pour lier l'IA à mon futur 
domaine professionnel :

| Sujet exploré | Résumé | Faisabilité | Intérêt personnel | Pourquoi rejeté ? |
| :--- | :--- | :--- | :--- | :--- |
| **Console rétro ESP32 via SDD (Volet 1)** | Utiliser un outil comme SpecKit pour générer l'architecture et le code d'un clone de console bas niveau sur un microcontrôleur ESP32. | Faible – contraintes matérielles et débogage bas niveau trop risqués pour 7 jours. | Le matériel embarqué m'intéresse, mais le projet s'éloigne de mon domaine cible. | Trop risqué pour le délai strict. |
| **Analyse de modèles d'IA (Volet 2)** | Mettre en place un serveur IA local pour héberger et comparer les architectures. | Moyenne – sujet vaste, difficile à délimiter en MVP concret. | Fascinant sur le plan de la recherche, mais je préfère un résultat tangible. | Manque de concret pour le temps donné. |
| **Triage IA (Choix final)** | **Création d'une API Flask pour classifier et prioriser les billets de support.** | **Élevée – périmètre clair et technologies accessibles.** | **Combine un défi technique motivant avec une application directe en support informatique.** | **Choix retenu.** |

### Choix du projet et justification

J'ai choisi de développer une solution de triage automatisé pour un système de 
billetterie générique (ITSM*). Ce projet représente un réel défi d'apprentissage : 
bien que j'ai de l'expérience avec Ruby on Rails et Angular pour le développement web, 
je n'ai jamais utilisé **Python** ni le micro-framework **Flask**. Sortir de ma zone 
de confort en apprenant un nouvel écosystème tout en répondant à un besoin concret 
en support technique constitue pour moi une expérience de veille technologique idéale.

*ITSM (IT Service Management) : La gestion des services informatiques est la pratique 
consistant à planifier, mettre en œuvre, gérer et optimiser l'accompagnement de bout en 
bout de services informatiques afin de répondre aux besoins des utilisateurs et aux 
objectifs commerciaux.

---

# Objectifs

Le but de ce projet est de mettre en place une API capable de traiter des données de 
billetterie brutes. Mes objectifs spécifiques sont :

* **Apprentissage technique** : Maîtriser les bases du langage Python et du framework 
  Flask pour créer une API fonctionnelle.
* **Automatisation du triage** : Réduire le temps de traitement manuel nécessaire à 
  la catégorisation d'un billet.
* **Analyse de priorité** : Utiliser l'IA pour détecter les contextes d'urgence et 
  assigner une priorité adéquate.
* **Interopérabilité** : Produire un système capable de recevoir des requêtes JSON et 
  de retourner des données structurées.

---

# MVP (Minimum Viable Product)

Le MVP est considéré atteint lorsque les éléments suivants fonctionnent :

- **Un endpoint `/triage`** qui accepte une requête POST avec un champ `description` en JSON
- **Une réponse structurée** contenant au minimum une `catégorie` et une `priorité`
- **L'intégration à l'API Gemini** est fonctionnelle et retourne des résultats cohérents
- **Le serveur Flask démarre localement** sans erreur et répond aux requêtes via curl ou Postman

Tout ce qui dépasse ces quatre points (interface, logs, métriques, endpoints supplémentaires) 
est considéré comme hors-portée du MVP.

---

# Méthodologie

Le développement sera organisé en phases intensives pour respecter le délai de 7 jours :

**Jour 1-2 : Apprentissage et Environnement**
* Installation de Python et configuration d'un environnement virtuel (`venv`).
* Apprentissage de la syntaxe de base et mise en place d'un serveur "Hello World" avec Flask.
* Préparation d'un ensemble de données de test simulant des requêtes d'utilisateurs.

**Jour 3-4 : Développement de l'API et Intégration IA**
* Création des routes (endpoints) Flask pour recevoir les billets.
* Configuration de la communication avec l'API Google Gemini Pro.
* Ingénierie du *prompt* pour garantir des réponses structurées.

**Jour 5 : Traitement des données et Logique de triage**
* Développement de la logique permettant d'extraire la catégorie et la priorité.
* Formatage de la réponse JSON retournée par l'API.

**Jour 6 : Tests et Optimisation**
* Tests de performance avec plusieurs types d'incidents (Matériel, Logiciel, Réseau, Accès).
* Ajustements des paramètres du modèle pour améliorer la précision.

**Jour 7 : Documentation et Rapport final**
* Rédaction du fichier `README.md` et finalisation du rapport final.

---

# Outils et technologies

* **Langage de programmation** : Python.
* **Framework Web** : Flask (Nouvelle technologie explorée).
* **Intelligence Artificielle** : API Google Gemini Pro (via Google AI Studio / Google Gen AI Python SDK).
* **Logiciel cible** : Simulation de données d'un centre de services (ITSM).
* **Gestion de versions** : Git et GitHub.

---

# Résultats attendus

- **API fonctionnelle** : Un endpoint `/triage` capable de recevoir un billet en texte 
  libre (JSON) et de retourner une catégorie (ex. : Matériel, Logiciel, Réseau, Accès) 
  ainsi qu'un niveau de priorité (Faible, Moyen, Élevé, Critique).

- **Validation par jeu de test** : Le système sera évalué sur un ensemble d'au moins 
  20 billets simulés couvrant les quatre catégories. Le projet sera considéré réussi 
  si le taux de classification correcte atteint 80 % selon une validation humaine.

- **Démonstration fonctionnelle** : Une série de requêtes exécutées via un client REST 
  (ex. : Postman ou curl) illustrant le comportement du système face à des cas variés, 
  incluant des cas limites ou ambigus.

---

# Annexe - Utilisation de l'IA

Je déclare avoir utilisé l'IA Gemini pour m'aider à structurer ma pensée, comparer mes 
idées de projet et formuler cette proposition.

**Liste des prompts utilisés :**
```text
1. Aide-moi à explorer des idées de projet de veille techno pour le volet support informatique et IA.
2. Aide-moi à structurer la section MVP pour un projet de triage automatisé de billets de support.
3. Quelles technologies Python devrais-je utiliser pour sortir de ma zone de confort (Ruby/Angular) ?
4. Peux-tu reformuler ma méthodologie pour un projet Flask sur 7 jours ?
5. Intègre Flask dans ma proposition formelle.
6. Crée un tableau de prérecherche comparant mes 3 idées de projets.
7. Ajuste le document pour qu'il soit plus généraliste et qu'il ne fasse pas référence à un 
   logiciel spécifique, en utilisant plutôt des termes comme centre de services ou ITSM.
```
