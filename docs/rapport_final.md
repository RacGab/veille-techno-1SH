---
title: Rapport Final
---

<div align="center" style="margin-top: 40px; margin-bottom: 60px;">

  <h2><strong>Veille technologique</strong></h2>
  <h3><strong>420-1SH-SW</strong></h3>

  <br><br><br><br>

  <h2>TicketFlow : Automatisation du triage des incidents informatiques</h2>

  <br><br><br><br>

  <p><strong>Présenté à :</strong><br>
  Nicolas Bourré</p>

  <br><br>

  <p><strong>Réalisé par :</strong><br>
  Gabriel Racine</p>

  <br><br><br><br>

  <p><strong>Date de remise :</strong><br>
  5 juin 2026</p>

</div>

<div style="page-break-after: always;"></div>

---

### 1. Contexte et Problématique
Dans les environnements informatiques modernes, les centres de services (ITSM) font face à un volume écrasant de requêtes. Chaque jour, les techniciens doivent lire, catégoriser et prioriser manuellement des centaines de billets. Ce processus de triage prend beaucoup de temps, retarde la résolution des incidents critiques et augmente considérablement le risque d'erreur humaine en période de forte affluence. Le triage manuel est devenu un goulot d'étranglement inacceptable pour la productivité des équipes de support.

### 2. La Solution : TicketFlow
TicketFlow est un système ITSM de bout en bout conçu pour réduire à zéro le temps de triage manuel. En exploitant l'intelligence artificielle générative (Gemini 2.5 Flash), le système automatise la classification (catégorie) et la priorisation des incidents dès leur soumission par l'utilisateur, permettant ainsi aux techniciens de se concentrer immédiatement sur la résolution des problèmes plutôt que sur leur assignation.

### 3. Architecture Technique et RAG
L'application est propulsée par une API REST robuste développée en Python avec **Flask 3.1**. L'innovation majeure de TicketFlow réside dans l'intégration d'un moteur **RAG (Retrieval-Augmented Generation)**. 
Pour éviter les "hallucinations" inhérentes aux modèles d'IA, chaque billet soumis est d'abord comparé à une base de connaissances de procédures internes. Le système propose deux moteurs RAG basculables en temps réel :

*   **TicketRAGBasic** : Un moteur en mémoire utilisant la similarité cosinus (NumPy) pour les environnements légers.

*   **TicketRAGChroma** : Un moteur persistant sur disque utilisant **ChromaDB**, conçu pour la scalabilité et la gestion de gros volumes documentaires.

Le prompt envoyé à l'IA est ainsi enrichi par le contexte d'entreprise réel, garantissant un triage précis, pertinent et justifié par une documentation interne.

### 4. Résilience et Haute Disponibilité
Un système d'entreprise ne peut se permettre d'être hors ligne. Pour palier aux instabilités potentielles des services cloud, TicketFlow intègre une **cascade de fallback à trois niveaux** garantissant 100 % de disponibilité :

1.  **Gemini 2.5 Flash** : Moteur principal, fournissant une sortie JSON structurée via Pydantic.

2.  **Groq / Llama 3** : IA de secours qui prend le relais automatiquement en cas d'erreur de quota (HTTP 429) ou d'indisponibilité de l'API Google.
   
3.  **Algorithme par mots-clés** : Triage local pur, sans aucune dépendance réseau, qui s'active en dernier recours si les deux API externes échouent.

### 5. Interface Utilisateur
Développée avec Bootstrap 5 et Jinja2, l'interface web est conçue pour éliminer toute friction. Elle se divise en trois portails distincts : 

*   **Landing page** : Un point d'entrée unique et visuel.
  
*   **Portail demandeur** : Une interface ultra-simplifiée permettant la soumission rapide d'un problème sans jargon technique.
  
*   **Dashboard technicien** : Un tableau de bord avancé offrant aux équipes ITSM le contrôle total sur les modèles d'IA, les moteurs RAG, et la visualisation des résultats stockés de manière atomique dans la base de données **SQLite**.


### 6. Conclusion
TicketFlow démontre avec succès qu'il est possible d'intégrer des technologies d'intelligence artificielle de pointe (LLM, RAG, bases vectorielles) au sein d'une architecture web classique (Flask/SQLite). Ce projet résout un problème d'affaires concret et prouve que l'automatisation par l'IA, lorsqu'elle est architecturée avec des mécanismes de résilience et de RAG, offre la fiabilité technique et opérationnelle exigée par le milieu corporatif.