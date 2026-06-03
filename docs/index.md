# Bienvenue sur la documentation de TicketFlow

## Automatisation du triage des incidents informatiques via une API Flask et l'IA

Ce projet est réalisé dans le cadre du cours de **Veille technologique (420-1SH-SW)**.

L'objectif est de concevoir un système capable de qualifier et prioriser les demandes techniques (billets ITSM) sans intervention humaine, en utilisant l'intelligence artificielle, un moteur RAG local, une API Flask et une interface web complète avec des portails distincts pour les demandeurs et les techniciens.

### Structure de la documentation

* **[Structure du Projet](structure.md)** : Rôle et emplacement de chaque fichier et dossier de l'application.
* **[Recherche](recherche.md)** : Documentation des sources, technologies explorées et concepts clés (RAG, API REST).
* **[Architecture RAG](architecture_rag.md)** : Fonctionnement du moteur de recherche sémantique et du cache d'embeddings.
* **[Architecture des données](database.md)** : Modèles SQLite, relations SQLAlchemy et migrations atomiques.
* **[Interface Web](interface_web.md)** : Landing page, portail demandeur simplifié, dashboard technicien, templates Jinja2, Bootstrap 5 et requêtes asynchrones.
* **[Guide Technique](basics.md)** : Instructions pour l'installation et le démarrage du projet.

### Objectifs du projet

* **Apprentissage technique** : Maîtriser Python et Flask.
* **Automatisation du triage** : Réduire le temps de traitement manuel.
* **Analyse de priorité** : Utiliser l'IA pour détecter l'urgence.
* **Interopérabilité** : Produire une API JSON structurée, maintenant consommée par le tableau de bord interne `/dashboard`.

---
*Réalisé par Gabriel Racine*
