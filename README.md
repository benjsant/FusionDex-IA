## 🧬 Description complète du projet

FusionAI Dex est un Pokédex intelligent conçu pour le jeu Pokémon Infinite Fusion.

Le projet vise à centraliser, structurer et exploiter les données du jeu à travers une architecture complète allant de la collecte des données jusqu’à leur utilisation via une interface et une API.

### 🔄 Pipeline de données (ETL)

Le projet repose sur un pipeline ETL qui :

- extrait les données depuis les fichiers du jeu (ou sources externes)
- transforme ces données en un format structuré et exploitable
- les charge dans une base de données PostgreSQL

Ce pipeline permet d’automatiser la mise à jour et la cohérence des données.

---

### 🗄️ Base de données

Les données sont stockées dans PostgreSQL, avec une structure permettant :

- de représenter les Pokémon (stats, types, etc.)
- d’associer les sprites
- d’évoluer vers des données plus complexes (fusions, capacités, localisation, etc.)

---

### 🌐 API Backend

Une API développée avec FastAPI permet :

- d’accéder aux données des Pokémon
- d’effectuer des recherches
- de filtrer selon différents critères
- de servir les données au frontend ou à d’autres services

---

### 🖥️ Interface Web

Une interface construite avec Next.js permet :

- d’explorer les Pokémon
- de consulter leurs statistiques
- d’effectuer des recherches simples
- d’interagir avec les données via l’API

---

### 🧬 Gestion des sprites

Le projet intègre les sprites directement depuis les fichiers du jeu :

- sprites des Pokémon
- potentiellement sprites des fusions
- affichage dynamique dans l’interface

---

### 🤖 Recherche assistée par IA (optionnel)

Une couche IA peut être ajoutée pour :

- interpréter des requêtes en langage naturel
- traduire ces requêtes en filtres ou requêtes SQL
- améliorer l’exploration des données

Exemple :
"Pokémon rapide de type feu"

---

### 🔄 Orchestration et automatisation (évolution)

Le projet peut évoluer avec :

- Prefect pour orchestrer les pipelines ETL
- n8n pour automatiser certaines tâches (notifications, mises à jour)

---

### 📈 Évolutions prévues

Le projet est conçu pour évoluer progressivement :

- ajout des fusions Pokémon
- intégration des capacités (movepool)
- ajout de données de localisation
- gestion des mises à jour du jeu
- amélioration de l’interface utilisateur

---

### 🎯 Objectif global

FusionAI Dex a pour objectif de démontrer la capacité à concevoir un projet complet incluant :

- ingestion et traitement de données
- modélisation de base de données
- développement backend
- création d’API
- développement frontend
- intégration d’IA

Le tout dans un contexte concret et évolutif.