# Proposition formelle : Veille technologique (420-1SH-SW)

**Titre du projet** : Automatisation du triage des incidents informatiques via une API Flask et l'IA  
**Date de remise** : 19 avril 2026  
**Étudiant** : Gabriel Racine  
**Cours** : Veille technologique (420-1SH-SW) - Cégep de Shawinigan  

---

# Introduction

Dans le cadre de mon cheminement en informatique et de mon expérience en soutien aux opérations, j'ai constaté que la gestion manuelle du volume de billets peut rapidement devenir un goulot d'étranglement. L'identification de la nature d'un incident et son niveau d'urgence sont des étapes critiques pour le respect des ententes de niveau de service (SLA) dans tout centre de services.

Ce projet vise à explorer comment l'intelligence artificielle peut transformer le rôle de technicien en automatisant le triage initial. Mon objectif est de concevoir un système capable de qualifier et prioriser les demandes techniques sans intervention humaine, permettant ainsi aux équipes de se concentrer sur la résolution plutôt que sur l'administration d'un système de billetterie.

---

# Prérecherche

Avant de fixer mon choix, j'ai exploré plusieurs avenues pour lier l'IA à mon futur domaine professionnel :

| Sujet exploré | Résumé | Pourquoi rejeté ? |
| :--- | :--- | :--- |
| **SDD avec SpecKit** | Générer une architecture complète (Rails/Angular) via des spécifications. | Trop proche de mes acquis actuels en développement web. |
| **Analyse de contexte LLM** | Tester la mémoire des modèles locaux face à de longues documentations. | Risque de dépassement du délai de 7 jours pour les tests matériels. |
| **Générateur de tests IA** | Automatiser la création de tests unitaires pour des applications existantes. | Moins pertinent pour mon intérêt marqué envers le support informatique. |
| **Triage IA (Choix final)** | **Création d'une API Flask pour classifier et prioriser les billets de support.** | **Défi technique motivant (Python) et application directe à mon milieu de travail.** |

### Choix du projet et justification
J'ai choisi de développer une solution de triage automatisé pour un système de billetterie générique (ITSM*). Ce projet représente un réel défi d'apprentissage : bien que je sois à l'aise avec Ruby on Rails et Angular pour le développement web, je n'ai jamais utilisé **Python** ni le micro-framework **Flask**. Sortir de ma zone de confort en apprenant un nouvel écosystème tout en répondant à un besoin concret en support technique constitue pour moi une expérience de veille technologique idéale.

*ITSM (IT Service Management) : La gestion des services informatiques est la pratique consistant à planifier, mettre en œuvre, gérer et optimiser la fourniture de bout en bout de services informatiques afin de répondre aux besoins des utilisateurs et aux objectifs commerciaux.

---

# Objectifs

Le but de ce projet est de mettre en place une API capable de traiter des données de billetterie brutes. Mes objectifs spécifiques sont :

* **Apprentissage technique** : Maîtriser les bases du langage Python et du framework Flask pour créer une API fonctionnelle.
* **Automatisation du triage** : Réduire le temps de traitement manuel nécessaire à la catégorisation d'un billet.
* **Analyse de priorité** : Utiliser l'IA pour détecter les contextes d'urgence et assigner une priorité adéquate.
* **Interopérabilité** : Produire un système capable de recevoir des requêtes JSON et de retourner des données structurées.

---

# Plan de réalisation (7 jours)

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
* Rédaction du fichier `README.md` et finalisation du rapport de veille.

---

# Outils et technologies

* **Langage de programmation** : Python (Nouvelle technologie explorée).
* **Framework Web** : Flask.
* **Intelligence Artificielle** : API Google Gemini Pro (via Google AI Studio).
* **Logiciel cible** : Simulation de données d'un centre de services (ITSM).
* **Gestion de versions** : Git et GitHub.

---

# Résultats attendus

* **API Fonctionnelle** : Un endpoint capable de recevoir un texte de billet et de retourner une classification instantanée.
* **Taux de précision** : Le système doit classifier correctement au moins 80 % des billets de test selon une validation humaine.
* **Code Propre** : Utilisation des standards Python (PEP 8) et documentation claire pour l'installation des dépendances.

---

# Conclusion

Ce projet est une opportunité de combiner mon intérêt pour le support technique et mon désir d'évoluer vers des outils de développement modernes. Apprendre Python et Flask à travers ce cas d'usage concret me permettra d'élargir mes compétences de manière significative.

---

# Annexe - Utilisation de l'IA

Je déclare avoir utilisé l'IA Gemini pour m'aider à structurer ma pensée, comparer mes idées de projet et formuler cette proposition.

**Liste des prompts utilisés :**
```text
1. Aide-moi à explorer des idées de projet de veille techno pour le volet support informatique et IA.
2. Aide-moi à structurer la section MVP pour un projet de triage automatisé de billets de support.
3. Quelles technologies Python devrais-je utiliser pour sortir de ma zone de confort (Ruby/Angular) ?
4. Peux-tu reformuler ma méthodologie pour un projet Flask sur 7 jours ?
5. Intègre Flask dans ma proposition formelle.
6. Crée un tableau de prérecherche comparant mes 4 idées de projets.
7. Ajuste le document pour qu'il soit plus généraliste et qu'il ne fasse pas référence à un logiciel spécifique, en utilisant plutôt des termes comme centre de services ou ITSM.
